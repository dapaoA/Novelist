from __future__ import annotations

from typing import List

from models import ChapterPlan, CharacterCard, OutlineSummary


def format_scene_block(chapter: ChapterPlan) -> str:
    scene_desc_lines: List[str] = []
    for sc in chapter.scenes:
        scene_desc_lines.append(
            f"Scene {sc.scene_index}: [{sc.short_label}]\n"
            f"- 视角人物：{sc.pov_character}\n"
            f"- 目标：{sc.goal}\n"
            f"- 冲突：{sc.conflict}\n"
            f"- 结果：{sc.outcome}\n"
            f"- 备注：{sc.notes}\n"
        )
    return "\n".join(scene_desc_lines)


def format_chapter_title(chapter_index: int, chapter_title: str) -> str:
    return f"# 第 {chapter_index} 章 {chapter_title}\n\n"


def format_character_context(characters: List[CharacterCard]) -> str:
    lines: List[str] = []
    for c in characters:
        lines.append(
            f"\n"
            f"- 职能/角色：{c.role}\n"
            f"- 目标：{c.goal}\n"
            f"- 利害：{c.stake}\n"
            f"- 缺点：{c.flaw}\n"
            f"- 说话风格：{c.voice}\n"
            f"- 人际关系：{c.relationship_summary}\n"
        )
    return "\n".join(lines)


def format_outline_raw(outline: OutlineSummary) -> str:
    return (
        f"【核心前提】{outline.core_premise}\n"
        f"【本卷主要冲突】{outline.main_conflict}\n"
        f"【主角目标】{outline.protagonist_goal}\n"
    )
