"""Claude-powered repository summarisation for Repolens.

Claude is the primary AI provider for the B3 executive summary.
Set ANTHROPIC_API_KEY in the server environment to enable it.
"""

import os
from anthropic import Anthropic

DEFAULT_MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = """You are a senior software architect writing a concise technical
briefing for a developer who is about to work on an unfamiliar codebase.

Write exactly one paragraph of 4 to 6 sentences. Do not use bullet points or
numbered lists. Use plain English, but be technically specific. Mention actual
file names, framework names, architectural patterns, the entry point, startup
behaviour, important files, and notable structural observations. Only state
facts supported by the supplied repository analysis."""

USER_TEMPLATE = """Based on the following analysis of a GitHub repository, write an
intelligent one-paragraph summary covering the tech stack, architectural pattern,
entry point and startup behaviour, critical files, and notable observations.

=== REPOSITORY ===
URL: {repo_url}
Language: {language}
Total files analysed: {total_files}
Detected architecture: {architecture_hint}

=== FOLDER STRUCTURE ===
{folder_summary}

=== ENTRY POINT AND EXECUTION FLOW ===
Entry file: {entry_file}
Confidence: {confidence}
Manifest declared: {manifest_declared}
{execution_flow}

=== DEPENDENCY ANALYSIS ===
Total dependency edges: {total_edges}
Critical files:
{critical_files}
Circular dependencies: {cycles}

Write the paragraph now. Start directly with the project description."""

def generate_claude_summary(*, repo_url, language, total_files, architecture_hint,
                            folder_summary, entry_file, confidence, manifest_declared,
                            execution_flow, total_edges, critical_files, cycles):
    """Call Claude through Anthropic’s official Messages API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not configured")

    client = Anthropic(api_key=api_key)
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    response = client.messages.create(
        model=model,
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_TEMPLATE.format(
            repo_url=repo_url, language=language, total_files=total_files,
            architecture_hint=architecture_hint, folder_summary=folder_summary,
            entry_file=entry_file, confidence=confidence,
            manifest_declared=manifest_declared, execution_flow=execution_flow,
            total_edges=total_edges, critical_files=critical_files, cycles=cycles
        )}]
    )
    text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    summary = " ".join(text_blocks).strip()
    if not summary:
        raise RuntimeError("Claude returned no text content")
    return summary
