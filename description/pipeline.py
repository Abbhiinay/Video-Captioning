import os
import logging
from description.utils.io import download_video
from src.preprocessing.extract_frames import extract_frames
from src.perception.analyze_video import analyze_video
from config.settings import FRAME_COUNT

logger = logging.getLogger(__name__)

def process_task(task: dict) -> dict:
    """
    Orchestrates the captioning pipeline for a single video task.
    Catches all exceptions internally to prevent single task failures from crashing the batch.
    Ensures temporary video files and frames are cleaned up before exit.
    """
    task_id = task.get("task_id")
    video_url = task.get("video_url")
    styles = task.get("styles", [])

    logger.info(f"--- Starting Processing Task: {task_id} ---")
    
    # Initialize response structure with empty captions
    result = {
        "task_id": task_id,
        "captions": {style: "" for style in styles}
    }

    if not video_url:
        logger.error(f"Task {task_id} has no video_url.")
        return result

    video_path = None
    frame_paths = []

    try:
        # Step 1: Download Video
        try:
            video_path = download_video(video_url)
        except Exception as e:
            logger.error(f"Task {task_id}: Downloading video failed: {e}")
            return result

        # Step 2: Extract Frames
        try:
            frame_paths = extract_frames(video_path, n=FRAME_COUNT)
        except Exception as e:
            logger.error(f"Task {task_id}: Frame extraction failed: {e}")
            return result

        # Step 3: Analyze Video and Generate Captions in one API call
        try:
            # We pass transcript=None for now (audio support can be integrated here later if needed)
            analysis_result = analyze_video(frame_paths, transcript=None, styles=styles)
            
            # Extract captions from the structured JSON
            captions = analysis_result.get("captions", {})
            for style in styles:
                result["captions"][style] = captions.get(style, "")
                
            # Log video understanding for debugging/insights
            video_understanding = analysis_result.get("video_understanding", {})
            logger.debug(f"Task {task_id} video understanding: {video_understanding}")
                
        except Exception as e:
            logger.error(f"Task {task_id}: Analysis and caption generation failed: {e}")
            return result

    except Exception as e:
        logger.error(f"Task {task_id}: Unexpected error in pipeline: {e}")
    finally:
        # Cleanup temporary files
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                logger.info(f"Cleaned up temporary video file: {video_path}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to delete temp video file {video_path}: {cleanup_err}")

        for fpath in frame_paths:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to delete temp frame file {fpath}: {cleanup_err}")
        if frame_paths:
            logger.info(f"Cleaned up {len(frame_paths)} temporary frames.")

    logger.info(f"--- Finished Processing Task: {task_id} ---")
    return result