import os
import time
import base64
import logging
import requests

from config.settings import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

def analyze_video_frames(frame_paths: list[str], transcript: str | None, prompt: str) -> dict:
    """
    Sends frames and prompt to Gemini API, expecting a structured JSON response.
    Handles rate limiting and transient errors with exponential backoff.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is missing")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    parts = []
    
    full_prompt = prompt
    if transcript:
        full_prompt += f"\n\nVideo Transcript:\n{transcript}"
    parts.append({"text": full_prompt})

    for path in frame_paths:
        if not os.path.exists(path):
            logger.warning(f"Frame file not found: {path}, skipping.")
            continue
        try:
            with open(path, "rb") as f:
                img_data = f.read()
                base64_data = base64.b64encode(img_data).decode("utf-8")
                parts.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": base64_data
                    }
                })
        except Exception as e:
            logger.error(f"Error encoding frame image {path}: {e}")
            raise

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    headers = {"Content-Type": "application/json"}

    max_attempts = 4
    delay = 2.0
    for attempt in range(max_attempts):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60.0)
            if response.status_code == 200:
                data = response.json()
                try:
                    text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                    return text_content
                except (KeyError, IndexError) as parse_err:
                    raise RuntimeError(f"Unexpected response structure from Gemini API: {data}") from parse_err
            
            if response.status_code in [429, 500, 502, 503, 504]:
                if attempt < max_attempts - 1:
                    logger.warning(f"Gemini API returned status {response.status_code}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2.0
                    continue
            
            response.raise_for_status()
        except requests.RequestException as e:
            if attempt < max_attempts - 1:
                logger.warning(f"Gemini API request failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2.0
            else:
                raise e

    raise RuntimeError("Failed to analyze frames after multiple attempts.")
