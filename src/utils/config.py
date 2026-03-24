"""配置管理工具"""
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
load_dotenv()

# 支持的语言列表
SUPPORTED_LANGUAGES = ["zh", "en", "ja"]
DEFAULT_LANGUAGE = "zh"
SUPPORTED_GENERATION_MODES = ["sandbox", "observer"]
DEFAULT_GENERATION_MODE = "sandbox"


def get_language() -> str:
    """获取语言设置，默认为中文"""
    language = os.getenv("LANGUAGE", DEFAULT_LANGUAGE).lower()
    if language not in SUPPORTED_LANGUAGES:
        print(f"警告: 不支持的语言 '{language}'，使用默认语言 '{DEFAULT_LANGUAGE}'")
        language = DEFAULT_LANGUAGE
    return language


def get_generation_mode() -> str:
    """获取当前生成模式。

    `observer` 保留为旧别名，统一映射到 `sandbox`。
    """
    mode = os.getenv("NOVELIST_MODE", DEFAULT_GENERATION_MODE).lower()
    if mode not in SUPPORTED_GENERATION_MODES:
        print(
            f"警告: 不支持的生成模式 '{mode}'，使用默认模式 '{DEFAULT_GENERATION_MODE}'"
        )
        mode = DEFAULT_GENERATION_MODE
    if mode == "observer":
        return "sandbox"
    return mode


def get_api_key() -> str:
    """获取API密钥，优先使用OPENAI_API_KEY，如果没有则使用DEEPSEEK_API_KEY"""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        return api_key
    
    raise ValueError("未找到OPENAI_API_KEY或DEEPSEEK_API_KEY，请在.env文件中配置")


def get_api_base_url() -> str:
    """根据使用的API密钥返回对应的API base URL"""
    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    elif os.getenv("DEEPSEEK_API_KEY"):
        return os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    return "https://api.openai.com/v1"


def get_model_name() -> str:
    """根据使用的API密钥返回对应的模型名称"""
    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_MODEL", "gpt-4")
    elif os.getenv("DEEPSEEK_API_KEY"):
        return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    return "gpt-4"
