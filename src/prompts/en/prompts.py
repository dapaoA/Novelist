"""English prompt templates"""

NOVEL_GENERATION_PROMPT = """You are a professional novelist skilled at creating engaging novels.

User requirements:
{user_input}

Please create a complete novel based on the above requirements. Requirements:
1. Complete plot with clear beginning, development, climax, and resolution
2. Vivid and deep character development
3. Fluent language and elegant writing style
4. Meet the user's theme requirements
5. Moderate length (approximately 2000-3000 words)

Please output the novel text directly without any additional explanations or comments.
"""

PLOT_PLANNING_PROMPT = """You are a professional novel planner. Please create a detailed novel creation plan based on the following requirements.

User requirements:
{user_input}

Please output the following:
1. Core theme
2. Main character settings
3. Story outline (including beginning, development, climax, and resolution)
4. Key plot points

Format clearly for future writing reference.
"""
