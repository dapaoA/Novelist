"""文件操作工具"""
import os
from pathlib import Path


def read_input_file(input_path: str = "input/input.txt") -> str:
    """读取输入文件内容"""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_output_file(content: str, output_path: str = "output/小说正文.txt"):
    """保存输出文件"""
    path = Path(output_path)
    # 确保输出目录存在
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def save_intermediate_file(content: str, filename: str):
    """保存中间文件（剧情、设定等）"""
    intermediate_dir = Path("intermediate")
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = intermediate_dir / filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return str(output_path)
