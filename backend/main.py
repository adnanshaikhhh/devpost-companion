"""
Devpost Companion — FastAPI entry point.

Wires together the database, CORS, routers, and a small static-file
fallback so a single Railway container can serve both the API and
the built React app.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from database import init_db
from routers import generate, memory, projects, stats, export as export_router

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("devpost_companion")

# ── Settings ──────────────────────────────────────────────────────────────
settings = get_settings()


# ── Lifespan: init DB on startup ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising database at %s", settings.database_url)
    init_db()
    logger.info("App ready (env=%s)", settings.app_env)
    yield
    logger.info("Shutting down")


# ── App factory ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Devpost Companion",
    version="1.0.0",
    description="AI-powered productivity companion for hackathon builders.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(export_router.router, prefix="/api/export", tags=["export"])


# ── Healthcheck ───────────────────────────────────────────────────────────
@app.get("/api/health", tags=["meta"])
def health() -> dict:
    """Liveness probe used by Railway / Docker healthchecks."""
    return {
        "status": "ok",
        "env": settings.app_env,
        "ai_provider": "openai" if settings.has_openai else "mock",
    }


# ── Static file serving (frontend build) ──────────────────────────────────
STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if STATIC_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=STATIC_DIR / "assets"),
        name="assets",
    )

    @app.get("/", include_in_schema=False)
    def serve_index() -> FileResponse:
        """Serve the React SPA root."""
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        """Fallback for client-side routes."""
        # Never shadow API routes
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/", tags=["meta"])
    def root() -> dict:
        """API root when the frontend has not been built yet."""
        return {
            "message": "Devpost Companion API",
            "docs": "/docs",
            "frontend": "run `npm run build` in /frontend to enable static serving",
        }