# M3 Analyzer

M3 Analyzer helps inspect and explain code repositories through a web interface and backend analysis services.

The project is split into two parts:

- `frontend/` - user interface (React/Vite)
- `backend/` - API and analysis logic (Python)

## Project Structure

- `frontend/src/app/` - main UI pages, components, and context
- `backend/main.py` - backend API entrypoint
- `backend/m1/`, `backend/m2/`, `backend/b3/` - analysis modules

## Prerequisites

Install these before running locally:

- Node.js (LTS recommended)
- npm
- Python 3.10+ (or your project-supported version)
- pip

## Quick Start

### 1) Clone and open the project

```bash
git clone
cd m3_analyzer
```

### 2) Start the backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

By default, this should start the API on a local port (for example, `http://localhost:8000`).

### 3) Start the frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Then open the frontend URL shown in terminal (typically `http://localhost:5173`).

## How It Works

1. You provide repository/folder input in the frontend.
2. Frontend sends requests to the backend API.
3. Backend runs analysis modules and returns structured results.
4. Frontend renders summaries, flow explanations, and visual outputs.

## Configuration Notes

- If frontend and backend use different ports, ensure API base URL is set correctly in the frontend configuration.
- Keep backend dependencies in `backend/requirements.txt`.
- Keep frontend dependencies in `frontend/package.json`.

## Common Commands

Frontend:

```bash
npm run dev      # start dev server
npm run build    # build production assets
```

Backend:

```bash
uvicorn main:app --reload --port 8000   # run API service
```

## Troubleshooting

- If `npm install` fails, verify Node.js and npm versions.
- If Python packages fail to install, upgrade pip: `python -m pip install --upgrade pip`.
- If the frontend cannot reach backend, check API URL, ports, and terminal logs.

## Contributing

Keep changes focused and update this README when setup or behavior changes.