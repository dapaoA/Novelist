from models import ChapterPlan


def build_writer_prompt(
    character_ctx: str, chapter: ChapterPlan, scene_block: str
) -> tuple[str, str]:
    prompt = f"""
You are a webnovel author.

[Character cards]
{character_ctx}

[Current chapter plan]
- Chapter index: {chapter.chapter_index}
- Chapter title: {chapter.chapter_title}
- Chapter summary: {chapter.chapter_summary}

[Scene list]
{scene_block}

Write the full chapter text based on the above:
- Use webnovel-style prose (conversational, easy to read)
- Keep character voices consistent
- Connect scenes naturally; avoid hard cuts
- Maintain pacing: dialogue, action, inner thoughts; avoid dry exposition
- No recap; write only this chapter

Output the chapter text only.
"""

    system_prompt = "You are an experienced webnovel writer."
    return system_prompt, prompt
