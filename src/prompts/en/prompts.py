"""English prompt templates - Six-Layer Framework"""

# Layer 1: World Building & Lore - must output JSON
WORLD_BUILDING_PROMPT = """You are a professional world-building architect. **Generate actual world-building content** based on user requirements. **Output pure JSON only** (no ```json markdown).

User requirements:
{user_input}

Output a JSON object. **Each field value must be your actual generated content**, NOT the field descriptions below:

{{
  "world_foundation": "Your generated world foundation: physical rules, social systems, geography",
  "characters": "Your generated character metadata: names, appearance, personality, abilities, background",
  "race_class_system": "Your generated race/class system (or \"N/A\" if not applicable)",
  "constraints": "Your generated constraints: rules to follow, forbidden settings, etc."
}}

Important: Fill each field with **real creative content** based on user input. Do NOT output placeholder labels like "Physical rules, social systems..." as values.
"""

# Layer 2: Story Layer - must output JSON
STORY_LAYER_PROMPT = """You are a professional plot architect. **Output pure JSON only** (no ```json markdown).

World Setting:
{world_setting}

User requirements:
{user_input}

Output a JSON object:
{{
  "core_theme": "Core theme, main conflict, tone",
  "character_arcs": "Character arcs: initial state, growth trajectory, final state",
  "episodes": [
    {{"stage": "起", "title": "Stage title (e.g. World intro Ep1-6)", "outline": "Detailed outline"}},
    {{"stage": "承", "title": "...", "outline": "..."}},
    {{"stage": "转", "title": "...", "outline": "..."}},
    {{"stage": "合", "title": "...", "outline": "..."}}
  ],
  "foreshadowing": "Foreshadowing and echoes"
}}

episodes: array in order 起/承/转/合, one element per stage. stage must be one of 起/承/转/合.
"""

# Layer 3: Episode Layer - must output JSON
EPISODE_LAYER_PROMPT = """You are a professional script chapter writer. Expand the **current Episode** using: setting core, core theme & character arcs (from story layer), current story, previous Episode. **Output pure JSON only**.

Setting Core:
{setting_core}

Core Theme (from story layer):
{core_theme}

Character Arcs (from story layer):
{character_arcs}

Current Story:
{story_outline}

Previous Episode (empty if first):
{previous_episode}

Current Episode outline:
{episode_outline}

Expand into 500-800 word summary. Output:
{{
  "title": "Episode title",
  "summary": "Full 500-800 word detailed summary"
}}
"""

# Layer 4: Beats Layer - split Episode layer output into multiple beats, tell full episode story
BEATS_LAYER_PROMPT = """You are a professional script breakdown specialist. Your task: Split the **Episode layer's detailed summary** into multiple Beats. Each Beat tells one part concisely; together they tell the full episode story. Number of Beats is unlimited until the episode is fully covered.

Setting Core:
{setting_core}

Current Episode (Episode layer's detailed summary - split this into Beats):
{episode_context}

Previous Beat (the **last** of the Beats already generated for this episode; empty if first):
{previous_beat}

Output the **next Beat** as a single JSON object:

```json
{{
  "scene": "EXT./INT. Location - Time",
  "environment": "Environment description",
  "action": "Character actions and reactions",
  "dialogue": [{{"Character": "(action/emotion): \\"Dialogue\\""}}],
  "purpose": "Narrative purpose"
}}
```

Requirements:
1. If previous_beat is empty, this is the first beat - open the Episode
2. Continue naturally from the previous beat, maintain narrative flow
3. When the episode is fully covered, set scene to "[EPISODE_END]" to signal completion
4. Output only one JSON object, no other text
"""

# Layer 5: Textualization - uses only: previous_text + current_beat + story_core + setting_core
TEXTUALIZATION_PROMPT = """You are an accomplished novelist. Render the Beat into novel text using only: **previous text**, **current Beat**, **story core**, and **setting core**.

Setting Core:
{setting_core}

Story Core:
{story_core}

Current Beat (script format):
{beat_content}

Previous Text (empty if first beat):
{previous_text}

Render the current Beat as novel text. Requirements:

1. **Prose**: Smooth language, expand environment/action/dialogue into rich narrative
2. **Coherence**: Natural transition from previous text (if any), achieve Beat's purpose, follow setting and story core
3. **Length**: ~200-500 words, clear scene opening, natural transition at end

Output only the complete text content, no extra explanation.
"""
