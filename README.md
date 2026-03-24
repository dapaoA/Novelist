# Novelist - AI小说家

一个基于LangChain的AI小说生成项目，支持OpenAI和DeepSeek API。

当前版本的产品定位是 `沙盘模式（Sandbox Mode）`：给定需求和设定后，让 LLM 在约束内自主推进故事，产出可供作者观察、挑选和再创作的蓝本。`Author Mode` 仍是后续目标，但当前仓库还没有 IDE / editor / 审批流来支撑作者主导式工作流。

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
│   ├── input.txt          # 输入文件（小说需求）
│   ├── volume_preparation.json  # 可选：当前卷的重要角色准备信息
│   └── knowledge/         # 可选：导入已有知识库（角色等）
├── intermediate/          # 中间结果目录
│   ├── 01_世界设定.txt
│   ├── 02_故事大纲与Episode梗概.txt
│   ├── 03_Episode详细概括.txt
│   ├── 04_Beats.json
│   └── knowledge/
│       ├── characters.json
│       ├── ambiguous_resolutions.json
│       └── discovered_candidates.json
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
   - 角色知识库快照保存在 `intermediate/knowledge/characters.json`
   - 歧义角色解析报告保存在 `intermediate/knowledge/ambiguous_resolutions.json`
   - 新发现角色候选报告保存在 `intermediate/knowledge/discovered_candidates.json`
   - 小说正文保存在 `output/` 目录（文件名根据语言不同）

## 当前模式

- 当前只实现了 `沙盘模式（Sandbox Mode）`
- 它更像“沙盘 / 看海”模式：系统会自行推进剧情，并可能自然形成伏笔、呼应、关系变化和意外转折
- 这些发展方向未必与作者长期意图一致，因此当前输出更适合作为 demo、灵感源、世界演化样本或后续人工改写的蓝本
- `Author Mode` 暂未实现，因为它需要 IDE 能力来承载编辑、审批、状态查看、局部重写和不可逆事件管控

可选地，你也可以在 `input/knowledge/characters.json` 中放入已有角色知识库。若该目录存在，运行时会先导入它，用于识别后续卷中的重复角色；若不存在，则本次运行按全新项目处理，只做角色发现。
你也可以在 `input/volume_preparation.json` 中提供当前卷的重要角色准备信息。若该文件存在，角色解析会优先参考这份清单；若不存在，则默认由 LLM 从本次文本中自行推断会用到哪些角色。

## 功能特性

- **六层架构**：设定 → 故事(Episode梗概) → Episode扩写 → Beats拆分 → 文字生成
- **沙盘模式定位**：当前版本以自主推进和内部自洽为目标，不承诺作者主导式的长期剧情控制
- **古典戏剧结构**：故事层按起承转合组织 Episode，形成完整 callback
- **剧本式 Beats**：标准格式（scene, environment, action, dialogue, purpose），支持局部重生成
- **多语言支持**：中文(zh)、英文(en)、日文(ja)，可扩展
- 支持 OpenAI 和 DeepSeek 双 API

## Character Module

项目现在额外提供了一个独立的角色域模块，位于 `src/characters/`。这个模块已经能在主流程结束后自动产出角色知识库快照，但它仍然保持清晰的边界：角色发现、解析、更新和存储都放在独立模块里，后续可以继续接入关系图、记忆或别的检索方案。

目录结构：

```text
src/characters/
├── __init__.py
├── extractor.py        # LangChain + Pydantic 结构化角色发现提取器
├── interfaces.py       # 协议定义：store / discovery / updater / resolver
├── knowledge.py        # 角色知识库的 JSON 导入导出
├── models.py           # Character、Candidate、UpdateCandidate 等数据结构
├── resolver.py         # 角色身份解析（新角色 / 复现角色 / 歧义）
├── service.py          # 角色创建、更新、查找、合并逻辑
├── updater.py          # 复现角色的保守 patch 生成
├── workflow.py         # 导入知识库、发现、解析、更新、导出快照
└── stores/
    ├── __init__.py
    └── in_memory.py    # 内存版存储，适合本地开发和测试
```

设计原则：

- `models.py` 只定义数据结构
- `interfaces.py` 只定义模块之间的契约
- `extractor.py` 负责把原始文本提取成结构化角色候选（发现阶段）
- `resolver.py` 负责判断角色候选是新角色、已存在角色还是歧义项
- `updater.py` 负责把已匹配角色转换成保守的更新 patch
- `service.py` 负责业务规则，不关心底层存储细节
- `knowledge.py` / `workflow.py` 负责知识库、卷准备信息、歧义报告的导入导出与流程编排
- `stores/` 可以按需替换成 SQLite、Postgres 或别的实现

最小用法：

```python
from src.characters.service import CharacterService
from src.characters.extractor import LangChainCharacterExtractor
from src.characters.models import ProfileDepth
from src.characters.stores import InMemoryCharacterStore

store = InMemoryCharacterStore()
service = CharacterService(store)
extractor = LangChainCharacterExtractor()

alice = service.create_character(
    canonical_name="Alice",
    aliases=["Al"],
    profile_depth=ProfileDepth.CORE,
    salient_concept="curious mechanic with a stubborn streak",
    stable_tendencies=["curious", "stubborn"],
)

same_character = service.find_character("Al")
candidates = extractor.extract("Alice, known as Al, is a stubborn but curious mechanic.")
```

知识库工作流示例：

```python
from src.characters.workflow import CharacterKnowledgeWorkflow

workflow = CharacterKnowledgeWorkflow()
result = workflow.process_text("Alice, known as Al, is a stubborn but curious mechanic.")
print(result.snapshot_path)
print(result.ambiguous_report_path)
```

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
- 当前为 `沙盘模式`，系统可能生成并回收自己的伏笔，但不保证这些方向符合作者原始意图
- 涉及角色死亡、身份揭露、关系断裂等不可逆剧情时，建议把结果视为候选分支，而不是直接视为正史

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
- `intermediate/knowledge/characters.json`
- `intermediate/knowledge/ambiguous_resolutions.json`
- `intermediate/knowledge/discovered_candidates.json`
- `output/小说正文.txt`

### 特性

- 自顶向下设计，自底向上反馈
- 逐层冻结（每层结果保存为中间文件）
- Episode 按古典戏剧学起承转合组织，形成完整 callback
- Beats 为标准剧本格式，支持局部重新生成 `regenerate_beat(episode_index, beat_index)`
