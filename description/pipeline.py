"""
pipeline.py

End-to-end task orchestrator for the video captioning pipeline.

Coordinates:
  1. Video download (description/utils/io.py)
  2. Frame extraction (src/preprocessing/extract_frames.py)
  3. Unified perception + caption generation (src/perception/analyze_video.py)
  4. Temporary file cleanup

Design principles:
  - Never crash the batch. Every exception is caught internally; a graceful
    empty-caption result is returned for the failed task so other tasks continue.
  - Temporary files are always cleaned up in a `finally` block.
  - All dictionary lookups use .get() with safe defaults (Task 14).
  - Detailed logs cover each pipeline stage and the overall task outcome (Task 13).
"""

from __future__ import annotations

import logging
import os

from description.utils.io import download_video
from src.preprocessing.extract_frames import extract_frames
from src.perception.analyze_video import analyze_video
from config.settings import FRAME_COUNT

logger = logging.getLogger(__name__)


def process_task(task: dict) -> dict:
    """
    Run the full captioning pipeline for a single video task.

    Args:
        task: A task dict with keys:
              - "task_id"   (str)         — unique identifier.
              - "video_url" (str)         — URL to download.
              - "styles"    (list[str])   — caption styles to generate.

    Returns:
        A result dict ``{"task_id": str, "captions": {style: str, …}}``.
        Caption values are empty strings when any stage fails.
        This function never raises.
    """
    task_id: str = task.get("task_id", "unknown")
    video_url: str | None = task.get("video_url")
    styles: list[str] = task.get("styles") or []

    logger.info(f"[{task_id}] Pipeline started (styles={styles}).")

    # Build safe fallback result up front
    result: dict = {
        "task_id": task_id,
        "captions": {style: "" for style in styles},
    }

    if not video_url:
        logger.error(f"[{task_id}] No video_url in task — skipping.")
        return result

    video_path: str | None = None
    frame_paths: list[str] = []

    try:
        # ── Stage 1: Download ──────────────────────────────────────────────
        try:
            logger.info(f"[{task_id}] Downloading video from {video_url}…")
            video_path = download_video(video_url)
            logger.info(f"[{task_id}] Video downloaded to {video_path}.")
        except Exception as exc:
            logger.error(f"[{task_id}] Video download failed: {exc}")
            return result

        # ── Stage 2: Frame extraction ──────────────────────────────────────
        try:
            logger.info(
                f"[{task_id}] Extracting up to {FRAME_COUNT} frames from video."
            )
            frame_paths = extract_frames(video_path, n=FRAME_COUNT)
            logger.info(
                f"[{task_id}] Extracted {len(frame_paths)} frame(s): "
                f"{[os.path.basename(p) for p in frame_paths]}."
            )
        except Exception as exc:
            logger.error(f"[{task_id}] Frame extraction failed: {exc}")
            return result

        # ── Stage 3: Perception + caption generation ───────────────────────
        try:
            logger.info(
                f"[{task_id}] Sending {len(frame_paths)} frame(s) to Gemini…"
            )
            # transcript=None — audio support can be wired here if needed
            analysis: dict = analyze_video(frame_paths, transcript=None, styles=styles)

            # Extract captions, defaulting missing styles to empty string (Task 14)
            captions: dict = analysis.get("captions") or {}
            for style in styles:
                result["captions"][style] = captions.get(style, "")

            # Log video understanding for debugging insight (Task 13)
            vu: dict = analysis.get("video_understanding") or {}
            logger.info(
                f"[{task_id}] Caption generation succeeded. "
                f"main_action='{vu.get('main_action', 'unknown')}', "
                f"camera_motion='{vu.get('camera_motion', 'unknown')}', "
                f"apparent_emotion='{vu.get('apparent_emotion', 'unknown')}'."
            )
        except Exception as exc:
            logger.error(
                f"[{task_id}] Perception/caption generation failed: {exc}"
            )
            return result

    except Exception as exc:
        # Catch-all safety net — should not normally be reached
        logger.error(f"[{task_id}] Unexpected pipeline error: {exc}")

    finally:
        # ── Cleanup temporary files ────────────────────────────────────────
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                logger.info(f"[{task_id}] Removed temporary video: {video_path}.")
            except OSError as cleanup_err:
                logger.warning(
                    f"[{task_id}] Failed to remove temp video {video_path}: {cleanup_err}."
                )

        removed_frames = 0
        for fpath in frame_paths:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                    removed_frames += 1
                except OSError as cleanup_err:
                    logger.warning(
                        f"[{task_id}] Failed to remove temp frame {fpath}: {cleanup_err}."
                    )
        if frame_paths:
            logger.info(
                f"[{task_id}] Cleaned up {removed_frames}/{len(frame_paths)} temp frame(s)."
            )

    # ── Task 10: Result Validation ─────────────────────────────────────────
    # Validate result is JSON serializable, has task_id, captions, all styles, no None.
    import json
    try:
        json.dumps(result)
    except (TypeError, ValueError) as e:
        logger.error(f"[{task_id}] Result is not JSON serializable: {e}. Falling back.")
        result = {"task_id": task_id, "captions": {style: "" for style in styles}}

    if result.get("task_id") is None or result.get("captions") is None:
        logger.error(f"[{task_id}] Result missing required keys. Falling back.")
        result = {"task_id": task_id, "captions": {style: "" for style in styles}}

    # Check for None values anywhere in the result
    def _has_none(obj):
        if obj is None: return True
        if isinstance(obj, dict): return any(_has_none(v) for v in obj.values())
        if isinstance(obj, list): return any(_has_none(v) for v in obj)
        return False

    if _has_none(result):
        logger.error(f"[{task_id}] Result contains None values. Falling back.")
        result = {"task_id": task_id, "captions": {style: "" for style in styles}}
        
    for style in styles:
        if style not in result["captions"]:
            logger.error(f"[{task_id}] Result missing requested style '{style}'. Adding empty.")
            result["captions"][style] = ""

    logger.info(f"[{task_id}] Pipeline finished.")
    return result