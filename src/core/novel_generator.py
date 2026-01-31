"""小说生成核心模块 - 六层架构

流程：自上而下、自左而右
1. 故事层：生成整体故事（含Episode梗概）
2. Episode层：一节一节链式生成，使用 设定+当前故事+上一个episode → 当前episode
   - 全部Episode完成后才进入Beats层
3. Beats层：从第一个Episode开始，横着链式拆分，使用 上一个beat+设定核心+当前Episode
4. 文字层：从头到尾链式生成，使用 上一个文字+当前beat+故事核心+设定核心

数据结构（有序，保证从头到尾正确读取）：
  world_setting     # 设定层
  story_outline     # 故事层
  episodes: [       # Episode层，按顺序 [ep0, ep1, ep2, ...]
    {title, outline, summary, beats: [b0, b1, ...]},
    ...
  ]
  beat_texts: {ep0_b0: text, ep0_b1: text, ep1_b0: text, ...}  # 文字层
"""
import json
import re
from typing import List, Dict, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.utils.config import get_api_key, get_api_base_url, get_model_name, get_language
from src.utils.file_utils import read_input_file, save_output_file, save_intermediate_file
from src.prompts.prompt_loader import load_prompts


class NovelGenerator:
    """六层架构小说生成器"""

    def __init__(self, language: str = None):
        """
        初始化小说生成器

        Args:
            language: 语言代码 (zh, en, ja等)，如果为None则使用配置的语言
        """
        api_key = get_api_key()
        api_base = get_api_base_url()
        model_name = get_model_name()

        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            base_url=api_base,
            model=model_name,
            temperature=0.8,
        )

        self.language = language if language else get_language()
        self.prompts = load_prompts(self.language)
        print(f"已加载语言: {self.language}")

        # 存储各层生成的数据
        self.world_setting: Optional[str] = None
        self.story_outline: Optional[str] = None
        self._story_data: Optional[Dict] = None  # 故事层JSON
        self.episodes: List[Dict] = []  # [{outline, summary, beats}]
        self.beat_texts: Dict[str, str] = {}  # beat_id -> 文字内容

        # 核心内容长度限制（用于设定核心、故事层核心）
        self.core_length = 600

    def _extract_json(self, content: str) -> Any:
        """从AI输出中提取JSON（处理 ```json 包裹的情况）"""
        content = content.strip()
        # 移除 ```json 或 ``` 包裹
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # 尝试找到第一个 { 和最后一个 } 之间的内容
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"无法解析JSON: {e}") from e

    def _is_placeholder_world_setting(self, data: Dict) -> bool:
        """检测是否为 schema 占位符而非真实生成内容"""
        if not data:
            return True
        # 典型占位符：AI 直接复制的 schema 示例
        known_placeholders = [
            "世界观基础：物理规则、社会体系、地理环境",
            "角色元数据：各主要角色的姓名、外貌、性格核心、能力、背景",
            "Physical rules, social systems, geographic environment",
        ]
        for v in data.values():
            if isinstance(v, str) and v.strip() in known_placeholders:
                return True
        total_len = sum(len(str(v)) for v in data.values() if v)
        return total_len < 100

    def generate_world_building(self, user_input: str) -> str:
        """第一层：生成世界设定（JSON格式）"""
        prompt = ChatPromptTemplate.from_template(self.prompts.world_building)
        messages = prompt.format_messages(user_input=user_input)
        response = self.llm.invoke(messages)
        data = self._extract_json(response.content)

        if self._is_placeholder_world_setting(data):
            raise ValueError(
                "世界设定层返回了占位符内容而非真实设定。请重新运行，或检查模型是否按要求生成了实际内容。"
            )

        # 组合为可读文本供后续层使用
        parts = []
        for k in ["world_foundation", "characters", "race_class_system", "constraints"]:
            if k in data and data[k]:
                label = {"world_foundation": "世界观基础", "characters": "角色元数据",
                        "race_class_system": "种族/职业系统", "constraints": "约束"}.get(k, k)
                parts.append(f"## {label}\n{data[k]}")
        world_content = "\n\n".join(parts) if parts else json.dumps(data, ensure_ascii=False, indent=2)

        save_intermediate_file(json.dumps(data, ensure_ascii=False, indent=2), "01_世界设定.json")
        save_intermediate_file(world_content, "01_世界设定.txt")
        self.world_setting = world_content
        return world_content

    def generate_story_layer(self, user_input: str, world_setting: str) -> str:
        """第二层：生成故事大纲与Episode梗概（JSON格式）"""
        prompt = ChatPromptTemplate.from_template(self.prompts.story_layer)
        messages = prompt.format_messages(world_setting=world_setting, user_input=user_input)
        response = self.llm.invoke(messages)
        data = self._extract_json(response.content)

        # 保存JSON
        save_intermediate_file(json.dumps(data, ensure_ascii=False, indent=2), "02_故事大纲.json")
        # 组合为可读文本
        parts = []
        if data.get("core_theme"):
            parts.append(f"## 核心主题\n{data['core_theme']}")
        if data.get("character_arcs"):
            parts.append(f"## 人物弧光\n{data['character_arcs']}")
        if data.get("episodes"):
            parts.append("## Episode梗概\n" + "\n\n".join(
                f"### {e.get('stage','')} - {e.get('title','')}\n{e.get('outline','')}"
                for e in data["episodes"]
            ))
        if data.get("foreshadowing"):
            parts.append(f"## 伏笔与呼应\n{data['foreshadowing']}")
        self.story_outline = "\n\n".join(parts) if parts else json.dumps(data, ensure_ascii=False, indent=2)
        self._story_data = data
        return self.story_outline

    def _parse_episode_outlines(self, story_content: str) -> List[Dict[str, str]]:
        """从故事层解析Episode列表。优先使用JSON数据，无则兜底解析。"""
        if getattr(self, "_story_data", None) and "episodes" in self._story_data:
            eps = self._story_data["episodes"]
            return [
                {
                    "title": f"{e.get('stage', '')} - {e.get('title', '')}".strip(" -"),
                    "outline": e.get("outline", ""),
                    "stage": e.get("stage", f"stage_{i+1}"),
                }
                for i, e in enumerate(eps)
            ]
        # 兜底：无JSON时返回单个Episode
        return [{"title": "Episode 1", "outline": story_content[:2000], "stage": "stage_1"}]

    def generate_episode_layer(
        self,
        episode_outline: str,
        previous_episode_summary: Optional[str] = None,
    ) -> str:
        """
        第三层：链式生成当前Episode的详细概括
        设定 + 核心主题与人物弧光 + 当前故事 + 上一个episode → 当前episode
        """
        setting_core = self._get_setting_core()
        previous_ep = previous_episode_summary if previous_episode_summary else "无"
        story_data = getattr(self, "_story_data", None) or {}
        core_theme = story_data.get("core_theme", "")
        character_arcs = story_data.get("character_arcs", "")

        prompt = ChatPromptTemplate.from_template(self.prompts.episode_layer)
        messages = prompt.format_messages(
            setting_core=setting_core,
            core_theme=core_theme,
            character_arcs=character_arcs,
            story_outline=self.story_outline or "",
            previous_episode=previous_ep,
            episode_outline=episode_outline,
        )
        response = self.llm.invoke(messages)
        content = response.content
        try:
            data = self._extract_json(content)
            return data.get("summary", content)
        except (ValueError, json.JSONDecodeError):
            return content

    def _get_setting_core(self) -> str:
        """获取设定层核心（截取前N字）"""
        if not self.world_setting:
            return ""
        return self.world_setting[: self.core_length] + ("..." if len(self.world_setting) > self.core_length else "")

    def _get_story_core(self, episode_summary: str = None) -> str:
        """获取故事层核心：整体大纲摘要 + 当前Episode（若有）"""
        parts = []
        if self.story_outline:
            parts.append(self.story_outline[: self.core_length] + ("..." if len(self.story_outline) > self.core_length else ""))
        if episode_summary:
            parts.append(episode_summary[: self.core_length] + ("..." if len(episode_summary) > self.core_length else ""))
        return "\n\n".join(parts) if parts else ""

    def generate_next_beat(
        self, episode_summary: str, previous_beat: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        第四层：增量生成下一个Beat
        仅用：上一个beat + 设定核心 + 当前Episode
        """
        setting_core = self._get_setting_core()
        previous_beat_str = (
            json.dumps(previous_beat, ensure_ascii=False, indent=2) if previous_beat else "无"
        )

        prompt = ChatPromptTemplate.from_template(self.prompts.beats_layer)
        messages = prompt.format_messages(
            setting_core=setting_core,
            episode_context=episode_summary,
            previous_beat=previous_beat_str
        )
        response = self.llm.invoke(messages)
        content = response.content
        beats = self._parse_beats(content)

        if not beats:
            return None
        beat = beats[0]
        if isinstance(beat.get("scene"), str) and "[EPISODE_END]" in beat.get("scene", ""):
            return None
        return beat

    def _parse_beats(self, content: str) -> List[Dict[str, Any]]:
        """解析Beats层输出的JSON格式"""
        beats = []
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        raw_blocks = re.split(r'\n---+\n', content)

        def extract_json_objects(text: str) -> List[Dict]:
            result = []
            i = 0
            while i < len(text):
                if text[i] == '{':
                    depth = 0
                    start = i
                    for j in range(i, len(text)):
                        if text[j] == '{':
                            depth += 1
                        elif text[j] == '}':
                            depth -= 1
                            if depth == 0:
                                try:
                                    obj = json.loads(text[start:j + 1])
                                    if isinstance(obj, dict):
                                        result.append(obj)
                                except json.JSONDecodeError:
                                    pass
                                i = j + 1
                                break
                    else:
                        i += 1
                else:
                    i += 1
            return result

        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue
            for obj in extract_json_objects(block):
                if isinstance(obj, dict) and ("scene" in obj or "action" in obj or "environment" in obj):
                    beats.append(obj)

        if not beats:
            beats = [{
                "scene": "INT./EXT. Unknown - Day",
                "environment": content[:200],
                "action": content[:300],
                "dialogue": [],
                "purpose": "Narrative development"
            }]

        return beats

    def generate_beat_text(
        self, beat: Dict, beat_id: str, previous_text: str = "", episode_summary: str = ""
    ) -> str:
        """
        第五层：根据Beat生成小说文字
        仅用：上一个文字 + 当前beat + 故事层核心 + 设定核心
        """
        beat_str = json.dumps(beat, ensure_ascii=False, indent=2)
        setting_core = self._get_setting_core()
        story_core = self._get_story_core(episode_summary)
        prev_text = previous_text if previous_text else "无"

        prompt = ChatPromptTemplate.from_template(self.prompts.textualization)
        messages = prompt.format_messages(
            setting_core=setting_core,
            story_core=story_core,
            beat_content=beat_str,
            previous_text=prev_text
        )
        response = self.llm.invoke(messages)
        text = response.content
        self.beat_texts[beat_id] = text
        return text

    def _get_previous_text_for_beat(self, episode_index: int, beat_index: int) -> str:
        """获取指定Beat的上一个文字（跨Episode：ep1_b0的上一个是ep0的最后一个beat）"""
        if episode_index == 0 and beat_index == 0:
            return ""
        if beat_index > 0:
            prev_id = f"ep{episode_index}_beat{beat_index - 1}"
            return self.beat_texts.get(prev_id, "")
        # beat_index==0 且 episode_index>0：上一个为前一个Episode的最后一个beat
        prev_ep = self.episodes[episode_index - 1]
        prev_beats = prev_ep.get("beats", [])
        if not prev_beats:
            return ""
        prev_id = f"ep{episode_index - 1}_beat{len(prev_beats) - 1}"
        return self.beat_texts.get(prev_id, "")

    def regenerate_beat(self, episode_index: int, beat_index: int) -> str:
        """重新生成指定Beat的文字"""
        if episode_index >= len(self.episodes):
            raise ValueError(f"Episode索引 {episode_index} 超出范围")
        ep = self.episodes[episode_index]
        beats = ep.get("beats", [])
        if beat_index >= len(beats):
            raise ValueError(f"Beat索引 {beat_index} 超出范围")
        beat_id = f"ep{episode_index}_beat{beat_index}"
        prev_text = self._get_previous_text_for_beat(episode_index, beat_index)
        text = self.generate_beat_text(
            beats[beat_index], beat_id,
            previous_text=prev_text,
            episode_summary=ep["summary"]
        )
        return text

    def run(self, input_path: str = "input/input.txt", output_path: str = None):
        """运行完整的六层小说生成流程"""
        if output_path is None:
            fn_map = {"zh": "小说正文.txt", "en": "Novel.txt", "ja": "小説本文.txt"}
            output_path = f"output/{fn_map.get(self.language, 'Novel.txt')}"

        msg = {
            "zh": {"read": "已读取输入需求：", "l1": "🏗️ 第一层：生成世界设定...", "l2": "📖 第二层：生成故事大纲与Episode梗概...",
                   "l3": "🎬 第三层：Episode扩写为详细概括...", "l3p": "  Episode {n}/{t}：{name}",
                   "l4": "📋 第四层：拆分为Beats...", "l4p": "  Episode {n}/{t}：{name}",
                   "l5": "✍️ 第五层：生成Beat文字...", "l5p": "  Beat {n}/{t}",
                   "asm": "正在组装完整小说...", "saved": "小说已保存到 "},
            "en": {"read": "Input read: ", "l1": "🏗️ Layer 1: World setting...", "l2": "📖 Layer 2: Story & Episode outlines...",
                   "l3": "🎬 Layer 3: Episode expansion...", "l3p": "  Episode {n}/{t}: {name}",
                   "l4": "📋 Layer 4: Beats decomposition...", "l4p": "  Episode {n}/{t}: {name}",
                   "l5": "✍️ Layer 5: Beat text...", "l5p": "  Beat {n}/{t}",
                   "asm": "Assembling novel...", "saved": "Novel saved to "},
            "ja": {"read": "入力読み取り：", "l1": "🏗️ 第1層：世界設定...", "l2": "📖 第2層：物語とEpisode梗概...",
                   "l3": "🎬 第3層：Episode拡張...", "l3p": "  Episode {n}/{t}：{name}",
                   "l4": "📋 第4層：Beats分解...", "l4p": "  Episode {n}/{t}：{name}",
                   "l5": "✍️ 第5層：Beat文章...", "l5p": "  Beat {n}/{t}",
                   "asm": "小説を組み立て中...", "saved": "小説が "},
        }
        m = msg.get(self.language, msg["en"])

        user_input = read_input_file(input_path)
        print(f"{m['read']}{user_input[:80]}...")

        # Layer 1
        print(m["l1"])
        self.generate_world_building(user_input)
        print("✓ 世界设定已保存")

        # Layer 2
        print(m["l2"])
        self.generate_story_layer(user_input, self.world_setting)
        print("✓ 故事大纲已保存")

        # 解析Episode梗概（有序列表）
        self.episodes = []
        parsed = self._parse_episode_outlines(self.story_outline)

        # Layer 3: Episode层链式生成（设定+当前故事+上一个episode → 当前episode）
        # 一节一节生成，全部完成后才进入Beats层
        print(m["l3"])
        prev_episode_summary = None
        for i, ep in enumerate(parsed):
            print(m["l3p"].format(n=i + 1, t=len(parsed), name=ep.get("title", f"Ep{i+1}")[:30]))
            summary = self.generate_episode_layer(
                ep["outline"],
                previous_episode_summary=prev_episode_summary,
            )
            self.episodes.append({
                "title": ep["title"],
                "outline": ep["outline"],
                "summary": summary,
                "beats": [],
            })
            prev_episode_summary = summary

        # 保存Episode详细概括
        ep_data = [{"title": e["title"], "outline": e["outline"], "summary": e["summary"]} for e in self.episodes]
        save_intermediate_file(json.dumps(ep_data, ensure_ascii=False, indent=2), "03_Episode详细概括.json")
        ep_content = "\n\n---\n\n".join([f"## {e['title']}\n\n{e['summary']}" for e in self.episodes])
        save_intermediate_file(ep_content, "03_Episode详细概括.txt")

        # Layer 4: Beats层 - 从第一个Episode开始横着链式拆分
        # 每个Episode内：上一个beat + 设定核心 + 当前Episode → 下一个beat
        # 按episodes顺序处理，保证从左到右
        print(m["l4"])
        all_beats_flat = []
        max_beats_per_episode = 15
        for i, ep in enumerate(self.episodes):
            print(m["l4p"].format(n=i + 1, t=len(self.episodes), name=ep["title"][:30]))
            beats = []
            prev_beat = None
            for j in range(max_beats_per_episode):
                next_beat = self.generate_next_beat(ep["summary"], prev_beat)
                if next_beat is None:
                    break
                beats.append(next_beat)
                prev_beat = next_beat
            self.episodes[i]["beats"] = beats
            for j, b in enumerate(beats):
                all_beats_flat.append((i, j, b))

        # 保存Beats JSON
        beats_data = [{"episode": i, "beat_index": j, "beat": b} for i, j, b in all_beats_flat]
        save_intermediate_file(json.dumps(beats_data, ensure_ascii=False, indent=2), "04_Beats.json")

        # Layer 5: 文字层 - 从头到尾链式生成
        # 上一个文字 + 当前beat + 故事层核心 + 设定核心 → 当前文字
        # all_beats_flat 已按 ep0_b0, ep0_b1, ..., ep1_b0, ... 有序排列
        print(m["l5"])
        total = len(all_beats_flat)
        prev_text = ""
        for idx, (ei, bi, beat) in enumerate(all_beats_flat):
            print(m["l5p"].format(n=idx + 1, t=total))
            beat_id = f"ep{ei}_beat{bi}"
            ep_summary = self.episodes[ei]["summary"]
            self.generate_beat_text(beat, beat_id, previous_text=prev_text, episode_summary=ep_summary)
            prev_text = self.beat_texts[beat_id]

        # 组装
        print(m["asm"])
        complete = self._assemble_novel()
        save_output_file(complete, output_path)
        print(f"✓ {m['saved']}{output_path}")
        return complete

    def _assemble_novel(self) -> str:
        """组装完整小说"""
        parts = []
        for i, ep in enumerate(self.episodes):
            beats = ep.get("beats", [])
            for j in range(len(beats)):
                bid = f"ep{i}_beat{j}"
                if bid in self.beat_texts:
                    parts.append(self.beat_texts[bid])
                    parts.append("\n\n")
        return "".join(parts).strip()
