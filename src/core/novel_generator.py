"""小说生成核心模块"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.utils.config import get_api_key, get_api_base_url, get_model_name, get_language
from src.utils.file_utils import read_input_file, save_output_file, save_intermediate_file
from src.prompts.prompt_loader import load_prompts


class NovelGenerator:
    """小说生成器"""
    
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
        self.novel_prompt, self.plot_prompt = load_prompts(self.language)
        print(f"已加载语言: {self.language}")
    
    def generate_plot(self, user_input: str) -> str:
        """生成剧情大纲"""
        prompt = ChatPromptTemplate.from_template(self.plot_prompt)
        messages = prompt.format_messages(user_input=user_input)
        
        response = self.llm.invoke(messages)
        plot_content = response.content
        
        # 根据语言保存中间结果文件名
        plot_filename_map = {
            "zh": "剧情大纲.txt",
            "en": "Plot_Outline.txt",
            "ja": "プロット概要.txt"
        }
        plot_filename = plot_filename_map.get(self.language, "Plot_Outline.txt")
        
        # 保存中间结果
        save_intermediate_file(plot_content, plot_filename)
        
        return plot_content
    
    def generate_novel(self, user_input: str, plot: str = None) -> str:
        """生成小说正文"""
        # 根据语言设置剧情大纲的标签
        plot_label_map = {
            "zh": "剧情大纲",
            "en": "Plot Outline",
            "ja": "プロット概要"
        }
        plot_label = plot_label_map.get(self.language, "Plot Outline")
        
        # 如果有剧情大纲，将其加入输入
        if plot:
            enhanced_input = f"{user_input}\n\n{plot_label}：\n{plot}"
        else:
            enhanced_input = user_input
        
        prompt = ChatPromptTemplate.from_template(self.novel_prompt)
        messages = prompt.format_messages(user_input=enhanced_input)
        
        response = self.llm.invoke(messages)
        novel_content = response.content
        
        return novel_content
    
    def run(self, input_path: str = "input/input.txt", output_path: str = None):
        """
        运行完整的小说生成流程
        
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
                "generating_plot": "正在生成剧情大纲...",
                "plot_saved": "剧情大纲已保存到 intermediate/",
                "generating_novel": "正在生成小说正文...",
                "novel_saved": "小说已保存到 "
            },
            "en": {
                "read_input": "Input requirements read: ",
                "generating_plot": "Generating plot outline...",
                "plot_saved": "Plot outline saved to intermediate/",
                "generating_novel": "Generating novel content...",
                "novel_saved": "Novel saved to "
            },
            "ja": {
                "read_input": "入力要件を読み取りました：",
                "generating_plot": "プロット概要を生成中...",
                "plot_saved": "プロット概要が intermediate/ に保存されました",
                "generating_novel": "小説本文を生成中...",
                "novel_saved": "小説が "
            }
        }
        messages = messages_map.get(self.language, messages_map["en"])
        
        # 读取输入
        user_input = read_input_file(input_path)
        print(f"{messages['read_input']}{user_input[:100]}...")
        
        # 生成剧情大纲（中间步骤）
        print(messages["generating_plot"])
        plot = self.generate_plot(user_input)
        plot_filename_map = {
            "zh": "剧情大纲.txt",
            "en": "Plot_Outline.txt",
            "ja": "プロット概要.txt"
        }
        plot_filename = plot_filename_map.get(self.language, "Plot_Outline.txt")
        print(f"{messages['plot_saved']}{plot_filename}")
        
        # 生成小说正文
        print(messages["generating_novel"])
        novel = self.generate_novel(user_input, plot)
        
        # 保存输出
        save_output_file(novel, output_path)
        print(f"{messages['novel_saved']}{output_path}")
        
        return novel
