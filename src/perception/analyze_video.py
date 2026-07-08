"""
analyze_video.py

Calls Gemini Flash with sampled video frames to produce a structured JSON response
containing both video understanding metadata and all requested caption styles
in a single API call.

Responsibilities:
  - Build and send the unified prompt to gemini_client.
  - Strip any accidental markdown wrapping from the raw response.
  - Parse the JSON response with an automatic repair-retry on failure (Task 1).
  - Validate and back-fill every required key with safe defaults (Task 2).
  - Never raise; always return a safe result dict so the batch never crashes.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from description.utils.gemini_client import analyze_video_frames
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

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json … ``` or ``` … ``` fences that Gemini sometimes emits."""
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
        logger.warning("Gemini returned valid JSON but it was not a dict object.")
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
    - camera_motion: must be one of the allowed values; falls back to "unknown".
    - apparent_emotion: patched in if the model returned the old "emotion" key.
    - No exceptions are raised here (Task 14 / Task 2).
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

    # ── Task 15: Output Verification ─────────────────────────────────────────
    # Verify captions are single sentence, non-empty, within word limits,
    # plain text (no markdown, emojis, numbering, quotes).
    for style in all_expected_styles:
        caption = parsed["captions"].get(style, "")
        if not _verify_caption(caption, style):
            logger.warning(f"Caption '{style}' failed verification. Setting to empty.")
            parsed["captions"][style] = ""

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
        
    # Single sentence (exactly one ending punctuation mark)
    # Allowed ending punctuation: ., !, ?
    ends_with_punct = caption.endswith(".") or caption.endswith("!") or caption.endswith("?")
    
    # Count internal sentence terminators (we allow commas, semicolons, etc, but only one sentence terminator)
    terminator_count = caption.count(".") + caption.count("!") + caption.count("?")
    
    if not ends_with_punct or terminator_count != 1:
        logger.warning(f"Caption failed single sentence check (terminators={terminator_count}): {caption}")
        return False
        
    # Word limits
    words = caption.split()
    word_count = len(words)
    
    if style == "formal" and word_count > 18:
        logger.warning(f"Caption failed word limit ({word_count} > 18): {caption}")
        return False
    elif style != "formal" and word_count > 16:
        logger.warning(f"Caption failed word limit ({word_count} > 16): {caption}")
        return False
        
    return True


# ── Public API ─────────────────────────────────────────────────────────────────

def analyze_video(
    frame_paths: list[str],
    transcript: str | None,
    styles: list[str],
) -> dict:
    """
    Call Gemini Flash to analyze frames and generate all requested captions
    in a single API call.

    Robust JSON handling (Task 1):
      1. Send the unified prompt; attempt to parse the JSON response.
      2. On parse failure, send one repair prompt and re-parse.
      3. On second failure, return a safe empty-caption result — never crash.

    Key validation (Task 2):
      After parsing, _validate_and_patch() ensures every required key exists.

    Returns a dict with keys: "captions" (dict), "video_understanding" (dict).
    """
    if not frame_paths:
        logger.error("Cannot analyze video: no frame paths provided.")
        return _empty_result(styles)

    unified_prompt = get_unified_prompt(styles)

    # ── Attempt 1: primary call ─────────────────────────────────────────────
    logger.info(
        f"Calling Gemini with {len(frame_paths)} frames "
        f"for perception + caption generation (styles={styles})."
    )
    raw_text: str | None = None
    api_call_failed = False  # tracks whether the API itself failed (429, network) vs bad JSON
    try:
        raw_text = analyze_video_frames(frame_paths, transcript, unified_prompt)
    except Exception as exc:
        logger.error(f"Gemini primary API call failed: {exc}")
        api_call_failed = True

    parsed = None
    if raw_text:
        cleaned = _strip_markdown_fences(raw_text)
        parsed = _safe_parse_json(cleaned)
        if parsed:
            logger.info("Gemini response parsed successfully on first attempt.")
        else:
            logger.warning(
                "First Gemini response was not valid JSON — attempting JSON repair retry."
            )

    # ── Attempt 2: repair-retry (Task 1) ───────────────────────────────────
    # ONLY attempt repair if:
    #   - We got a response (raw_text is not None) but it was invalid JSON
    # Do NOT attempt repair if the primary API call itself failed (429, network error).
    # Sending another request immediately after a 429 just makes rate limiting worse.
    if parsed is None and raw_text is not None and not api_call_failed:
        logger.info("Sending JSON repair prompt to Gemini (retry attempt 1).")
        repair_prompt = get_repair_prompt(styles, raw_text)
        try:
            raw_text = analyze_video_frames(frame_paths, transcript, repair_prompt)
            logger.info("JSON repair retry: Gemini call succeeded.")
        except Exception as exc:
            logger.error(f"Gemini repair retry call failed: {exc}")
            raw_text = None

        if raw_text:
            cleaned = _strip_markdown_fences(raw_text)
            parsed = _safe_parse_json(cleaned)
            if parsed:
                logger.info("Gemini response parsed successfully after repair retry.")
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
            "Primary API call failed (rate limit or network error). "
            "Skipping repair retry to avoid worsening rate limit. "
            "Returning graceful empty captions."
        )

    # ── Graceful fallback ───────────────────────────────────────────────────
    if parsed is None:
        logger.warning(
            f"Caption generation failed for this task after 2 attempts — "
            "returning empty captions to keep the batch alive."
        )
        return _empty_result(styles)

    # ── Validate & patch all required keys (Task 2) ─────────────────────────
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
