"""English prompt templates - Four-Layer Framework"""

# Layer 1: World Building & Lore
WORLD_BUILDING_PROMPT = """You are a professional world-building architect. Based on user requirements, construct a complete and consistent world setting foundation.

User requirements:
{user_input}

Please output the following structured content:

## 1. World Foundation
- Physical rules (magic, technology level, etc.)
- Social systems (political structure, organizational systems)
- Geographic environment (main regions, important locations)

## 2. Character Metadata (Core Characters)
For each main character, provide:
- Name, age, appearance
- Core personality traits (3-5 keywords)
- Core abilities/skills
- Background (origin, important experiences)

## 3. Race/Class System (if applicable)
- Racial features and settings
- Class system and levels
- Ability system and balance

## 4. Long-term Variables and Constraints
- Rules the story must follow
- Settings that are not allowed
- Elements that need consistency

Please output in a structured and clear format. This will serve as the "foundation" and consistency check reference for all subsequent layers.
"""

# Layer 2: Story Layer (Plot & Character Arc)
STORY_LAYER_PROMPT = """You are a professional plot architect. Based on the constructed world setting, design a complete story skeleton and character arcs.

World Setting:
{world_setting}

User requirements:
{user_input}

Please output the following:

## 1. Core Theme and Main Plot
- Core theme of the story
- Main conflict line
- Basic tone of the story (light/serious/suspenseful, etc.)

## 2. Plot Outline (Plot Points)
Divide the story into main stages (e.g., opening, development, turning point, climax, conclusion), each stage containing:
- Main events
- Key turning points
- Foreshadowing setup
- Emotional rhythm

## 3. Character Arcs
For each main character, design:
- Initial state (personality, abilities, goals)
- Growth trajectory (key turning points)
- Final state (changes after experiencing the story)
- Behavioral pattern change stages

## 4. Interest and Echo Design
- Hook points (key scenes that attract readers)
- Foreshadowing and echo design (list key foreshadowing and their echo positions)
- Suspense setup

Please ensure character arcs are dynamic, with character behavioral patterns shifting based on experiences at different stages.
"""

# Layer 3: Scene Layer (Scene Decomposition)
SCENE_DECOMPOSITION_PROMPT = """You are a professional scene decomposition specialist. Break down the story outline into executable specific scene units.

World Setting:
{world_setting}

Story Outline:
{story_outline}

Please break down the story into specific scenes, each scene containing:

## Scene List (in order)
For each scene, output:

### Scene [Number]: [Scene Name]
- **Location**: Specific place
- **Characters**: Characters appearing
- **Goal**: Core objective of the scene (what the character wants to achieve)
- **Conflict**: Conflict/contradiction in the scene
- **Emotional Tone**: Atmosphere of the scene
- **Connection to Previous/Next Scenes**: How it connects
- **Key Dialogue/Actions**: Elements that must appear
- **Foreshadowing/Echo**: Foreshadowing or echoes involved in this scene

Please ensure each scene is an independent minimum narrative unit, supporting local modification without affecting the overall framework.
Scene breakdown should be detailed. For example, "entering the city" can be broken into "arriving at city gate" -> "undergoing inspection" -> "entering the city" and other scenes.
"""

# Layer 4: Textualization Layer
TEXTUALIZATION_PROMPT = """You are an accomplished novelist with exquisite prose. Based on all preceding layer information, render the scene into beautiful literary text.

World Setting:
{world_setting}

Story Context:
{story_context}

Current Scene Description:
{scene_description}

Character History/Status:
{character_context}

Please render the above scene as novel text, requirements:

1. **Prose Requirements**
   - Smooth and elegant language, matching the emotional tone of the scene
   - Natural and vivid dialogue, matching character personality
   - Detailed environmental description, creating atmosphere

2. **Consistency Check**
   - Strictly follow the rules of world setting
   - Character behavior matches their current stage character arc
   - Maintain coherence with previous scenes

3. **Detail Requirements**
   - Pay attention to subtle character expressions and actions
   - Show character psychology through details
   - Use five-sense descriptions to enhance immersion

4. **Structure Requirements**
   - Scene opening should have clear scene sense
   - Scene ending should have appropriate transition or suspense
   - Word count approximately 800-1500 words (adjust based on scene complexity)

Please directly output the complete text content of the scene without any additional explanations or comments.
"""
