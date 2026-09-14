# InsightFlow AI Data Analysis Assistant

## Structure

- `frontend/` — Vite single-page client
- `fastapi/` — FastAPI API, SQLite persistence, uploaded files, charts, and tests

## Run locally

Start the API:

```bash
cd fastapi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In another terminal, start the client:

```bash
cd frontend
npm install
npm run dev
```

## Run with Docker

Build and start both services:

```bash
docker compose up --build
```

- App: `http://localhost:8080`
- API: `http://localhost:8000/`
- API documentation: `http://localhost:8000/docs`

Uploaded datasets, charts, and the SQLite database are stored in the named
`insightflow-data` Docker volume. Stop containers with `docker compose down`;
the data volume remains intact.

## CI/CD

The GitHub Actions workflow in `.github/workflows/ci-cd.yml` runs backend tests
and the frontend production build on pull requests. A push to `main` also builds
and publishes tagged API and frontend images to GitHub Container Registry (GHCR).
Ensure GitHub Actions has permission to write packages for the repository.

The published image names are `ghcr.io/<your-github-user-or-org>/insightflow-api`
and `ghcr.io/<your-github-user-or-org>/insightflow-frontend`.

Copy `fastapi/.env.example` to `fastapi/.env` to customize storage, expiry, and CORS settings. The client reads `frontend/.env` when you want to set a different API address.

## Deploy on Render (free tier)

This repository includes `render.yaml` for a free Render deployment:

- `insightflow-api` is built from `fastapi/Dockerfile`.
- `insightflow-frontend` is deployed as a Vite static site.

When creating the Blueprint, Render will ask for two values:

1. `VITE_API_URL`: `https://<your-api-service>.onrender.com/api/v1`
2. `FRONTEND_ORIGINS`: `https://<your-frontend-service>.onrender.com`

The free plan has temporary storage. Consequently, the SQLite database, uploaded
datasets, generated charts, and conversation history reset after an API restart
or redeploy. No paid disk is required, but this deployment is suitable only for
demo or portfolio use.
