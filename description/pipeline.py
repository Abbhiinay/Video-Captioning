import os
import logging
from description.utils.io import download_video
from src.preprocessing.extract_frames import extract_frames
from src.perception.describe_video import describe_video
from description.style_engine.generate_captions import generate_captions

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

        # Step 2: Extract Frames (default N=5)
        try:
            # We sample 5 frames by default
            frame_paths = extract_frames(video_path, n=5)
        except Exception as e:
            logger.error(f"Task {task_id}: Frame extraction failed: {e}")
            return result

        # Step 3: Describe Video (Generates neutral description. Optional transcript is None here)
        try:
            description = describe_video(frame_paths, transcript=None)
        except Exception as e:
            logger.error(f"Task {task_id}: Factual description generation failed: {e}")
            return result

        # Step 4: Rewrite description in requested styles
        if not description:
            logger.error(f"Task {task_id}: Visual description was empty.")
            return result

        try:
            captions = generate_captions(description, styles)
            for style in styles:
                result["captions"][style] = captions.get(style, "")
        except Exception as e:
            logger.error(f"Task {task_id}: Style engine generation failed: {e}")

    except Exception as e:
        logger.error(f"Task {task_id}: Unexpected error in pipeline: {e}")
    finally:
        # Cleanup temporary files to prevent disk usage spikes
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