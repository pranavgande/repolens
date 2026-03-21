# m2/entry_detector.py

"""
Phase 1 of the M2 pipeline: Entry Point Detection.

The goal is to identify which file in the repository is the "front door" —
the file that starts executing when someone runs the application.

We use three signals, checked in order of reliability:
  1. Filename pattern matching (strongest signal — industry conventions)
  2. Content heuristics (read the file and look for entry-point fingerprints)
  3. Package manifest inspection (package.json "main"/"scripts" fields)
We also accept M3's entry_candidates list as a starting shortlist,
which significantly narrows the search space before we apply heuristics.
"""
import json
from pathlib import Path
# ── Filename patterns by language ─────────────────────────────────────────────
# These are universally recognised entry point filenames across the industry.
# The order within each list reflects descending confidence — if a repo has
# both "server.js" and "index.js", "server.js" is the stronger signal.

ENTRY_FILENAME_PATTERNS = {
    "javascript": [
        "server.js", "app.js", "index.js",
        "server.ts", "app.ts", "index.ts",
        "main.js", "main.ts",
    ],
    "python": [
        "main.py", "app.py", "run.py",
        "manage.py",   # Django's entry point
        "wsgi.py",     # WSGI server entry
        "asgi.py",     # ASGI server entry (FastAPI, Starlette)
        "__main__.py", # Python package entry point
    ],
    "java": [
        "Main.java", "Application.java", "App.java",
    ],
}

# Flatten to a single set for fast membership testing, but keep the
# ordered list around for priority scoring (lower index = higher priority).
ALL_ENTRY_FILENAMES = {
    name
    for patterns in ENTRY_FILENAME_PATTERNS.values()
    for name in patterns
}


# ── Content fingerprints by language ──────────────────────────────────────────
# These are code patterns that only appear in entry point files.
# We search for these as plain substrings in the file's source code —
# no regex, no AST, just fast string membership checks.

CONTENT_FINGERPRINTS = {
    "javascript": [
        "app.listen(",       # Express server starting
        "server.listen(",    # Raw HTTP server starting
        "createServer(",     # Node http.createServer
        "connectDB(",        # Database connection call (common pattern)
        "dotenv.config(",    # Loading environment variables
        "mongoose.connect(", # MongoDB connection
        "sequelize.sync(",   # SQL ORM sync
    ],
    "python": [
        "if __name__ == '__main__'",  # Python's universal entry guard
        "uvicorn.run(",               # FastAPI / Starlette startup
        "app.run(",                   # Flask startup
        "execute_from_command_line(", # Django management entry
        "asyncio.run(",               # Async application startup
    ],
}


def _score_filename(filename: str) -> int:
    """
    Give a file a score based on how strongly its name suggests it's an entry point.
    Higher score = stronger signal.

    We use the position in the patterns list to assign priority:
    index 0 (e.g. "server.js") scores highest, later entries score lower.
    Files not in any list score 0.
    """
    for language, patterns in ENTRY_FILENAME_PATTERNS.items():
        if filename in patterns:
            # Score inversely by position: first in list = highest score
            position = patterns.index(filename)
            return max(10 - position, 1)  # minimum score of 1 if it matches at all
    return 0


def _score_content(source_bytes: bytes, filename: str) -> int:
    """
    Scan the file's source code for entry-point fingerprints.
    Each fingerprint found adds 2 points to the score.

    We determine which fingerprint list to use based on file extension,
    so we don't waste time looking for Python patterns in a JS file.
    """
    score = 0
    source_str = source_bytes.decode("utf-8", errors="ignore")
    extension = Path(filename).suffix.lower()

    if extension in (".js", ".ts", ".jsx", ".tsx"):
        fingerprints = CONTENT_FINGERPRINTS["javascript"]
    elif extension == ".py":
        fingerprints = CONTENT_FINGERPRINTS["python"]
    else:
        return 0  # We don't have fingerprints for this language yet

    for fingerprint in fingerprints:
        if fingerprint in source_str:
            score += 2  # Each matching fingerprint adds to our confidence

    return score


def _check_package_manifest(file_contents: dict[str, bytes]) -> str | None:
    """
    Check package.json (Node.js) for an explicit entry point declaration.
    This is ground truth — the developer explicitly told us the entry file.

    Returns the declared entry point path if found, None otherwise.
    """
    if "package.json" not in file_contents:
        return None

    try:
        manifest = json.loads(file_contents["package.json"].decode("utf-8"))

        # The "main" field directly declares the entry point file
        if "main" in manifest:
            return manifest["main"]

        # The "scripts.start" field often reveals the entry point
        # e.g. "start": "node server.js" → entry is "server.js"
        start_script = manifest.get("scripts", {}).get("start", "")
        if start_script:
            # Extract the filename from a command like "node server.js"
            # or "ts-node src/index.ts"
            parts = start_script.split()
            for part in parts:
                # The entry file is the argument after the runtime command
                if part not in ("node", "ts-node", "nodemon", "python", "python3"):
                    if "." in part:  # It has an extension, likely a filename
                        return part

    except (json.JSONDecodeError, KeyError):
        pass  # Malformed package.json — just skip it

    return None


def detect_entry_point(
    file_contents: dict[str, bytes],
    entry_candidates: list[str] | None = None,
) -> dict:
    """
    Main function for Phase 1. Identifies the most likely entry point file.

    Parameters:
        file_contents:    the full dict of {filepath: source_bytes} for the repo
        entry_candidates: optional shortlist from M3's graph analyser
                          (files with in-degree 0 and out-degree > 0).
                          If provided, we score only these files first.
                          If not provided (M2 running standalone), we score all files.

    Returns a dict with:
        "entry_file":     the detected entry point path (e.g. "server.js")
        "language":       detected primary language ("javascript", "python", etc.)
        "confidence":     "high", "medium", or "low" based on total score
        "manifest_declared": True if package.json explicitly declared it
        "all_scores":     the full scoring breakdown for every candidate
    """

    # ── Step 1: Check manifest first — it's definitive ────────────────────────
    manifest_entry = _check_package_manifest(file_contents)
    if manifest_entry and manifest_entry in file_contents:
        return {
            "entry_file": manifest_entry,
            "language": "javascript",
            "confidence": "high",
            "manifest_declared": True,
            "all_scores": {manifest_entry: 99},  # Treat manifest as max confidence
        }

    # ── Step 2: Build the candidate list ──────────────────────────────────────
    # If M3 gave us a shortlist, use it. Otherwise, consider all files
    # whose names match known entry point patterns.
    if entry_candidates:
        candidates = entry_candidates
    else:
        candidates = [
            filepath for filepath in file_contents
            if Path(filepath).name in ALL_ENTRY_FILENAMES
        ]

    if not candidates:
        # No recognisable entry point found — return a low-confidence result
        return {
            "entry_file": None,
            "language": "unknown",
            "confidence": "low",
            "manifest_declared": False,
            "all_scores": {},
        }

    # ── Step 3: Score every candidate ─────────────────────────────────────────
    scores = {}
    for filepath in candidates:
        filename = Path(filepath).name
        source  = file_contents.get(filepath, b"")

        filename_score = _score_filename(filename)
        content_score  = _score_content(source, filename)
        total_score    = filename_score + content_score

        scores[filepath] = {
            "total":    total_score,
            "filename": filename_score,
            "content":  content_score,
        }

        print(f"  Scored '{filepath}': filename={filename_score}, "
              f"content={content_score}, total={total_score}")

    # ── Step 4: Pick the highest-scoring candidate ────────────────────────────
    best_file = max(scores, key=lambda f: scores[f]["total"])
    best_score = scores[best_file]["total"]

    # Determine confidence based on score magnitude
    if best_score >= 10:
        confidence = "high"
    elif best_score >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    # Detect language from the winning file's extension
    ext = Path(best_file).suffix.lower()
    if ext in (".js", ".ts", ".jsx", ".tsx"):
        language = "javascript"
    elif ext == ".py":
        language = "python"
    elif ext == ".java":
        language = "java"
    else:
        language = "unknown"

    return {
        "entry_file":        best_file,
        "language":          language,
        "confidence":        confidence,
        "manifest_declared": False,
        "all_scores":        scores,
    }


# Run this temporarily to test Phase 1 in isolation:
# python m2/entry_detector.py

if __name__ == "__main__":
    from mock_data.mock_repo import MOCK_REPO_FILES

    print("Testing Phase 1: Entry Point Detection")
    print("=" * 50)

    # Simulate what M3 would hand over
    m3_entry_candidates = ["server.js"]

    result = detect_entry_point(MOCK_REPO_FILES, m3_entry_candidates)

    print(f"\nEntry file detected : {result['entry_file']}")
    print(f"Language            : {result['language']}")
    print(f"Confidence          : {result['confidence']}")
    print(f"Manifest declared   : {result['manifest_declared']}")