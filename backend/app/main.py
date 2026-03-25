"""
OpenDocket API — Government Document Accessibility Platform

Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.api.documents import router as documents_router
from app.api.changes import router as changes_router
from app.api.discourse import router as discourse_router
from app.api.glossary import router as glossary_router
from app.api.webhooks import router as webhooks_router
from app.api.releases import router as releases_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: load active release config, verify DB connection
    print(f"🗂️  OpenDocket starting — active release: {settings.active_release}")
    yield
    # Shutdown
    print("🗂️  OpenDocket shutting down")


app = FastAPI(
    title="OpenDocket",
    description="Government Document Accessibility Platform — View, Track, Understand",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the frontend and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(changes_router, prefix="/api/changes", tags=["Changes"])
app.include_router(discourse_router, prefix="/api/discourse", tags=["Discourse"])
app.include_router(glossary_router, prefix="/api/glossary", tags=["Glossary"])
app.include_router(webhooks_router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(releases_router, prefix="/api/config", tags=["Config"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "release": settings.active_release}
