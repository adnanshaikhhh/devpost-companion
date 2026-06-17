async def generate_submission(idea: str, problem: str, tech: str) -> SubmissionResult:
    """Generate a complete hackathon submission from a rough idea."""
    if not has_openai_key():
        return template_generate(idea, problem, tech)
    # ... use LangChain