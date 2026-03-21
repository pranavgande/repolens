# resolver/import_resolver.py

from pathlib import Path

# These are well-known external packages for Node.js and Python.
# Any import that matches these is definitely NOT a local file.
# This list doesn't need to be exhaustive — the path resolution logic
# handles the remaining cases by checking if the resolved path exists
# in the file set.
KNOWN_EXTERNAL_PACKAGES = {
    # Node.js built-ins
    "path", "fs", "http", "https", "os", "crypto", "events",
    "stream", "util", "url", "net", "child_process", "cluster",
    # Common npm packages
    "express", "mongoose", "jsonwebtoken", "bcrypt", "dotenv",
    "axios", "lodash", "moment", "cors", "helmet", "morgan",
    # Python standard library
    "os", "sys", "re", "json", "typing", "pathlib", "datetime",
    "collections", "itertools", "functools", "abc", "io",
    # Common Python packages
    "fastapi", "flask", "django", "sqlalchemy", "pydantic",
    "requests", "numpy", "pandas",
}


def resolve_import(
        importing_file: str,
        raw_import: str,
        all_files: set[str],
) -> str | None:
    """
    Convert a raw import string into a canonical repo-relative file path.

    Returns the resolved path if it matches a real file in the repo,
    or None if the import is external (a package, not a local file).

    Walk-through example:
        importing_file = "routes/auth.routes.js"
        raw_import     = "../controllers/auth.controller"
        all_files      = {"controllers/auth.controller.js", ...}

        Step 1: base_dir = "routes/"
        Step 2: candidate = "routes/../controllers/auth.controller"
                           = "controllers/auth.controller" (after normalization)
        Step 3: try "controllers/auth.controller.js" → found! ✓
        Returns: "controllers/auth.controller.js"
    """

    # ── Fast exit: definitely an external package ─────────────────────
    # Relative imports always start with '.' in both JS and Python.
    # If it doesn't start with '.', it's either an external npm package
    # OR an absolute Python import like 'from services.auth import login'.
    # Either way, check against our known externals first.
    if not raw_import.startswith("."):
        # Extract the top-level package name (e.g. 'services' from 'services.auth')
        top_level = raw_import.split(".")[0].split("/")[0]
        if top_level in KNOWN_EXTERNAL_PACKAGES:
            return None
        # For Python absolute imports that we don't recognise as external,
        # we'll still try to resolve them — they might be internal modules.
        # Convert Python dot notation to path: 'services.auth' → 'services/auth'
        candidate_path = raw_import.replace(".", "/")
    else:
        # Relative import: compute path relative to the importing file's directory
        base_dir = Path(importing_file).parent

        # Path resolution handles the '..' components automatically.
        # PurePosixPath is used to ensure forward slashes on all platforms.
        candidate_path = str((base_dir / raw_import).as_posix())

        # Normalise: remove any remaining './' prefixes
        # Path().as_posix() already handles this, but belt-and-suspenders
        if candidate_path.startswith("./"):
            candidate_path = candidate_path[2:]

    # ── Try to match against known files ─────────────────────────────
    # The import might omit the extension (very common in JS: './auth.controller'
    # instead of './auth.controller.js'). Try adding each likely extension.
    extensions_to_try = ["", ".js", ".ts", ".jsx", ".tsx", ".py"]

    for ext in extensions_to_try:
        candidate = candidate_path + ext
        if candidate in all_files:
            return candidate  # Found a match — return the canonical path

    # Could also be a directory import pointing to its index file.
    # e.g. require('./routes') might resolve to routes/index.js
    for index_file in ["index.js", "index.ts", "index.py", "__init__.py"]:
        index_candidate = f"{candidate_path}/{index_file}"
        if index_candidate in all_files:
            return index_candidate

    # If nothing matched, this import doesn't resolve to a local file.
    # It's probably an external package we didn't know about. Skip it.
    return None