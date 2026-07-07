import os
import tempfile
import logging

logger = logging.getLogger(__name__)

def extract_frames(video_path: str, n: int = 5) -> list[str]:
    """
    Samples n frames evenly spaced across the video duration.
    Attempts to use ffmpeg-python first. If ffmpeg is not installed on the system,
    falls back to using OpenCV (cv2) for robustness.
    Saves frames as temporary JPEGs and returns their paths.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at {video_path}")
        
    if n <= 0:
        return []

    # 1. Try ffmpeg-python first
    try:
        import ffmpeg
        logger.info("Attempting frame extraction using ffmpeg-python...")
        probe = ffmpeg.probe(video_path)
        
        # Get duration
        duration = None
        if 'format' in probe and 'duration' in probe['format']:
            duration = float(probe['format']['duration'])
        else:
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if video_stream and 'duration' in video_stream:
                duration = float(video_stream['duration'])
                
        if duration is None:
            raise ValueError("Could not determine video duration from probe")
            
        if n == 1:
            timestamps = [duration / 2.0]
        else:
            timestamps = [i * duration / (n - 1) for i in range(n)]
            if timestamps[-1] >= duration:
                timestamps[-1] = max(0.0, duration - 0.1)
                
        frame_paths = []
        temp_dir = tempfile.gettempdir()
        
        for i, ts in enumerate(timestamps):
            out_path = os.path.join(temp_dir, f"frame_{os.path.basename(video_path)}_{i}_{int(ts*1000)}.jpg")
            (
                ffmpeg
                .input(video_path, ss=ts)
                .output(out_path, vframes=1)
                .run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
            )
            if os.path.exists(out_path):
                frame_paths.append(out_path)
                
        if len(frame_paths) == n:
            logger.info("Frame extraction via ffmpeg-python succeeded.")
            return frame_paths
        else:
            logger.warning("ffmpeg-python did not extract all requested frames, falling back to OpenCV.")
    except Exception as e:
        logger.warning(f"ffmpeg-python extraction failed or ffmpeg not in PATH: {e}. Falling back to OpenCV.")

    # 2. Fallback to OpenCV
    try:
        import cv2
        logger.info("Attempting frame extraction using OpenCV...")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"OpenCV failed to open video file: {video_path}")
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            raise ValueError("OpenCV reports total frames <= 0")
            
        if n == 1:
            indices = [total_frames // 2]
        else:
            indices = [int(i * (total_frames - 1) / (n - 1)) for i in range(n)]
            
        frame_paths = []
        temp_dir = tempfile.gettempdir()
        
        for i, idx in enumerate(indices):
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
    except Exception as cv_err:
        logger.error(f"OpenCV frame extraction also failed: {cv_err}")
        raise RuntimeError(f"All frame extraction methods failed: {cv_err}") from cv_err