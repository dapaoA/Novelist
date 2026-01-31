"""单层调试脚本：从 intermediate 读取数据，执行指定层级一次，保存 prompt 与 response。

用法:
  python -m src.debug_layer --layer 1
  python -m src.debug_layer --layer 2
  python -m src.debug_layer --layer 3 --episode 0
  python -m src.debug_layer --layer 3 --episode 2
  python -m src.debug_layer --layer 4 --episode 0 --beat 0
  python -m src.debug_layer --layer 4 --episode 1 --beat 2
  python -m src.debug_layer --layer 5 --episode 0 --beat 0 [--prev-text-file path]

输出: debug/debug_L{layer}_prompt.txt, debug/debug_L{layer}_response.txt
"""
import argparse
import json
from pathlib import Path
import sys

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

INTERMEDIATE = PROJECT_ROOT / "intermediate"
DEBUG_DIR = PROJECT_ROOT / "debug"


def load_json(name: str) -> dict | list:
    path = INTERMEDIATE / name
    if not path.exists():
        raise FileNotFoundError(f"缺少中间文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_text(name: str) -> str:
    path = INTERMEDIATE / name
    if not path.exists():
        raise FileNotFoundError(f"缺少中间文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_input() -> str:
    path = PROJECT_ROOT / "input" / "input.txt"
    if not path.exists():
        raise FileNotFoundError(f"缺少输入文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_debug(suffix: str, content: str):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    path = DEBUG_DIR / f"debug_{suffix}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已保存: {path}")


def messages_to_prompt_str(messages) -> str:
    """将 LangChain messages 转为可读字符串"""
    lines = []
    for m in messages:
        role = getattr(m, "type", "unknown")
        if hasattr(m, "content"):
            lines.append(f"[{role}]\n{m.content}")
        else:
            lines.append(str(m))
        lines.append("")
    return "\n".join(lines).strip()


def main():
    parser = argparse.ArgumentParser(description="单层调试：执行指定层级一次，保存 prompt 与 response")
    parser.add_argument("--layer", "-l", type=int, required=True, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--episode", "-e", type=int, default=0, help="Episode 索引（layer 3/4/5 需要）")
    parser.add_argument("--beat", "-b", type=int, default=0, help="Beat 索引（layer 4/5 需要）")
    parser.add_argument("--prev-text-file", type=str, default=None, help="Layer 5 的上一段文字文件路径")
    parser.add_argument("--lang", type=str, default=None, help="语言 (zh/en/ja)，默认从配置读取")
    args = parser.parse_args()

    from src.core.novel_generator import NovelGenerator
    from src.utils.config import get_language
    from langchain_core.prompts import ChatPromptTemplate

    lang = args.lang or get_language()
    gen = NovelGenerator(language=lang)
    core_len = gen.core_length

    # 按需从 intermediate 加载
    def safe_load_json(name):
        p = INTERMEDIATE / name
        if not p.exists():
            return {} if "世界设定" in name or "故事" in name else []
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def safe_load_text(name):
        p = INTERMEDIATE / name
        if not p.exists():
            return ""
        with open(p, "r", encoding="utf-8") as f:
            return f.read()

    world_txt = safe_load_text("01_世界设定.txt")
    if not world_txt and (INTERMEDIATE / "01_世界设定.json").exists():
        wj = safe_load_json("01_世界设定.json")
        if isinstance(wj, dict):
            parts = []
            for k, label in [("world_foundation", "世界观基础"), ("characters", "角色元数据"), ("race_class_system", "种族/职业系统"), ("constraints", "约束")]:
                if k in wj and wj[k]:
                    parts.append(f"## {label}\n{wj[k]}")
            world_txt = "\n\n".join(parts)
    story_json = safe_load_json("02_故事大纲.json")
    episodes_data = safe_load_json("03_Episode详细概括.json")
    beats_data = safe_load_json("04_Beats.json")
    if not isinstance(beats_data, list):
        beats_data = []

    gen.world_setting = world_txt
    gen._story_data = story_json
    gen.story_outline = safe_load_text("02_故事大纲与Episode梗概.txt") or json.dumps(story_json, ensure_ascii=False, indent=2)

    gen.episodes = []
    for i, ep in enumerate(episodes_data if isinstance(episodes_data, list) else []):
        ep_item = {"title": ep.get("title", ""), "outline": ep.get("outline", ""), "summary": ep.get("summary", ""), "beats": []}
        for item in beats_data:
            if isinstance(item, dict) and item.get("episode") == i:
                ep_item["beats"].append(item.get("beat", item))
        gen.episodes.append(ep_item)

    setting_core = world_txt[:core_len] + ("..." if len(world_txt) > core_len else "") if world_txt else ""

    layer = args.layer
    suffix = f"L{layer}"
    if layer in (3, 4, 5):
        suffix += f"_ep{args.episode}"
    if layer in (4, 5):
        suffix += f"_beat{args.beat}"

    # 构建 prompt 并调用
    if layer == 1:
        user_input = load_input()
        prompt = ChatPromptTemplate.from_template(gen.prompts.world_building)
        messages = prompt.format_messages(user_input=user_input)

    elif layer == 2:
        if not world_txt:
            raise FileNotFoundError("Layer 2 需要 01_世界设定.txt 或 01_世界设定.json")
        user_input = load_input()
        prompt = ChatPromptTemplate.from_template(gen.prompts.story_layer)
        messages = prompt.format_messages(world_setting=world_txt, user_input=user_input)

    elif layer == 3:
        eps = story_json.get("episodes", [])
        if args.episode >= len(eps):
            raise ValueError(f"Episode {args.episode} 超出范围 (共 {len(eps)} 个)")
        ep_outline = eps[args.episode].get("outline", "")
        prev_summary = ""
        if args.episode > 0 and episodes_data and isinstance(episodes_data, list) and len(episodes_data) > args.episode - 1:
            prev_summary = episodes_data[args.episode - 1].get("summary", "")

        prompt = ChatPromptTemplate.from_template(gen.prompts.episode_layer)
        messages = prompt.format_messages(
            setting_core=setting_core,
            core_theme=story_json.get("core_theme", ""),
            character_arcs=story_json.get("character_arcs", ""),
            story_outline=gen.story_outline or "",
            previous_episode=prev_summary or "无",
            episode_outline=ep_outline,
        )

    elif layer == 4:
        if not episodes_data or args.episode >= len(episodes_data):
            raise ValueError(f"Episode {args.episode} 超出范围，03_Episode详细概括.json 中无此集 (共 {len(episodes_data) if episodes_data else 0} 集)")
        ep_summary = episodes_data[args.episode].get("summary", "")

        prev_beat = None
        for item in beats_data:
            if isinstance(item, dict) and item.get("episode") == args.episode and item.get("beat_index") == args.beat - 1:
                prev_beat = item.get("beat", item)
                break
        prev_beat_str = json.dumps(prev_beat, ensure_ascii=False, indent=2) if prev_beat else "无"

        prompt = ChatPromptTemplate.from_template(gen.prompts.beats_layer)
        messages = prompt.format_messages(
            setting_core=setting_core,
            episode_context=ep_summary,
            previous_beat=prev_beat_str,
        )

    elif layer == 5:
        beat_obj = None
        ep_summary = ""
        for item in beats_data:
            if isinstance(item, dict) and item.get("episode") == args.episode and item.get("beat_index") == args.beat:
                beat_obj = item.get("beat", item)
                break
        if not beat_obj:
            raise ValueError(f"未找到 Episode {args.episode} Beat {args.beat}，请检查 04_Beats.json")

        if episodes_data and args.episode < len(episodes_data):
            ep_summary = episodes_data[args.episode].get("summary", "")

        prev_text = ""
        if args.prev_text_file:
            with open(args.prev_text_file, "r", encoding="utf-8") as f:
                prev_text = f.read()
        else:
            # 尝试从 output 或已生成文本推断（简化：只支持首 beat 或手动传入）
            pass

        story_core = (gen.story_outline or "")[:core_len] + ("..." if len(gen.story_outline or "") > core_len else "")
        if ep_summary:
            story_core += "\n\n" + (ep_summary[:core_len] + ("..." if len(ep_summary) > core_len else ""))

        prompt = ChatPromptTemplate.from_template(gen.prompts.textualization)
        messages = prompt.format_messages(
            setting_core=setting_core,
            story_core=story_core,
            beat_content=json.dumps(beat_obj, ensure_ascii=False, indent=2),
            previous_text=prev_text or "无",
        )

    # 保存 prompt
    prompt_str = messages_to_prompt_str(messages)
    save_debug(f"{suffix}_prompt", prompt_str)

    # 调用模型
    print(f"调用模型 (Layer {layer})...")
    response = gen.llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)

    save_debug(f"{suffix}_response", content)
    print("完成。")


if __name__ == "__main__":
    main()
