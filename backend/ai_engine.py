"""
AI engine — orchestrates LangChain + OpenAI (with a mock fallback).

The mock provider is deterministic and offline-friendly, which makes
the project demoable on a hackathon judging rig with no internet.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Result container ─────────────────────────────────────────────────────
@dataclass
class GenerationResult:
    """A complete generated brief, ready to persist."""
    name: str = ""
    tagline: str = ""
    problem: str = ""
    solution: str = ""
    marketing: str = ""
    features: List[str] = field(default_factory=list)
    stack: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    fingerprint: str = ""

    def to_persist_dict(self) -> Dict:
        return {
            "name": self.name,
            "tagline": self.tagline,
            "problem": self.problem,
            "solution": self.solution,
            "marketing": self.marketing,
            "features": self.features,
            "stack": self.stack,
            "tags": self.tags,
            "fingerprint": self.fingerprint,
        }


# ── Mock provider (deterministic, offline) ──────────────────────────────
class MockProvider:
    """Generate a plausible brief from a concept using template rules."""

    SUFFIXES = ["Forge", "ly", "Hub", "Mind", "Pilot", "Loop", "Kit", "OS"]

    STACK_POOL = [
        "React", "FastAPI", "PostgreSQL", "OpenAI", "LangChain",
        "TailwindCSS", "Vite", "SQLite", "Redis", "Next.js",
        "TypeScript", "Python", "Docker", "Railway", "Vercel",
    ]

    TAG_POOL = [
        "ai", "productivity", "education", "developer-tools",
        "saas", "consumer", "no-code", "automation",
    ]

    def _extract_noun(self, concept: str) -> str:
        """Naively pull the dominant noun from the concept."""
        cleaned = re.sub(r"[^a-zA-Z\s]", "", concept).strip()
        words = [w for w in cleaned.split() if len(w) > 3]
        return words[0].capitalize() if words else "Idea"

    def _make_name(self, concept: str) -> str:
        noun = self._extract_noun(concept)
        suffix = self.SUFFIXES[hash(concept) % len(self.SUFFIXES)]
        return f"{noun}{suffix}"

    def _make_tagline(self, concept: str, name: str) -> str:
        return f"{name} turns raw {self._extract_noun(concept).lower()} into outcomes that compound."

    def _make_problem(self, concept: str) -> str:
        noun = self._extract_noun(concept).lower()
        return (
            f"• {noun.capitalize()} work is fragmented across too many tools and notecards.\n"
            f"• People lose hours every week doing {noun} tasks that should be automatic.\n"
            f"• Existing solutions either oversimplify the problem or overshoot the budget."
        )

    def _make_solution(self, concept: str, name: str) -> str:
        return (
            f"{name} is an AI-native workflow that ingests a user's raw {self._extract_noun(concept).lower()} "
            f"and converts it into structured, shareable, and reusable artifacts. "
            f"It learns from prior sessions, suggesting the next best action with full context. "
            f"Aim: replace a 90-minute manual flow with a 30-second one-tap interaction."
        )

    def _make_features(self, concept: str) -> List[str]:
        noun = self._extract_noun(concept).lower()
        return [
            f"One-tap {noun} generation with explainable AI",
            "Persistent memory across sessions and devices",
            "Beautiful, shareable output in Markdown, HTML, and PNG",
            "Real-time visualization that reacts as you build",
            "Open API and webhook integrations for power users",
        ]

    def _make_stack(self) -> List[str]:
        # Stable but concept-fingerprinted subset
        seed = int(hashlib.sha1(b"stack").hexdigest(), 16)
        return self.STACK_POOL[seed % 3 : seed % 3 + 5]

    def _make_tags(self, concept: str) -> List[str]:
        seed = sum(ord(c) for c in concept.lower())
        return [self.TAG_POOL[seed % len(self.TAG_POOL)],
                self.TAG_POOL[(seed + 2) % len(self.TAG_POOL)]]

    def _make_marketing(self, concept: str, name: str) -> str:
        return (
            f"🚀 Just launched {name} — {concept.lower()}. "
            f"From blank page to submission-ready brief in 30 seconds. "
            f"#buildinpublic #ai #hackathon"
        )

    def _fingerprint(self, concept: str) -> str:
        return hashlib.sha256(concept.strip().lower().encode()).hexdigest()[:32]

    def generate(self, concept: str, memory_context: Optional[str] = None) -> GenerationResult:
        """Produce a deterministic GenerationResult from a concept string."""
        result = GenerationResult(
            name=self._make_name(concept),
            tagline=self._make_tagline(concept, self._make_name(concept)),
            problem=self._make_problem(concept),
            solution=self._make_solution(concept, self._make_name(concept)),
            features=self._make_features(concept),
            stack=self._make_stack(),
            tags=self._make_tags(concept),
            marketing=self._make_marketing(concept, self._make_name(concept)),
            fingerprint=self._fingerprint(concept),
        )
        if memory_context:
            # Slight nudge to differentiate from prior generations
            result.tagline += f" (v{len(memory_context) % 9 + 2})"
        return result


# ── OpenAI / LangChain provider ─────────────────────────────────────────
class OpenAIProvider:
    """Thin wrapper around LangChain's ChatOpenAI for our 7 fields."""

    def __init__(self) -> None:
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser

        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )
        self.prompt_tmpl = ChatPromptTemplate.from_messages(
            [
                ("system", "You generate concise, distinctive hackathon project briefs. "
                           "Return strict JSON with keys: name, tagline, problem, solution, "
                           "marketing, features (array of 5 strings), stack (array of 5), "
                           "tags (array of 3)."),
                ("user", "Concept: {concept}\n\nMemory hints: {memory}\n\nReturn JSON only."),
            ]
        )
        self.parser = JsonOutputParser()

    def generate(self, concept: str, memory_context: Optional[str] = None) -> GenerationResult:
        from langchain_core.runnables import RunnableLambda
        try:
            chain = self.prompt_tmpl | self.llm | self.parser
            data = chain.invoke({
                "concept": concept,
                "memory": memory_context or "none",
            })
        except Exception as exc:  # pragma: no cover - network errors
            logger.warning("OpenAI call failed (%s); falling back to mock", exc)
            return MockProvider().generate(concept, memory_context)

        fingerprint = hashlib.sha256(concept.strip().lower().encode()).hexdigest()[:32]
        return GenerationResult(
            name=str(data.get("name", ""))[:120],
            tagline=str(data.get("tagline", ""))[:240],
            problem=str(data.get("problem", "")),
            solution=str(data.get("solution", "")),
            marketing=str(data.get("marketing", "")),
            features=[str(x) for x in (data.get("features") or [])][:8],
            stack=[str(x) for x in (data.get("stack") or [])][:8],
            tags=[str(x) for x in (data.get("tags") or [])][:6],
            fingerprint=fingerprint,
        )


# ── Public facade ────────────────────────────────────────────────────────
class AIEngine:
    """The single entry point used by the routers."""

    def __init__(self) -> None:
        self._provider = OpenAIProvider() if settings.has_openai else MockProvider()
        logger.info("AI engine initialised with %s",
                    "OpenAI" if settings.has_openai else "mock provider")

    def generate(
        self,
        concept: str,
        memory_context: Optional[str] = None,
        section_callback: Optional[Callable[[str, str, int], None]] = None,
    ) -> GenerationResult:
        """Generate a brief. If a section_callback is provided, emit progress.

        Note: section_callback is supported by the OpenAI provider via
        individual field calls; the mock provider emits synchronously.
        """
        if section_callback is None:
            return self._provider.generate(concept, memory_context)

        # Synchronous section emission works for both providers
        result = self._provider.generate(concept, memory_context)
        sections: List[tuple] = [
            ("name", result.name, 14),
            ("tagline", result.tagline, 28),
            ("problem", result.problem, 42),
            ("solution", result.solution, 56),
            ("features", json.dumps(result.features), 70),
            ("stack", json.dumps(result.stack), 84),
            ("marketing", result.marketing, 100),
        ]
        for section, value, progress in sections:
            section_callback(section, value, progress)
        return result


# ── Module-level singleton ───────────────────────────────────────────────
_engine: Optional[AIEngine] = None


def get_engine() -> AIEngine:
    """Lazy singleton accessor used as a FastAPI dependency."""
    global _engine
    if _engine is None:
        _engine = AIEngine()
    return _engine