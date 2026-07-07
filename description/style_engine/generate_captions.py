import logging
from description.style_engine.prompts import load_style_instructions, build_prompts
from description.utils.fireworks_client import complete

logger = logging.getLogger(__name__)

def generate_captions(description: str, styles: list[str]) -> dict[str, str]:
    """
    Generates style rewrites for only the requested styles.
    Ensures that a failure in one style does not prevent the generation of others.
    """
    try:
        instructions = load_style_instructions()
    except Exception as e:
        logger.error(f"Could not load style instructions: {e}. Using fallback instructions.")
        instructions = {
            "formal": "Write an objective, professional caption describing the video.",
            "sarcastic": "Write a dry, sarcastic caption that pokes fun at the obvious.",
            "humorous_tech": "Write a joke caption using software/tech metaphors an engineer would appreciate.",
            "humorous_non_tech": "Write a lighthearted, relatable joke caption avoiding tech jargon."
        }

    results = {}
    for style in styles:
        logger.info(f"Generating caption for style: {style}...")
        try:
            system_prompt, user_prompt = build_prompts(style, description, instructions)
            caption = complete(system_prompt=system_prompt, user_prompt=user_prompt)
            results[style] = caption.strip() if caption else ""
        except Exception as e:
            logger.error(f"Failed to generate caption for style '{style}': {e}")
            results[style] = ""  # Keep empty string on failure instead of raising, so we degrade gracefully
            
    return results