# src/routers/projects.py
"""CRUD endpoints for saved projects."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("/", response_model=List[schemas.ProjectOut])
async def list_projects(db: Session = Depends(get_db)):
    """Return all saved projects, newest first."""
    rows = db.query(models.Project).order_by(models.Project.created_at.desc()).all()
    return [r.to_dict() for r in rows]


@router.get("/{project_id}", response_model=schemas.ProjectOut)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Return a single project by id."""
    row = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return row.to_dict()


@router.post("/", response_model=schemas.ProjectOut)
async def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Persist a new project from a rough idea."""
    row = models.Project(
        name=payload.name.strip(),
        problem=payload.problem.strip(),
        tech_stack=payload.tech_stack.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.to_dict()


@router.patch("/{project_id}", response_model=schemas.ProjectOut)
async def update_project(project_id: int, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    """Update an existing project (typically after generation)."""
    row = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row.to_dict()


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project by id."""
    row = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(row)
    db.commit()
    return {"deleted": project_id}