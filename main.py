# main.py

"""
M3 Dependency Analysis Pipeline — full end-to-end runner.

Run with:  python main.py

This simulates the full pipeline that your FastAPI endpoint would run
when it receives a GitHub URL. The only difference in production is
that file_contents comes from the GitHub API instead of MOCK_REPO_FILES.
"""

import json
from mock_data.mock_repo import MOCK_REPO_FILES
from graph.builder import build_dependency_graph
from graph.analyzer import analyze_graph
from serializer.graph_serializer import to_llm_text, to_react_flow_json


def run_m3_pipeline(file_contents: dict[str, bytes]) -> dict:
    """
    The complete M3 pipeline. Returns a dict with everything the
    frontend and LLM need.

    In your FastAPI endpoint, this function's return value gets
    serialised and streamed back to the Next.js frontend.
    """

    print("\n" + "=" * 60)
    print("PHASE 1: Building dependency graph")
    print("=" * 60)
    graph = build_dependency_graph(file_contents)
    print(f"\nGraph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    print("\n" + "=" * 60)
    print("PHASE 2: Analysing graph structure")
    print("=" * 60)
    stats = analyze_graph(graph)

    print(f"\nCritical files (by in-degree):")
    for filepath, degree in stats["critical_files"]:
        print(f"  {filepath}  ← imported by {degree} file(s)")

    print(f"\nEntry point candidates (in-degree = 0):")
    for fp in stats["entry_candidates"]:
        print(f"  {fp}")

    if stats["cycles"]:
        print(f"\nCircular dependencies detected: {len(stats['cycles'])}")
    else:
        print(f"\nNo circular dependencies — clean architecture ✓")

    print("\n" + "=" * 60)
    print("PHASE 3: Serialising for LLM")
    print("=" * 60)
    llm_text = to_llm_text(graph, stats)
    print(llm_text)

    print("\n" + "=" * 60)
    print("PHASE 4: Generating React Flow JSON")
    print("=" * 60)
    react_flow_data = to_react_flow_json(graph, stats)
    print(f"Nodes: {len(react_flow_data['nodes'])}")
    print(f"Edges: {len(react_flow_data['edges'])}")

    # Pretty-print a sample to verify structure
    print("\nSample node:")
    print(json.dumps(react_flow_data["nodes"][0], indent=2))
    print("\nSample edge:")
    print(json.dumps(react_flow_data["edges"][0], indent=2))

    return {
        "llm_context": llm_text,
        "graph_stats": stats,
        "react_flow_data": react_flow_data,
    }


if __name__ == "__main__":
    print("Running M3 pipeline on mock repository...")
    print(f"Files in mock repo: {list(MOCK_REPO_FILES.keys())}")

    result = run_m3_pipeline(MOCK_REPO_FILES)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"LLM context size: {len(result['llm_context'])} characters")
    print(f"React Flow nodes: {len(result['react_flow_data']['nodes'])}")
    print(f"React Flow edges: {len(result['react_flow_data']['edges'])}")
    print("\nThis output is now ready to be:")
    print("  1. Sent to Claude/Gemini API for natural language explanation")
    print("  2. Sent to the Next.js frontend for React Flow visualisation")