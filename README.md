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
│   ├── 01_世界设定.txt
│   ├── 02_故事大纲与Episode梗概.txt
│   ├── 03_Episode详细概括.txt
│   └── 04_Beats.json
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
   - 各层中间结果保存在 `intermediate/` 目录（世界设定、故事大纲、Episode概括、Beats.json）
   - 小说正文保存在 `output/` 目录（文件名根据语言不同）

## 功能特性

- **六层架构**：设定 → 故事(Episode梗概) → Episode扩写 → Beats拆分 → 文字生成
- **古典戏剧结构**：故事层按起承转合组织 Episode，形成完整 callback
- **剧本式 Beats**：标准格式（scene, environment, action, dialogue, purpose），支持局部重生成
- **多语言支持**：中文(zh)、英文(en)、日文(ja)，可扩展
- 支持 OpenAI 和 DeepSeek 双 API

## 多语言配置

### 当前支持的语言
- `zh` - 中文（默认）
- `en` - English
- `ja` - 日本語

### 添加新语言
要添加新语言，只需：

1. 在 `src/prompts/` 下创建新的语言文件夹（例如 `fr/` 用于法语）
2. 在新文件夹中创建 `prompts.py` 文件，包含六层提示词：
   - `WORLD_BUILDING_PROMPT` - 设定层
   - `STORY_LAYER_PROMPT` - 故事层
   - `EPISODE_LAYER_PROMPT` - Episode层
   - `BEATS_LAYER_PROMPT` - Beats层
   - `TEXTUALIZATION_PROMPT` - 文字层
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

## 六层架构 (Six-Layer Framework)

本小说写作器采用**自上而下设计、自底向上反馈、逐层冻结**的六层架构：

### 层级说明

| 层级 | 名称 | 说明 |
|------|------|------|
| **1** | 设定层 (World Building) | 世界观、角色元数据、种族/职业系统、长期约束。系统的"根基"。 |
| **2** | 故事层 (Story Layer) | 剧情大纲、人物弧光、按**起承转合**组织的多个 Episode 梗概。形成完整 callback。 |
| **3** | Episode层 (Episode Layer) | 将每个 Episode 梗概扩写为**详细概括**（500–800 字），作为 Beats 拆分的输入。 |
| **4** | Beats层 (Beats Layer) | 将 Episode 详细概括拆分为标准剧本格式的 **Beats**，用于指导表演的最小叙事单位。 |
| **5** | 文字层 (Textualization) | 根据每个 Beat 生成小说正文，实现文笔润色与氛围渲染。 |

### Beat 数据结构

每个 Beat 为标准剧本格式的 JSON：

```json
{
  "scene": "EXT. 跨江大桥下 - 夜",
  "environment": "桥下一个小型聚会，灯光闪烁，卡拉ok机播放着怀旧金曲。",
  "action": "两人停下脚步，被大叔唱的歌声吸引。",
  "dialogue": [
    {"A": "（感慨）：\"这样的景象，真是别有一番滋味。\""},
    {"B": "（轻轻笑着抓住丽娜的手）：\"有时候，我想我们也应该这样，简单快乐。\""}
  ],
  "purpose": "通过共同的怀旧体验深化两人之间的情感联系，暗示友情的重要性。"
}
```

### 数据流（自上而下、自左而右）

```
用户输入 → 设定层 → 故事层 → Episode层(链式) → [全部完成] → Beats层(链式) → 文字层(链式) → 小说正文
```

### 顺序与上下文规则

| 层级 | 顺序 | 上下文 |
|------|------|--------|
| **Episode层** | 一节一节，从左到右 | 设定 + 当前故事 + **上一个episode** → 当前episode |
| **Beats层** | 从第一个Episode开始横着链式 | 上一个beat + 设定核心 + 当前Episode → 下一个beat |
| **文字层** | 从头到尾链式 | 上一个文字 + 当前beat + 故事核心 + 设定核心 → 当前文字 |

### 数据结构（有序）

```
world_setting
story_outline
episodes: [ep0, ep1, ep2, ...]   # 按顺序链式生成
  └── 每episode: {title, outline, summary, beats: [b0, b1, ...]}
beat_texts: {ep0_b0, ep0_b1, ep1_b0, ...}  # 按顺序链式生成
```

- Episode 层必须**全部完成**后才进入 Beats 层
- 每层按顺序读取上一层的输出，保证从头到尾正确

### 中间文件（均为 JSON，读取稳定）

- `01_世界设定.json` / `01_世界设定.txt`
- `02_故事大纲.json`
- `03_Episode详细概括.json` / `03_Episode详细概括.txt`
- `04_Beats.json`
- `output/小说正文.txt`

### 特性

- 自顶向下设计，自底向上反馈
- 逐层冻结（每层结果保存为中间文件）
- Episode 按古典戏剧学起承转合组织，形成完整 callback
- Beats 为标准剧本格式，支持局部重新生成 `regenerate_beat(episode_index, beat_index)`