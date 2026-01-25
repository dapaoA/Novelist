from models import ChapterPlan


def build_writer_prompt(
    character_ctx: str, chapter: ChapterPlan, scene_block: str
) -> tuple[str, str]:
    prompt = f"""
你是一个网文小说作者。

【角色卡】
{character_ctx}

【本卷章节规划 - 当前章节】
- 章节序号：{chapter.chapter_index}
- 章节标题：{chapter.chapter_title}
- 章节概括：{chapter.chapter_summary}

【本章 scene 列表】：
{scene_block}

请你根据这些信息写出这一整章的正文：
- 采用网文风格的中文（偏口语、易读），涵盖中式玄幻、韩式地下城、日式异世界等
- 保持角色说话风格一致
- 每个 scene 之间有自然的衔接，不要硬切
- 适度保留节奏：有 dialogue，有行动，有内心活动，但不要长篇流水账说明
- 不需要写卷首回顾，只写这一章本身

直接输出章节正文，不要再解释。
"""

    system_prompt = "你是一名非常有经验的网文作者。"
    return system_prompt, prompt
