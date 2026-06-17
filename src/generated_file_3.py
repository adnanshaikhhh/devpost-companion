# src/main.py
"""DevPost Companion - FastAPI application entry point.

Serves both the REST API and the React frontend as a single deployable unit.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db, seed_demo_data
from .routers import generate, metrics, projects, share

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    init_db()
    seed_demo_data()
    yield


app = FastAPI(
    title="DevPost Companion",
    description="AI-powered hackathon submission generator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(share.router, prefix="/api/share", tags=["share"])

# Serve frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    """Serve the React app shell."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
async def health():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "devpost-companion",
        "version": "1.0.0",
    }