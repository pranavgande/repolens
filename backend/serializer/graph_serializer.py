# serializer/graph_serializer.py

from pathlib import Path
import json
import networkx as nx


def to_llm_text(graph: nx.DiGraph, stats: dict) -> str:
    """
    Serialise the graph into a compact, LLM-friendly text format.

    The goal is maximum information density with minimum token count.
    We use abbreviated file names (not full paths) where unambiguous,
    and group the adjacency list by directory to mirror the architecture.

    For a 40,000-line repo, this output is typically 500-2000 tokens,
    compared to hundreds of thousands of tokens for the full source code.
    That's a 100-200x compression ratio.
    """

    lines = []

    # ── Header summary ────────────────────────────────────────────────
    lines.append("=== CODEBASE DEPENDENCY ANALYSIS ===")
    lines.append(f"Files analysed: {stats['total_files']}")
    lines.append(f"Import edges found: {stats['total_edges']}")
    lines.append("")

    # ── Directory clusters ────────────────────────────────────────────
    lines.append("=== MODULE CLUSTERS (by directory) ===")
    for folder, files in stats["clusters"].items():
        folder_label = folder if folder != "." else "(root)"
        lines.append(f"  {folder_label}/: {', '.join(files)}")
    lines.append("")

    # ── Adjacency list ────────────────────────────────────────────────
    # Format: each file followed by its direct dependencies.
    # We sort by out-degree descending so the most "active" files appear first.
    lines.append("=== DEPENDENCY GRAPH (A → B means A imports B) ===")

    sorted_nodes = sorted(
        graph.nodes,
        key=lambda n: graph.out_degree(n),
        reverse=True
    )

    for node in sorted_nodes:
        successors = list(graph.successors(node))
        if successors:
            # Use just the filename for readability, but keep path for disambiguation
            node_label = Path(node).name
            dep_labels = [Path(s).name for s in successors]
            lines.append(f"  {node_label} → {', '.join(dep_labels)}")
        else:
            # Leaf node: show it but mark it as having no local dependencies
            node_label = Path(node).name
            lines.append(f"  {node_label} → (no local dependencies)")
    lines.append("")

    # ── Critical files ────────────────────────────────────────────────
    lines.append("=== MOST-IMPORTED FILES (critical dependencies) ===")
    for filepath, in_degree in stats["critical_files"][:5]:
        lines.append(f"  {Path(filepath).name} (imported by {in_degree} file(s))")
    lines.append("")

    # ── Entry candidates ──────────────────────────────────────────────
    lines.append("=== LIKELY ENTRY POINTS (nothing imports these) ===")
    for filepath in stats["entry_candidates"]:
        lines.append(f"  {filepath}")
    lines.append("")

    # ── Circular dependencies ─────────────────────────────────────────
    if stats["cycles"]:
        lines.append("=== CIRCULAR DEPENDENCIES DETECTED ===")
        for cycle in stats["cycles"]:
            cycle_names = [Path(f).name for f in cycle]
            lines.append(f"  {' → '.join(cycle_names)} → {cycle_names[0]}")
    else:
        lines.append("=== NO CIRCULAR DEPENDENCIES DETECTED ===")

    return "\n".join(lines)


def to_react_flow_json(graph: nx.DiGraph, stats: dict) -> dict:
    """
    Serialise the graph as React Flow-compatible nodes and edges.

    React Flow expects:
        nodes: [{ id, data: { label }, position: { x, y }, style }]
        edges: [{ id, source, target }]

    We assign positions using a simple layered layout:
    files in the same directory cluster get the same x-column,
    and within a cluster they're stacked vertically.

    In a real implementation you'd use a proper layout algorithm
    like dagre (the standard choice for React Flow), but this
    simple version works fine for a hackathon demo.
    """

    # ── Determine node colours by directory ───────────────────────────
    # Each directory gets a consistent colour so the clusters are
    # visually obvious in the React Flow diagram.
    PALETTE = [
        "#4f46e5",  # indigo   — typically routes
        "#0891b2",  # cyan     — typically controllers
        "#059669",  # emerald  — typically services
        "#d97706",  # amber    — typically models
        "#7c3aed",  # violet   — typically middleware
        "#dc2626",  # red      — typically config
        "#6b7280",  # gray     — root-level files
    ]

    folders = list(stats["clusters"].keys())
    folder_colour = {
        folder: PALETTE[i % len(PALETTE)]
        for i, folder in enumerate(folders)
    }

    # ── Build node list ───────────────────────────────────────────────
    critical_file_paths = {fp for fp, _ in stats["critical_files"]}

    nodes = []
    # Simple layout: group by folder, position vertically within each group
    folder_file_lists: dict[str, list[str]] = {}
    for node in graph.nodes:
        folder = str(Path(node).parent)
        folder_file_lists.setdefault(folder, []).append(node)

    x_start = 50
    x_gap = 220
    y_start = 50
    y_gap = 80

    for col_idx, (folder, files) in enumerate(folder_file_lists.items()):
        colour = folder_colour.get(folder, "#6b7280")
        for row_idx, filepath in enumerate(files):
            is_critical = filepath in critical_file_paths
            is_entry = filepath in stats["entry_candidates"]

            nodes.append({
                "id": filepath,
                "data": {
                    "label": Path(filepath).name,
                    "folder": folder,
                    "isCritical": is_critical,
                    "isEntry": is_entry,
                },
                "position": {
                    "x": x_start + (col_idx * x_gap),
                    "y": y_start + (row_idx * y_gap),
                },
                "style": {
                    "background": colour,
                    "color": "#ffffff",
                    "border": "3px solid #facc15" if is_critical else "none",
                    "borderRadius": "8px",
                    "padding": "8px 12px",
                    "fontWeight": "600" if is_entry else "400",
                },
            })

    # ── Build edge list ───────────────────────────────────────────────
    edges = []
    for idx, (source, target) in enumerate(graph.edges):
        edges.append({
            "id": f"e{idx}",
            "source": source,
            "target": target,
            "animated": False,
            "style": {"stroke": "#94a3b8", "strokeWidth": 1.5},
        })

    return {"nodes": nodes, "edges": edges}