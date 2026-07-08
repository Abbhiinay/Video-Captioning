"""
extract_frames.py

Extracts representative frames from a video file using OpenCV.

Frame selection strategy (Task 12 — improved scene detection):
  - Instead of sampling a fixed count of 30 frames for diff-checking, frames
    are sampled at a temporal interval driven by the video's actual FPS, targeting
    one candidate sample every 0.5 seconds. This scales correctly from slow 12 fps
    dashcam footage to 60 fps high-speed video, avoiding over-sampling short clips
    and under-sampling long ones.

When ENABLE_SCENE_DETECTION is True and n >= 3:
  - 3 evenly-spaced "anchor" frames are always included for temporal coverage.
  - The remaining (n-3) frame slots are filled by the frames with the highest
    histogram difference from their temporal neighbours (scene-change frames).

Otherwise:
  - n evenly-spaced frames are returned.

Task 13: Logs selected frame indices, scene-change indices, and frame count.
Task 14: All dictionary/attribute accesses are guarded; no bare KeyError/IndexError.
Task 15: Functions are small and focused. Full type hints throughout.
"""

from __future__ import annotations

import os
import tempfile
import logging
from typing import Sequence

import cv2
import numpy as np

from config.settings import ENABLE_SCENE_DETECTION

logger = logging.getLogger(__name__)

# Temporal sampling interval for scene-detection candidate frames (seconds).
# One candidate sample per this many seconds of video.
_SCENE_SAMPLE_INTERVAL_S: float = 0.5

# Minimum and maximum candidate samples for diff computation.
_MIN_SCENE_SAMPLES: int = 10
_MAX_SCENE_SAMPLES: int = 120


# ── Histogram utilities ────────────────────────────────────────────────────────

def _histogram_correlation(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """
    Compute the Bhattacharyya-normalised histogram correlation between two BGR frames.

    Returns a value in [-1, 1].  Lower correlation means the frames look more
    different — i.e. a higher probability of a scene change.
    """
    hist1 = cv2.calcHist([frame1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([frame2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)
    return float(cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL))


# ── Frame selection ────────────────────────────────────────────────────────────

def _uniform_indices(total: int, count: int) -> list[int]:
    """Return `count` evenly-spaced integer frame indices in [0, total-1]."""
    if count <= 0:
        return []
    if count == 1:
        return [total // 2]
    return [int(i * (total - 1) / (count - 1)) for i in range(count)]


def _scene_candidate_indices(total_frames: int, fps: float) -> list[int]:
    """
    Build the list of frame indices used as candidates for scene-change detection.

    Spacing is based on the video's FPS so that we sample approximately every
    _SCENE_SAMPLE_INTERVAL_S seconds (Task 12).
    """
    if fps <= 0:
        fps = 25.0  # sensible fallback

    step = max(1, int(round(fps * _SCENE_SAMPLE_INTERVAL_S)))
    candidate_count = max(_MIN_SCENE_SAMPLES, min(_MAX_SCENE_SAMPLES, total_frames // step))
    return _uniform_indices(total_frames, candidate_count)


def _detect_scene_changes(
    cap: cv2.VideoCapture,
    candidate_indices: list[int],
    n_changes: int,
    exclude: set[int],
    fps: float,
) -> list[int]:
    """
    Read candidate frames and return up to `n_changes` frame indices with the
    largest histogram differences from their temporal neighbours.

    Args:
        cap:               Open cv2.VideoCapture handle.
        candidate_indices: Frame indices to evaluate.
        n_changes:         How many scene-change indices to return.
        exclude:           Indices already selected (not re-added).
        fps:               Video frames per second.

    Returns:
        sorted list of chosen scene-change frame indices.
    """
    diffs: list[tuple[float, int]] = []  # (correlation, frame_idx_after_change)
    prev_frame: np.ndarray | None = None
    prev_idx: int | None = None

    for idx in candidate_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, float(idx))
        ret, frame = cap.read()
        if not ret or frame is None:
            logger.debug(f"Scene detection: could not read frame at index {idx}, skipping.")
            prev_frame = None
            prev_idx = None
            continue

        if prev_frame is not None and prev_idx is not None:
            corr = _histogram_correlation(prev_frame, frame)
            diffs.append((corr, idx))

        prev_frame = frame
        prev_idx = idx

    # Ascending sort: lowest correlation = highest visual change (strongest first)
    diffs.sort(key=lambda x: x[0])

    selected: list[int] = []
    min_spacing = max(1, int(round(fps * 0.5)))

    for _corr, idx in diffs:
        if len(selected) >= n_changes:
            break
        if idx not in exclude:
            # Task 2: spacing constraint - skip if too close to an already selected scene change frame
            too_close = False
            for sel in selected:
                if abs(idx - sel) < min_spacing:
                    too_close = True
                    break
            if not too_close:
                selected.append(idx)

    logger.info(
        f"Scene detection: evaluated {len(diffs)} adjacent pairs from "
        f"{len(candidate_indices)} candidates; "
        f"selected {len(selected)} scene-change frame(s): {sorted(selected)}."
    )
    return sorted(selected)


# ── Public API ─────────────────────────────────────────────────────────────────

def extract_frames(video_path: str, n: int = 5) -> list[str]:
    """
    Extract n representative frames from the video at `video_path`.

    Hybrid mode (ENABLE_SCENE_DETECTION=True, n >= 3):
      - Always selects 3 uniformly-spaced anchor frames for temporal coverage.
      - Fills remaining slots with the scene-change frames that have the largest
        histogram differences, sampled at a ~0.5-second interval (Task 12).

    Uniform mode:
      - Selects n evenly-spaced frames.

    Saves each frame as a temporary JPEG and returns sorted file paths.
    Logs selected frame indices and scene-change indices (Task 13).
    All failures are guarded — never raises on a single bad frame (Task 14).

    Args:
        video_path: Absolute path to the downloaded video file.
        n:          Total number of frames to extract.

    Returns:
        List of paths to the extracted JPEG files, sorted chronologically.

    Raises:
        FileNotFoundError: If `video_path` does not exist.
        RuntimeError:      If OpenCV cannot open the file or extracts 0 frames.
        ValueError:        If OpenCV reports 0 total frames.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if n <= 0:
        return []

    logger.info(f"Opening video for frame extraction: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV failed to open video: {video_path}")

    total_frames: int = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps: float = cap.get(cv2.CAP_PROP_FPS) or 25.0

    if total_frames <= 0:
        cap.release()
        raise ValueError(f"OpenCV reports 0 total frames for: {video_path}")

    duration_s = total_frames / fps
    logger.info(
        f"Video metadata — total_frames={total_frames}, fps={fps:.2f}, "
        f"duration={duration_s:.1f}s, requested_frames={n}."
    )

    selected: set[int] = set()

    # ── Hybrid scene-aware selection ───────────────────────────────────────
    use_hybrid = ENABLE_SCENE_DETECTION and n >= 3
    if use_hybrid:
        anchor_count = min(3, n)
        anchor_indices = _uniform_indices(total_frames, anchor_count)
        selected.update(anchor_indices)
        logger.info(f"Hybrid mode: anchor frame indices = {sorted(anchor_indices)}.")

        slots_remaining = n - len(selected)
        if slots_remaining > 0:
            candidate_indices = _scene_candidate_indices(total_frames, fps)
            logger.info(
                f"Scene detection: sampling {len(candidate_indices)} candidates "
                f"at ~{_SCENE_SAMPLE_INTERVAL_S}s interval (fps={fps:.2f})."
            )
            scene_indices = _detect_scene_changes(
                cap, candidate_indices, slots_remaining, selected, fps
            )
            selected.update(scene_indices)

        # Backfill with uniform frames if scene detection did not fill all slots
        still_needed = n - len(selected)
        if still_needed > 0:
            backfill = _uniform_indices(total_frames, n)
            for idx in backfill:
                if still_needed <= 0:
                    break
                if idx not in selected:
                    selected.add(idx)
                    still_needed -= 1
            if still_needed < (n - len(anchor_indices) - len(scene_indices if 'scene_indices' in dir() else [])):
                logger.debug(
                    f"Backfilled {n - len(selected) + still_needed} frame(s) "
                    "with uniform indices."
                )
    else:
        # ── Uniform selection ──────────────────────────────────────────────
        uniform = _uniform_indices(total_frames, n)
        selected.update(uniform)
        logger.info(f"Uniform mode: frame indices = {sorted(uniform)}.")

    sorted_indices = sorted(selected)
    logger.info(f"Final selected frame indices ({len(sorted_indices)}): {sorted_indices}.")

    # ── Extract and save frames ────────────────────────────────────────────
    frame_paths: list[str] = []
    temp_dir = tempfile.gettempdir()
    video_basename = os.path.basename(video_path)

    for i, idx in enumerate(sorted_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, float(idx))
        ret, frame = cap.read()
        if not ret or frame is None:
            logger.warning(f"Failed to read frame at index {idx} — skipping.")
            continue

        out_path = os.path.join(temp_dir, f"frame_{video_basename}_{i}_{idx}.jpg")
        try:
            success = cv2.imwrite(out_path, frame)
            if success and os.path.exists(out_path):
                frame_paths.append(out_path)
            else:
                logger.warning(f"cv2.imwrite failed for frame index {idx}.")
        except Exception as write_err:
            logger.error(f"Error saving frame {idx} to {out_path}: {write_err}")

    cap.release()

    if not frame_paths:
        raise RuntimeError(
            f"Frame extraction produced 0 frames from: {video_path}"
        )

    logger.info(
        f"Frame extraction complete: {len(frame_paths)} frames saved to {temp_dir}."
    )
    return frame_paths