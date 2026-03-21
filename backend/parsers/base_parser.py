# parsers/base_parser.py

from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    Every language parser must follow this contract.

    Input:  raw source code as bytes (what you get from the GitHub API)
    Output: list of raw import strings, exactly as written in the source

    Example output for JavaScript:
        ['express', '../controllers/auth.controller', './db.config']

    We deliberately do NOT resolve paths here. The parser's only job
    is to read the syntax tree and pull out what the developer wrote.
    Resolution is a separate concern handled by the resolver module.
    """

    @abstractmethod
    def extract_imports(self, source_code: bytes) -> list[str]:
        """Return all raw import/require strings found in the source."""
        pass