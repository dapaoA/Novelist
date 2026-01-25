from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from models import OutlineSummary, NovelState, get_model_classes
from prompts.registry import outline_prompt, outline_fill_metadata


def node_draft_outline(state: NovelState, llm: ChatOpenAI) -> NovelState:
    """根据 user_input / user_outline 得到卷级大纲 / Draft volume outline."""

    user_input = state.get("user_input", "").strip()
    user_outline = state.get("user_outline", "").strip()
    prompt_lang = state.get("prompt_lang", "zh")

    if not user_input and not user_outline:
        raise ValueError("必须至少提供 user_input 或 user_outline 之一")

    system_prompt, prompt, source = outline_prompt(
        prompt_lang, user_input, user_outline
    )

    models = get_model_classes(prompt_lang)
    structured_llm = llm.with_structured_output(models.OutlineSummary)

    outline = structured_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]
    )
    outline_fill_metadata(prompt_lang, outline, source)

    new_state = dict(state)
    new_state["outline"] = outline
    return new_state
