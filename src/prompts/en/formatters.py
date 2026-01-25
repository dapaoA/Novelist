from __future__ import annotations

from typing import List

from models import ChapterPlan, CharacterCard, OutlineSummary


def format_scene_block(chapter: ChapterPlan) -> str:
    scene_desc_lines: List[str] = []
    for sc in chapter.scenes:
        scene_desc_lines.append(
            f"Scene {sc.scene_index}: [{sc.short_label}]\n"
            f"- POV: {sc.pov_character}\n"
            f"- Goal: {sc.goal}\n"
            f"- Conflict: {sc.conflict}\n"
            f"- Outcome: {sc.outcome}\n"
            f"- Notes: {sc.notes}\n"
        )
    return "\n".join(scene_desc_lines)


def format_chapter_title(chapter_index: int, chapter_title: str) -> str:
    return f"# Chapter {chapter_index}: {chapter_title}\n\n"


def format_character_context(characters: List[CharacterCard]) -> str:
    lines: List[str] = []
    for c in characters:
        lines.append(
            f"\n"
            f"- Role: {c.role}\n"
            f"- Goal: {c.goal}\n"
            f"- Stakes: {c.stake}\n"
            f"- Flaw: {c.flaw}\n"
            f"- Voice: {c.voice}\n"
            f"- Relationships: {c.relationship_summary}\n"
        )
    return "\n".join(lines)


def format_outline_raw(outline: OutlineSummary) -> str:
    return (
        f"[Core Premise]{outline.core_premise}\n"
        f"[Main Conflict]{outline.main_conflict}\n"
        f"[Protagonist Goal]{outline.protagonist_goal}\n"
    )
