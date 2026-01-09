# Novelist - AI小说家

一个基于LangChain的AI小说生成项目，支持OpenAI和DeepSeek API。

## 项目结构

```
Novelist/
├── src/                    # 源代码目录
│   ├── prompts/           # 提示词模板
│   │   ├── __init__.py
│   │   ├── prompt_loader.py  # 提示词加载器
│   │   ├── zh/            # 中文提示词
│   │   │   ├── __init__.py
│   │   │   └── prompts.py
│   │   ├── en/            # 英文提示词
│   │   │   ├── __init__.py
│   │   │   └── prompts.py
│   │   └── ja/            # 日文提示词
│   │       ├── __init__.py
│   │       └── prompts.py
│   ├── utils/             # 工具类
│   │   ├── __init__.py
│   │   ├── config.py      # 配置管理
│   │   └── file_utils.py  # 文件操作工具
│   ├── core/              # 核心代码
│   │   ├── __init__.py
│   │   └── novel_generator.py  # 小说生成器
│   └── main.py            # 主程序入口
├── input/                 # 输入目录
│   └── input.txt          # 输入文件（小说需求）
├── intermediate/          # 中间结果目录
│   └── 剧情大纲.txt       # AI生成的剧情大纲
├── output/                # 输出目录
│   └── 小说正文.txt       # 生成的小说正文
├── requirements.txt       # Python依赖
├── env.example            # 环境变量示例
└── README.md
```

## 安装步骤

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
   - 复制 `env.example` 为 `.env`
   - 在 `.env` 文件中配置：
     ```
     # 语言配置（可选，默认为zh）
     # 支持的语言: zh (中文), en (English), ja (日本語)
     LANGUAGE=zh
     
     # 方式1：使用OpenAI
     OPENAI_API_KEY=your_openai_api_key_here
     
     # 方式2：使用DeepSeek（优先使用OpenAI，如果没有则使用DeepSeek）
     DEEPSEEK_API_KEY=your_deepseek_api_key_here
     ```

## 使用方法

1. 在 `input/input.txt` 文件中输入你的小说需求，例如：
   ```
   请生成一部科幻小说，主题关于人工智能与人类的未来关系。
   ```

2. 运行主程序：
```bash
python src/main.py
```

3. 生成完成后：
   - 剧情大纲会保存在 `intermediate/` 目录（文件名根据语言不同）
   - 小说正文会保存在 `output/` 目录（文件名根据语言不同）

## 功能特性

- **多语言支持**：支持中文(zh)、英文(en)、日文(ja)，可轻松扩展更多语言
- 支持OpenAI和DeepSeek双API
- 自动生成剧情大纲（中间结果）
- 基于剧情大纲生成完整小说
- 模块化设计，易于扩展

## 多语言配置

### 当前支持的语言
- `zh` - 中文（默认）
- `en` - English
- `ja` - 日本語

### 添加新语言
要添加新语言，只需：

1. 在 `src/prompts/` 下创建新的语言文件夹（例如 `fr/` 用于法语）
2. 在新文件夹中创建 `prompts.py` 文件，包含：
   - `NOVEL_GENERATION_PROMPT` - 小说生成提示词
   - `PLOT_PLANNING_PROMPT` - 剧情大纲提示词
3. 在 `src/utils/config.py` 的 `SUPPORTED_LANGUAGES` 列表中添加新语言代码
4. 在 `src/core/novel_generator.py` 的相应映射中添加文件命名规则

### 设置语言
- **方法1**：在 `.env` 文件中设置 `LANGUAGE=语言代码`（例如 `LANGUAGE=en`）
- **方法2**：在代码中直接指定：`generator = NovelGenerator(language="en")`

## 注意事项

- 确保已正确配置API密钥
- 生成小说需要消耗API调用次数，请注意成本
- 可以根据需要修改对应语言文件夹中的 `prompts.py` 来调整提示词模板
- 不同语言的输出文件名会自动调整（例如：中文为"小说正文.txt"，英文为"Novel.txt"）