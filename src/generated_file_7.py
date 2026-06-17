# src/ai_engine.py
"""AI generation engine with LangChain + OpenAI and a smart template fallback."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class SubmissionResult:
    """Structured output of the generation pipeline."""
    title: str
    tagline: str
    description: str
    features: List[str]
    talking_points: List[str]
    tech_tags: List[str]
    judge_appeal: dict
    score: int
    word_count: int
    source: str  # "openai" or "template"


def has_openai_key() -> bool:
    """Check whether an OpenAI key is available."""
    return bool(os.getenv("OPENAI_API_KEY"))


# ---------- Heuristic analysis ----------

POSITIVE_KEYWORDS = {
    "ai", "agent", "automation", "real-time", "instant", "one-tap", "beautiful",
    "memory", "delightful", "elegant", "fast", "simple", "smart", "learns",
    "personal", "beautiful", "polished", "production", "shipping", "launch",
    "open source", "free", "developer", "designer", "team", "collaborate",
}

INNOVATION_KEYWORDS = {
    "novel", "first", "new", "unique", "innovative", "agentic", "rag",
    "fine-tuned", "multimodal", "voice", "vision", "generative", "synthesis",
    "real-time", "live", "streaming", "autonomous", "self-improving",
}

ORIGINALITY_KEYWORDS = {
    "companion", "sidekick", "buddy", "co-pilot", "ghost", "wizard", "oracle",
    "crystal", "spark", "lens", "forge", "atelier", "studio",
}


def _keyword_score(text: str, keywords: set) -> int:
    """Return a 0-100 score for keyword density in the text."""
    if not text:
        return 40
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 40
    hits = sum(1 for w in words if w in keywords)
    density = hits / max(len(words), 1) * 100
    return min(100, int(40 + density * 6))


def analyze_judge_appeal(name: str, problem: str, tech_stack: str, description: str = "") -> dict:
    """Heuristically score a submission on 5 dimensions judges care about."""
    text = " ".join([name, problem, tech_stack, description]).lower()
    name_len = len(name.split()) if name else 0
    problem_len = len(problem.split()) if problem else 0
    tech_count = len([t for t in re.split(r"[,\s]+", tech_stack) if t.strip()])

    clarity = min(100, 50 + problem_len * 2 - abs(name_len - 2) * 5)
    innovation = _keyword_score(text, INNOVATION_KEYWORDS)
    feasibility = min(100, 55 + tech_count * 6)
    polish = min(100, 45 + _keyword_score(text, POSITIVE_KEYWORDS) // 2)
    originality = _keyword_score(text, ORIGINALITY_KEYWORDS)

    return {
        "clarity": max(20, min(100, clarity)),
        "innovation": max(20, min(100, innovation)),
        "feasibility": max(20, min(100, feasibility)),
        "polish": max(20, min(100, polish)),
        "originality": max(20, min(100, originality)),
    }


def _overall_score(appeal: dict) -> int:
    """Weighted average of judge appeal dimensions."""
    weights = {
        "clarity": 0.25,
        "innovation": 0.20,
        "feasibility": 0.20,
        "polish": 0.20,
        "originality": 0.15,
    }
    return int(sum(appeal[k] * w for k, w in weights.items()))


# ---------- Template generator ----------

TITLE_PATTERNS = [
    "{name}: {verb} {object} with {magic}",
    "Meet {name}, the {adj} {category} that {benefit}",
    "{name} — {benefit} in {speed}",
    "Build {thing} faster with {name}",
]


def _pick_word(bank: List[str], seed: str, default: str) -> str:
    """Deterministic word picker from a small bank, keyed off a seed string."""
    if not bank:
        return default
    idx = sum(ord(c) for c in seed) % len(bank)
    return bank[idx]


ADJ_BANK = ["AI-powered", "delightful", "lightning-fast", "elegant", "intuitive"]
CATEGORY_BANK = ["companion", "sidekick", "co-pilot", "assistant", "studio"]
MAGIC_BANK = ["LLMs", "AI", "agents", "RAG", "embeddings"]
SPEED_BANK = ["seconds", "a weekend", "minutes", "a single tap"]


def template_generate(name: str, problem: str, tech_stack: str, idea: str = "") -> SubmissionResult:
    """Produce a high-quality submission from a rough idea without an LLM."""
    seed = name or idea or "project"
    tags = [t.strip() for t in re.split(r"[,\s]+", tech_stack) if t.strip()][:6]
    if not tags:
        tags = ["Python", "FastAPI", "OpenAI"]

    # Title
    title_pattern = _pick_word(TITLE_PATTERNS, seed, TITLE_PATTERNS[0])
    title = title_pattern.format(
        name=name or "MyProject",
        verb=_pick_word(["craft", "ship", "launch", "build", "polish"], seed, "ship"),
        object=_pick_word(["submissions", "wins", "ideas", "demos"], seed, "submissions"),
        magic=_pick_word(MAGIC_BANK, seed, "AI"),
        adj=_pick_word(ADJ_BANK, seed, "AI-powered"),
        category=_pick_word(CATEGORY_BANK, seed, "companion"),
        benefit=_pick_word(["win hackathons", "ship faster", "save hours", "stand out"], seed, "ship faster"),
        speed=_pick_word(SPEED_BANK, seed, "seconds"),
        thing=_pick_word(["submissions", "demos", "prototypes"], seed, "submissions"),
    )

    # Tagline
    benefit = _pick_word(
        ["saves time", "wins judges", "delights users", "ships in a weekend"],
        seed, "ships in a weekend",
    )
    audience = _pick_word(
        ["hackathon builders", "busy developers", "indie hackers", "student teams"],
        seed, "hackathon builders",
    )
    tagline = f"{name} is the { _pick_word(ADJ_BANK, seed, 'AI-powered')} companion that {benefit} for {audience}."

    # Description
    desc_paras = [
        f"**{name}** turns rough hackathon ideas into polished, judge-ready submissions in seconds. "
        f"Built for {audience}, it removes the blank-page problem that costs teams hours of momentum.",

        f"At its core, {name} combines a streamlined intake form with an LLM-powered drafting engine. "
        f"You describe the problem, drop in your tech stack, and the app returns a complete submission — "
        f"optimized title, punchy tagline, three-paragraph description, feature list, and demo talking points — "
        f"ready to paste straight into Devpost.",

        f"What makes {name} memorable is the live, real-time **judge appeal radar**: as you type, five "
        f"dimensions (clarity, innovation, feasibility, polish, originality) update on the spot, so you can "
        f"see exactly where your submission lands and where to push it further. Ship the demo, save the "
        f"project, export a beautiful share card, and submit with confidence.",
    ]
    description = "\n\n".join(desc_paras)

    # Features
    features = [
        "One-tap submission generation from a rough idea",
        "Live judge-appeal radar with five real-time scores",
        "Persistent project memory across sessions",
        "Beautiful shareable export card",
        "Tech-stack-aware tag suggestions",
        "Metrics dashboard for portfolio tracking",
    ]

    # Talking points
    talking_points = [
        "Show the empty state — zero to first idea in 5 seconds",
        "Type a one-line problem, hit Generate",
        "Watch the judge-appeal radar animate in real time",
        "Save the submission and reopen from history",
        "Export a beautiful share card for social",
        "End on the metrics dashboard — total projects, average score, top tech",
    ]

    appeal = analyze_judge_appeal(name, problem, tech_stack, description)
    score = _overall_score(appeal)
    word_count = len(description.split())

    return SubmissionResult(
        title=title,
        tagline=tagline,
        description=description,
        features=features,
        talking_points=talking_points,
        tech_tags=tags,
        judge_appeal=appeal,
        score=score,
        word_count=word_count,
        source="template",
    )


# ---------- OpenAI / LangChain generator ----------

async def openai_generate(name: str, problem: str, tech_stack: str, idea: str = "") -> SubmissionResult:
    """Generate a submission using LangChain + OpenAI. Falls back to templates on error."""
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser

        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.7)
        parser = JsonOutputParser()

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert Devpost hackathon submission strategist. "
                       "You write concise, punchy, judge-winning copy. Always return strict JSON."),
            ("human",
             "Generate a complete hackathon submission as JSON with keys: "
             "title, tagline, description (3 paragraphs), features (list of 5-6 short strings), "
             "talking_points (list of 5-6 short strings), tech_tags (list), judge_appeal "
             "(object with clarity, innovation, feasibility, polish, originality integers 0-100).\n\n"
             "Project name: {name}\n"
             "Problem: {problem}\n"
             "Tech stack: {tech_stack}\n"
             "Idea: {idea}\n\n"
             "Return only the JSON object, no markdown fences."),
        ])

        chain = prompt | llm | parser
        result = await chain.ainvoke({
            "name": name, "problem": problem, "tech_stack": tech_stack, "idea": idea,
        })

        appeal = result.get("judge_appeal") or analyze_judge_appeal(name, problem, tech_stack, result.get("description", ""))
        for k in ("clarity", "innovation", "feasibility", "polish", "originality"):
            appeal[k] = max(0, min(100, int(appeal.get(k, 70))))

        description = result.get("description", "")
        return SubmissionResult(
            title=result.get("title", name),
            tagline=result.get("tagline", ""),
            description=description,
            features=result.get("features", []),
            talking_points=result.get("talking_points", []),
            tech_tags=result.get("tech_tags", [t.strip() for t in tech_stack.split(",") if t.strip()]),
            judge_appeal=appeal,
            score=_overall_score(appeal),
            word_count=len(description.split()),
            source="openai",
        )
    except Exception as exc:  # pragma: no cover - network path
        # Fall back to templates if the LLM call fails for any reason
        result = template_generate(name, problem, tech_stack, idea)
        result.source = "template-fallback"
        return result


async def generate_submission(name: str, problem: str, tech_stack: str, idea: str = "") -> SubmissionResult:
    """Top-level entry point — uses OpenAI when available, templates otherwise."""
    if has_openai_key():
        return await openai_generate(name, problem, tech_stack, idea)
    return template_generate(name, problem, tech_stack, idea)


def result_to_dict(result: SubmissionResult) -> dict:
    """Convert a SubmissionResult to a JSON-serializable dict."""
    d = asdict(result)
    d["judge_appeal"] = json.dumps(result.judge_appeal)
    return d