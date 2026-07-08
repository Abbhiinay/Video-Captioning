"""
gemini_client.py

Low-level REST wrapper for the Gemini multimodal API.

Responsibilities:
  - Encode video frames as base64 inline data parts.
  - POST a structured request to the Gemini generateContent endpoint.
  - Enforce application/json output mode so the model is biased toward
    well-formed JSON without needing post-hoc parsing of markdown fences.
  - Retry on transient HTTP errors (429, 500–504) with exponential backoff.
  - If a 429 rate limit is encountered, wait for the duration specified in the
    Retry-After header, or fall back to a 30-second sleep to allow the quota to clear.
"""

from __future__ import annotations

import base64
import logging
import os
import time
from typing import Any

import requests

from config.settings import (
    GEMINI_API_KEY, GEMINI_MODEL,
    TEMPERATURE, TOP_P, MAX_OUTPUT_TOKENS
)

logger = logging.getLogger(__name__)

# HTTP status codes that warrant an automatic retry.
_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})

# Maximum total number of attempts (1 initial + 3 retries = 4 total).
_MAX_ATTEMPTS: int = 4

# Initial backoff delay in seconds for general retryable errors.
_INITIAL_DELAY_S: float = 2.0

# Fallback backoff delay in seconds specifically for HTTP 429 when Retry-After is missing.
_RATE_LIMIT_DELAY_S: float = 30.0

# Per-request timeout (seconds).
_REQUEST_TIMEOUT_S: float = 60.0


# ── Frame encoding ─────────────────────────────────────────────────────────────

def _encode_frame(path: str) -> dict[str, Any] | None:
    """
    Read a JPEG frame from disk and encode it as a Gemini inlineData part.

    Returns None (and logs a warning) if the file is missing or unreadable
    so a single bad frame never aborts the whole request.
    """
    if not os.path.exists(path):
        logger.warning(f"Frame file not found, skipping: {path}")
        return None
    try:
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("utf-8")
        return {"inlineData": {"mimeType": "image/jpeg", "data": b64}}
    except OSError as exc:
        logger.error(f"Could not read frame file {path}: {exc}")
        return None


def _extract_text_from_response(data: dict[str, Any]) -> str:
    """
    Safely navigate the Gemini response envelope to retrieve the generated text.

    Expected shape:
      data["candidates"][0]["content"]["parts"][0]["text"]

    Raises RuntimeError if the shape is unexpected so callers can handle it
    cleanly (no bare KeyError / IndexError).
    """
    try:
        candidates: list = data.get("candidates") or []
        if not candidates:
            raise KeyError("candidates list is empty")
        content: dict = candidates[0].get("content") or {}
        parts: list = content.get("parts") or []
        if not parts:
            raise KeyError("parts list is empty")
        text: str = parts[0].get("text", "")
        return text
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            f"Unexpected Gemini response structure: {exc}. Response: {data}"
        ) from exc


# ── Public API ─────────────────────────────────────────────────────────────────

def analyze_video_frames(
    frame_paths: list[str],
    transcript: str | None,
    prompt: str,
) -> str:
    """
    Send video frames and a prompt to the Gemini API and return the raw text response.

    The request enforces ``responseMimeType: "application/json"`` to bias the model
    toward producing a well-formed JSON string.

    Retries up to _MAX_ATTEMPTS times with exponential backoff on transient errors.
    If HTTP 429 is encountered, sleeps for the time indicated in the Retry-After
    header or 30 seconds.

    Args:
        frame_paths: Absolute paths to JPEG frame files. Missing files are skipped.
        transcript:  Optional video transcript appended to the prompt.
        prompt:      Fully-formed instruction string from prompts.py.

    Returns:
        The raw text content from the first successful Gemini response.

    Raises:
        ValueError:  If GEMINI_API_KEY is not configured.
        RuntimeError: If all retry attempts are exhausted.
    """
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Configure it in your .env file."
        )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    headers = {"Content-Type": "application/json"}

    # ── Build request parts ────────────────────────────────────────────────
    parts: list[dict[str, Any]] = []

    full_prompt = prompt
    if transcript:
        full_prompt += f"\n\nVideo Transcript:\n{transcript}"
    parts.append({"text": full_prompt})

    encoded_count = 0
    for path in frame_paths:
        part = _encode_frame(path)
        if part is not None:
            parts.append(part)
            encoded_count += 1

    logger.info(
        f"Sending request to Gemini ({GEMINI_MODEL}): "
        f"{encoded_count} frame(s) encoded, "
        f"prompt length={len(full_prompt)} chars."
    )

    payload: dict[str, Any] = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": TEMPERATURE,
            "topP": TOP_P,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
        },
    }

    # ── Retry loop ─────────────────────────────────────────────────────────
    delay = _INITIAL_DELAY_S
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=_REQUEST_TIMEOUT_S
            )

            if response.status_code == 200:
                data: dict[str, Any] = response.json()
                text = _extract_text_from_response(data)
                logger.info(
                    f"Gemini responded successfully on attempt {attempt}/{_MAX_ATTEMPTS}."
                )
                return text

            if response.status_code in _RETRYABLE_STATUS_CODES:
                if attempt < _MAX_ATTEMPTS:
                    # Calculate wait time
                    wait = delay
                    if response.status_code == 429:
                        # Extract Retry-After if available, otherwise sleep 30s
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                wait = float(retry_after)
                                logger.warning(
                                    f"Gemini returned HTTP 429 rate limit. "
                                    f"Retry-After header specifies {wait:.1f}s. Waiting..."
                                )
                            except ValueError:
                                wait = _RATE_LIMIT_DELAY_S
                        else:
                            wait = _RATE_LIMIT_DELAY_S
                            logger.warning(
                                f"Gemini returned HTTP 429 rate limit. "
                                f"No Retry-After header found. Waiting {wait}s to cool down..."
                            )
                    else:
                        logger.warning(
                            f"Gemini returned HTTP {response.status_code} "
                            f"(attempt {attempt}/{_MAX_ATTEMPTS}). "
                            f"Retrying in {wait:.1f}s…"
                        )
                    
                    time.sleep(wait)
                    delay *= 2.0
                    continue
                # Final attempt also returned a retryable error
                response.raise_for_status()

            # Non-retryable 4xx errors — raise immediately
            response.raise_for_status()

        except requests.RequestException as exc:
            if attempt < _MAX_ATTEMPTS:
                logger.warning(
                    f"Gemini request failed with network error "
                    f"(attempt {attempt}/{_MAX_ATTEMPTS}): {exc}. "
                    f"Retrying in {delay:.1f}s…"
                )
                time.sleep(delay)
                delay *= 2.0
            else:
                raise RuntimeError(
                    f"Gemini API request failed after {_MAX_ATTEMPTS} attempts: {exc}"
                ) from exc

    raise RuntimeError(
        f"Gemini API call did not succeed after {_MAX_ATTEMPTS} attempts."
    )
