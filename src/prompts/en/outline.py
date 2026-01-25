from __future__ import annotations

from models import OutlineSummary
from prompts.en.formatters import format_outline_raw


def build_outline_prompt(user_input: str, user_outline: str | None) -> tuple[str, str, str]:
    """Return (system_prompt, user_prompt, source)."""

    user_outline = (user_outline or "").strip()
    user_input = (user_input or "").strip()

    if user_outline:
        source = "user_provided"
        prompt = f"""
You are a webnovel editor. The author has provided an outline.

[Author setup]
{user_input or "(No extra setup provided.)"}

[Volume-level outline]
{user_outline}

Summarize this outline into a volume-level summary. Follow these fields and only answer with the content:
- core_premise: 1–2 sentences describing the core premise
- main_conflict: the main conflict for this volume
- protagonist_goal: the protagonist's main goal in this volume
- expected_volume_count: rough estimate of total volumes (integer)
"""
    else:
        source = "auto_drafted"
        prompt = f"""
You are an editor. Draft the outline for Volume 1 based on the author's setup.

[Author setup]
{user_input}

Focus on Volume 1 only (not the full series).
Follow these fields and only answer with the content:
- core_premise: 1–2 sentences describing the core premise
- main_conflict: the main conflict for this volume
- protagonist_goal: the protagonist's main goal in this volume
- expected_volume_count: rough estimate of total volumes (integer)
Also include a natural-language volume-level outline.
"""

    system_prompt = "You are an editor skilled at structuring webnovel narratives."
    return system_prompt, prompt, source


def fill_outline_metadata(outline: OutlineSummary, source: str) -> None:
    outline.source = source
    outline.raw_outline = format_outline_raw(outline)
