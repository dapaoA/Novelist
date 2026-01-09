"""主程序入口"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.novel_generator import NovelGenerator
from src.utils.config import get_language


def main():
    """主函数"""
    # 获取语言设置（可以从环境变量读取，也可以作为命令行参数）
    language = get_language()
    
    print("=" * 50)
    title_map = {
        "zh": "AI小说家 - 开始生成小说",
        "en": "AI Novelist - Starting novel generation",
        "ja": "AI小説家 - 小説生成を開始"
    }
    print(title_map.get(language, "AI Novelist - Starting novel generation"))
    print("=" * 50)
    
    try:
        generator = NovelGenerator(language=language)
        generator.run()
        
        print("=" * 50)
        success_msg_map = {
            "zh": "小说生成完成！",
            "en": "Novel generation completed!",
            "ja": "小説生成が完了しました！"
        }
        print(success_msg_map.get(language, "Novel generation completed!"))
        print("=" * 50)
    
    except ValueError as e:
        print(f"配置错误: {e}")
        print("请确保在.env文件中配置了OPENAI_API_KEY或DEEPSEEK_API_KEY")
        sys.exit(1)
    
    except FileNotFoundError as e:
        print(f"文件错误: {e}")
        sys.exit(1)
    
    except Exception as e:
        print(f"生成过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
