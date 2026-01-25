from models import OutlineSummary


def build_structure_prompt(outline: OutlineSummary) -> tuple[str, str]:
    prompt = f"""
You are a webnovel structure writer familiar with CN/KR/JP fantasy tropes.

Based on this volume outline, plan only Volume 1:

- Core premise: {outline.core_premise}
- Main conflict: {outline.main_conflict}
- Protagonist goal: {outline.protagonist_goal}
- Estimated volumes: {outline.expected_volume_count}

Requirements:
- 6–10 chapters for this volume
- 2–4 scenes per chapter
- For each scene include: pov_character / goal / conflict / outcome

Return structured information only. No prose.
"""

    system_prompt = (
        "Split the volume outline into volume -> chapters -> scenes. "
        "Keep scenes granular but not too many (2–4 per chapter)."
    )
    return system_prompt, prompt
