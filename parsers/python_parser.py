# parsers/python_parser.py

from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from .base_parser import BaseParser

PY_LANGUAGE = Language(tspython.language())


def _walk(node):
    """Same recursive tree walker — kept in each file to avoid cross-imports."""
    yield node
    for child in node.children:
        yield from _walk(child)


class PythonParser(BaseParser):
    """
    Parses Python files and extracts imported module names.

    We look for two patterns:

    Pattern 1 — Simple import:
        import os
        AST shape: import_statement → dotted_name["os"]

    Pattern 2 — From import (absolute or relative):
        from .models import User
        from services.auth import login
        AST shape: import_from_statement → dotted_name or relative_import

    Note: we collect ALL imports here (both external packages like 'fastapi'
    and relative ones like '.models'). The resolver downstream is responsible
    for deciding which ones are local files vs external packages — that's not
    the parser's concern.
    """

    def __init__(self):
        self.parser = Parser(PY_LANGUAGE)

    def extract_imports(self, source_code: bytes) -> list[str]:
        tree = self.parser.parse(source_code)
        imports = []

        for node in _walk(tree.root_node):

            # ── Pattern 1: import os / import os, sys ─────────────────────
            # AST: import_statement → dotted_name (one per imported name)
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        raw = child.text.decode("utf-8").strip()
                        imports.append(raw)

            # ── Pattern 2: from .models import User ───────────────────────
            # AST: import_from_statement
            #         relative_import or dotted_name  ← the module path
            #         import (keyword)
            #         dotted_name or wildcard          ← what's being imported
            # We only want the MODULE part (what comes after "from"),
            # not the names being imported from it.
            elif node.type == "import_from_statement":
                for child in node.children:
                    # relative_import covers "from .models" and "from ..utils"
                    # dotted_name covers "from services.auth"
                    if child.type in ("dotted_name", "relative_import"):
                        raw = child.text.decode("utf-8").strip()
                        imports.append(raw)
                        # Break after the first match — we only want the module,
                        # not the names being imported FROM that module.
                        break

        return imports
