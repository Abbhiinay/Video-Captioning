import logging
from description.utils.gemini_client import describe_frames
from description.utils.fireworks_client import complete

logger = logging.getLogger(__name__)


def describe_video(frame_paths: list[str], transcript: str | None) -> str:
    """
    Step 1: Calls Gemini Flash to describe frames (and optional transcript) for raw observations.
    Step 2: Calls Fireworks LLM to write a single neutral, objective, factual paragraph description.
    """
    if not frame_paths:
        raise ValueError("Cannot describe video: No frame paths provided.")

    gemini_prompt = (
        "You are the perception step's eyes. Analyze the provided video frames chronologically. "
        "Provide raw, unpolished factual visual observations only (actions, objects, setting, and notable details). "
        "Avoid any tone, style, jokes, opinions, or interpretations."
    )

    logger.info(f"Calling Gemini Flash with {len(frame_paths)} frames for raw visual observations...")
    try:
        raw_observations = describe_frames(frame_paths, transcript, gemini_prompt)
    except Exception as e:
        logger.error(f"Gemini perception call failed: {e}")
        raise RuntimeError(f"Gemini perception call failed: {e}") from e

    if not raw_observations:
        raise RuntimeError("Gemini returned empty visual observations.")

    fireworks_system_prompt = (
        "You are the perception step's writer. "
        "Your task is to take raw visual observations of a video (and an optional audio transcript) "
        "and produce a single, neutral, objective, factual, plain-text description paragraph. "
        "Do not include any planning, explanations, thinking process, style, opinion, jokes, or creative embellishments. "
        "Start directly with the description paragraph itself."
    )

    fireworks_user_prompt = f"Raw observations:\n{raw_observations}"
    if transcript:
        fireworks_user_prompt += f"\n\nTranscript:\n{transcript}"

    logger.info("Calling Fireworks LLM to summarize raw observations into a single neutral paragraph...")
    try:
        factual_description = complete(
            system_prompt=fireworks_system_prompt,
            user_prompt=fireworks_user_prompt
        )
        return factual_description.strip()
    except Exception as e:
        logger.error(f"Fireworks description synthesis failed: {e}")
        raise RuntimeError(f"Fireworks description synthesis failed: {e}") from e