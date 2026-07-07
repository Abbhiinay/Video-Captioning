import os
import tempfile
import logging
import cv2
import numpy as np

from config.settings import ENABLE_SCENE_DETECTION

logger = logging.getLogger(__name__)

def get_histogram_diff(frame1, frame2):
    """Calculates the absolute difference between histograms of two frames."""
    hist1 = cv2.calcHist([frame1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([frame2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)
    return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

def extract_frames(video_path: str, n: int = 5) -> list[str]:
    """
    Extracts frames from the video.
    If ENABLE_SCENE_DETECTION is True and n >= 5, uses hybrid selection:
      - 3 evenly spaced frames
      - Remaining frames (n-3) selected via scene detection (highest histogram diffs)
    Otherwise, selects n evenly spaced frames.
    Saves frames as temporary JPEGs and returns their paths sorted by timestamp.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at {video_path}")
        
    if n <= 0:
        return []

    logger.info("Attempting frame extraction using OpenCV...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV failed to open video file: {video_path}")
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        raise ValueError("OpenCV reports total frames <= 0")
        
    use_hybrid = ENABLE_SCENE_DETECTION and n >= 3
    selected_indices = set()

    if use_hybrid:
        logger.info(f"Using hybrid scene detection. Will pick 3 uniform + {n-3} scene-change frames.")
        # 1. Select 3 evenly spaced frames
        uniform_indices = [int(i * (total_frames - 1) / 2) for i in range(3)]
        selected_indices.update(uniform_indices)

        # 2. Scene detection: Sample frames at regular intervals to find scene changes
        num_samples = min(total_frames, 30) # sample up to 30 frames for diff checking
        sample_indices = [int(i * (total_frames - 1) / (num_samples - 1)) for i in range(num_samples)]
        
        diffs = []
        prev_frame = None
        prev_idx = None

        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            
            if prev_frame is not None:
                # Lower correlation means higher difference
                correlation = get_histogram_diff(prev_frame, frame)
                diffs.append((correlation, prev_idx, idx))
                
            prev_frame = frame
            prev_idx = idx

        # Sort by correlation (ascending, since lower = more different)
        diffs.sort(key=lambda x: x[0])
        
        # Add the frame after the scene change for the top N-3 differences
        needed = n - len(selected_indices)
        for _, _, idx in diffs:
            if needed <= 0:
                break
            if idx not in selected_indices:
                selected_indices.add(idx)
                needed -= 1
                
        # If we still need frames, just add uniform ones
        needed = n - len(selected_indices)
        if needed > 0:
            extra = [int(i * (total_frames - 1) / (n - 1)) for i in range(n)]
            for e in extra:
                if needed <= 0:
                    break
                if e not in selected_indices:
                    selected_indices.add(e)
                    needed -= 1
    else:
        # Standard uniform sampling
        if n == 1:
            selected_indices.add(total_frames // 2)
        else:
            uniform_indices = [int(i * (total_frames - 1) / (n - 1)) for i in range(n)]
            selected_indices.update(uniform_indices)

    # Sort indices chronologically
    sorted_indices = sorted(list(selected_indices))
    
    frame_paths = []
    temp_dir = tempfile.gettempdir()
    
    for i, idx in enumerate(sorted_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            out_path = os.path.join(temp_dir, f"frame_{os.path.basename(video_path)}_{i}_cv2_{idx}.jpg")
            cv2.imwrite(out_path, frame)
            if os.path.exists(out_path):
                frame_paths.append(out_path)
        else:
            logger.warning(f"OpenCV failed to read frame at index {idx}")
            
    cap.release()
    
    if not frame_paths:
        raise RuntimeError("OpenCV extraction failed to produce any frames.")
        
    logger.info(f"Frame extraction via OpenCV succeeded. Extracted {len(frame_paths)} frames.")
    return frame_paths