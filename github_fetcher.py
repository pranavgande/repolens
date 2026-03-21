# github_fetcher.py

"""
Fetches a GitHub repository's source files and returns them as a
{filepath: bytes} dictionary — the same shape as MOCK_REPO_FILES.

This is the only file that needs to change to take the system from
mock data to real GitHub repos. Everything else in the pipeline
(parsers, graph builder, M1/M2/M3 pipelines) remains identical
because they all consume the same dict format regardless of where
the data came from.
"""

import os
import base64
import asyncio
import httpx          # async HTTP client — faster than requests for parallel calls
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# File extensions we actually know how to parse.
# We skip everything else to avoid wasting API calls on files
# that would never produce useful dependency information anyway.
SUPPORTED_EXTENSIONS = {
    ".js", ".ts", ".jsx", ".tsx",   # JavaScript / TypeScript
    ".py",                           # Python
    ".java",                         # Java
    ".json",                         # package.json, tsconfig.json etc.
}

# Folders that contain third-party dependencies, not the project's own code.
# Fetching these would waste hundreds of API calls and pollute the graph
# with external library relationships rather than internal ones.
SKIP_FOLDERS = {
    "node_modules", ".venv", "venv", "__pycache__",
    ".git", "dist", "build", ".next", "out",
    "coverage", ".pytest_cache", ".mypy_cache",
}

# Files larger than this threshold (in bytes) get skipped.
# Very large files are usually auto-generated (e.g. bundled JS, lockfiles)
# and would overwhelm the LLM context without adding useful signal.
MAX_FILE_SIZE_BYTES = 100_000  # 100 KB


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Extract the owner and repo name from a GitHub URL.

    Handles the common formats people actually type:
        https://github.com/expressjs/express
        https://github.com/expressjs/express/
        https://github.com/expressjs/express/tree/master
        github.com/expressjs/express

    Returns a (owner, repo) tuple like ("expressjs", "express").
    Raises ValueError if the URL doesn't look like a valid GitHub repo URL.
    """
    # Normalise: strip protocol, trailing slashes, and tree/branch suffixes
    url = url.strip().rstrip("/")
    url = url.replace("https://", "").replace("http://", "")
    url = url.replace("github.com/", "")

    # At this point we should have something like "expressjs/express"
    # or "expressjs/express/tree/master" — split on "/" and take first two parts
    parts = url.split("/")
    if len(parts) < 2:
        raise ValueError(
            f"Could not parse GitHub URL: '{url}'. "
            f"Expected format: https://github.com/owner/repo"
        )

    owner = parts[0]
    repo  = parts[1]

    if not owner or not repo:
        raise ValueError(f"Could not extract owner/repo from URL: '{url}'")

    return owner, repo


def _should_skip(path: str) -> bool:
    """
    Decide whether to skip a file based on its path.

    Returns True (skip this file) if:
    - Any component of the path is in SKIP_FOLDERS (e.g. node_modules)
    - The file extension is not in SUPPORTED_EXTENSIONS
    - The file is a hidden dotfile (starts with .)
    """
    parts = path.replace("\\", "/").split("/")

    # Skip if any folder in the path is a known dependency/build folder
    for part in parts[:-1]:  # all parts except the filename itself
        if part in SKIP_FOLDERS or part.startswith("."):
            return True

    # Check the filename itself
    filename = parts[-1]
    if filename.startswith("."):
        return True  # dotfiles like .eslintrc, .gitignore

    # Check extension
    ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        return True

    return False


async def _fetch_file_content(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    path: str,
    headers: dict,
) -> tuple[str, bytes] | None:
    """
    Fetch the content of a single file from the GitHub contents API.

    Returns a (path, bytes) tuple on success, or None if the file
    should be skipped (too large, empty, or API error).

    We use async here because we'll be fetching many files in parallel.
    Without async, fetching 100 files sequentially would take 30-60 seconds
    (network round-trip per file). With async parallel fetching, the same
    100 files take roughly the same time as fetching one file.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    try:
        response = await client.get(url, headers=headers)

        if response.status_code == 404:
            # File exists in tree but can't be fetched individually — skip it
            return None

        if response.status_code != 200:
            print(f"  Warning: could not fetch {path} (HTTP {response.status_code})")
            return None

        data = response.json()

        # GitHub returns size in bytes — skip files above our threshold
        if data.get("size", 0) > MAX_FILE_SIZE_BYTES:
            print(f"  Skipping {path} — too large ({data['size']} bytes)")
            return None

        # Decode the base64 content.
        # GitHub always encodes file content in base64 regardless of file type.
        # The content field may contain newlines (GitHub breaks base64 across lines)
        # so we strip whitespace before decoding.
        encoded = data.get("content", "")
        if not encoded:
            return None

        decoded_bytes = base64.b64decode(encoded.replace("\n", ""))
        return (path, decoded_bytes)

    except Exception as e:
        print(f"  Warning: error fetching {path}: {e}")
        return None


async def fetch_repo_files(github_url: str) -> dict[str, bytes]:
    """
    Main entry point. Given a GitHub URL, returns a {filepath: bytes}
    dictionary containing the source files of that repository.

    This is a drop-in replacement for MOCK_REPO_FILES — the dict it
    returns has exactly the same shape, so no other code needs to change.

    The function works in two phases:
      Phase 1 — Fetch the full file tree in one API call (fast)
      Phase 2 — Fetch individual file contents in parallel (fast with async)
    """
    owner, repo = parse_github_url(github_url)
    print(f"\nFetching repository: {owner}/{repo}")

    # Build headers — the token dramatically increases rate limits and
    # also allows access to private repos if needed in future.
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        print("  Using authenticated requests (5000 req/hr limit)")
    else:
        print("  Warning: no GITHUB_TOKEN found — using unauthenticated (60 req/hr limit)")

    async with httpx.AsyncClient(timeout=30.0) as client:

        # ── Phase 1: Get the full file tree ───────────────────────────────────
        # The ?recursive=1 parameter returns ALL files in all subdirectories
        # in a single response, rather than requiring one call per directory.
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        print(f"  Fetching file tree from: {tree_url}")

        tree_response = await client.get(tree_url, headers=headers)

        if tree_response.status_code == 404:
            raise ValueError(
                f"Repository not found: {owner}/{repo}. "
                f"Check that the URL is correct and the repo is public."
            )
        if tree_response.status_code == 403:
            raise ValueError(
                "GitHub API rate limit exceeded. "
                "Add a GITHUB_TOKEN to your .env file to increase the limit."
            )
        if tree_response.status_code != 200:
            raise ValueError(
                f"GitHub API error: HTTP {tree_response.status_code} "
                f"when fetching tree for {owner}/{repo}"
            )

        tree_data  = tree_response.json()
        all_items  = tree_data.get("tree", [])

        # Filter to only files (not directories) that we want to analyse
        # "blob" is GitHub's term for a file node in the tree
        files_to_fetch = [
            item["path"]
            for item in all_items
            if item["type"] == "blob" and not _should_skip(item["path"])
        ]

        print(f"  Total items in tree: {len(all_items)}")
        print(f"  Files to fetch after filtering: {len(files_to_fetch)}")

        if not files_to_fetch:
            raise ValueError(
                f"No supported source files found in {owner}/{repo}. "
                f"The repository may be empty or use unsupported languages."
            )

        # ── Phase 2: Fetch file contents in parallel ──────────────────────────
        # We use asyncio.gather to fire all content requests simultaneously.
        # This is the key performance optimisation — instead of sequential
        # requests (slow), we send all requests at once and wait for all
        # responses together (fast).
        #
        # We batch in groups of 20 to avoid overwhelming the GitHub API
        # with hundreds of simultaneous connections, which could trigger
        # secondary rate limiting even within the 5000/hr quota.
        print(f"  Fetching {len(files_to_fetch)} file contents in parallel batches...")

        file_contents: dict[str, bytes] = {}
        batch_size = 20

        for i in range(0, len(files_to_fetch), batch_size):
            batch = files_to_fetch[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(files_to_fetch) + batch_size - 1) // batch_size
            print(f"  Batch {batch_num}/{total_batches} ({len(batch)} files)...")

            # Create one coroutine per file in this batch
            tasks = [
                _fetch_file_content(client, owner, repo, path, headers)
                for path in batch
            ]

            # Run all coroutines in this batch concurrently
            results = await asyncio.gather(*tasks)

            # Collect successful results into our dict
            for result in results:
                if result is not None:
                    path, content = result
                    file_contents[path] = content

        print(f"  Successfully fetched {len(file_contents)} files")
        return file_contents


# ── Standalone test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import asyncio

    # Test with a small, well-known public repo
    TEST_URL = "https://github.com/expressjs/express"

    async def test():
        files = await fetch_repo_files(TEST_URL)
        print(f"\nFetched {len(files)} files from {TEST_URL}")
        print("\nSample file paths:")
        for path in list(files.keys())[:10]:
            print(f"  {path}  ({len(files[path])} bytes)")

    asyncio.run(test())