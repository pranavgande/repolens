# Repolens

> AI-powered codebase intelligence for understanding unfamiliar repositories faster.

Repolens analyzes a repository and turns its structure and important source files into structured technical understanding: architecture, entry points, dependencies, execution flow, and critical files.

## Why Repolens?

Understanding an unfamiliar codebase is often the first bottleneck when joining a project or making a change. Repolens is designed to compress that first-pass investigation into a technical map engineers can use.

## Current architecture

- `frontend/` — React/Vite user interface
- `backend/` — Python analysis/API services
- `backend/m1/`, `backend/m2/`, `backend/b3/` — analysis modules

## Product workflow

```
Repository / folder
       ↓
Repository analysis
       ↓
Structure + important files
       ↓
AI-assisted technical analysis
       ↓
Architecture / flows / critical files
       ↓
Repolens dashboard
```

## Current status

Repolens is an early-stage developer tool. The repository currently contains the frontend and backend analysis system; the AI-assisted codebase-intelligence layer is being developed as part of the product roadmap.

## Roadmap

- [ ] GitHub repository ingestion
- [ ] Claude-powered repository analysis
- [ ] Structured architecture summaries
- [ ] Entry-point and execution-flow detection
- [ ] Dependency graph visualization
- [ ] Critical-file detection
- [ ] Change-impact analysis
- [ ] Shared team workspaces
- [ ] Evaluation benchmarks for codebase understanding

## Local development

### Prerequisites

- Node.js LTS
- npm
- Python 3.10+
- pip

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend normally runs on the Vite development URL shown in the terminal.

## Product positioning

Repolens is intended for:

- developers joining unfamiliar projects
- engineering teams onboarding contributors
- developers working with poorly documented repositories
- teams that need faster technical orientation before making changes

## Contributing

Issues and pull requests are welcome. Keep changes focused and document changes to setup or product behavior.

## License

See the repository license file.


## Claude configuration

Repolens uses Anthropic's official Python SDK for the B3 executive repository summary.

Set `ANTHROPIC_API_KEY` in the backend environment and optionally set `ANTHROPIC_MODEL` to choose the model. Keep API credentials server-side and never commit them.

Without an Anthropic key, the existing Gemini provider remains available as a development fallback.

The Claude integration uses Anthropic's Messages API.
