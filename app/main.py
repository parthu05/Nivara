from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.journal import router as journal_router
from app.api.mood import router as mood_router
from app.config import settings
from app.database.models import init_db
from app.rag.retriever import ingest_knowledge_base

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


async def _ingest_knowledge_base() -> None:
    try:
        await asyncio.to_thread(ingest_knowledge_base)
    except Exception as exc:
        print(f"[nivara] knowledge ingest skipped: {exc}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    ingest_task = asyncio.create_task(_ingest_knowledge_base())
    try:
        yield
    finally:
        ingest_task.cancel()


app = FastAPI(
    title="Nivara",
    description="Local-first mental wellness companion. Not therapy or emergency care.",
    lifespan=lifespan,
)
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(journal_router)
app.include_router(mood_router)


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "provider": settings.llm_provider,
        "disclaimer": "Nivara is not a medical service.",
    }


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
