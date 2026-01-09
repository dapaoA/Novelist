"""小说生成核心模块 - 四层架构"""
import json
import re
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.utils.config import get_api_key, get_api_base_url, get_model_name, get_language
from src.utils.file_utils import read_input_file, save_output_file, save_intermediate_file
from src.prompts.prompt_loader import load_prompts


class NovelGenerator:
    """四层架构小说生成器"""
    
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
            temperature=0.8,  # 提高创造性
        )
        
        # 加载对应语言的提示词
        self.language = language if language else get_language()
        self.prompts = load_prompts(self.language)
        print(f"已加载语言: {self.language}")
        
        # 存储各层生成的数据
        self.world_setting: Optional[str] = None
        self.story_outline: Optional[str] = None
        self.scenes: List[Dict] = []
        self.novel_texts: Dict[int, str] = {}  # 场景编号 -> 文字内容
    
    def generate_world_building(self, user_input: str) -> str:
        """
        第一层：生成世界设定（World Building & Lore）
        
        Args:
            user_input: 用户输入的需求
            
        Returns:
            世界设定内容
        """
        prompt = ChatPromptTemplate.from_template(self.prompts.world_building)
        messages = prompt.format_messages(user_input=user_input)
        
        response = self.llm.invoke(messages)
        world_content = response.content
        
        # 保存世界设定
        filename_map = {
            "zh": "01_世界设定.txt",
            "en": "01_World_Setting.txt",
            "ja": "01_世界設定.txt"
        }
        filename = filename_map.get(self.language, "01_World_Setting.txt")
        save_intermediate_file(world_content, filename)
        self.world_setting = world_content
        
        return world_content
    
    def generate_story_layer(self, user_input: str, world_setting: str) -> str:
        """
        第二层：生成故事层（Plot & Character Arc）
        
        Args:
            user_input: 用户输入的需求
            world_setting: 世界设定内容
            
        Returns:
            故事大纲和人物弧光内容
        """
        prompt = ChatPromptTemplate.from_template(self.prompts.story_layer)
        messages = prompt.format_messages(
            world_setting=world_setting,
            user_input=user_input
        )
        
        response = self.llm.invoke(messages)
        story_content = response.content
        
        # 保存故事大纲
        filename_map = {
            "zh": "02_故事大纲与人物弧光.txt",
            "en": "02_Story_Outline_Character_Arc.txt",
            "ja": "02_物語概要_キャラクターアーク.txt"
        }
        filename = filename_map.get(self.language, "02_Story_Outline.txt")
        save_intermediate_file(story_content, filename)
        self.story_outline = story_content
        
        return story_content
    
    def generate_scene_decomposition(self, world_setting: str, story_outline: str) -> List[Dict]:
        """
        第三层：生成场景分解（Scene Decomposition）
        
        Args:
            world_setting: 世界设定
            story_outline: 故事大纲
            
        Returns:
            场景列表，每个场景是一个字典
        """
        prompt = ChatPromptTemplate.from_template(self.prompts.scene_decomposition)
        messages = prompt.format_messages(
            world_setting=world_setting,
            story_outline=story_outline
        )
        
        response = self.llm.invoke(messages)
        scenes_content = response.content
        
        # 保存场景分解
        filename_map = {
            "zh": "03_场景分解.txt",
            "en": "03_Scene_Decomposition.txt",
            "ja": "03_シーン分解.txt"
        }
        filename = filename_map.get(self.language, "03_Scene_Decomposition.txt")
        save_intermediate_file(scenes_content, filename)
        
        # 解析场景列表（简单解析，可以根据需要改进）
        scenes = self._parse_scenes(scenes_content)
        self.scenes = scenes
        
        # 保存场景的JSON格式（便于后续修改）
        scenes_json_filename = "03_场景列表.json" if self.language == "zh" else "03_Scene_List.json"
        save_intermediate_file(json.dumps(scenes, ensure_ascii=False, indent=2), scenes_json_filename)
        
        return scenes
    
    def _parse_scenes(self, scenes_content: str) -> List[Dict]:
        """
        解析场景内容为结构化数据
        
        Args:
            scenes_content: 场景分解的文本内容
            
        Returns:
            场景列表
        """
        scenes = []
        
        # 使用正则表达式匹配场景
        # 匹配 "### 场景 [编号]：[场景名称]" 或类似格式
        scene_pattern = r'(?:###|##|#)\s*场景?\s*\[?(\d+)\]?:?\s*([^\n]+)'
        matches = list(re.finditer(scene_pattern, scenes_content, re.IGNORECASE))
        
        for i, match in enumerate(matches):
            scene_num = int(match.group(1))
            scene_name = match.group(2).strip()
            
            # 找到下一个场景的位置，或者到文本末尾
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(scenes_content)
            scene_text = scenes_content[start_pos:end_pos]
            
            # 提取场景的各个字段
            scene_dict = {
                "number": scene_num,
                "name": scene_name,
                "raw_text": scene_text,
                "location": self._extract_field(scene_text, ["地点", "Location", "場所"]),
                "characters": self._extract_field(scene_text, ["人物", "Characters", "人物"]),
                "goal": self._extract_field(scene_text, ["目标", "Goal", "目標"]),
                "conflict": self._extract_field(scene_text, ["冲突", "Conflict", "対立"]),
                "emotional_tone": self._extract_field(scene_text, ["情感基调", "Emotional Tone", "感情的基調"]),
            }
            scenes.append(scene_dict)
        
        # 如果没有找到结构化场景，至少创建一个包含原始文本的场景
        if not scenes:
            scenes = [{
                "number": 1,
                "name": "场景1",
                "raw_text": scenes_content,
                "location": "",
                "characters": "",
                "goal": "",
                "conflict": "",
                "emotional_tone": "",
            }]
        
        return scenes
    
    def _extract_field(self, text: str, field_names: List[str]) -> str:
        """从文本中提取指定字段的内容"""
        for field_name in field_names:
            # 匹配 "**字段名**：内容" 格式
            pattern = rf'\*+\s*{re.escape(field_name)}\s*\*+:?\s*([^\n]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""
    
    def generate_scene_text(self, scene: Dict, scene_index: int) -> str:
        """
        第四层：生成单个场景的文字内容（Textualization）
        
        Args:
            scene: 场景字典
            scene_index: 场景索引（用于获取前面的场景上下文）
            
        Returns:
            场景的文字内容
        """
        # 构建角色历史/状态上下文（从之前的场景中提取）
        character_context = self._build_character_context(scene_index)
        
        # 构建故事背景（世界设定 + 故事大纲的摘要）
        story_context = f"{self.world_setting[:500]}...\n\n{self.story_outline[:500]}..."
        
        # 构建场景描述
        scene_description = f"""
场景名称：{scene.get('name', '')}
地点：{scene.get('location', '')}
人物：{scene.get('characters', '')}
目标：{scene.get('goal', '')}
冲突：{scene.get('conflict', '')}
情感基调：{scene.get('emotional_tone', '')}

详细描述：
{scene.get('raw_text', '')}
"""
        
        prompt = ChatPromptTemplate.from_template(self.prompts.textualization)
        messages = prompt.format_messages(
            world_setting=self.world_setting or "",
            story_context=story_context,
            scene_description=scene_description,
            character_context=character_context
        )
        
        response = self.llm.invoke(messages)
        scene_text = response.content
        
        # 保存场景文字
        self.novel_texts[scene.get('number', scene_index + 1)] = scene_text
        
        return scene_text
    
    def _build_character_context(self, current_scene_index: int) -> str:
        """构建角色上下文，包括之前场景中角色的状态"""
        if current_scene_index == 0:
            return "这是第一个场景，角色处于初始状态。"
        
        # 简单实现：返回之前场景的文字内容摘要
        context_parts = []
        for i in range(min(current_scene_index, 3)):  # 只看最近3个场景
            scene_num = self.scenes[i].get('number', i + 1)
            if scene_num in self.novel_texts:
                text = self.novel_texts[scene_num]
                context_parts.append(f"场景{scene_num}：{text[:200]}...")
        
        return "\n\n".join(context_parts) if context_parts else "无之前的场景上下文。"
    
    def regenerate_scene(self, scene_number: int) -> str:
        """
        重新生成指定场景的文字（场景层局部修改功能）
        
        Args:
            scene_number: 要重新生成的场景编号
            
        Returns:
            重新生成的场景文字
        """
        # 找到对应的场景
        scene = None
        for s in self.scenes:
            if s.get('number') == scene_number:
                scene = s
                break
        
        if not scene:
            raise ValueError(f"未找到场景编号 {scene_number}")
        
        scene_index = self.scenes.index(scene)
        return self.generate_scene_text(scene, scene_index)
    
    def run(self, input_path: str = "input/input.txt", output_path: str = None):
        """
        运行完整的四层小说生成流程
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如果为None则根据语言自动生成
        """
        # 根据语言设置默认输出文件名
        if output_path is None:
            output_filename_map = {
                "zh": "小说正文.txt",
                "en": "Novel.txt",
                "ja": "小説本文.txt"
            }
            output_filename = output_filename_map.get(self.language, "Novel.txt")
            output_path = f"output/{output_filename}"
        
        # 根据语言设置提示信息
        messages_map = {
            "zh": {
                "read_input": "已读取输入需求：",
                "layer1": "🏗️ 第一层：正在生成世界设定...",
                "layer1_saved": "世界设定已保存",
                "layer2": "📖 第二层：正在生成故事大纲与人物弧光...",
                "layer2_saved": "故事大纲已保存",
                "layer3": "🎬 第三层：正在分解场景...",
                "layer3_saved": "场景分解完成，共 {count} 个场景",
                "layer4": "✍️ 第四层：正在生成场景文字...",
                "layer4_progress": "  场景 {num}/{total}：{name}",
                "layer4_complete": "所有场景文字生成完成",
                "assembling": "正在组装完整小说...",
                "novel_saved": "小说已保存到 "
            },
            "en": {
                "read_input": "Input requirements read: ",
                "layer1": "🏗️ Layer 1: Generating world setting...",
                "layer1_saved": "World setting saved",
                "layer2": "📖 Layer 2: Generating story outline and character arcs...",
                "layer2_saved": "Story outline saved",
                "layer3": "🎬 Layer 3: Decomposing scenes...",
                "layer3_saved": "Scene decomposition complete, {count} scenes total",
                "layer4": "✍️ Layer 4: Generating scene texts...",
                "layer4_progress": "  Scene {num}/{total}: {name}",
                "layer4_complete": "All scene texts generated",
                "assembling": "Assembling complete novel...",
                "novel_saved": "Novel saved to "
            },
            "ja": {
                "read_input": "入力要件を読み取りました：",
                "layer1": "🏗️ 第1層：世界設定を生成中...",
                "layer1_saved": "世界設定が保存されました",
                "layer2": "📖 第2層：物語概要とキャラクターアークを生成中...",
                "layer2_saved": "物語概要が保存されました",
                "layer3": "🎬 第3層：シーンを分解中...",
                "layer3_saved": "シーン分解が完了しました、合計 {count} シーン",
                "layer4": "✍️ 第4層：シーンテキストを生成中...",
                "layer4_progress": "  シーン {num}/{total}：{name}",
                "layer4_complete": "すべてのシーンテキストが生成されました",
                "assembling": "完全な小説を組み立て中...",
                "novel_saved": "小説が "
            }
        }
        messages = messages_map.get(self.language, messages_map["en"])
        
        # 读取输入
        user_input = read_input_file(input_path)
        print(f"{messages['read_input']}{user_input[:100]}...")
        
        # 第一层：世界设定
        print(messages["layer1"])
        world_setting = self.generate_world_building(user_input)
        print(f"✓ {messages['layer1_saved']}")
        
        # 第二层：故事大纲
        print(messages["layer2"])
        story_outline = self.generate_story_layer(user_input, world_setting)
        print(f"✓ {messages['layer2_saved']}")
        
        # 第三层：场景分解
        print(messages["layer3"])
        scenes = self.generate_scene_decomposition(world_setting, story_outline)
        print(f"✓ {messages['layer3_saved'].format(count=len(scenes))}")
        
        # 第四层：为每个场景生成文字
        print(messages["layer4"])
        for i, scene in enumerate(scenes):
            scene_num = scene.get('number', i + 1)
            scene_name = scene.get('name', f'Scene {scene_num}')
            print(messages["layer4_progress"].format(
                num=i + 1,
                total=len(scenes),
                name=scene_name
            ))
            self.generate_scene_text(scene, i)
        print(f"✓ {messages['layer4_complete']}")
        
        # 组装完整小说
        print(messages["assembling"])
        complete_novel = self._assemble_novel()
        
        # 保存输出
        save_output_file(complete_novel, output_path)
        print(f"✓ {messages['novel_saved']}{output_path}")
        
        return complete_novel
    
    def _assemble_novel(self) -> str:
        """组装完整小说"""
        parts = []
        
        # 按场景编号排序
        sorted_scenes = sorted(self.scenes, key=lambda x: x.get('number', 0))
        
        for scene in sorted_scenes:
            scene_num = scene.get('number', 0)
            if scene_num in self.novel_texts:
                # 添加场景标题（可选）
                scene_name = scene.get('name', '')
                if scene_name:
                    title_map = {
                        "zh": f"\n\n## {scene_name}\n\n",
                        "en": f"\n\n## {scene_name}\n\n",
                        "ja": f"\n\n## {scene_name}\n\n"
                    }
                    parts.append(title_map.get(self.language, f"\n\n## {scene_name}\n\n"))
                
                parts.append(self.novel_texts[scene_num])
                parts.append("\n\n")
        
        return "".join(parts).strip()
