from typing import List as _ListType

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from models import CharacterCard, OutlineSummary, VolumeStructure, NovelState, get_model_classes
from prompts.registry import characters_prompt, format_character_context


def node_generate_characters(state: NovelState, llm: ChatOpenAI) -> NovelState:
    """根据 outline + structure 生成“演员型角色卡” / Generate character cards."""

    outline: OutlineSummary = state["outline"]
    structure: VolumeStructure = state["structure"]
    prompt_lang = state.get("prompt_lang", "zh")

    system_prompt, prompt = characters_prompt(prompt_lang, outline, structure)

    models = get_model_classes(prompt_lang)

    class CharacterList(BaseModel):
        characters: _ListType[models.CharacterCard]

    structured_llm = llm.with_structured_output(CharacterList)
    result = structured_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]
    )
    characters = result.characters

    new_state = dict(state)
    new_state["characters"] = characters
    return new_state


def render_character_context(
    characters: _ListType[CharacterCard], prompt_lang: str = "zh"
) -> str:
    """给写作节点用的人物摘要 / Build a short character context block."""

    return format_character_context(prompt_lang, characters)
