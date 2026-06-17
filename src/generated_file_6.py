# src/schemas.py
"""Pydantic schemas for request/response validation."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Payload for creating a new project from a rough idea."""
    name: str = Field(..., min_length=1, max_length=120, description="Working project name")
    problem: str = Field(..., min_length=10, description="Problem the project solves")
    tech_stack: str = Field("", description="Comma or space separated tech tags")
    idea: Optional[str] = Field("", description="Optional longer description of the idea")


class ProjectUpdate(BaseModel):
    """Payload for updating an existing project."""
    name: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    problem: Optional[str] = None
    tech_stack: Optional[str] = None
    features: Optional[str] = None
    talking_points: Optional[str] = None
    score: Optional[int] = None
    word_count: Optional[int] = None
    judge_appeal_json: Optional[str] = None


class ProjectOut(BaseModel):
    """Response shape for a saved project."""
    id: int
    name: str
    tagline: Optional[str] = None
    description: Optional[str] = None
    problem: Optional[str] = None
    tech_stack: Optional[str] = None
    features: List[str] = []
    talking_points: List[str] = []
    judge_appeal: Optional[str] = None
    score: int = 0
    word_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    """Payload for the headline generation call."""
    name: str
    problem: str
    tech_stack: str = ""
    idea: str = ""


class MetricsOut(BaseModel):
    """Aggregate stats for the metrics dashboard."""
    total_projects: int
    total_words_generated: int
    average_score: float
    top_tech_tags: List[dict]
    score_distribution: List[dict]
    recent_projects: List[ProjectOut]