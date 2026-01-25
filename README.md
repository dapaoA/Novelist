# Novelist (LangGraph Webnovel Workflow)

A modular LangGraph + LangChain(OpenAI) pipeline for generating webnovels in stages:
outline → structure → character cards → chapters → output file.

This version supports multi‑language prompts (Chinese/English) and language‑specific formatting.

## Features

- **Multi‑stage generation** via LangGraph nodes
- **Language‑aware prompts** (Chinese/English; extendable)
- **Language‑aware formatting** for scene blocks, chapter headers, and character summaries
- **Structured outputs** using Pydantic models
- **File output** for generated chapters

## Project Structure

```
src/
  main.py                 # Entry point
  graph_builder.py        # LangGraph wiring
  llm_config.py           # LLM factory
  models.py               # Pydantic models + state
  nodes/
    outline.py            # Draft outline
    structure.py          # Plan volume structure
    characters.py         # Generate characters + render summary
    writer.py             # Write chapters
    io.py                 # Save output to file
  prompts/
    registry.py           # Routes prompts/formatters by language
    zh/
      outline.py
      structure.py
      characters.py
      writer.py
      formatters.py       # Scene/character/chapter formatting
    en/
      outline.py
      structure.py
      characters.py
      writer.py
      formatters.py
```

## Requirements

- Python 3.10+
- Packages:
  ```bash
  pip install "langchain-openai" "langgraph" "pydantic<3"
  ```

## Environment Variables

- `OPENAI_API_KEY` (required)
- `PROMPT_LANG` (optional, default: `zh`)

Examples:
```bash
export OPENAI_API_KEY="sk-..."
export PROMPT_LANG="en"
```

## Usage

Run the demo script:
```bash
python src/main.py
```

Output goes to:
```
output/novel.txt
```

## Language Support

Prompt/format selection is controlled by `PROMPT_LANG`:
- `zh` → Chinese prompts + formatting
- `en` → English prompts + formatting

To add a new language later (e.g., `ja`, `ko`):
1. Create `src/prompts/ja/` or `src/prompts/ko/`
2. Add `outline.py`, `structure.py`, `characters.py`, `writer.py`, and `formatters.py`
3. Update `src/prompts/registry.py` to route the new language

## Notes

- The model is currently set in `src/llm_config.py` (default: `gpt-4o-mini`).
- The demo `user_input` in `src/main.py` is Chinese by default; you can change it to English.

## Workflow (Exact Graph Order)

This is the precise LangGraph pipeline defined in `src/graph_builder.py`:

**Entry point**
- `draft_outline`

**Edges (linear chain)**
- `draft_outline` → `plan_volume_structure`
- `plan_volume_structure` → `generate_characters`
- `generate_characters` → `write_chapters`
- `write_chapters` → `save_output`
- `save_output` → `END`

**What each node writes into state**
- `draft_outline`: sets `state["outline"]`
- `plan_volume_structure`: sets `state["structure"]`
- `generate_characters`: sets `state["characters"]`
- `write_chapters`: sets `state["chapters"]`
- `save_output`: writes file (does not add new fields)

## Roadmap Ideas

- Character subsystem expansion (relationships, skills, classes)
- Multi‑volume continuity support
- GraphRAG/encyclopedia layer for long‑running series
