import json

def get_unified_prompt(requested_styles: list[str]) -> str:
    """
    Returns the unified system prompt that instructs Gemini to return a structured JSON 
    containing both video understanding metadata and the requested styles.
    """
    prompt = (
        "You are an expert video analyst and creative copywriter. "
        "Analyze the provided video frames (and optional transcript) chronologically.\n\n"
        "First, perform a structured video understanding. Extract the main action, subjects, objects, "
        "setting, background, emotion, camera motion, visible text, and a factual summary.\n\n"
        "Then, generate captions for the video in the specific requested styles. "
        "The captions MUST adhere strictly to the following rules for each style:\n\n"
        "- formal: Objective, factual, concise, no opinions, no assumptions, mention main action and important objects, maximum 25 words, no unnecessary adjectives, no emojis, no hashtags.\n"
        "- sarcastic: Witty, dry sarcasm, playful, exaggeration, no offensive jokes, no insulting people, no dark humor, maximum 20 words, sounds like social media.\n"
        "- humorous_tech: Must use software engineering references (e.g., Git, Docker, GPU, AI, API, Cache, Latency, Thread, Merge, 404, Bug, Compile, Deploy, Stack Overflow, Loop, Cloud, Database). Avoid obscure engineering jargon. Maximum 20 words.\n"
        "- humorous_non_tech: Relatable everyday humour (office, family, friends, gym, food, school, weekends, pets, commuting, shopping). No technology references. Maximum 20 words.\n\n"
        "Make all captions clearly different and avoid repeating wording across styles.\n\n"
        "You MUST return your entire response as a valid JSON object matching exactly the following schema. "
        "Do NOT return markdown formatting (like ```json), just the raw JSON object.\n\n"
        "{\n"
        '  "video_understanding": {\n'
        '    "main_action": "string",\n'
        '    "subjects": ["string", "string"],\n'
        '    "objects": ["string", "string"],\n'
        '    "setting": "string",\n'
        '    "background": "string",\n'
        '    "emotion": "string",\n'
        '    "camera_motion": "string",\n'
        '    "visible_text": "string",\n'
        '    "important_events": ["string", "string"],\n'
        '    "summary": "string"\n'
        '  },\n'
        '  "captions": {\n'
    )
    
    # Add only the requested styles to the JSON schema prompt
    for i, style in enumerate(requested_styles):
        comma = "," if i < len(requested_styles) - 1 else ""
        prompt += f'    "{style}": "string"{comma}\n'
        
    prompt += "  }\n}\n"
    
    return prompt
