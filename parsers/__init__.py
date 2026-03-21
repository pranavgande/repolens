# parsers/__init__.py

from .javascript_parser import JavaScriptParser
from .python_parser import PythonParser
from .base_parser import BaseParser

# Map file extensions to their parser instances.
# We instantiate once and reuse — creating a Parser object is slightly expensive.
_PARSERS: dict[str, BaseParser] = {
    ".js": JavaScriptParser(),
    ".ts": JavaScriptParser(),  # TypeScript uses the same import syntax
    ".jsx": JavaScriptParser(),
    ".tsx": JavaScriptParser(),
    ".py": PythonParser(),
}


def get_parser(extension: str) -> BaseParser | None:
    """
    Return the appropriate parser for a given file extension,
    or None if we don't support that file type.

    Returning None is better than raising an exception here — unsupported
    files (like .json, .md, .css) should simply be skipped, not crash the pipeline.
    """
    return _PARSERS.get(extension.lower())