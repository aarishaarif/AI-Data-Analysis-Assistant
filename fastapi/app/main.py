from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import chat, conversations, datasets, health
from app.config import settings
from app.db.database import Base, engine

settings.dataset_storage_path.mkdir(parents=True, exist_ok=True)
settings.chart_storage_path.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="InsightFlow API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    """Provide a useful response when the API address is opened in a browser."""
    return {
        "status": "ok",
        "message": "InsightFlow API is running.",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


app.include_router(health.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.mount("/charts", StaticFiles(directory=settings.chart_storage_path), name="charts")
