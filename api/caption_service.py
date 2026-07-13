"""
caption_service.py

FastAPI backend service delegating video captioning to the new Fireworks VLM pipeline.
Replaces the old Google Gemini API logic while keeping backend routing functional.
"""

import sys
import os

# Add project root to sys.path so sibling directories can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
