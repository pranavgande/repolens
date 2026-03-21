# parsers/javascript_parser.py

from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjavascript
from .base_parser import BaseParser

JS_LANGUAGE = Language(tsjavascript.language())


def _walk(node):
    """
    A simple recursive generator that visits every node in the AST tree.

    Think of the AST like a family tree — this function visits the root,
    then every child, then every grandchild, all the way to the leaves.
    Using a generator (yield) means we don't build a massive list in memory;
    we visit one node at a time and stop early if needed.
    """
    yield node
    for child in node.children:
        yield from _walk(child)


class JavaScriptParser(BaseParser):
    """
    Parses JavaScript/TypeScript files and extracts import sources.

    We look for two patterns by checking node types as we walk the tree:

    Pattern 1 — ES Module imports:
        import express from 'express'
        AST shape: import_statement → string (the source)

    Pattern 2 — CommonJS require() calls:
        const db = require('./config/db')
        AST shape: call_expression → identifier["require"] + arguments → string
    """

    def __init__(self):
        self.parser = Parser(JS_LANGUAGE)

    def extract_imports(self, source_code: bytes) -> list[str]:
        tree = self.parser.parse(source_code)
        imports = []

        for node in _walk(tree.root_node):

            # ── Pattern 1: import_statement ───────────────────────────────
            # The AST for `import x from './module'` looks like:
            #   import_statement
            #     import_clause: ...
            #     string: "'./module'"    ← this is what we want
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "string":
                        raw = child.text.decode("utf-8").strip().strip("'\"")
                        imports.append(raw)

            # ── Pattern 2: require() call ─────────────────────────────────
            # The AST for `require('./module')` looks like:
            #   call_expression
            #     identifier: "require"   ← check this is literally "require"
            #     arguments
            #       string: "'./module'"  ← this is what we want
            elif node.type == "call_expression":
                # The first child of a call_expression is the function being called
                children = node.children
                if not children:
                    continue

                func_node = children[0]

                # Only proceed if the function is literally the identifier "require"
                if func_node.type == "identifier" and func_node.text == b"require":
                    # Find the arguments node, then the string inside it
                    for child in children:
                        if child.type == "arguments":
                            for arg in child.children:
                                if arg.type == "string":
                                    raw = arg.text.decode("utf-8").strip().strip("'\"")
                                    imports.append(raw)

        return imports