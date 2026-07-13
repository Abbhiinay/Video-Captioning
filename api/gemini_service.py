"""
gemini_service.py

FastAPI backend adapter delegating video captioning to the new Fireworks VLM pipeline.
Replaces the old Google Gemini API logic while keeping backend routing functional.
"""

import logging
from src.perception.analyze_video import analyze_video

logger = logging.getLogger(__name__)

def generate_captions(
    frame_paths: list[str],
    styles: list[str] | None = None,
) -> dict:
    """
    Delegate caption generation to the Fireworks visual perception pipeline.
    
    Args:
        frame_paths: Paths to the extracted JPEG frames.
        styles: List of styles to generate.
    """
    if styles is None:
        styles = ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]
        
    logger.info("Delegating caption generation to the Fireworks VLM pipeline.")
    return analyze_video(frame_paths, transcript=None, styles=styles)
