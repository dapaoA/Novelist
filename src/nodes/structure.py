from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from models import OutlineSummary, VolumeStructure, NovelState, get_model_classes
from prompts.registry import structure_prompt


def node_plan_volume_structure(state: NovelState, llm: ChatOpenAI) -> NovelState:
    """根据 OutlineSummary 生成章节/scene 结构 / Plan volume structure."""

    outline: OutlineSummary = state["outline"]
    prompt_lang = state.get("prompt_lang", "zh")

    system_prompt, prompt = structure_prompt(prompt_lang, outline)

    models = get_model_classes(prompt_lang)
    structured_llm = llm.with_structured_output(models.VolumeStructure)
    structure = structured_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]
    )

    new_state = dict(state)
    new_state["structure"] = structure
    return new_state
