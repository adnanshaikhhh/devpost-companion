# src/routers/generate.py
"""Headline generation endpoint — the 5-second wow moment."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..ai_engine import generate_submission, result_to_dict
from ..database import get_db

router = APIRouter()


@router.post("/")
async def generate(payload: schemas.GenerateRequest, db: Session = Depends(get_db)):
    """Generate a complete submission from a rough idea.

    Returns the full generated bundle and, if `persist` is true, also saves
    it to the projects table.
    """
    result = await generate_submission(
        name=payload.name, problem=payload.problem,
        tech_stack=payload.tech_stack, idea=payload.idea,
    )
    data = result_to_dict(result)
    return {
        "ok": True,
        "source": result.source,
        "submission": data,
    }


@router.post("/save")
async def generate_and_save(payload: schemas.GenerateRequest, db: Session = Depends(get_db)):
    """Generate and immediately persist a submission."""
    result = await generate_submission(
        name=payload.name, problem=payload.problem,
        tech_stack=payload.tech_stack, idea=payload.idea,
    )
    row = models.Project(
        name=payload.name.strip(),
        problem=payload.problem.strip(),
        tech_stack=payload.tech_stack.strip(),
        tagline=result.tagline,
        description=result.description,
        features=",".join(result.features),
        talking_points="|".join(result.talking_points),
        judge_appeal_json=str(result.judge_appeal).replace("'", '"'),
        score=result.score,
        word_count=result.word_count,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "source": result.source, "project": row.to_dict()}