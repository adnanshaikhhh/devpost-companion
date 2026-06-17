"""
ORM models for projects and memory entries.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Project(Base):
    """A generated hackathon project brief."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    tagline: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    problem: Mapped[str] = mapped_column(Text, nullable=False, default="")
    solution: Mapped[str] = mapped_column(Text, nullable=False, default="")
    marketing: Mapped[str] = mapped_column(Text, nullable=False, default="")
    features_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    stack_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Convenience accessors (JSON columns) ──────────────────────────
    @property
    def features(self) -> List[str]:
        """Parse features_json into a Python list."""
        try:
            return json.loads(self.features_json or "[]")
        except json.JSONDecodeError:
            return []

    @features.setter
    def features(self, value: Optional[List[str]]) -> None:
        self.features_json = json.dumps(value or [])

    @property
    def stack(self) -> List[str]:
        try:
            return json.loads(self.stack_json or "[]")
        except json.JSONDecodeError:
            return []

    @stack.setter
    def stack(self, value: Optional[List[str]]) -> None:
        self.stack_json = json.dumps(value or [])

    @property
    def tags(self) -> List[str]:
        try:
            return json.loads(self.tags_json or "[]")
        except json.JSONDecodeError:
            return []

    @tags.setter
    def tags(self, value: Optional[List[str]]) -> None:
        self.tags_json = json.dumps(value or [])

    def to_dict(self) -> dict:
        """Serialise to a JSON-safe dict (used by Pydantic layer)."""
        return {
            "id": self.id,
            "concept": self.concept,
            "name": self.name,
            "tagline": self.tagline,
            "problem": self.problem,
            "solution": self.solution,
            "marketing": self.marketing,
            "features": self.features,
            "stack": self.stack,
            "tags": self.tags,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }