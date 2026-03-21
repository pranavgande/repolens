# m1/m1_pipeline.py

"""
M1 Pipeline orchestrator — walks the folder structure and produces
a plain-English description for every directory in the repository.

The pipeline runs in three passes:

Pass 1 — Run every folder through the two-tier analyzer (pattern match
         then content inference). Most folders will be resolved here
         with zero external calls.

Pass 2 — Collect all folders that the analyzer couldn't resolve
         (source='unknown') and send them to the LLM fallback one
         by one. In a typical well-structured project this list is
         empty or contains one or two entries.

Pass 3 — Assemble the final result dictionary combining all descriptions,
         the architecture hint, and summary statistics.

Like M2, this pipeline accepts the M3 graph_stats dict directly so it
never needs to re-walk the file tree — M3 already did that work and
stored the results in graph_stats["clusters"].
"""

from m1.folder_analyzer import analyze_folder, detect_architecture
from m1.folder_explainer import explain_folder


def run_m1_pipeline(
    file_contents: dict[str, bytes],
    graph_stats:   dict | None = None,
    language:      str = "javascript",
) -> dict:
    """
    Full M1 pipeline. Returns a structured description of every folder
    in the repository.

    Parameters:
        file_contents: the full {filepath: bytes} dict — used as fallback
                       to build the clusters dict if graph_stats is absent.
        graph_stats:   the stats dict from M3's graph analyser. When present,
                       we read graph_stats["clusters"] directly rather than
                       re-deriving the folder structure ourselves.
        language:      the detected project language (from M2's result).
                       Passed to the LLM fallback so it can produce more
                       accurate descriptions for language-specific patterns.

    Returns a dict with:
        folder_tree:      {folder_name: {description, files, source}} for every folder
        total_folders:    count of folders analysed
        llm_calls_made:   how many LLM calls were needed (useful for the demo)
        architecture_hint: detected architectural pattern (e.g. "MVC + Service")
    """

    # ── Step 1: Get the clusters dict ──────────────────────────────────────────
    # Clusters maps each folder name to the list of files inside it.
    # Ideally this comes from M3's graph_stats, which already computed it.
    # If graph_stats isn't available (M1 running standalone), we derive it
    # ourselves from the file_contents keys by grouping on parent directory.
    if graph_stats and "clusters" in graph_stats:
        clusters = graph_stats["clusters"]
        print("  Using M3 graph_stats clusters — no re-parsing needed")
    else:
        from pathlib import Path
        clusters: dict[str, list[str]] = {}
        for filepath in file_contents:
            folder = str(Path(filepath).parent)
            folder = folder.replace("\\", "/")
            clusters.setdefault(folder, []).append(Path(filepath).name)
        print("  No graph_stats provided — derived clusters from file paths")

    print(f"  Folders to analyse: {list(clusters.keys())}")

    # ── Step 2: Run the two-tier analyzer on every folder ─────────────────────
    # We skip the root folder "." because it contains the entry point file
    # (server.js, main.py, etc.) rather than a logical module group.
    # Describing "." as a folder would confuse a new developer — the entry
    # point is better described by M2, not M1.
    folder_tree   = {}
    unknown_folders = []  # folders that need LLM fallback

    print("\n" + "=" * 60)
    print("M1 PASS 1: Pattern matching and content inference")
    print("=" * 60)

    for folder, files in clusters.items():

        # Skip root-level grouping — it's not a meaningful module folder
        if folder in (".", ""):
            continue

        # Normalise: use just the last segment of the path as the folder name
        # for matching purposes. A folder at "src/controllers" should match
        # the "controllers" pattern, not "src/controllers".
        folder_display = folder  # keep the full path for display
        folder_name    = folder.split("/")[-1].split("\\")[-1]

        result = analyze_folder(folder_name, files)

        if result["source"] == "unknown":
            # Flag for LLM fallback — don't describe it yet
            unknown_folders.append(folder_display)
            print(f"  {folder_display}/ → needs LLM fallback")
        else:
            folder_tree[folder_display] = {
                "description": result["description"],
                "files":       files,
                "source":      result["source"],
            }
            source_label = "✓ pattern" if result["source"] == "pattern_match" else "~ inferred"
            print(f"  {folder_display}/ → {source_label}")

    # ── Step 3: Detect architecture from folder names ─────────────────────────
    # We do this after Pass 1 so we have a clean set of all folder names.
    all_folder_names = set(clusters.keys()) - {".", ""}
    architecture_hint = detect_architecture(all_folder_names)
    print(f"\n  Detected architecture: {architecture_hint}")

    # ── Step 4: LLM fallback for unrecognised folders ─────────────────────────
    llm_calls_made = 0

    if unknown_folders:
        print("\n" + "=" * 60)
        print(f"M1 PASS 2: LLM fallback for {len(unknown_folders)} unrecognised folder(s)")
        print("=" * 60)

        for folder_display in unknown_folders:
            folder_name  = folder_display.split("/")[-1].split("\\")[-1]
            files        = clusters.get(folder_display, [])

            description = explain_folder(
                folder_name       = folder_name,
                files_inside      = files,
                language          = language,
                architecture_hint = architecture_hint,
            )

            folder_tree[folder_display] = {
                "description": description,
                "files":       files,
                "source":      "llm_fallback",
            }
            llm_calls_made += 1
            print(f"  {folder_display}/ → LLM described")
    else:
        print("\n  No LLM calls needed — all folders resolved by pattern matching")

    # ── Step 5: Assemble the final result ─────────────────────────────────────
    return {
        "folder_tree":      folder_tree,
        "total_folders":    len(folder_tree),
        "llm_calls_made":   llm_calls_made,
        "architecture_hint": architecture_hint,
    }


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, json
    sys.path.insert(0, ".")

    from mock_data.mock_repo import MOCK_REPO_FILES
    from graph.builder import build_dependency_graph
    from graph.analyzer import analyze_graph

    print("Running M1 pipeline on mock repository...")
    print(f"Files: {list(MOCK_REPO_FILES.keys())}")

    # Build the M3 graph and stats — exactly as the real endpoint does —
    # so M1 can consume the pre-computed clusters rather than re-deriving them.
    graph       = build_dependency_graph(MOCK_REPO_FILES)
    graph_stats = analyze_graph(graph)

    result = run_m1_pipeline(
        file_contents = MOCK_REPO_FILES,
        graph_stats   = graph_stats,
        language      = "javascript",
    )

    print("\n" + "=" * 60)
    print("M1 PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Total folders analysed : {result['total_folders']}")
    print(f"LLM calls made         : {result['llm_calls_made']}")
    print(f"Architecture detected  : {result['architecture_hint']}")
    print("\nFolder tree:")
    for folder, info in result["folder_tree"].items():
        print(f"\n  {folder}/  [{info['source']}]")
        print(f"    {info['description']}")