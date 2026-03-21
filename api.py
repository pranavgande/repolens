# api.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.builder import build_dependency_graph
from graph.analyzer import analyze_graph
from m1.m1_pipeline import run_m1_pipeline
from m2.m2_pipeline import run_m2_pipeline
from m2.entry_detector import detect_entry_point
from m1.m1_pipeline import run_m1_pipeline
from main import run_m3_pipeline
from github_fetcher import fetch_repo_files   # ← the new import

app = FastAPI(title="Codebase Intelligence Agent — M1, M2, M3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyseRequest(BaseModel):
    github_url: str


# ── Health checks ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "ok", "message": "Codebase Intelligence Agent API"}


# ── Feature endpoints ──────────────────────────────────────────────────────────

@app.post("/analyse/m1")
async def analyse_m1(request: AnalyseRequest):
    """
    M1 — Folder Structure Analysis.
    Fetches the real repo, then describes every directory in plain English.
    """
    try:
        # Fetch the real repo — this replaces MOCK_REPO_FILES entirely.
        # The returned dict has the same shape {filepath: bytes} so nothing
        # downstream needs to change at all.
        file_contents = await fetch_repo_files(request.github_url)

        graph       = build_dependency_graph(file_contents)
        graph_stats = analyze_graph(graph)

        # Detect language from the actual entry point of the fetched repo
        in_degrees       = dict(graph.in_degree())
        out_degrees      = dict(graph.out_degree())
        entry_candidates = [
            n for n in graph.nodes
            if in_degrees.get(n, 0) == 0 and out_degrees.get(n, 0) > 0
        ]
        detection = detect_entry_point(file_contents, entry_candidates)
        language  = detection.get("language", "javascript")

        result = run_m1_pipeline(
            file_contents = file_contents,
            graph_stats   = graph_stats,
            language      = language,
        )
        return result
    except ValueError as e:
        # ValueError means a bad URL or repo not found — that's a 400,
        # not a 500, because the problem is with the request not the server
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyse/m2")
async def analyse_m2(request: AnalyseRequest):
    """
    M2 — Entry Point Detection and Execution Flow Explanation.
    Fetches the real repo, detects the entry file, and explains startup flow.
    """
    try:
        file_contents = await fetch_repo_files(request.github_url)
        graph         = build_dependency_graph(file_contents)
        result        = run_m2_pipeline(file_contents, graph)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyse/m3")
async def analyse_m3(request: AnalyseRequest):
    """
    M3 — Dependency Mapping.
    Fetches the real repo and returns the full dependency graph,
    React Flow data, LLM context, and graph statistics.
    """
    try:
        file_contents = await fetch_repo_files(request.github_url)
        result        = run_m3_pipeline(file_contents)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))