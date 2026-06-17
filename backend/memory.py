"""
Persistent memory layer.

We use a TF-IDF + n-gram fingerprint for fast similarity search across
project concepts. No external vector DB needed for the MVP.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models import Project

logger = logging.getLogger(__name__)


@dataclass
class MemoryHit:
    """A similarity hit against stored memory."""
    project: Project
    similarity: float


def _normalise(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class MemoryIndex:
    """In-memory TF-IDF index over the projects table.

    Recomputes lazily; for the MVP, the project count is small (<< 10k).
    """

    def __init__(self) -> None:
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None
        self._ids: List[int] = []
        self._dirty = True

    def invalidate(self) -> None:
        """Mark the index as needing a rebuild."""
        self._dirty = True

    def _rebuild(self, db) -> None:
        projects: List[Project] = db.query(Project).order_by(Project.id).all()
        self._ids = [p.id for p in projects]
        corpus = [_normalise(f"{p.concept} {p.name} {p.tagline} {' '.join(p.tags)}")
                  for p in projects]
        if not corpus:
            self._vectorizer = None
            self._matrix = None
            return
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_features=2000,
        )
        self._matrix = self._vectorizer.fit_transform(corpus)
        self._dirty = False
        logger.info("Memory index rebuilt: %d projects", len(projects))

    def recall(self, db, concept: str, top_k: int = 3) -> List[MemoryHit]:
        """Return the top-k most similar prior projects."""
        if self._dirty:
            self._rebuild(db)
        if not self._ids or self._vectorizer is None:
            return []
        query_vec = self._vectorizer.transform([_normalise(concept)])
        sims = cosine_similarity(query_vec, self._matrix).flatten()
        ranked = sims.argsort()[::-1][:top_k]
        hits: List[MemoryHit] = []
        projects = {p.id: p for p in db.query(Project).all()}
        for idx in ranked:
            pid = self._ids[idx]
            sim = float(sims[idx])
            if sim <= 0.0:
                continue
            proj = projects.get(pid)
            if proj:
                hits.append(MemoryHit(project=proj, similarity=sim))
        return hits

    def as_prompt_context(self, db, concept: str, top_k: int = 3) -> str:
        """Format the top-k hits as an LLM prompt string."""
        hits = self.recall(db, concept, top_k=top_k)
        if not hits:
            return ""
        lines = ["Prior projects to differentiate from:"]
        for h in hits:
            lines.append(
                f"- '{h.project.name}' — {h.project.tagline} "
                f"(similarity {h.similarity:.2f})"
            )
        return "\n".join(lines)


# ── Module-level singleton ───────────────────────────────────────────────
_index = MemoryIndex()


def get_index() -> MemoryIndex:
    """Return the process-wide index."""
    return _index