"""
CRUD endpoints for generated projects.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from memory import get_index
from models import Project
from schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter()


@router.get("", response_model=List[ProjectRead])
def list_projects(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[Project]:
    """List all projects, most recent first."""
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    return (
        db.query(Project)
        .order_by(Project.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    """Create a project manually (rarely used — generation endpoint saves too)."""
    project = Project(
        concept=payload.concept,
        name=payload.name,
        tagline=payload.tagline,
        problem=payload.problem,
        solution=payload.solution,
        marketing=payload.marketing,
    )
    project.features = payload.features
    project.stack = payload.stack
    project.tags = payload.tags
    db.add(project)
    db.commit()
    db.refresh(project)
    get_index().invalidate()
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    """Fetch a single project by id."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
) -> Project:
    """Partially update a project."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        if field_name in {"features", "stack", "tags"} and value is not None:
            setattr(project, field_name, value)
        elif value is not None:
            setattr(project, field_name, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a project permanently."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    get_index().invalidate()