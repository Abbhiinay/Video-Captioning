import json
import logging
from description.utils.gemini_client import analyze_video_frames
from description.style_engine.prompts import get_unified_prompt

logger = logging.getLogger(__name__)

def analyze_video(frame_paths: list[str], transcript: str | None, styles: list[str]) -> dict:
    """
    Calls Gemini Flash to analyze the frames and generate all requested captions in a single API call.
    Returns the parsed JSON response.
    """
    if not frame_paths:
        raise ValueError("Cannot analyze video: No frame paths provided.")

    unified_prompt = get_unified_prompt(styles)

    logger.info(f"Calling Gemini 2.5 Flash with {len(frame_paths)} frames for perception and caption generation...")
    try:
        response_text = analyze_video_frames(frame_paths, transcript, unified_prompt)
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise RuntimeError(f"Gemini API call failed: {e}") from e

    if not response_text:
        raise RuntimeError("Gemini returned empty response.")

    # Clean up response text if the model wraps it in markdown despite instructions
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]

    try:
        parsed_json = json.loads(response_text)
        return parsed_json
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}\nResponse: {response_text}")
        raise RuntimeError(f"Failed to parse Gemini response as JSON: {e}") from e
