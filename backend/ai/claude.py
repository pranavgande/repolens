"""Shared Claude provider for Repolens AI analysis."""

import os
from anthropic import Anthropic

DEFAULT_MODEL = "claude-sonnet-5-5"


def is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def generate(*, system_prompt: str, user_prompt: str, max_tokens: int = 700) -> str:
    """Generate text with Claude through Anthropic's official Messages API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not configured")

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text_blocks = [
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text"
    ]
    result = " ".join(text_blocks).strip()
    if not result:
        raise RuntimeError("Claude returned no text content")
    return result
