"""提示词加载器"""
import importlib
from pathlib import Path
from src.utils.config import get_language, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE


def load_prompts(language: str = None) -> tuple[str, str]:
    """
    根据语言加载对应的提示词
    
    Args:
        language: 语言代码 (zh, en, ja等)，如果为None则使用配置的语言
    
    Returns:
        tuple: (NOVEL_GENERATION_PROMPT, PLOT_PLANNING_PROMPT)
    
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
        novel_prompt = prompt_module.NOVEL_GENERATION_PROMPT
        plot_prompt = prompt_module.PLOT_PLANNING_PROMPT
        return novel_prompt, plot_prompt
    except ImportError as e:
        raise ValueError(
            f"无法加载语言 '{language}' 的提示词: {e}. "
            f"请确保 src/prompts/{language}/prompts.py 文件存在。"
        )
