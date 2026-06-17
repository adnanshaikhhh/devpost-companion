# src/database.py
"""SQLite database configuration and session management."""
from pathlib import Path
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "companion.db"

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a database session and ensure cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def seed_demo_data():
    """Insert a couple of example projects on first run."""
    from . import models
    from datetime import datetime
    db = SessionLocal()
    try:
        if db.query(models.Project).count() > 0:
            return
        demo = models.Project(
            name="StudyBuddy",
            tagline="AI study partner that turns your notes into practice tests.",
            description="StudyBuddy uses LLMs to convert lecture notes into spaced-repetition flashcards and mock exams, helping students learn 3x faster.",
            problem="Students spend hours re-reading notes without active recall.",
            tech_stack="Python, FastAPI, React, OpenAI, PostgreSQL",
            features="Auto-generated flashcards,Spaced repetition,Mock exams,Progress tracking",
            talking_points="Show empty state,Demo one-tap flashcard generation,Display retention metrics",
            judge_appeal_json='{"clarity":88,"innovation":82,"feasibility":91,"polish":79,"originality":75}',
            score=83,
            word_count=42,
        )
        db.add(demo)
        db.commit()
    finally:
        db.close()