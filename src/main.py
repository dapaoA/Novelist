"""主程序入口"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.novel_generator import NovelGenerator
from src.utils.config import get_generation_mode, get_language


def _update_character_knowledge(complete_text: str, *, language: str) -> None:
    """Build or refresh the character knowledge snapshot after generation.

    Character knowledge is a secondary artifact compared with the final novel
    text. The workflow therefore runs on a best-effort basis so knowledge
    extraction failures do not erase a successfully generated novel.
    """
    message_map = {
        "zh": {
            "start": "正在更新角色知识库...",
            "saved": "角色知识库快照已保存到 ",
            "summary_title": "角色知识库摘要",
            "loaded": "- 已导入角色: ",
            "created": "- 新建角色: ",
            "updated": "- 更新角色: ",
            "ambiguous": "- 歧义解析: ",
            "warnings": "- 准备文件警告: ",
            "ambiguous_report": "- 歧义报告: ",
            "discovered_report": "- 新发现角色报告: ",
            "warn": "角色知识库更新失败：",
        },
        "en": {
            "start": "Updating character knowledge...",
            "saved": "Character knowledge snapshot saved to ",
            "summary_title": "Character Knowledge Summary",
            "loaded": "- loaded from input: ",
            "created": "- created: ",
            "updated": "- updated: ",
            "ambiguous": "- ambiguous: ",
            "warnings": "- preparation warnings: ",
            "ambiguous_report": "- ambiguous report: ",
            "discovered_report": "- discovered candidates report: ",
            "warn": "Character knowledge update failed: ",
        },
        "ja": {
            "start": "キャラクター知識を更新中...",
            "saved": "キャラクター知識スナップショットを保存しました: ",
            "summary_title": "キャラクター知識サマリー",
            "loaded": "- 読み込み済みキャラクター: ",
            "created": "- 新規作成: ",
            "updated": "- 更新: ",
            "ambiguous": "- 曖昧な解決: ",
            "warnings": "- 準備ファイル警告: ",
            "ambiguous_report": "- 曖昧性レポート: ",
            "discovered_report": "- 新規候補レポート: ",
            "warn": "キャラクター知識の更新に失敗しました: ",
        },
    }
    messages = message_map.get(language, message_map["en"])

    try:
        print(messages["start"])
        from src.characters.workflow import CharacterKnowledgeWorkflow

        workflow = CharacterKnowledgeWorkflow()
        result = workflow.process_text(complete_text)
        if result.snapshot_path is not None:
            print(f"{messages['saved']}{result.snapshot_path}")
        print(messages["summary_title"])
        print(f"{messages['loaded']}{len(result.loaded_characters)}")
        print(f"{messages['created']}{len(result.created_characters)}")
        print(f"{messages['updated']}{len(result.updated_characters)}")
        print(f"{messages['ambiguous']}{len(result.ambiguous_resolutions)}")
        print(f"{messages['warnings']}{len(result.preparation_warnings)}")
        if result.ambiguous_report_path is not None:
            print(f"{messages['ambiguous_report']}{result.ambiguous_report_path}")
        if result.discovered_candidates_path is not None:
            print(f"{messages['discovered_report']}{result.discovered_candidates_path}")
        for warning in result.preparation_warnings:
            print(f"  {warning}")
    except Exception as error:  # noqa: BLE001 - this is best-effort post-processing.
        print(f"{messages['warn']}{error}")


def main():
    """主函数"""
    # 获取语言设置（可以从环境变量读取，也可以作为命令行参数）
    language = get_language()
    generation_mode = get_generation_mode()

    print("=" * 50)
    title_map = {
        "zh": "AI小说家 - 沙盘模式",
        "en": "AI Novelist - Sandbox Mode",
        "ja": "AI小説家 - Sandbox Mode",
    }
    print(title_map.get(language, "AI Novelist - Starting novel generation"))
    print(f"Mode: {generation_mode}")
    print("=" * 50)

    try:
        generator = NovelGenerator(language=language)
        complete_text = generator.run()
        _update_character_knowledge(complete_text, language=language)

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
