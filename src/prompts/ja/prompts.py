"""日本語プロンプトテンプレート - 六層フレームワーク"""

# 第1層：設定層 - JSON出力必須
WORLD_BUILDING_PROMPT = """あなたは専門的な世界観構築者です。ユーザー要件に基づき**実際の世界観内容を生成**してください。**純粋なJSONのみ出力**（```json等のマーク不要）。

ユーザーの要件：
{user_input}

JSONオブジェクトを出力。**各フィールドの値はあなたが生成した実際の内容**であり、下の説明をそのままコピーしないこと：

{{
  "world_foundation": "生成した世界観の基礎",
  "characters": "生成したキャラクターメタデータ",
  "race_class_system": "生成した種族/職業システム（該当なしなら「なし」）",
  "constraints": "生成した制約・ルール"
}}

重要：各フィールドに**ユーザー要件に基づく実際の設定テキスト**を記入すること。説明文をそのまま値として出力しないこと。
"""

# 第2層：物語層 - JSON出力必須
STORY_LAYER_PROMPT = """あなたは専門的なプロット構築者です。**純粋なJSONのみ出力**。

世界設定：
{world_setting}

ユーザーの要件：
{user_input}

JSONオブジェクトを出力：
{{
  "core_theme": "核心テーマとメインプロット",
  "character_arcs": "キャラクターアーク",
  "episodes": [
    {{"stage": "起", "title": "タイトル", "outline": "詳細梗概"}},
    {{"stage": "承", "title": "...", "outline": "..."}},
    {{"stage": "转", "title": "...", "outline": "..."}},
    {{"stage": "合", "title": "...", "outline": "..."}}
  ],
  "foreshadowing": "伏線と呼応"
}}

episodesは起承転結の順。stageは起/承/转/合のいずれか。
"""

# 第3層：Episode層 - JSON出力必須
EPISODE_LAYER_PROMPT = """あなたは専門的な脚本章節作家です。設定核心・核心テーマと人物弧光・当前故事・前のEpisodeを使って当前Episodeを拡張。**純粋なJSONのみ出力**。

設定核心：{setting_core}
核心テーマと主线（物語層より）：{core_theme}
人物弧光（物語層より）：{character_arcs}
当前故事：{story_outline}
前のEpisode：{previous_episode}
当前Episode梗概：{episode_outline}

500-800字の詳細概括に拡張。出力：
{{
  "title": "Episodeタイトル",
  "summary": "詳細概括全文"
}}
"""

# 第4層：Beats層 - Episode層の詳細概括を複数Beatsに分割、本Episodeの物語を完全に述べる
BEATS_LAYER_PROMPT = """あなたは専門的な脚本分解者です。**Episode層の詳細概括**を本Episode用の複数Beatsに分割してください。各Beatは一部分を精煉に述べ、全体で本Episodeの物語を完全にカバー。Beats数に制限なし。

設定核心：{setting_core}
当前Episode（Episode層の詳細概括、これをBeatsに分割）：{episode_context}
前のBeat（本Episodeで既に生成したBeatsの**最後のもの**；最初の場合は空）：{previous_beat}

**次のBeat**を単一のJSONで出力：
```json
{{"scene":"...", "environment":"...", "action":"...", "dialogue":[...], "purpose":"..."}}
```
Episodeが完全にカバーされたら scene を "[EPISODE_END]" に設定。
"""

# 第5層：文字層 - 上一个文字 + 当前beat + 故事层核心 + 設定核心 のみ使用
TEXTUALIZATION_PROMPT = """あなたは優れた小説家です。**上一个文字**、**当前Beat**、**故事层核心**、**設定核心**のみを使って、Beatを小説テキストにレンダリングしてください。

設定核心：
{setting_core}

故事层核心：
{story_core}

当前Beat（脚本形式）：
{beat_content}

上一个文字（最初のBeatの場合は空）：
{previous_text}

当前Beatを小説テキストとしてレンダリング。要件：

1. **文体**：流暢な言語、environment/action/dialogueを豊かな叙述に展開
2. **連続性**：上一个文字から自然に接続、Beatのpurposeを達成、設定・物語核心に従う
3. **文字数**：約200-500字、冒頭にシーン感、終わりに自然な転換

完全なテキストのみ出力、追加の説明なし。
"""
