# Novel Workflow (LangGraph) — README

这是一个用 **LangGraph + LangChain(OpenAI)** 搭建的“卷级/章级”小说生成原型脚本。  
当前版本以 **一个 Python 文件**为主（你现在正在运行的那个脚本），支持从设定出发生成：大纲 →（可选）结构 → 章节正文 → 输出到文件。

> 目标：快速验证“分阶段生成 + 可迭代”的写作工作流，而不是一次性把整本书塞进 prompt。


## 功能概览

- 输入一段故事设定（`user_input`），可选输入你自己的大纲（`user_outline`）
- 通过 LangGraph 串联多个节点（nodes）进行生成
- 输出：
  - 结构化大纲对象（OutlineSummary / 或你的对应模型）
  - 章节正文（chapters 列表）
  - 落盘文件（例如 `outputs/novel_v3.txt`）
     ```

## 使用方法

1. 在 `input/input.txt` 文件中输入你的小说需求，例如：
   ```
   请生成一部科幻小说，主题关于人工智能与人类的未来关系。
   ```

2. 运行主程序：
```bash
python main_0.py
```
## 依赖与环境

### Python 版本
建议 Python 3.10+

### 安装依赖

> 依赖名称以你脚本里实际 import 为准。下面是常见组合。

```bash
pip install langgraph langchain langchain-openai pydantic python-dotenv