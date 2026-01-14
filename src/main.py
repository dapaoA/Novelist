"""
main.py

一个简化版的 LangGraph 小说工作流：
- 先根据 user_input / user_outline 生成卷级大纲（OutlineSummary）
- 再生成这一卷的结构（VolumeStructure：chapters + scenes）
- 再生成角色卡（CharacterCard，偏“演员型”）
- 再按章生成正文（每章内部按 scene 写）
- 最后保存到文件

依赖：
    pip install "langchain-openai" "langgraph" "pydantic<3"
环境变量：
    export OPENAI_API_KEY="sk-..."
"""

from __future__ import annotations

from typing import List, Optional, TypedDict, Literal

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

import logging
import os
from pathlib import Path

# =============== 日志 ===============
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# =============== 1. 数据模型（可以单独拆成 models.py） ===============

class OutlineSummary(BaseModel):
    """卷级大纲（简化版）"""
    source: Literal["user_provided", "auto_drafted"] = Field(
        description="大纲来源：user_provided 或 auto_drafted"
    )
    raw_outline: str = Field(
        description="原始大纲文本：要么是用户大纲，要么是系统自动草拟的卷级大纲"
    )

    core_premise: str = Field(description="故事核心前提，一两句话")
    main_conflict: str = Field(description="本卷主冲突 / 主问题")
    protagonist_goal: str = Field(description="本卷主角核心目标")
    expected_volume_count: int = Field(
        description="预计卷数（简单估算，先留着做扩展用）"
    )


class ScenePlan(BaseModel):
    scene_index: int = Field(description="本章内的 scene 序号，从 1 开始")
    short_label: str = Field(description="一句话的 scene 名称/标签")
    pov_character: str = Field(description="视角人物名")
    goal: str = Field(description="这个 scene 主角/视角人物想达成什么")
    conflict: str = Field(description="遇到什么阻碍或冲突")
    outcome: str = Field(description="scene 的结果（成功/失败/暧昧/留钩子）")
    notes: str = Field(
        default="",
        description="给后续写作节点的补充说明",
    )


class ChapterPlan(BaseModel):
    chapter_index: int = Field(description="第几章，从 1 开始")
    chapter_title: str = Field(description="章节标题")
    chapter_summary: str = Field(description="章节的简要概括")
    scenes: List[ScenePlan] = Field(description="本章包含的 scene 列表")


class VolumeStructure(BaseModel):
    volume_title: str = Field(description="这一卷的标题")
    volume_summary: str = Field(description="这一卷的整体概括")
    chapters: List[ChapterPlan] = Field(description="该卷的章节规划")


class CharacterCard(BaseModel):
    """偏“演员型”的角色卡，不是深度心理传记"""

    name: str = Field(description="角色姓名")
    role: str = Field(
        description="在队伍/组织/故事系统中的职能/岗位，例如：剑士、商人、工匠、魔法师"
    )
    goal: str = Field(description="近期想要达成的目标（故事期内）")
    stake: str = Field(description="如果失败/成功，对他有什么利害")
    flaw: str = Field(description="一个明显的短板/缺点，用来制造冲突")
    voice: str = Field(description="说话风格/气质，一两句描述")
    relationship_summary: str = Field(
        description="人际关系：与其他人物/组织的关系简述（可包含多人），例如：'米莉的导师；与布兰德合作但互不信任；受雇于公会。'"
    )


# =============== 2. Workflow 的 State（可以拆成 state.py） ===============

class NovelState(TypedDict, total=False):
    # 输入
    user_input: str
    user_outline: str

    # 中间产物
    outline: OutlineSummary
    structure: VolumeStructure
    characters: List[CharacterCard]
    chapters: List[str]  # 每章的正文文本

    # 输出文件
    novel_output_file: str


# =============== 3. LLM 构建（可以拆成 llm_config.py） ===============

def build_llm() -> ChatOpenAI:
    """
    统一创建一个 LLM 实例。
    后续如果你想切换到别的模型，只改这里就行。
    """
    api_key = os.getenvb("OPENAI_API_KEY")
    if api_key:
        raise RuntimeError("请先设置环境变量 OPENAI_API_KEY")
    # 你可以按需换成 gpt-4.1 / o3-mini 等
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7
    )


# =============== 4. 各个节点（可以拆成 nodes_outline.py / nodes_structure.py / ...） ===============

def node_draft_outline(state: NovelState, llm: ChatOpenAI) -> NovelState:
    """根据 user_input / user_outline 得到卷级大纲 OutlineSummary"""

    user_input = state.get("user_input", "").strip()
    user_outline = state.get("user_outline", "").strip()

    if not user_input and not user_outline:
        raise ValueError("必须至少提供 user_input 或 user_outline 之一")

    if user_outline:
        # 用户有自带大纲：让模型帮忙“结构化理解”一下
        source = "user_provided"
        prompt = f"""
你是一个轻小说编辑，现在有作者提供的大纲。

【用户设定】:
{user_input or "（作者没有额外设定）"}

【用户卷级大纲】:
{user_outline}

请你把这个大纲归纳为一个卷级总结，输出时遵守以下字段含义（只需要按照字段内容自然语言回答，不要多余解释）：
- core_premise：一两句话，说明故事的基本前提
- main_conflict：本卷的主要冲突/矛盾
- protagonist_goal：本卷主角最想达成的目标
- expected_volume_count：根据文本粗略估计整个长篇大概需要多少卷（整数，随便估就行）
"""
    else:
        # 用户没有大纲：让模型自己草拟一份卷 1 的大纲
        source = "auto_drafted"
        prompt = f"""
你是一个编辑，帮作者根据设定草拟【第一卷】的大纲。

【作者设定】:
{user_input}

请你专注在【第一卷】要讲的内容上，而不是整个长篇。
输出时遵守以下字段含义（只需要按照字段内容自然语言回答，不要多余解释）：
- core_premise：一两句话，说明故事的基本前提
- main_conflict：本卷的主要冲突/矛盾
- protagonist_goal：本卷主角最想达成的目标
- expected_volume_count：根据文本粗略估计整个长篇大概需要多少卷（整数，随便估就行）
并附上一个自然语言的卷级大纲（章节大致走向就可以）。
"""

    structured_llm = llm.with_structured_output(OutlineSummary)

    outline = structured_llm.invoke(
        [
            SystemMessage(content="你是一个擅长通俗小说，尤其是网文结构化分析的编辑。"),
            HumanMessage(content=prompt),
        ]
    )
    # 改写 source, raw_outline
    outline.source = source  # 覆盖一下 source 字段
    # 简单把 raw_outline 填一下（这里直接用 main_conflict + protagonist_goal 做一个简短汇总）
    outline.raw_outline = (
        f"【核心前提】{outline.core_premise}\n"
        f"【本卷主要冲突】{outline.main_conflict}\n"
        f"【主角目标】{outline.protagonist_goal}\n"
    )

    new_state = dict(state)
    new_state["outline"] = outline
    return new_state


def node_plan_volume_structure(state: NovelState, llm: ChatOpenAI) -> NovelState:
    """根据 OutlineSummary 生成这一卷的章节/scene 结构"""

    outline: OutlineSummary = state["outline"]
    prompt = f"""
你是一个日式剑与魔法轻小说的构成作家。

请你根据下面这份【卷级大纲】只规划【第一卷】的结构：

- 核心前提：{outline.core_premise}
- 本卷主冲突：{outline.main_conflict}
- 主角目标：{outline.protagonist_goal}
- 预估卷数：{outline.expected_volume_count}

要求：
- 这一卷大致 6–10 章
- 每一章划分 2–4 个 scene
- 每个 scene 要写出：pov_character / goal / conflict / outcome，简短即可

只用返回结构化信息，不要写正文。
"""

    structured_llm = llm.with_structured_output(VolumeStructure)
    structure = structured_llm.invoke(
        [
            SystemMessage(
                content=(
                    "你负责把卷级大纲拆成 volume -> chapters -> scenes 结构。"
                    "注意：scene 粒度稍微细一点，但不要太多（每章 2–4 个）。"
                )
            ),
            HumanMessage(content=prompt),
        ]
    )

    new_state = dict(state)
    new_state["structure"] = structure
    return new_state


def node_generate_characters(state: NovelState, llm: ChatOpenAI) -> NovelState:
    """根据 outline + structure 生成一批“演员型角色卡”"""

    outline: OutlineSummary = state["outline"]
    structure: VolumeStructure = state["structure"]

    prompt = f"""
你是轻小说的角色设计编辑。现在有一部日式剑与魔法轻小说的第一卷规划如下。

【卷级信息】
- 核心前提：{outline.core_premise}
- 本卷主冲突：{outline.main_conflict}
- 主角目标：{outline.protagonist_goal}

【卷结构摘要】
- 卷标题：{structure.volume_title}
- 卷概括：{structure.volume_summary}
- 章节数：{len(structure.chapters)}

请你根据这些信息，设计一批“演员型角色卡”，用于后续写作：
- 不需要写他们完整人生史
- 重点是：在故事系统中的职能/岗位 + 动机/利害 + 明显短板 + 说话风格
- 每个角色要有 clear 的 relationship_summary, 也就是人际关系

请至少给出：
- 主角 1 名
- 核心同伴/徒弟 2–4 名
- 若有反派或对立势力，可以给 1–2 名代表人物
"""

    # 这里用 List[CharacterCard] 作为 structured 输出
    from typing import List as _ListType  # 避免和上面混淆

    class CharacterList(BaseModel):
        characters: _ListType[CharacterCard]

    structured_llm = llm.with_structured_output(CharacterList)
    result = structured_llm.invoke(
        [
            SystemMessage(
                content="你负责轻小说的角色卡设计，输出结构化角色信息。"
            ),
            HumanMessage(content=prompt),
        ]
    )
    characters = result.characters

    new_state = dict(state)
    new_state["characters"] = characters
    return new_state


def _render_character_context(characters: List[CharacterCard]) -> str:
    """给写作节点用的人物摘要，简单自然语言拼接即可"""
    lines = []
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


def node_write_chapters(state: NovelState, llm: ChatOpenAI) -> NovelState:
    """根据结构 + 角色卡，逐章生成正文文本"""

    structure: VolumeStructure = state["structure"]
    characters: List[CharacterCard] = state["characters"]

    character_ctx = _render_character_context(characters)

    chapters_text: List[str] = []

    for chap in structure.chapters:
        # 把 scene 信息整理成一个简明列表给 LLM
        scene_desc_lines = []
        for sc in chap.scenes:
            scene_desc_lines.append(
                f"Scene {sc.scene_index}: [{sc.short_label}]\n"
                f"- 视角人物：{sc.pov_character}\n"
                f"- 目标：{sc.goal}\n"
                f"- 冲突：{sc.conflict}\n"
                f"- 结果：{sc.outcome}\n"
                f"- 备注：{sc.notes}\n"
            )
        scene_block = "\n".join(scene_desc_lines)

        prompt = f"""
你是一个(网文)小说作者。

【角色卡】
{character_ctx}

【本卷章节规划 - 当前章节】
- 章节序号：{chap.chapter_index}
- 章节标题：{chap.chapter_title}
- 章节概括：{chap.chapter_summary}

【本章 scene 列表】：
{scene_block}

请你根据这些信息写出这一整章的正文：
- 采用网文风格的中文（偏口语、易读），这里的网文包括日式异世界，中式玄幻或者韩式地下城等
- 保持角色说话风格一致
- 每个 scene 之间有自然的衔接，不要硬切
- 适度保留节奏：有 dialogue，有行动，有内心活动，但不要长篇流水账说明
- 不需要写卷首回顾，只写这一章本身

直接输出章节正文，不要再解释。
"""

        resp = llm.invoke(
            [
                SystemMessage(
                    content="你是一名非常有经验的网文作者。"
                ),
                HumanMessage(content=prompt),
            ]
        )
        chapter_text = resp.content if isinstance(resp.content, str) else str(
            resp.content
        )
        chapters_text.append(
            f"# 第 {chap.chapter_index} 章 {chap.chapter_title}\n\n{chapter_text}\n"
        )

        log.info("Chapter %d generated.", chap.chapter_index)

    new_state = dict(state)
    new_state["chapters"] = chapters_text
    return new_state


def node_save_output(state: NovelState) -> NovelState:
    """把章节拼接写入文件"""

    output_file = state.get("novel_output_file") or "outputs/novel.txt"
    chapters = state.get("chapters", [])

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    text = "\n\n".join(chapters)
    Path(output_file).write_text(text, encoding="utf-8")

    log.info("Novel saved to %s", output_file)

    return state


# =============== 5. 构建 LangGraph（可以拆成 graph_builder.py） ===============

def build_graph() -> StateGraph:
    llm = build_llm()

    graph = StateGraph(NovelState)

    # 用闭包把 llm 捕获进去
    graph.add_node("draft_outline", lambda s: node_draft_outline(s, llm))
    graph.add_node("plan_volume_structure", lambda s: node_plan_volume_structure(s, llm))
    graph.add_node("generate_characters", lambda s: node_generate_characters(s, llm))
    graph.add_node("write_chapters", lambda s: node_write_chapters(s, llm))
    graph.add_node("save_output", node_save_output)

    # 边：线性流程
    graph.set_entry_point("draft_outline")
    graph.add_edge("draft_outline", "plan_volume_structure")
    graph.add_edge("plan_volume_structure", "generate_characters")
    graph.add_edge("generate_characters", "write_chapters")
    graph.add_edge("write_chapters", "save_output")
    graph.add_edge("save_output", END)

    return graph.compile()


# =============== 6. CLI 入口（可以拆成 cli.py） ===============

if __name__ == "__main__":
    """
    简单示例：
    - 把 user_input 换成你的“日式剑与魔法 + 某套路设定”
    - user_outline 目前先留空，交给系统 auto draft 第一卷
    - 输出会写到 outputs/novel.txt
    """
    graph = build_graph()

    init_state: NovelState = {
        "user_input": (
            "我要写一部日式剑与魔法轻小说，偏套路系。\n"
            "主角原本在首都作为精锐部队队长，后因为勇者召唤而被辞退。\n"
            "他躺平回到乡下边境小镇，打算当个咸鱼，结果不断被卷入各种麻烦。\n"
            "最后解决麻烦，获得了小镇居民的认同，主角找到了方向\n"
            "整体风格：轻松、稍微带点职场吐槽，不搞狗血恋爱。\n"
            "另外这次主要是测试这个脚本，所以故事不宜太长\n"
        ),
        "user_outline": "",
        "novel_output_file": "output/novel.txt",
    }

    config = {"configurable": {"thread_id": "novel-demo"}}

    final_state = graph.invoke(init_state, config=config)
    log.info(
        "Done. Chapters generated: %d",
        len(final_state.get("chapters", [])),
    )