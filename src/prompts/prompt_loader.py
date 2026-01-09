"""提示词加载器"""
import importlib
from pathlib import Path
from typing import NamedTuple
from src.utils.config import get_language, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE


class Prompts(NamedTuple):
    """四层提示词结构"""
    world_building: str
    story_layer: str
    scene_decomposition: str
    textualization: str


def load_prompts(language: str = None) -> Prompts:
    """
    根据语言加载对应的四层提示词
    
    Args:
        language: 语言代码 (zh, en, ja等)，如果为None则使用配置的语言
    
    Returns:
        Prompts: 包含四层提示词的命名元组
        - world_building: 设定层提示词
        - story_layer: 故事层提示词
        - scene_decomposition: 场景层提示词
        - textualization: 文字层提示词
    
    Raises:
        ValueError: 如果语言不支持或找不到提示词模块
    """
    if language is None:
        language = get_language()
    
    if language not in SUPPORTED_LANGUAGES:
        print(f"警告: 不支持的语言 '{language}'，使用默认语言 '{DEFAULT_LANGUAGE}'")
        language = DEFAULT_LANGUAGE
    
    # 动态导入对应语言的提示词模块
    try:
        prompt_module = importlib.import_module(f"src.prompts.{language}.prompts")
        
        return Prompts(
            world_building=prompt_module.WORLD_BUILDING_PROMPT,
            story_layer=prompt_module.STORY_LAYER_PROMPT,
            scene_decomposition=prompt_module.SCENE_DECOMPOSITION_PROMPT,
            textualization=prompt_module.TEXTUALIZATION_PROMPT
        )
    except ImportError as e:
        raise ValueError(
            f"无法加载语言 '{language}' 的提示词: {e}. "
            f"请确保 src/prompts/{language}/prompts.py 文件存在。"
        )
    except AttributeError as e:
        raise ValueError(
            f"提示词模块缺少必需的提示词模板: {e}. "
            f"请确保 src/prompts/{language}/prompts.py 包含所有四层提示词。"
        )