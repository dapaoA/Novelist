from __future__ import annotations

from __future__ import annotations

from typing import List, TypedDict, Literal

from pydantic import BaseModel, Field


class OutlineSummaryZh(BaseModel):
    """卷级大纲（简化版）/ Volume-level outline (simplified)."""

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


class ScenePlanZh(BaseModel):
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


class ChapterPlanZh(BaseModel):
    chapter_index: int = Field(description="第几章，从 1 开始")
    chapter_title: str = Field(description="章节标题")
    chapter_summary: str = Field(description="章节的简要概括")
    scenes: List[ScenePlan] = Field(description="本章包含的 scene 列表")


class VolumeStructureZh(BaseModel):
    volume_title: str = Field(description="这一卷的标题")
    volume_summary: str = Field(description="这一卷的整体概括")
    chapters: List[ChapterPlan] = Field(description="该卷的章节规划")


class CharacterCardZh(BaseModel):
    """偏“演员型”的角色卡，不是深度心理传记 / Actor-style character card."""

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


class NovelState(TypedDict, total=False):
    # 输入 / Inputs
    user_input: str
    user_outline: str
    prompt_lang: Literal["zh", "en"]

    # 中间产物 / Intermediate artifacts
    outline: object
    structure: object
    characters: List[object]
    chapters: List[str]  # 每章的正文文本

    # 输出文件 / Output file
    novel_output_file: str


class OutlineSummaryEn(BaseModel):
    """Volume-level outline (simplified)."""

    source: Literal["user_provided", "auto_drafted"] = Field(
        description="Outline source: user_provided or auto_drafted"
    )
    raw_outline: str = Field(
        description="Raw outline text: either user outline or auto-drafted outline"
    )

    core_premise: str = Field(description="Core premise in 1–2 sentences")
    main_conflict: str = Field(description="Main conflict for this volume")
    protagonist_goal: str = Field(description="Protagonist's main goal in this volume")
    expected_volume_count: int = Field(
        description="Estimated total volume count (rough guess)"
    )


class ScenePlanEn(BaseModel):
    scene_index: int = Field(description="Scene index within the chapter, starting at 1")
    short_label: str = Field(description="One-line scene label")
    pov_character: str = Field(description="POV character name")
    goal: str = Field(description="What the POV wants to achieve in this scene")
    conflict: str = Field(description="Obstacle or conflict in this scene")
    outcome: str = Field(description="Outcome (success/fail/ambiguous/hook)")
    notes: str = Field(default="", description="Extra notes for writing")


class ChapterPlanEn(BaseModel):
    chapter_index: int = Field(description="Chapter index, starting at 1")
    chapter_title: str = Field(description="Chapter title")
    chapter_summary: str = Field(description="Short chapter summary")
    scenes: List["ScenePlanEn"] = Field(description="List of scenes in this chapter")


class VolumeStructureEn(BaseModel):
    volume_title: str = Field(description="Volume title")
    volume_summary: str = Field(description="Overall volume summary")
    chapters: List["ChapterPlanEn"] = Field(description="Chapter plan for the volume")


class CharacterCardEn(BaseModel):
    """Actor-style character card (not a deep psychological biography)."""

    name: str = Field(description="Character name")
    role: str = Field(description="Role/job in the story system")
    goal: str = Field(description="Short-term goal within the story arc")
    stake: str = Field(description="What's at stake for success/failure")
    flaw: str = Field(description="A clear flaw to create conflict")
    voice: str = Field(description="Speaking style/voice in 1–2 lines")
    relationship_summary: str = Field(
        description="Relationship summary with others (may include multiple people)"
    )


class ModelBundle:
    """Container for language-specific Pydantic model classes."""
    __slots__ = (
        "OutlineSummary",
        "ScenePlan",
        "ChapterPlan",
        "VolumeStructure",
        "CharacterCard",
    )

    def __init__(
        self,
        OutlineSummary: type[BaseModel],
        ScenePlan: type[BaseModel],
        ChapterPlan: type[BaseModel],
        VolumeStructure: type[BaseModel],
        CharacterCard: type[BaseModel],
    ) -> None:
        self.OutlineSummary = OutlineSummary
        self.ScenePlan = ScenePlan
        self.ChapterPlan = ChapterPlan
        self.VolumeStructure = VolumeStructure
        self.CharacterCard = CharacterCard


def get_model_classes(lang: Literal["zh", "en"]) -> ModelBundle:
    """Return the model class bundle for the requested language."""
    if lang == "en":
        return ModelBundle(
            OutlineSummary=OutlineSummaryEn,
            ScenePlan=ScenePlanEn,
            ChapterPlan=ChapterPlanEn,
            VolumeStructure=VolumeStructureEn,
            CharacterCard=CharacterCardEn,
        )
    return ModelBundle(
        OutlineSummary=OutlineSummaryZh,
        ScenePlan=ScenePlanZh,
        ChapterPlan=ChapterPlanZh,
        VolumeStructure=VolumeStructureZh,
        CharacterCard=CharacterCardZh,
    )


# Default aliases (keep existing imports working; default to Chinese schema)
OutlineSummary = OutlineSummaryZh
ScenePlan = ScenePlanZh
ChapterPlan = ChapterPlanZh
VolumeStructure = VolumeStructureZh
CharacterCard = CharacterCardZh
