# src/models.py
"""SQLAlchemy ORM models for the DevPost Companion."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from .database import Base


class Project(Base):
    """A saved hackathon project / generated submission."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    tagline = Column(String(280), nullable=True)
    description = Column(Text, nullable=True)
    problem = Column(Text, nullable=True)
    tech_stack = Column(String(500), nullable=True)
    features = Column(Text, nullable=True)
    talking_points = Column(Text, nullable=True)
    judge_appeal_json = Column(Text, nullable=True)
    score = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Serialize the project to a JSON-friendly dict."""
        return {
            "id": self.id,
            "name": self.name,
            "tagline": self.tagline,
            "description": self.description,
            "problem": self.problem,
            "tech_stack": self.tech_stack,
            "features": self.features.split(",") if self.features else [],
            "talking_points": self.talking_points.split("|") if self.talking_points else [],
            "judge_appeal": self.judge_appeal_json,
            "score": self.score,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }