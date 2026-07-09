"""
frame_extractor.py

Async wrapper for OpenCV frame extraction.
Runs CPU-bound cv2 work in asyncio.to_thread() to avoid blocking the event loop.
"""

import os
import tempfile
import logging
import asyncio

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _histogram_correlation(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """Compute histogram correlation between two BGR frames."""
    hist1 = cv2.calcHist([frame1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([frame2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)
    return float(cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL))


def _uniform_indices(total: int, count: int) -> list[int]:
    """Return count evenly-spaced indices in [0, total-1]."""
    if count <= 0:
        return []
    if count == 1:
        return [total // 2]
    return [int(i * (total - 1) / (count - 1)) for i in range(count)]


def _extract_frames_sync(video_path: str, n: int = 5) -> list[str]:
    """
    Synchronous frame extraction using OpenCV with hybrid
    uniform + scene-change selection.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if n <= 0:
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV failed to open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    if total_frames <= 0:
        cap.release()
        raise ValueError(f"OpenCV reports 0 total frames for: {video_path}")

    logger.info(
        f"Video: total_frames={total_frames}, fps={fps:.1f}, "
        f"duration={total_frames/fps:.1f}s, requested={n}"
    )

    selected: set[int] = set()

    # Fast mode: uniform sampling only (skips heavy scene detection)
    selected.update(_uniform_indices(total_frames, n))
    sorted_indices = sorted(selected)
    logger.info(f"Selected frame indices: {sorted_indices}")

    # Extract and save frames
    frame_paths = []
    temp_dir = tempfile.gettempdir()
    video_basename = os.path.basename(video_path)

    for i, idx in enumerate(sorted_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, float(idx))
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        out_path = os.path.join(temp_dir, f"api_frame_{video_basename}_{i}_{idx}.jpg")
        try:
            if cv2.imwrite(out_path, frame) and os.path.exists(out_path):
                frame_paths.append(out_path)
        except Exception as e:
            logger.error(f"Error saving frame {idx}: {e}")

    cap.release()

    if not frame_paths:
        raise RuntimeError(f"Frame extraction produced 0 frames from: {video_path}")

    logger.info(f"Extracted {len(frame_paths)} frames")
    return frame_paths


async def extract_frames(video_path: str, n: int = 5) -> list[str]:
    """Async wrapper — runs OpenCV frame extraction in a thread."""
    return await asyncio.to_thread(_extract_frames_sync, video_path, n)
