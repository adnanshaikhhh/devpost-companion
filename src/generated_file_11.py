# src/routers/metrics.py
"""Aggregate metrics for the dashboard view."""
from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter()


@router.get("/")
async def metrics(db: Session = Depends(get_db)):
    """Compute dashboard statistics over all saved projects."""
    rows = db.query(models.Project).all()
    total = len(rows)
    total_words = sum(r.word_count or 0 for r in rows)
    avg_score = round(sum(r.score or 0 for r in rows) / total, 1) if total else 0.0

    # Tech tag frequency
    tag_counter: Counter = Counter()
    for r in rows:
        for tag in (r.tech_stack or "").replace(",", " ").split():
            tag = tag.strip()
            if tag:
                tag_counter[tag] += 1
    top_tags = [{"tag": t, "count": c} for t, c in tag_counter.most_common(8)]

    # Score distribution buckets
    buckets = {"0-40": 0, "40-60": 0, "60-75": 0, "75-90": 0, "90-100": 0}
    for r in rows:
        s = r.score or 0
        if s < 40: buckets["0-40"] += 1
        elif s < 60: buckets["40-60"] += 1
        elif s < 75: buckets["60-75"] += 1
        elif s < 90: buckets["75-90"] += 1
        else: buckets["90-100"] += 1
    distribution = [{"bucket": k, "count": v} for k, v in buckets.items()]

    # Recent projects
    recent = sorted(rows, key=lambda r: r.created_at or 0, reverse=True)[:5]
    return {
        "total_projects": total,
        "total_words_generated": total_words,
        "average_score": avg_score,
        "top_tech_tags": top_tags,
        "score_distribution": distribution,
        "recent_projects": [r.to_dict() for r in recent],
    }