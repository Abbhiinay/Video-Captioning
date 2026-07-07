import os
import json
import logging
import requests
import tempfile

logger = logging.getLogger(__name__)

def load_tasks(path: str = "/input/tasks.json") -> list[dict]:
    """
    Loads tasks from a JSON file.
    Each task is: {"task_id": str, "video_url": str, "styles": list[str]}
    """
    if not os.path.exists(path):
        logger.warning(f"Tasks file not found at {path}. Returning empty list.")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Tasks file must contain a JSON array of task objects.")
            return data
    except Exception as e:
        logger.error(f"Error loading tasks from {path}: {e}")
        raise

def save_results(results: list[dict], path: str = "/output/results.json"):
    """
    Saves the list of results to a JSON file.
    Creates directories if they do not exist.
    """
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved {len(results)} results to {path}.")
    except Exception as e:
        logger.error(f"Error saving results to {path}: {e}")
        raise

def download_video(url: str) -> str:
    """
    Downloads a video from a remote URL to a local temporary file and returns its path.
    """
    temp_dir = tempfile.gettempdir()
    
    # Extract extension or default to .mp4
    clean_url = url.split("?")[0] if "?" in url else url
    _, ext = os.path.splitext(clean_url)
    if not ext or len(ext) > 5:
        ext = ".mp4"

    try:
        temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False, dir=temp_dir)
        temp_path = temp_file.name
        temp_file.close() # Close so we can write to it
    except Exception as e:
        logger.error(f"Could not create temporary file for download: {e}")
        raise

    logger.info(f"Downloading video from {url} to {temp_path}...")
    try:
        # Stream the download to avoid holding large files in memory
        with requests.get(url, stream=True, timeout=60.0) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return temp_path
    except Exception as e:
        logger.error(f"Failed to download video from {url}: {e}")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise RuntimeError(f"Failed to download video from {url}: {e}") from e