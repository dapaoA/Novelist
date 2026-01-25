import logging
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from models import CharacterCard, VolumeStructure, NovelState
from nodes.characters import render_character_context
from prompts.registry import writer_prompt, format_scene_block, format_chapter_title

log = logging.getLogger(__name__)


def node_write_chapters(state: NovelState, llm: ChatOpenAI) -> NovelState:
    """根据结构 + 角色卡生成正文 / Write chapters from structure + cards."""

    structure: VolumeStructure = state["structure"]
    characters: List[CharacterCard] = state["characters"]
    prompt_lang = state.get("prompt_lang", "zh")

    character_ctx = render_character_context(characters, prompt_lang)

    chapters_text: List[str] = []

    for chap in structure.chapters:
        # 把 scene 信息整理成一个简明列表给 LLM
        # Build a concise scene list for the LLM.
        scene_block = format_scene_block(prompt_lang, chap)

        system_prompt, prompt = writer_prompt(
            prompt_lang, character_ctx, chap, scene_block
        )

        resp = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt),
            ]
        )
        chapter_text = resp.content if isinstance(resp.content, str) else str(resp.content)
        chapter_header = format_chapter_title(
            prompt_lang, chap.chapter_index, chap.chapter_title
        )
        chapters_text.append(f"{chapter_header}{chapter_text}\n")

        log.info("Chapter %d generated.", chap.chapter_index)

    new_state = dict(state)
    new_state["chapters"] = chapters_text
    return new_state
