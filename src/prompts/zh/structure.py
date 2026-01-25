from models import OutlineSummary


def build_structure_prompt(outline: OutlineSummary) -> tuple[str, str]:
    prompt = f"""
你是一个网文构成作家，熟悉中韩与日式题材。

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

    system_prompt = (
        "你负责把卷级大纲拆成 volume -> chapters -> scenes 结构。"
        "注意：scene 粒度稍微细一点，但不要太多（每章 2–4 个）。"
    )
    return system_prompt, prompt
