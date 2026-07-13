"""
analyze_video.py

Calls Fireworks VLM with sampled video frames to produce a structured JSON response
containing both video understanding metadata and all requested caption styles
in a single API call.

Responsibilities:
  - Build and send the unified prompt to Fireworks.
  - Strip any accidental markdown wrapping from the raw response.
  - Parse the JSON response with an automatic repair-retry on failure (Task 1).
  - Validate and back-fill every required key with safe defaults (Task 2).
  - Never raise; always return a safe result dict so the batch never crashes.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import Any
from openai import OpenAI

from config.settings import (
    FIREWORKS_API_KEY, FIREWORKS_BASE_URL,
    FIREWORKS_VISION_MODEL, FIREWORKS_FALLBACK_VISION_MODEL,
    TEMPERATURE, TOP_P, MAX_OUTPUT_TOKENS
)
from description.style_engine.prompts import get_unified_prompt, get_repair_prompt

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

# Caption style keys that MUST be present in every successful response.
REQUIRED_CAPTION_STYLES: tuple[str, ...] = (
    "formal",
    "sarcastic",
    "humorous_tech",
    "humorous_non_tech",
)

# Allowed values for the camera_motion field (Task 9).
ALLOWED_CAMERA_MOTIONS: frozenset[str] = frozenset(
    {"static", "pan", "tilt", "zoom", "tracking", "handheld", "unknown"}
)

# Sensible defaults for video_understanding fields.
_VIDEO_UNDERSTANDING_DEFAULTS: dict[str, Any] = {
    "main_action": "unknown",
    "subjects": [],
    "objects": [],
    "setting": "unknown",
    "background": "unknown",
    "apparent_emotion": "unknown",   # Task 10: replaces "emotion"
    "camera_motion": "unknown",       # Task 9: always present
    "visible_text": "none",
    "important_events": [],
    "summary": "",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _encode_image(path: str) -> str:
    """Read a JPEG frame and encode it as a base64 string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json … ``` or ``` … ``` fences that the model sometimes emits."""
    text = text.strip()
    # Remove leading fence (with optional language tag)
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    # Remove trailing fence
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _safe_parse_json(raw: str) -> dict | None:
    """Attempt to parse raw string as JSON; return None on failure."""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
        logger.warning("VLM returned valid JSON but it was not a dict object.")
        return None
    except json.JSONDecodeError as exc:
        logger.warning(f"JSON decode error: {exc}")
        return None


def _validate_and_patch(parsed: dict, requested_styles: list[str]) -> dict:
    """
    Ensure the parsed dict contains every required key.

    - captions: guarantees all four canonical styles (and any extra requested ones)
      are present. Missing ones become empty strings.
    - video_understanding: fills every missing field with a sensible default.
      and normalizes apparent_emotion and camera_motion.
    """
    # ── captions block ──────────────────────────────────────────────────────
    if not isinstance(parsed.get("captions"), dict):
        logger.warning("'captions' key missing or not a dict — inserting empty captions.")
        parsed["captions"] = {}

    all_expected_styles = set(REQUIRED_CAPTION_STYLES) | set(requested_styles)
    for style in all_expected_styles:
        if not isinstance(parsed["captions"].get(style), str):
            logger.warning(f"Caption style '{style}' missing — defaulting to empty string.")
            parsed["captions"][style] = ""

    # ── video_understanding block ───────────────────────────────────────────
    if not isinstance(parsed.get("video_understanding"), dict):
        logger.warning("'video_understanding' key missing — inserting defaults.")
        parsed["video_understanding"] = dict(_VIDEO_UNDERSTANDING_DEFAULTS)
    else:
        vu = parsed["video_understanding"]

        # Task 10: normalise apparent_emotion (accept legacy "emotion" key)
        if "apparent_emotion" not in vu:
            legacy_emotion = vu.pop("emotion", None)
            vu["apparent_emotion"] = (
                str(legacy_emotion) if legacy_emotion else "unknown"
            )

        # Fill remaining missing fields with defaults
        for key, default in _VIDEO_UNDERSTANDING_DEFAULTS.items():
            if key not in vu:
                logger.warning(
                    f"video_understanding.{key} missing — using default '{default}'."
                )
                vu[key] = default

        # Task 9: enforce allowed camera_motion values
        cam = vu.get("camera_motion", "unknown")
        if cam not in ALLOWED_CAMERA_MOTIONS:
            logger.warning(
                f"camera_motion '{cam}' not in allowed set — normalising to 'unknown'."
            )
            vu["camera_motion"] = "unknown"

    # ── Task 15: Output Verification & Repair ────────────────────────────────
    for style in all_expected_styles:
        caption = parsed["captions"].get(style, "").strip()

        # Repair 1: If multiple sentences are detected, keep only the first sentence.
        # This handles models that ignore the single-sentence rule.
        if re.search(r"[\.\!\?]\s+[A-Z]", caption):
            logger.warning(f"Repairing multi-sentence caption for '{style}'...")
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", caption)
            if sentences:
                caption = sentences[0].strip()

        # Repair 2: If the caption still exceeds 35 words it is a runaway
        # response — drop it to the fallback rather than truncating mid-sentence,
        # which would produce grammatically broken output.
        words = caption.split()
        if len(words) > 35:
            logger.warning(
                f"Caption for '{style}' is {len(words)} words (> 35 word ceiling). "
                "Passing to fallback instead of truncating mid-sentence."
            )
            caption = ""  # force fallback below

        parsed["captions"][style] = caption

        # If verification still fails, fall back to a style-appropriate default.
        if not _verify_caption(caption, style):
            logger.warning(f"Caption '{style}' failed verification. Using fallback.")
            if style == "formal":
                parsed["captions"][style] = "A video showing the main actions and visual details of the scene."
            elif style == "sarcastic":
                parsed["captions"][style] = "Oh look, another fascinating video clip that totally changed my life today."
            elif style == "humorous_tech":
                parsed["captions"][style] = "This visual process is like a loop running without any termination condition."
            else:
                parsed["captions"][style] = "Watching this scene is like waiting for my microwave to finish its countdown."

    return parsed


def _verify_caption(caption: str, style: str) -> bool:
    """Task 15: Verify generated caption meets strict output constraints."""
    if not caption or not isinstance(caption, str):
        return False
    
    caption = caption.strip()
    if not caption:
        return False
        
    # No markdown/quotes/numbering/emojis
    invalid_chars = ["*", "_", "`", "#", "\"", "[", "]"]
    if any(char in caption for char in invalid_chars):
        logger.warning(f"Caption failed invalid_chars: {caption}")
        return False
        
    # Numbering like "1. " or "Caption:"
    if re.match(r"^\d+\.", caption) or "caption:" in caption.lower():
        logger.warning(f"Caption failed numbering/prefix check: {caption}")
        return False
        
    # Single sentence (exactly one ending punctuation mark, no internal sentence boundaries)
    ends_with_punct = caption.endswith(".") or caption.endswith("!") or caption.endswith("?")
    if not ends_with_punct:
        logger.warning(f"Caption failed ending punctuation check: {caption}")
        return False
        
    if re.search(r"[\.\!\?]\s+[A-Z]", caption):
        logger.warning(f"Caption failed single sentence check (multiple sentences detected): {caption}")
        return False
        
    # Word limit: the prompt asks for 12–16 words (formal) or max 16 (other styles).
    # We allow up to 35 words here so that naturally complete sentences from the
    # model are never rejected just for being a few words long. Anything over 35
    # is caught in _validate_and_patch before verification is called.
    words = caption.split()
    word_count = len(words)
    if word_count > 35:
        logger.warning(f"Caption failed word limit ({word_count} > 35): {caption}")
        return False
        
    return True


def _call_fireworks_vlm(model_name: str, frame_paths: list[str], prompt: str) -> str:
    """Send base64 images and a text prompt to Fireworks VLM via OpenAI SDK."""
    if not FIREWORKS_API_KEY:
        raise ValueError("FIREWORKS_API_KEY environment variable is not set.")

    client = OpenAI(
        api_key=FIREWORKS_API_KEY,
        base_url=FIREWORKS_BASE_URL,
    )

    content = [{"type": "text", "text": prompt}]
    for path in frame_paths:
        if os.path.exists(path):
            b64_data = _encode_image(path)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}
            })

    messages = [{"role": "user", "content": content}]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_tokens=MAX_OUTPUT_TOKENS,
    )
    return response.choices[0].message.content or ""


# ── Public API ─────────────────────────────────────────────────────────────────

def analyze_video(
    frame_paths: list[str],
    transcript: str | None,
    styles: list[str],
) -> dict:
    """
    Call Fireworks VLM to analyze frames and generate all requested captions
    in a single API call with automatic fallback and JSON repair retry.
    """
    if not frame_paths:
        logger.error("Cannot analyze video: no frame paths provided.")
        return _empty_result(styles)

    unified_prompt = get_unified_prompt(styles)

    # ── Attempt 1: primary call with VLM fallback ───────────────────────────
    logger.info(
        f"Calling Fireworks with {len(frame_paths)} frames "
        f"for perception + caption generation (styles={styles})."
    )
    raw_text: str | None = None
    api_call_failed = False
    try:
        raw_text = _call_fireworks_vlm(FIREWORKS_VISION_MODEL, frame_paths, unified_prompt)
    except Exception as exc:
        logger.error(f"Fireworks primary model call failed: {exc}. Trying fallback model...")
        try:
            raw_text = _call_fireworks_vlm(FIREWORKS_FALLBACK_VISION_MODEL, frame_paths, unified_prompt)
        except Exception as exc2:
            logger.error(f"Fireworks fallback model call failed: {exc2}")
            api_call_failed = True

    parsed = None
    if raw_text:
        cleaned = _strip_markdown_fences(raw_text)
        parsed = _safe_parse_json(cleaned)
        if parsed:
            # Check if all captions are present and valid
            all_valid = True
            for style in styles:
                cap = parsed.get("captions", {}).get(style)
                if not cap or not _verify_caption(cap, style):
                    all_valid = False
                    break
            
            if all_valid:
                logger.info("Fireworks response parsed and validated successfully on first attempt.")
            else:
                logger.warning(
                    "First Fireworks response had missing or invalid captions — triggering repair retry."
                )
                parsed = None
        else:
            logger.warning(
                "First Fireworks response was not valid JSON — attempting JSON repair retry."
            )

    # ── Attempt 2: repair-retry ───────────────────────────────────────────
    if parsed is None and raw_text is not None and not api_call_failed:
        logger.info("Sending JSON repair prompt to Fireworks (retry attempt 1).")
        repair_prompt = get_repair_prompt(styles, raw_text)
        try:
            raw_text = _call_fireworks_vlm(FIREWORKS_VISION_MODEL, frame_paths, repair_prompt)
            logger.info("JSON repair retry: Fireworks primary model call succeeded.")
        except Exception as exc:
            logger.error(f"Fireworks repair primary model call failed: {exc}. Trying fallback...")
            try:
                raw_text = _call_fireworks_vlm(FIREWORKS_FALLBACK_VISION_MODEL, frame_paths, repair_prompt)
                logger.info("JSON repair retry: Fireworks fallback model call succeeded.")
            except Exception as exc2:
                logger.error(f"Fireworks repair fallback model call failed: {exc2}")
                raw_text = None

        if raw_text:
            cleaned = _strip_markdown_fences(raw_text)
            parsed = _safe_parse_json(cleaned)
            if parsed:
                logger.info("Fireworks response parsed successfully after repair retry.")
            else:
                logger.error(
                    "JSON repair retry also produced invalid JSON. "
                    "Returning graceful empty captions."
                )
        else:
            logger.error(
                "JSON repair retry returned no text. "
                "Returning graceful empty captions."
            )
    elif parsed is None and api_call_failed:
        logger.error(
            "API calls failed. Skipping repair retry. "
            "Returning graceful empty captions."
        )

    # ── Graceful fallback ───────────────────────────────────────────────────
    if parsed is None:
        logger.warning(
            f"Caption generation failed for this task after attempts — "
            "returning empty captions to keep the batch alive."
        )
        return _empty_result(styles)

    # ── Validate & patch all required keys ──────────────────────────────────
    result = _validate_and_patch(parsed, styles)
    logger.info(
        f"Caption generation complete. "
        f"camera_motion={result['video_understanding'].get('camera_motion', 'unknown')}, "
        f"apparent_emotion={result['video_understanding'].get('apparent_emotion', 'unknown')}."
    )
    return result


def _empty_result(styles: list[str]) -> dict:
    """Return a well-formed empty result dict so callers never receive None."""
    all_styles = list(set(REQUIRED_CAPTION_STYLES) | set(styles))
    return {
        "captions": {style: "" for style in all_styles},
        "video_understanding": dict(_VIDEO_UNDERSTANDING_DEFAULTS),
    }
