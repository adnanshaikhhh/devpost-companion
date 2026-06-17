"""
Pydantic request/response schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Project ────────────────────────────────────────────────────────────────
class ProjectBase(BaseModel):
    concept: str = Field(..., min_length=3, max_length=600)
    name: str = Field("", max_length=120)
    tagline: str = Field("", max_length=240)
    problem: str = ""
    solution: str = ""
    marketing: str = ""
    features: List[str] = []
    stack: List[str] = []
    tags: List[str] = []


class ProjectCreate(ProjectBase):
    """Used when the user manually saves a project."""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    marketing: Optional[str] = None
    features: Optional[List[str]] = None
    stack: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ProjectRead(ProjectBase):
    id: int
    fingerprint: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Generation ────────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    concept: str = Field(..., min_length=3, max_length=600)
    stream: bool = False


class SectionEvent(BaseModel):
    """One SSE event payload emitted during streaming generation."""
    section: str
    value: str
    progress: int


# ── Memory ────────────────────────────────────────────────────────────────
class MemoryHit(BaseModel):
    id: int
    name: str
    tagline: str
    concept: str
    similarity: float


# ── Stats ─────────────────────────────────────────────────────────────────
class StatsResponse(BaseModel):
    project_count: int
    section_count: int
    feature_count: int
    total_words: int
    top_tags: List[dict]
    recent_projects: List[ProjectRead]