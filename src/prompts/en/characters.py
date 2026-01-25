from models import OutlineSummary, VolumeStructure


def build_characters_prompt(
    outline: OutlineSummary, structure: VolumeStructure
) -> tuple[str, str]:
    prompt = f"""
You are a webnovel character editor. Here is the plan for Volume 1.

[Volume info]
- Core premise: {outline.core_premise}
- Main conflict: {outline.main_conflict}
- Protagonist goal: {outline.protagonist_goal}

[Volume structure]
- Volume title: {structure.volume_title}
- Volume summary: {structure.volume_summary}
- Chapter count: {len(structure.chapters)}

Design a batch of "actor-style" character cards for writing:
- No full life stories
- Focus on role/job in the story system + motivation/stakes + clear flaw + speaking voice
- Each character should include a clear relationship_summary

Include at minimum:
- 1 protagonist
- 2–4 core companions/apprentices
- 1–2 antagonists if applicable
"""

    system_prompt = "You design webnovel character cards and output structured info."
    return system_prompt, prompt
