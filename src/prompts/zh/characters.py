from models import OutlineSummary, VolumeStructure


def build_characters_prompt(
    outline: OutlineSummary, structure: VolumeStructure
) -> tuple[str, str]:
    prompt = f"""
你是网文的角色设计编辑。现在有一部偏奇幻冒险的网文第一卷规划如下。

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

    system_prompt = "你负责网文的角色卡设计，输出结构化角色信息。"
    return system_prompt, prompt
