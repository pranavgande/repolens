# api.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import your existing pipeline function — nothing in the pipeline changes
from main import run_m3_pipeline
from mock_data.mock_repo import MOCK_REPO_FILES

app = FastAPI(title="M3 Dependency Analyser")

# CORS is critical — without this, your Next.js frontend (running on
# localhost:3000) will be blocked from calling this API (on localhost:8000)
# because browsers enforce the "same-origin policy" by default.
# This middleware tells the browser "yes, cross-origin requests are allowed".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your Next.js dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic model defines the shape of the request body.
# FastAPI uses this to automatically validate incoming JSON.
class AnalyseRequest(BaseModel):
    github_url: str  # e.g. "https://github.com/expressjs/express"




@app.post("/analyse/m3")
async def analyse_m3(request: AnalyseRequest):
    """
    Main endpoint. Receives a GitHub URL, runs the full M3 pipeline,
    and returns all three outputs the frontend needs:
      - react_flow_data: nodes and edges for the graph visualisation
      - llm_context: compressed text ready to send to Claude/Gemini
      - graph_stats: critical files, entry points, clusters, etc.

    For now we're ignoring request.github_url and using mock data,
    which is the right approach — get the pipeline working end-to-end
    over the network first, then swap in real GitHub fetching later.
    """
    try:
        # This is your existing function — completely unchanged.
        # In a real implementation, you'd fetch file_contents from GitHub
        # using request.github_url instead of MOCK_REPO_FILES.
        result = run_m3_pipeline(MOCK_REPO_FILES)

        # FastAPI automatically converts this dict to a JSON HTTP response.
        # The dict already has exactly what the frontend needs.
        return result

    except Exception as e:
        # If something goes wrong, return a proper HTTP 500 error
        # rather than crashing the server silently.
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Simple endpoint to verify the server is running."""
    return {"status": "ok"}

@app.get("/")
async def health_check():
    """Simple endpoint to verify the server is running."""
    return {"status": "ok"}