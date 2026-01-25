from __future__ import annotations

from models import OutlineSummary
from prompts.zh.formatters import format_outline_raw


def build_outline_prompt(user_input: str, user_outline: str | None) -> tuple[str, str, str]:
    """返回 (system_prompt, user_prompt, source)."""

    user_outline = (user_outline or "").strip()
    user_input = (user_input or "").strip()

    if user_outline:
        source = "user_provided"
        prompt = f"""
你是一个网文编辑，现在有作者提供的大纲。

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

    system_prompt = "你是一个擅长网文结构化分析的编辑。"
    return system_prompt, prompt, source


def fill_outline_metadata(outline: OutlineSummary, source: str) -> None:
    outline.source = source
    outline.raw_outline = format_outline_raw(outline)
