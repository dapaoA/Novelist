"""
main.py

一个简化版的 LangGraph 小说工作流 / A simplified LangGraph novel workflow:
- 先根据 user_input / user_outline 生成卷级大纲（OutlineSummary）
  Generate a volume-level outline from user_input / user_outline.
- 再生成这一卷的结构（VolumeStructure：chapters + scenes）
  Generate the volume structure (chapters + scenes).
- 再生成角色卡（CharacterCard，偏“演员型”）
  Generate character cards (actor-style).
- 再按章生成正文（每章内部按 scene 写）
  Write full chapter text based on scenes.
- 最后保存到文件
  Save the final output to file.

依赖 / Dependencies:
    pip install "langchain-openai" "langgraph" "pydantic<3"
环境变量 / Env:
    export OPENAI_API_KEY="sk-..."
"""

import logging
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from graph_builder import build_graph
from models import NovelState


# =============== 日志 / Logging ===============
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# =============== CLI 入口 / CLI Entry (can be split into cli.py) ===============

if __name__ == "__main__":
    """
    简单示例 / Simple example:
    - 把 user_input 换成你的“网文题材 + 某套路设定”
      Replace user_input with your own webnovel premise.
    - user_outline 目前先留空，交给系统 auto draft 第一卷
      Leave user_outline empty to auto-draft volume 1.
    - 输出会写到 outputs/novel.txt
      Output is written to outputs/novel.txt.
    """
    graph = build_graph()

    prompt_lang = os.getenv("PROMPT_LANG", "zh").strip() or "zh"

    init_state: NovelState = {
        "user_input": (
            "我要写一部网文题材的奇幻冒险小说，偏套路系。\n"
            "主角原本在首都作为精锐部队队长，后因为勇者召唤而被辞退。\n"
            "他躺平回到乡下边境小镇，打算当个咸鱼，结果不断被卷入各种麻烦。\n"
            "最后解决麻烦，获得了小镇居民的认同，主角找到了方向\n"
            "整体风格：轻松、稍微带点职场吐槽，不搞狗血恋爱。\n"
            "另外这次主要是测试这个脚本，所以故事不宜太长\n"
        ),
        "user_outline": "",
        "prompt_lang": prompt_lang,
        "novel_output_file": "output/novel.txt",
    }

    config = {"configurable": {"thread_id": "novel-demo"}}

    final_state = graph.invoke(init_state, config=config)
    log.info(
        "Done. Chapters generated: %d",
        len(final_state.get("chapters", [])),
    )
