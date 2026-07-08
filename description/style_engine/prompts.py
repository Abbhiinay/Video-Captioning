"""
prompts.py

Builds the unified system prompt sent to Gemini for combined video perception
and multi-style caption generation in a single API call.

Prompt design principles implemented here:

  Task 3  — Anti-hallucination rules: never invent objects, actions, identities,
             or locations. Only describe visible evidence. Say "unknown" if unclear.
  Task 4  — Fact consistency: all four captions describe the SAME scene; only
             tone differs. No style may introduce new facts or assumptions.
  Task 5  — Video-grounded humor: every humorous caption must reference at least
             one visible object or action from the video.
  Task 6  — Formal caption length: 15–18 words, hard max 20, single sentence.
  Task 7  — One sentence: every caption regardless of style is exactly one sentence.
  Task 8  — Clean output: no markdown, quotes, bullets, hashtags, emojis, labels,
             numbering — raw caption text only.
  Task 9  — camera_motion: always present; restricted to allowed values.
  Task 10 — apparent_emotion: describes visible expression/body language only;
             never infers internal state.
"""

from __future__ import annotations

import json


# ── Allowed camera_motion values (mirrors analyze_video.py constant) ──────────
CAMERA_MOTION_VALUES = "static | pan | tilt | zoom | tracking | handheld | unknown"


# ── Primary unified prompt ─────────────────────────────────────────────────────

def get_unified_prompt(requested_styles: list[str]) -> str:
    """
    Return the unified prompt that instructs Gemini to output a single
    structured JSON object containing video_understanding and captions.

    Args:
        requested_styles: Caption styles the caller wants (e.g. ["formal", "sarcastic"]).

    Returns:
        A fully-formed prompt string ready to pass to the Gemini API.
    """
    styles_block = _build_styles_schema(requested_styles)

    prompt = (
        # ── Role & Generalization (Task 11) ───────────────────────────────
        "You are an expert video analyst and factual caption writer. "
        "Analyze the provided video frames chronologically and produce "
        "a structured JSON response. "
        "This analysis must work equally well for sports, food, weather, "
        "technology, people, nature, animals, urban, indoor, outdoor, "
        "medical, manufacturing, construction, retail, and any other domain. "
        "Do not overfit to specific tropes.\n\n"

        # ── Task 12: Prompt Quality (Observation -> Understanding -> Caption) ──
        "Follow a three-stage thinking process:\n"
        "Phase 1: Observation -> Phase 2: Understanding -> Phase 3: Caption Generation.\n\n"

        # ── Task 1: Strict Factual Grounding ──────────────────────────────
        "STRICT OBSERVATION RULES — you MUST follow all of these:\n"
        "• Only describe what is directly visible in the frames. "
        "Never invent details, objects, people, actions, or settings.\n"
        "• Never infer unseen actions or events beyond what the frames show.\n"
        "• Never infer intentions or internal thoughts.\n"
        "• Never assume the identity of any person or place unless it is "
        "explicitly shown as visible text in the frame.\n"
        "• Never guess a location. If the location is unclear, write \"unknown\".\n"
        "• If any element is uncertain, omit the detail or describe it as \"unknown\".\n"
        "• Every claim must be supported by visible evidence in the frames. "
        "Never sacrifice accuracy for humor.\n\n"

        # ── Phase 1 & 2: Video understanding ───────────────────────────────
        "PHASE 1 & 2 — OBSERVATION & UNDERSTANDING\n"
        "Produce a factual analysis of the video. "
        "Extract: main action, subjects, objects, setting, background, "
        "apparent_emotion, camera_motion, visible_text, important_events, "
        "and a brief factual summary.\n\n"

        # ── Task 10: apparent_emotion rules ───────────────────────────────
        "For apparent_emotion:\n"
        "• Describe ONLY what is visible in facial expressions or body language.\n"
        "• Never infer internal emotional states (e.g. do not say 'happy' "
        "unless a smile is clearly visible).\n"
        "• If no person is visible or emotion is unclear, return \"unknown\".\n\n"

        # ── Task 9: camera_motion rules ───────────────────────────────────
        f"For camera_motion, you MUST return exactly one of: {CAMERA_MOTION_VALUES}.\n\n"

        # ── Phase 3: Captions ──────────────────────────────────────────────
        "PHASE 3 — CAPTION GENERATION\n"
        "Generate one caption per requested style. "
        "Follow ALL of the rules below for EVERY caption:\n\n"

        "UNIVERSAL CAPTION RULES (apply to ALL styles):\n"
        # ── Task 7: One sentence ───────────────────────────────────────────
        "• Each caption MUST be exactly ONE sentence. No full stops in the middle.\n"
        # ── Task 8: Clean output ───────────────────────────────────────────
        "• Output raw caption text ONLY. "
        "No markdown, no quotes, no bullet points, no hashtags, "
        "no emojis, no caption labels, no numbering.\n"
        # ── Task 4: Visible Object Requirement ──────────────────────────────
        "• Every caption must explicitly mention at least one visible object OR "
        "one visible action. Never generate generic captions.\n"
        # ── Task 7: Anti Repetition ─────────────────────────────────────────
        "• Avoid repeating the same uncommon words across all four captions. "
        "Each caption should sound independently written.\n"
        # ── Task 2: Fact consistency (Wording Not Facts) ────────────────────
        "• ALL requested captions MUST describe the SAME scene. "
        "Only the wording changes between styles. "
        "Facts must remain identical. Objects remain identical. "
        "Actions remain identical. Visible text remains identical. "
        "No style may introduce new facts or assumptions not in the video.\n\n"

        # ── Per-style rules ────────────────────────────────────────────────
        "PER-STYLE RULES:\n"

        # ── Task 3: Shorter Captions (Formal 12-16, max 18) ───────────────
        "• formal: Objective, factual, single sentence. "
        "12 to 16 words. Hard maximum 18 words. "
        "Long captions introduce unnecessary opportunities for hallucination. "
        "Professional tone. No opinions, no assumptions, no adjectives "
        "that are not directly observable. No emojis.\n"

        # ── Task 3: Sarcastic max 16 words ─────────────────────────────────
        "• sarcastic: Witty, dry sarcasm, playful exaggeration. "
        "Maximum 16 words. Single sentence. "
        "No offensive jokes. No dark humor. Social-media tone.\n"

        # ── Task 5: Tech humor ─────────────────────────────────────────────
        "• humorous_tech: MUST directly reference at least one specific visible "
        "object or visible action from the video using a software engineering "
        "metaphor. Avoid generic software jokes. Instead, bind the joke to "
        "visible objects. Example mappings: Keyboard -> git merge, Traffic -> "
        "deadlock, Cat -> deploy, Bus -> background process, Monitor -> dashboard. "
        "Maximum 16 words. Single sentence.\n"

        # ── Task 6: Non-tech humor ─────────────────────────────────────────
        "• humorous_non_tech: MUST directly reference at least one specific "
        "visible object or visible action from the video in a relatable "
        "everyday context (office, family, friends, gym, food, school, etc.). "
        "Do NOT use technology references. Avoid generic jokes. "
        "Relate joke to visible action or visible object. "
        "Maximum 16 words. Single sentence.\n\n"

        # ── JSON schema instruction ────────────────────────────────────────
        "OUTPUT FORMAT\n"
        "Return ONLY a valid JSON object matching the schema below. "
        "Do NOT add markdown fences (```), comments, or any text outside the JSON.\n\n"
        + _build_json_schema(requested_styles)
    )

    return prompt


def get_repair_prompt(requested_styles: list[str], bad_response: str) -> str:
    """
    Return a repair prompt used when the primary Gemini response was not valid JSON.

    This is the Task 1 retry mechanism. It explicitly tells Gemini that the
    previous response failed and requests a clean, schema-compliant JSON object.

    Args:
        requested_styles: Same styles as the original request.
        bad_response:     The malformed text Gemini returned on the first attempt
                          (included so Gemini can see what went wrong).

    Returns:
        A repair prompt string.
    """
    # Truncate the bad response to keep the prompt size reasonable
    preview = bad_response[:500] if bad_response else "(empty)"

    return (
        "The previous response was not valid JSON and could not be parsed.\n"
        f"The invalid response started with:\n{preview}\n\n"
        "Correct the error and return ONLY a valid JSON object that exactly "
        "matches the required schema shown below. "
        "Do NOT add markdown fences (```json or ```), explanatory text, "
        "comments, or anything outside the JSON object.\n\n"
        + _build_json_schema(requested_styles)
    )


# ── Private helpers ────────────────────────────────────────────────────────────

def _build_styles_schema(requested_styles: list[str]) -> str:
    """Build a comma-separated string of requested style names (for display)."""
    return ", ".join(f'"{s}"' for s in requested_styles)


def _build_json_schema(requested_styles: list[str]) -> str:
    """
    Construct the JSON schema example block embedded in the prompt.

    Uses a real JSON serialisation so the schema is always syntactically correct
    regardless of which styles are requested.
    """
    captions_example: dict[str, str] = {style: "string" for style in requested_styles}

    schema: dict = {
        "video_understanding": {
            "main_action": "string",
            "subjects": ["string"],
            "objects": ["string"],
            "setting": "string",
            "background": "string",
            "apparent_emotion": "string — visible facial expression or body language only, or 'unknown'",
            "camera_motion": f"string — one of: {CAMERA_MOTION_VALUES}",
            "visible_text": "string",
            "important_events": ["string"],
            "summary": "string",
        },
        "captions": captions_example,
    }

    return json.dumps(schema, indent=2)
