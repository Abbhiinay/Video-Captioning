import os
import logging
import yaml

logger = logging.getLogger(__name__)

def load_style_instructions(yaml_path: str = None) -> dict[str, str]:
    """
    Loads style instructions from config/styles.yaml.
    """
    if yaml_path is None:
        # Resolve config/styles.yaml relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yaml_path = os.path.join(current_dir, "..", "..", "config", "styles.yaml")

    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Style specifications not found at: {yaml_path}")

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        instructions = {}
        if isinstance(data, dict):
            for style, content in data.items():
                if isinstance(content, dict) and "instruction" in content:
                    instructions[style] = content["instruction"]
                elif isinstance(content, str):
                    instructions[style] = content
        return instructions
    except Exception as e:
        logger.error(f"Error loading styles.yaml: {e}")
        raise

def build_prompts(style: str, description: str, instructions: dict[str, str]) -> tuple[str, str]:
    """
    Constructs the system and user prompts for a given style based on description.
    """
    instruction = instructions.get(style)
    if not instruction:
        logger.warning(f"No specific instruction found for style '{style}'. Using fallback.")
        instruction = "Write a creative caption."

    system_prompt = (
        f"You are a creative caption writer. {instruction} "
        "Return ONLY the final caption text. Do not include any introductory notes, explanations, "
        "planning, thinking process, quotes, or markdown wrappers. Start directly with the caption text."
    )

    user_prompt = f"Video Description: {description}"
    return system_prompt, user_prompt
