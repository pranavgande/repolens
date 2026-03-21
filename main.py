# main.py

"""
M3 Dependency Analysis Pipeline — full end-to-end runner.

Run with:  python main.py

This file serves two purposes simultaneously. When run directly
(python main.py), it acts as a standalone test runner against the
mock repository. When imported by api.py, it exposes run_m3_pipeline()
as a callable function that the FastAPI endpoints use.

The key design change from the original version is that run_m3_pipeline()
now accepts optional pre-built graph and graph_stats arguments. This
matters because the combined /analyse endpoint in api.py builds the graph
once and shares it across M1, M2, and M3. Without this change, M3 would
rebuild the graph from scratch internally — wasting the work already done.
With this change, M3 simply uses whatever it receives, and falls back to
building its own graph only when running in standalone mode.
"""

import json
import networkx as nx
from graph.builder import build_dependency_graph
from graph.analyzer import analyze_graph
from serializer.graph_serializer import to_llm_text, to_react_flow_json


def run_m3_pipeline(
    file_contents: dict[str, bytes],
    graph: nx.DiGraph | None = None,
    graph_stats: dict | None = None,
) -> dict:
    """
    The complete M3 pipeline. Returns a dict with everything the
    frontend and LLM need — the React Flow graph data, the compressed
    LLM context string, and the graph statistics.

    Parameters:
        file_contents: the {filepath: bytes} dict from the GitHub fetcher
                       or mock data. Always required.
        graph:         an already-built networkx DiGraph. When provided by
                       the combined endpoint, M3 skips Phase 1 entirely.
                       When None (standalone mode), M3 builds it itself.
        graph_stats:   the already-computed stats dict from analyze_graph().
                       Same logic — skipped if provided, computed if None.

    The optional parameters exist purely for efficiency in the combined
    endpoint. The function's output is identical regardless of whether
    the graph was passed in or built internally — the caller never needs
    to know which path was taken.
    """

    # ── Phase 1: Build the dependency graph ───────────────────────────────────
    # This is the most expensive phase — tree-sitter parses every supported
    # file, the resolver normalises relative imports, and networkx assembles
    # the directed graph. We skip it entirely if a pre-built graph was passed
    # in, which is what the combined /analyse endpoint does.
    print("\n" + "=" * 60)
    print("PHASE 1: Building dependency graph")
    print("=" * 60)

    if graph is None:
        # Standalone mode — build the graph from the raw file contents
        graph = build_dependency_graph(file_contents)
        print(f"\nGraph built: {graph.number_of_nodes()} nodes, "
              f"{graph.number_of_edges()} edges")
    else:
        # Combined endpoint mode — graph was pre-built upstream, reuse it
        print(f"\nUsing pre-built graph: {graph.number_of_nodes()} nodes, "
              f"{graph.number_of_edges()} edges (skipped rebuild)")

    # ── Phase 2: Analyse the graph ────────────────────────────────────────────
    # Pure graph mathematics — in-degrees, cycles, clusters, critical files.
    # Again, skip if the combined endpoint already did this work.
    print("\n" + "=" * 60)
    print("PHASE 2: Analysing graph structure")
    print("=" * 60)

    if graph_stats is None:
        graph_stats = analyze_graph(graph)
        print(f"\nCritical files (by in-degree):")
        for filepath, degree in graph_stats["critical_files"]:
            print(f"  {filepath}  ← imported by {degree} file(s)")
        print(f"\nEntry point candidates (in-degree = 0):")
        for fp in graph_stats["entry_candidates"]:
            print(f"  {fp}")
        if graph_stats["cycles"]:
            print(f"\nCircular dependencies detected: {len(graph_stats['cycles'])}")
        else:
            print(f"\nNo circular dependencies — clean architecture ✓")
    else:
        print(f"\nUsing pre-computed stats: {graph_stats['total_files']} files, "
              f"{graph_stats['total_edges']} edges (skipped analysis)")

    # ── Phase 3: Serialise for the LLM ────────────────────────────────────────
    # Converts the graph into a compact, human-readable text summary.
    # A 40,000-line repo becomes roughly 1,000-2,000 characters here —
    # that's the compression that makes LLM reasoning fast and accurate.
    print("\n" + "=" * 60)
    print("PHASE 3: Serialising for LLM")
    print("=" * 60)
    llm_text = to_llm_text(graph, graph_stats)
    print(llm_text)

    # ── Phase 4: Generate React Flow JSON ─────────────────────────────────────
    # Converts the graph into the node/edge format that React Flow expects.
    # Nodes arrive pre-styled (colour-coded by folder, bordered if critical)
    # so the frontend renders them correctly with zero additional logic.
    print("\n" + "=" * 60)
    print("PHASE 4: Generating React Flow JSON")
    print("=" * 60)
    react_flow_data = to_react_flow_json(graph, graph_stats)
    print(f"Nodes: {len(react_flow_data['nodes'])}")
    print(f"Edges: {len(react_flow_data['edges'])}")

    if react_flow_data["nodes"]:
        print("\nSample node:")
        print(json.dumps(react_flow_data["nodes"][0], indent=2))
    if react_flow_data["edges"]:
        print("\nSample edge:")
        print(json.dumps(react_flow_data["edges"][0], indent=2))

    return {
        "llm_context":     llm_text,
        "graph_stats":     graph_stats,
        "react_flow_data": react_flow_data,
    }


# ── Standalone runner ─────────────────────────────────────────────────────────
# This block only executes when you run `python main.py` directly.
# It is completely ignored when api.py imports run_m3_pipeline as a function.
# The if __name__ == "__main__" guard is what creates that separation.

if __name__ == "__main__":
    from mock_data.mock_repo import MOCK_REPO_FILES

    print("Running M3 pipeline on mock repository...")
    print(f"Files in mock repo: {list(MOCK_REPO_FILES.keys())}")

    # In standalone mode, no pre-built graph is passed — M3 builds its own.
    # This is equivalent to what happens when /analyse/m3 is called directly.
    result = run_m3_pipeline(MOCK_REPO_FILES)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"LLM context size    : {len(result['llm_context'])} characters")
    print(f"React Flow nodes    : {len(result['react_flow_data']['nodes'])}")
    print(f"React Flow edges    : {len(result['react_flow_data']['edges'])}")
    print("\nThis output is now ready to be:")
    print("  1. Sent to Claude/Gemini API for natural language explanation")
    print("  2. Sent to the Next.js frontend for React Flow visualisation")