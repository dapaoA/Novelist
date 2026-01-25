import logging
from pathlib import Path

from models import NovelState

log = logging.getLogger(__name__)


def node_save_output(state: NovelState) -> NovelState:
    """把章节拼接写入文件 / Save all chapters to file."""

    output_file = state.get("novel_output_file") or "outputs/novel.txt"
    chapters = state.get("chapters", [])

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    text = "\n\n".join(chapters)
    Path(output_file).write_text(text, encoding="utf-8")

    log.info("Novel saved to %s", output_file)

    return state
