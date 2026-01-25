import os

from langchain_openai import ChatOpenAI


def build_llm() -> ChatOpenAI:
    """
    统一创建一个 LLM 实例。
    后续如果你想切换到别的模型，只改这里就行。
    Create the LLM instance in one place so swapping models is easy.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置环境变量 OPENAI_API_KEY")
    # 你可以按需换成 gpt-4.1 / o3-mini 等
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
    )
