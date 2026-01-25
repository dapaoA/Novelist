from __future__ import annotations

from typing import Literal

from models import OutlineSummary, VolumeStructure, ChapterPlan, CharacterCard

PromptLang = Literal["zh", "en"]


def outline_prompt(lang: PromptLang, user_input: str, user_outline: str | None):
    if lang == "en":
        from prompts.en.outline import build_outline_prompt
    else:
        from prompts.zh.outline import build_outline_prompt
    return build_outline_prompt(user_input, user_outline)


def outline_fill_metadata(lang: PromptLang, outline: OutlineSummary, source: str) -> None:
    if lang == "en":
        from prompts.en.outline import fill_outline_metadata
    else:
        from prompts.zh.outline import fill_outline_metadata
    fill_outline_metadata(outline, source)


def structure_prompt(lang: PromptLang, outline: OutlineSummary):
    if lang == "en":
        from prompts.en.structure import build_structure_prompt
    else:
        from prompts.zh.structure import build_structure_prompt
    return build_structure_prompt(outline)


def characters_prompt(lang: PromptLang, outline: OutlineSummary, structure: VolumeStructure):
    if lang == "en":
        from prompts.en.characters import build_characters_prompt
    else:
        from prompts.zh.characters import build_characters_prompt
    return build_characters_prompt(outline, structure)


def writer_prompt(lang: PromptLang, character_ctx: str, chapter: ChapterPlan, scene_block: str):
    if lang == "en":
        from prompts.en.writer import build_writer_prompt
    else:
        from prompts.zh.writer import build_writer_prompt
    return build_writer_prompt(character_ctx, chapter, scene_block)


def format_scene_block(lang: PromptLang, chapter: ChapterPlan) -> str:
    if lang == "en":
        from prompts.en.formatters import format_scene_block as _fmt
    else:
        from prompts.zh.formatters import format_scene_block as _fmt
    return _fmt(chapter)


def format_chapter_title(lang: PromptLang, chapter_index: int, chapter_title: str) -> str:
    if lang == "en":
        from prompts.en.formatters import format_chapter_title as _fmt
    else:
        from prompts.zh.formatters import format_chapter_title as _fmt
    return _fmt(chapter_index, chapter_title)


def format_character_context(lang: PromptLang, characters: list[CharacterCard]) -> str:
    if lang == "en":
        from prompts.en.formatters import format_character_context as _fmt
    else:
        from prompts.zh.formatters import format_character_context as _fmt
    return _fmt(characters)
