from langgraph.graph import StateGraph, END

from llm_config import build_llm
from models import NovelState
from nodes.outline import node_draft_outline
from nodes.structure import node_plan_volume_structure
from nodes.characters import node_generate_characters
from nodes.writer import node_write_chapters
from nodes.io import node_save_output


def build_graph() -> StateGraph:
    llm = build_llm()

    graph = StateGraph(NovelState)

    # 用闭包把 llm 捕获进去 / Capture llm via closures
    graph.add_node("draft_outline", lambda s: node_draft_outline(s, llm))
    graph.add_node("plan_volume_structure", lambda s: node_plan_volume_structure(s, llm))
    graph.add_node("generate_characters", lambda s: node_generate_characters(s, llm))
    graph.add_node("write_chapters", lambda s: node_write_chapters(s, llm))
    graph.add_node("save_output", node_save_output)

    # 边：线性流程 / Linear flow
    graph.set_entry_point("draft_outline")
    graph.add_edge("draft_outline", "plan_volume_structure")
    graph.add_edge("plan_volume_structure", "generate_characters")
    graph.add_edge("generate_characters", "write_chapters")
    graph.add_edge("write_chapters", "save_output")
    graph.add_edge("save_output", END)

    return graph.compile()
