# m2/m2_pipeline.py

"""
M2 Pipeline orchestrator — chains Phase 1 and Phase 3 together.

This file has one job: take the file_contents dict and the already-built
M3 dependency graph, run them through entry detection and flow explanation,
and return a single clean result dict that the FastAPI endpoint can send
back as JSON.

It deliberately contains no parsing logic, no LLM calls, and no graph
math. All of that lives in the phase files. This file only coordinates.
"""

import networkx as nx
from m2.entry_detector import detect_entry_point
from m2.flow_explainer import explain_flow


def run_m2_pipeline(
    file_contents: dict[str, bytes],
    graph: nx.DiGraph | None = None,
) -> dict:
    """
    Full M2 pipeline. Accepts the same file_contents dict that M3 uses,
    plus the optional dependency graph that M3 already built.

    Why accept the graph as an optional parameter rather than rebuilding it?
    Because in the real FastAPI endpoint, both M2 and M3 will run against
    the same repo. It would be wasteful to parse all the files twice and
    build the graph twice. So the endpoint builds the graph once, passes it
    to both pipelines, and each one uses it for what it needs.

    The graph is optional (defaults to None) so that M2 can also run
    completely standalone — useful for testing in isolation, or if someone
    calls /analyse/m2 without having run M3 first.
    """

    print("\n" + "=" * 60)
    print("M2 PHASE 1: Entry Point Detection")
    print("=" * 60)

    # If we have the M3 graph, extract its entry candidates directly.
    # These are nodes with in-degree 0 (nothing imports them) and
    # out-degree > 0 (they import other things) — exactly what M3's
    # analyzer already computed. We recompute it here from the raw graph
    # rather than passing the stats dict, keeping the interface simple.
    if graph is not None:
        in_degrees  = dict(graph.in_degree())
        out_degrees = dict(graph.out_degree())
        entry_candidates = [
            node for node in graph.nodes
            if in_degrees.get(node, 0) == 0 and out_degrees.get(node, 0) > 0
        ]
        print(f"  Using M3 graph — entry candidates: {entry_candidates}")
    else:
        # No graph provided — let the detector search all files using
        # filename and content heuristics alone, with no shortlist.
        entry_candidates = None
        print("  No graph provided — running full filename/content scan")

    # Phase 1: detect the entry point
    detection_result = detect_entry_point(file_contents, entry_candidates)

    entry_file = detection_result["entry_file"]
    language   = detection_result["language"]
    confidence = detection_result["confidence"]

    print(f"\n  Detected entry point : {entry_file}")
    print(f"  Language             : {language}")
    print(f"  Confidence           : {confidence}")

    # If no entry point was found at all, return early with a clear message
    # rather than letting the explainer crash on a None entry_file.
    if entry_file is None:
        return {
            "entry_file":       None,
            "language":         "unknown",
            "confidence":       "low",
            "first_level_deps": [],
            "explanation":      "Could not detect an entry point in this repository.",
        }

    print("\n" + "=" * 60)
    print("M2 PHASE 2: Resolving First-Level Dependencies")
    print("=" * 60)

    # Get the direct imports of the entry file from the graph.
    # graph.successors(node) returns all nodes that 'node' has an edge TO —
    # i.e., all files that the entry point directly imports.
    # If no graph is available, fall back to an empty list — the explainer
    # will still work, it just won't have dependency context in the prompt.
    if graph is not None and entry_file in graph:
        first_level_deps = list(graph.successors(entry_file))
        print(f"  First-level deps from graph: {first_level_deps}")
    else:
        first_level_deps = []
        print("  No graph available — first-level deps will be empty")

    print("\n" + "=" * 60)
    print("M2 PHASE 3: Execution Flow Explanation (LLM)")
    print("=" * 60)

    source_bytes = file_contents[entry_file]

    explanation_result = explain_flow(
        entry_file       = entry_file,
        source_bytes     = source_bytes,
        language         = language,
        first_level_deps = first_level_deps,
    )

    # Assemble the final result dict.
    # This is exactly what the FastAPI endpoint will serialise to JSON
    # and send back to the Next.js frontend.
    return {
        "entry_file":        entry_file,
        "language":          language,
        "confidence":        confidence,
        "manifest_declared": detection_result["manifest_declared"],
        "first_level_deps":  first_level_deps,
        "explanation":       explanation_result["explanation"],
    }


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from mock_data.mock_repo import MOCK_REPO_FILES
    from graph.builder import build_dependency_graph

    print("Running M2 pipeline on mock repository...")
    print(f"Files: {list(MOCK_REPO_FILES.keys())}")

    # Build the M3 graph first — exactly as the real endpoint would do —
    # so M2 can pull entry candidates and first-level deps from it.
    graph = build_dependency_graph(MOCK_REPO_FILES)
    print(f"Graph built: {graph.number_of_nodes()} nodes, "
          f"{graph.number_of_edges()} edges")

    result = run_m2_pipeline(MOCK_REPO_FILES, graph)

    print("\n" + "=" * 60)
    print("M2 PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Entry file   : {result['entry_file']}")
    print(f"Language     : {result['language']}")
    print(f"Confidence   : {result['confidence']}")
    print(f"Dependencies : {result['first_level_deps']}")
    print(f"\nExplanation:\n{result['explanation']}")