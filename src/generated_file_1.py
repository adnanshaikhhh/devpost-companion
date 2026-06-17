"""DevPost Companion - FastAPI application entry point."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import init_db
from .routers import projects, generate, metrics, share

app = FastAPI(
    title="DevPost Companion",
    description="AI-powered hackathon submission generator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB
init_db()

# Routers
app.include_router(projects.router)
app.include_router(generate.router)
app.include_router(metrics.router)
app.include_router(share.router)

# Static files
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "devpost-companion"}