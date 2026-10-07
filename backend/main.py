# main.py
# Single source of truth for the entire backend.

import json
import base64
import networkx as nx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from graph.builder import build_dependency_graph
from graph.analyzer import analyze_graph
from serializer.graph_serializer import to_llm_text, to_react_flow_json
from m1.m1_pipeline import run_m1_pipeline
from m2.m2_pipeline import run_m2_pipeline
from m2.entry_detector import detect_entry_point
from b3.repo_summarizer import generate_summary
from b3.report_generator import generate_report
from github_fetcher import fetch_repo_files

app = FastAPI(title="Codebase Intelligence Agent — M1, M2, M3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ─────────────────────────────────────────────────────────────

class AnalyseRequest(BaseModel):
    github_url: str


# ── M3 pipeline ────────────────────────────────────────────────────────────────

def run_m3_pipeline(
    file_contents: dict[str, bytes],
    graph: nx.DiGraph | None = None,
    graph_stats: dict | None = None,
) -> dict:
    """
    The M3 dependency mapping pipeline.

    Accepts an optional pre-built graph and stats so _run_full_pipeline
    can pass them in and avoid rebuilding from scratch. When called from
    the debug /analyse/m3 endpoint without pre-built data, it builds
    everything itself exactly as it always did.
    """
    print("\n" + "=" * 60)
    print("PHASE 1: Building dependency graph")
    print("=" * 60)

    if graph is None:
        graph = build_dependency_graph(file_contents)
        print(f"\nGraph built: {graph.number_of_nodes()} nodes, "
              f"{graph.number_of_edges()} edges")
    else:
        print(f"\nUsing pre-built graph: {graph.number_of_nodes()} nodes, "
              f"{graph.number_of_edges()} edges (skipped rebuild)")

    print("\n" + "=" * 60)
    print("PHASE 2: Analysing graph structure")
    print("=" * 60)

    if graph_stats is None:
        graph_stats = analyze_graph(graph)
        for filepath, degree in graph_stats["critical_files"]:
            print(f"  {filepath}  ← imported by {degree} file(s)")
        for fp in graph_stats["entry_candidates"]:
            print(f"  Entry candidate: {fp}")
        if not graph_stats["cycles"]:
            print("  No circular dependencies — clean architecture ✓")
    else:
        print(f"  Using pre-computed stats ({graph_stats['total_files']} files, "
              f"{graph_stats['total_edges']} edges)")

    print("\n" + "=" * 60)
    print("PHASE 3: Serialising for LLM")
    print("=" * 60)
    llm_text = to_llm_text(graph, graph_stats)
    print(llm_text)

    print("\n" + "=" * 60)
    print("PHASE 4: Generating React Flow JSON")
    print("=" * 60)
    react_flow_data = to_react_flow_json(graph, graph_stats)
    print(f"Nodes: {len(react_flow_data['nodes'])}, "
          f"Edges: {len(react_flow_data['edges'])}")

    return {
        "llm_context":     llm_text,
        "graph_stats":     graph_stats,
        "react_flow_data": react_flow_data,
    }


# ── Full pipeline orchestrator ─────────────────────────────────────────────────

async def _run_full_pipeline(github_url: str) -> dict:
    """
    The core pipeline behind the /analyse endpoint.

    Fetches the repository once, builds the dependency graph once, and
    runs all five outputs (M1, M2, M3, B3 summary, PDF report) against
    that single shared result. The graph is never rebuilt twice.

    Execution order and reasoning:
      1. Fetch files     — network I/O, everything depends on this
      2. Build graph     — expensive CPU work, done exactly once
      3. Analyse graph   — pure maths on the graph, produces graph_stats
      4. Detect language — reads file contents and graph together
      5. Run M3          — pure serialisation, no LLM, essentially free
      6. Run M2          — one Claude call for the execution flow narrative (when configured)
      7. Run M1          — zero to a few LLM calls for folder descriptions
      8. B3 summary      — one Claude call synthesising M1 + M2 + M3 (when configured)
      9. PDF report      — reportlab assembles the report in memory,
                           encoded as Base64 so it travels in the JSON
    """

    # Step 1
    file_contents = await fetch_repo_files(github_url)

    # Step 2
    graph = build_dependency_graph(file_contents)

    # Step 3
    graph_stats = analyze_graph(graph)

    # Step 4 — detect language from the entry point so M1 has accurate
    # context for its LLM fallback without re-deriving it independently
    in_degrees  = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())
    entry_candidates = [
        n for n in graph.nodes
        if in_degrees.get(n, 0) == 0 and out_degrees.get(n, 0) > 0
    ]
    detection = detect_entry_point(file_contents, entry_candidates)
    language  = detection.get("language", "javascript")

    # Step 5 — pass pre-built graph and stats so M3 skips rebuilding
    m3_result = run_m3_pipeline(file_contents, graph, graph_stats)

    # Step 6
    m2_result = run_m2_pipeline(file_contents, graph)

    # Step 7
    m1_result = run_m1_pipeline(
        file_contents = file_contents,
        graph_stats   = graph_stats,
        language      = language,
    )

    # Step 8
    print("\n" + "=" * 60)
    print("B3: Generating intelligent repository summary")
    print("=" * 60)
    b3_summary = generate_summary(
        repo_url  = github_url,
        m1_result = m1_result,
        m2_result = m2_result,
        m3_result = m3_result,
    )
    print(f"  Summary generated ({len(b3_summary)} chars)")

    # Step 9 — PDF generated entirely in memory, no disk writes.
    # Base64 encoding inflates binary by ~33% but for typical repos
    # (50-150KB PDFs) this adds negligible size to the JSON response.
    # The frontend decodes it with atob() when the user clicks download.
    print("\n" + "=" * 60)
    print("REPORT: Generating PDF")
    print("=" * 60)
    pdf_bytes  = generate_report(
        repo_url   = github_url,
        b3_summary = b3_summary,
        m1_result  = m1_result,
        m2_result  = m2_result,
        m3_result  = m3_result,
    )
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    print(f"  PDF: {len(pdf_bytes):,} bytes → {len(pdf_base64):,} chars as Base64")

    return {
        "repository": {
            "url":         github_url,
            "total_files": graph_stats["total_files"],
            "language":    language,
        },
        "b3":        {"summary": b3_summary},
        "m1":        m1_result,
        "m2":        m2_result,
        "m3":        m3_result,
        "pdf_base64": pdf_base64,
    }


# ── Health checks ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "ok", "message": "Repolens Codebase Intelligence API"}


@app.get("/health/ai")
async def ai_health():
    """Report the configured AI provider without exposing credentials."""
    anthropic_configured = bool(__import__("os").environ.get("ANTHROPIC_API_KEY"))
    if anthropic_configured:
        provider = "anthropic"
        model = __import__("os").environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    else:
        provider = "gemini"
        model = __import__("os").environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
    return {
        "provider": provider,
        "model": model,
        "configured": True,
        "fallback_available": provider == "anthropic",
    }


# ── Primary endpoint ───────────────────────────────────────────────────────────

@app.post("/analyse")
async def analyse_all(request: AnalyseRequest):
    """
    The one endpoint the frontend calls for everything.

    Returns M1 folder analysis, M2 execution flow, M3 dependency graph,
    B3 executive summary, and a Base64-encoded PDF report — all from a
    single GitHub URL submission.

    Response shape:
    {
        "repository":  { url, total_files, language },
        "b3":          { summary },
        "m1":          { folder_tree, total_folders, llm_calls_made, architecture_hint },
        "m2":          { entry_file, language, confidence, first_level_deps, explanation },
        "m3":          { llm_context, graph_stats, react_flow_data },
        "pdf_base64":  "...base64 string..."
    }
    """
    try:
        return await _run_full_pipeline(request.github_url)
    except ValueError as e:
        # Bad URL or repo not found — the caller's fault, so 400 not 500
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print the full stack trace to the server logs
        raise HTTPException(status_code=500, detail=str(e))


# ── Debug endpoints ────────────────────────────────────────────────────────────
# These exist purely for isolated testing during development.
# The frontend only ever needs /analyse in production.

@app.post("/analyse/m1")
async def analyse_m1(request: AnalyseRequest):
    try:
        file_contents = await fetch_repo_files(request.github_url)
        graph         = build_dependency_graph(file_contents)
        graph_stats   = analyze_graph(graph)
        in_degrees    = dict(graph.in_degree())
        out_degrees   = dict(graph.out_degree())
        candidates    = [n for n in graph.nodes
                         if in_degrees.get(n,0)==0 and out_degrees.get(n,0)>0]
        language      = detect_entry_point(file_contents, candidates).get("language", "javascript")
        return run_m1_pipeline(file_contents, graph_stats, language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyse/m2")
async def analyse_m2(request: AnalyseRequest):
    try:
        file_contents = await fetch_repo_files(request.github_url)
        graph         = build_dependency_graph(file_contents)
        return run_m2_pipeline(file_contents, graph)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyse/m3")
async def analyse_m3(request: AnalyseRequest):
    try:
        file_contents = await fetch_repo_files(request.github_url)
        return run_m3_pipeline(file_contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
