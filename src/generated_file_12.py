# src/routers/share.py
"""Shareable export endpoint — the screenshot-worthy moment."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter()


@router.get("/{project_id}")
async def share_card(project_id: int, db: Session = Depends(get_db)):
    """Return a JSON payload describing a beautiful share card for a project."""
    row = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    data = row.to_dict()
    return {
        "project": data,
        "share_url": f"/?share={project_id}",
        "markdown": _to_markdown(data),
    }


@router.get("/{project_id}/markdown", response_class=PlainTextResponse)
async def share_markdown(project_id: int, db: Session = Depends(get_db)):
    """Return a copy-pasteable markdown export of a project."""
    row = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return _to_markdown(row.to_dict())


def _to_markdown(data: dict) -> str:
    """Render a project dict as a clean markdown export."""
    lines = [
        f"# {data['name']}",
        "",
        f"> {data.get('tagline', '')}",
        "",
    ]
    if data.get("description"):
        lines += [data["description"], ""]
    if data.get("features"):
        lines += ["## Features", ""]
        for f in data["features"]:
            lines += [f"- {f}"]
        lines.append("")
    if data.get("talking_points"):
        lines += ["## Demo talking points", ""]
        for t in data["talking_points"]:
            lines += [f"- {t}"]
        lines.append("")
    if data.get("tech_stack"):
        lines += ["## Tech stack", ""]
        for t in data["tech_stack"].replace(",", " ").split():
            lines += [f"`{t}`"]
        lines.append("")
    lines += [
        "---",
        "*Generated with [DevPost Companion](https://github.com/hermes/devpost-companion).*",
    ]
    return "\n".join(lines)