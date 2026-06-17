"""
Generation endpoints — the headline feature.

`POST /api/generate/full` returns a complete brief in one shot.
`GET  /api/stream/generate` streams per-section progress via SSE.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ai_engine import get_engine
from database import get_db
from memory import get_index
from models import Project
from schemas import GenerateRequest, ProjectRead

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Synchronous generation ───────────────────────────────────────────────
@router.post("/full", response_model=ProjectRead)
def generate_full(payload: GenerateRequest, db: Session = Depends(get_db)) -> Project:
    """Generate a complete brief and persist it."""
    if not payload.concept.strip():
        raise HTTPException(status_code=400, detail="concept cannot be empty")

    engine = get_engine()
    index = get_index()
    memory_ctx = index.as_prompt_context(db, payload.concept, top_k=3)
    result = engine.generate(payload.concept, memory_context=memory_ctx)

    project = Project(concept=payload.concept)
    for field_name, value in result.to_persist_dict().items():
        if field_name in {"features", "stack", "tags"}:
            setattr(project, field_name, value)
        else:
            setattr(project, field_name, value)
    db.add(project)
    db.commit()
    db.refresh(project)
    index.invalidate()
    logger.info("Generated project #%d: %s", project.id, project.name)
    return project


# ── Streaming generation (Server-Sent Events) ───────────────────────────
@router.get("/stream")
async def stream_generate(
    concept: str = Query(..., min_length=3, max_length=600),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream a generation as server-sent events for the live visualisation."""

    async def event_source() -> AsyncGenerator[str, None]:
        engine = get_engine()
        index = get_index()
        memory_ctx = index.as_prompt_context(db, concept, top_k=3)

        # Container to capture the result for persistence after streaming
        from ai_engine import GenerationResult
        captured: dict = {"result": None}

        def emit(section: str, value: str, progress: int) -> None:
            """Push one SSE event."""
            payload = json.dumps({
                "section": section,
                "value": value,
                "progress": progress,
            })
            # FastAPI's StreamingResponse will flush when we yield
            yield_lines.append(f"event: section\ndata: {payload}\n\n")

        # We use a list to capture the synchronous generator's yields
        yield_lines: list = []

        # Run the synchronous section_callback-based generator in a thread
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_sync() -> GenerationResult:
            return engine.generate(
                concept,
                memory_context=memory_ctx,
                section_callback=lambda s, v, p: emit(s, v, p) or None,
            )

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as ex:
            result: GenerationResult = await loop.run_in_executor(ex, run_sync)

        # Persist the result
        project = Project(concept=concept)
        for field_name, value in result.to_persist_dict().items():
            if field_name in {"features", "stack", "tags"}:
                setattr(project, field_name, value)
            else:
                setattr(project, field_name, value)
        db.add(project)
        db.commit()
        db.refresh(project)
        index.invalidate()

        # Append a final 'done' event with the project id
        done_payload = json.dumps({
            "project_id": project.id,
            "name": project.name,
            "tagline": project.tagline,
            "problem": project.problem,
            "solution": project.solution,
            "features": project.features,
            "stack": project.stack,
            "marketing": project.marketing,
            "tags": project.tags,
        })
        yield_lines.append(f"event: done\ndata: {done_payload}\n\n")

        # Emit all collected lines
        for line in yield_lines:
            yield line

    return StreamingResponse(event_source(), media_type="text/event-stream")