# graph/builder.py

from pathlib import Path
import networkx as nx

from parsers import get_parser
from resolver.import_resolver import resolve_import


def build_dependency_graph(file_contents: dict[str, bytes]) -> nx.DiGraph:
    """
    Build a directed dependency graph from a dict of {filepath: source_bytes}.

    The resulting graph has the following semantics:
        - Each NODE is a file path (e.g. "controllers/auth.controller.js")
        - Each EDGE A → B means "file A imports file B"

    So if you follow a path in the graph, you're following the import chain:
        server.js → routes/auth.routes.js → controllers/auth.controller.js → ...

    Why networkx DiGraph (directed graph)?
    Because the direction matters. "A imports B" is not the same as "B imports A".
    In-degree (how many files import you) tells you how critical a file is.
    Out-degree (how many files you import) tells you how much a file orchestrates.
    """

    all_files = set(file_contents.keys())
    graph = nx.DiGraph()

    # Add all files as nodes upfront — even files that have no imports
    # and nothing imports them. We want isolated nodes to appear in the graph
    # because they're still part of the repo structure.
    for filepath in all_files:
        # We store the filename as a label for display purposes.
        # The full path stays as the node ID for uniqueness.
        graph.add_node(filepath, label=Path(filepath).name)

    # Now build edges by parsing each file
    for filepath, source_bytes in file_contents.items():
        extension = Path(filepath).suffix
        parser = get_parser(extension)

        if parser is None:
            # Unsupported file type (e.g. .json, .md) — skip it
            continue

        # Extract raw import strings from this file's source code
        raw_imports = parser.extract_imports(source_bytes)

        for raw_import in raw_imports:
            resolved_path = resolve_import(filepath, raw_import, all_files)

            if resolved_path is not None:
                # Add a directed edge: "filepath depends on resolved_path"
                graph.add_edge(filepath, resolved_path)

                # Print for debugging during development — remove in production
                print(f"  EDGE: {filepath} → {resolved_path}")

    return graph