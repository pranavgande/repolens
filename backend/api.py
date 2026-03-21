# api.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.builder import build_dependency_graph
from graph.analyzer import analyze_graph
from m1.m1_pipeline import run_m1_pipeline
from m2.m2_pipeline import run_m2_pipeline
from m2.entry_detector import detect_entry_point
from WINGS_TEAM_KERNEL.backend.main import run_m3_pipeline
from WINGS_TEAM_KERNEL.backend.github_fetcher import fetch_repo_files

from fastapi.responses import Response
from b3.repo_summarizer import generate_summary
from b3.report_generator import generate_report

app = FastAPI(title="Codebase Intelligence Agent — M1, M2, M3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyseRequest(BaseModel):
    github_url: str


# ── Shared pipeline helper ─────────────────────────────────────────────────────

async def _run_full_pipeline(github_url: str) -> dict:
    """
    The core pipeline that all endpoints share.

    This function is the key architectural improvement over having three
    separate endpoints. Previously, each endpoint independently fetched
    the repo, parsed all files, and built the graph — three complete
    repetitions of the most expensive work. Now that work happens exactly
    once, and all three feature pipelines consume the shared result.

    The execution order is deliberately sequential rather than parallel
    because each step depends on the previous one:
      1. Fetch files        — network I/O, must complete before anything else
      2. Build graph        — CPU work on the fetched files
      3. Analyse graph      — pure math on the built graph, produces graph_stats
      4. Detect language    — reads file contents + graph, needed by M1 and M2
      5. Run M3             — serialises the graph into React Flow + LLM context
      6. Run M2             — uses graph for entry point, makes one LLM call
      7. Run M1             — uses graph_stats clusters, may make LLM calls

    M3 runs before M2 and M1 deliberately because it does no LLM work —
    it's pure serialisation and is essentially free. M2's Gemini call and
    M1's potential LLM fallback calls happen last, so if anything fails in
    the expensive LLM layer, the deterministic work is already complete
    and the error message is meaningful.
    """

    # ── Step 1: Fetch the repository ──────────────────────────────────────────
    # fetch_repo_files raises ValueError for bad URLs and repo-not-found cases,
    # which the endpoint catches and converts to HTTP 400.
    file_contents = await fetch_repo_files(github_url)

    # ── Step 2: Build the dependency graph ────────────────────────────────────
    # This is the most computationally expensive step — tree-sitter parses
    # every supported file, the resolver normalises relative import paths,
    # and networkx assembles the directed graph. Done once, shared by all.
    graph = build_dependency_graph(file_contents)

    # ── Step 3: Analyse the graph ─────────────────────────────────────────────
    # Pure graph mathematics — in-degrees, cycles, clusters, entry candidates.
    # This produces the graph_stats dict that M1 and M3 both consume.
    graph_stats = analyze_graph(graph)

    # ── Step 4: Detect language from the entry point ──────────────────────────
    # M1 needs the language to give the LLM fallback accurate context.
    # We compute it here from M3's entry candidates so neither M1 nor M2
    # needs to re-derive it independently.
    in_degrees       = dict(graph.in_degree())
    out_degrees      = dict(graph.out_degree())
    entry_candidates = [
        n for n in graph.nodes
        if in_degrees.get(n, 0) == 0 and out_degrees.get(n, 0) > 0
    ]
    detection = detect_entry_point(file_contents, entry_candidates)
    language  = detection.get("language", "javascript")

    # ── Step 5: Run M3 ────────────────────────────────────────────────────────
    # M3 takes the file_contents and internally rebuilds the graph...
    # but wait — run_m3_pipeline currently calls build_dependency_graph
    # internally, which would mean building the graph TWICE. We need to
    # pass our already-built graph to avoid that. Since main.py's
    # run_m3_pipeline accepts file_contents and rebuilds internally,
    # we call the individual M3 components directly instead.
    from serializer.graph_serializer import to_llm_text, to_react_flow_json

    llm_context     = to_llm_text(graph, graph_stats)
    react_flow_data = to_react_flow_json(graph, graph_stats)

    m3_result = {
        "llm_context":     llm_context,
        "graph_stats":     graph_stats,
        "react_flow_data": react_flow_data,
    }

    # ── Step 6: Run M2 ────────────────────────────────────────────────────────
    # M2 takes the graph we already built and uses it for entry detection
    # and first-level dependency resolution. One Gemini call happens here.
    m2_result = run_m2_pipeline(file_contents, graph)

    # ── Step 7: Run M1 ────────────────────────────────────────────────────────
    # M1 reads graph_stats["clusters"] — already computed in Step 3.
    # Zero to a few LLM calls happen here depending on folder name familiarity.
    m1_result = run_m1_pipeline(
        file_contents = file_contents,
        graph_stats   = graph_stats,
        language      = language,
    )

    # ── Step 8: Generate B3 intelligent summary ───────────────────────────────
    # Runs after M1, M2, M3 are all complete so it has full context to
    # synthesise. One Gemini call producing the paragraph that appears
    # at the top of the UI and as the executive summary in the PDF report.
    print("\n" + "=" * 60)
    print("B3: Generating intelligent repository summary")
    print("=" * 60)

    b3_summary = generate_summary(
        repo_url  = github_url,
        m1_result = m1_result,
        m2_result = m2_result,
        m3_result = m3_result,
    )
    print(f"  Summary: {b3_summary[:80]}...")

    return {
        "repository": {
            "url":          github_url,
            "total_files":  graph_stats["total_files"],
            "language":     language,
        },
        "b3": {
            "summary": b3_summary,
        },
        "m1": m1_result,
        "m2": m2_result,
        "m3": m3_result,
    }


# ── Health checks ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "ok", "message": "Codebase Intelligence Agent API"}


# ── Combined endpoint (primary — use this one) ────────────────────────────────

@app.post("/analyse")
async def analyse_all(request: AnalyseRequest):
    """
    Combined endpoint — runs M1, M2, and M3 in a single request.

    This is the primary endpoint the frontend should call. It fetches the
    repository once, builds the dependency graph once, and runs all three
    analysis pipelines against the shared result. The response contains
    everything the frontend needs nested under 'm1', 'm2', and 'm3' keys.

    Response shape:
    {
        "repository": { "url", "total_files", "language" },
        "m1": { "folder_tree", "total_folders", "llm_calls_made", "architecture_hint" },
        "m2": { "entry_file", "language", "confidence", "first_level_deps", "explanation" },
        "m3": { "llm_context", "graph_stats", "react_flow_data" }
    }
    """
    try:
        return await _run_full_pipeline(request.github_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Individual endpoints (kept for debugging and testing) ─────────────────────
# These remain available so you can test each feature in isolation during
# development or debug a specific pipeline without running the full stack.
# In production, the frontend only needs to call /analyse.

@app.post("/analyse/m1")
async def analyse_m1(request: AnalyseRequest):
    """M1 only — for isolated testing."""
    try:
        file_contents = await fetch_repo_files(request.github_url)
        graph         = build_dependency_graph(file_contents)
        graph_stats   = analyze_graph(graph)
        in_degrees    = dict(graph.in_degree())
        out_degrees   = dict(graph.out_degree())
        candidates    = [n for n in graph.nodes
                         if in_degrees.get(n,0)==0 and out_degrees.get(n,0)>0]
        detection     = detect_entry_point(file_contents, candidates)
        language      = detection.get("language", "javascript")
        return run_m1_pipeline(file_contents, graph_stats, language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyse/m2")
async def analyse_m2(request: AnalyseRequest):
    """M2 only — for isolated testing."""
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
    """M3 only — for isolated testing."""
    try:
        file_contents = await fetch_repo_files(request.github_url)
        return run_m3_pipeline(file_contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ReportRequest(BaseModel):
    """
    The frontend sends back the analysis data it already has in memory.
    The server has no session state — it receives everything it needs
    to generate the report in a single self-contained request.
    """
    repo_url:   str
    b3_summary: str
    m1_result:  dict
    m2_result:  dict
    m3_result:  dict


@app.post("/report")
async def download_report(request: ReportRequest):
    """
    Generate and return a downloadable PDF analysis report.

    The frontend calls this endpoint after receiving the /analyse response,
    passing back the stored analysis data. The server generates the PDF
    in memory and returns it as a file download with the appropriate headers.

    The Content-Disposition header with attachment tells the browser to
    download the file rather than trying to display it inline.
    The filename includes the repo name so the developer knows what
    they downloaded without opening it.
    """
    try:
        pdf_bytes = generate_report(
            repo_url   = request.repo_url,
            b3_summary = request.b3_summary,
            m1_result  = request.m1_result,
            m2_result  = request.m2_result,
            m3_result  = request.m3_result,
        )

        # Extract a clean filename from the repo URL
        # "https://github.com/expressjs/express" → "express_analysis.pdf"
        repo_name = request.repo_url.rstrip("/").split("/")[-1]
        filename  = f"{repo_name}_codebase_analysis.pdf"

        return Response(
            content     = pdf_bytes,
            media_type  = "application/pdf",
            headers     = {
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length":      str(len(pdf_bytes)),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))