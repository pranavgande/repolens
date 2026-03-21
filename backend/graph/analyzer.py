# graph/analyzer.py

from pathlib import Path
import networkx as nx


def analyze_graph(graph: nx.DiGraph) -> dict:
    """
    Compute structural insights from the dependency graph.

    Everything this function returns is 100% deterministic — the same graph
    always produces the same output. We deliberately do NOT call the LLM
    here. The LLM's job is to *explain* these facts in plain English,
    not to *compute* them.

    Key concepts:

    In-degree of a node:  how many other files import THIS file.
                          High in-degree = this file is a shared dependency.
                          Example: user.model.js is imported by both auth.service
                          and user.service, so it has in-degree 2.

    Out-degree of a node: how many files THIS file imports.
                          High out-degree = this file orchestrates many others.
                          Example: server.js imports routes, config, middleware.

    Strongly Connected Component: a group of files that all import each other
                          (directly or indirectly). If A→B→C→A exists, they form
                          a cycle — a circular dependency, which is a code smell.
    """

    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())

    # ── Critical files (Bonus B1) ─────────────────────────────────────
    # Sort by in-degree descending — files imported by the most other files
    # are the most critical (removing them would break the most things).
    critical_files = sorted(
        [(node, deg) for node, deg in in_degrees.items() if deg > 0],
        key=lambda x: x[1],
        reverse=True
    )

    # ── Entry point candidates ────────────────────────────────────────
    # Files with in-degree 0 are not imported by anyone — they're "roots"
    # of the dependency tree. The real entry point is among these.
    # We further filter to files with out-degree > 0 to exclude true
    # isolates (files that import nothing and are imported by nothing).
    entry_candidates = [
        node for node in graph.nodes
        if in_degrees.get(node, 0) == 0 and out_degrees.get(node, 0) > 0
    ]

    # ── Circular dependencies ─────────────────────────────────────────
    # A cycle like A→B→C→A means these modules can't be cleanly separated.
    # nx.simple_cycles returns all elementary cycles in the graph.
    # For large graphs this can be slow, so we cap it at 10 cycles.
    all_cycles = list(nx.simple_cycles(graph))
    cycles = all_cycles[:10]

    # ── Architectural clusters ────────────────────────────────────────
    # Group files by their directory — this reveals the layered structure.
    # A file at "controllers/auth.controller.js" belongs to the "controllers" cluster.
    clusters: dict[str, list[str]] = {}
    for node in graph.nodes:
        folder = str(Path(node).parent)
        clusters.setdefault(folder, []).append(Path(node).name)

    # ── Leaf nodes ───────────────────────────────────────────────────
    # Files that import nothing themselves (out-degree 0) but are imported
    # by others. These are typically data models or pure utility functions.
    leaf_nodes = [
        node for node in graph.nodes
        if out_degrees.get(node, 0) == 0 and in_degrees.get(node, 0) > 0
    ]

    return {
        "total_files": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "critical_files": critical_files,  # list of (filepath, in_degree)
        "entry_candidates": entry_candidates,  # list of filepaths
        "cycles": cycles,  # list of cycle paths
        "clusters": clusters,  # dict of folder → [filenames]
        "leaf_nodes": leaf_nodes,  # list of filepaths (models, utils)
    }