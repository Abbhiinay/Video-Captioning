import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

FIREWORKS_MODEL = "accounts/fireworks/models/llama-v3p3-70b-instruct"

def complete(system_prompt: str, user_prompt: str, model: str = None, max_tokens: int = 512) -> str:
    """
    Calls the Fireworks OpenAI-compatible endpoint with exponential backoff on transient errors.
    """
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        raise ValueError("FIREWORKS_API_KEY environment variable is missing")

    if model is None:
        model = os.getenv("FIREWORKS_LLM_MODEL", FIREWORKS_MODEL)

    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens
    }

    max_attempts = 3
    delay = 1.0
    for attempt in range(max_attempts):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                try:
                    msg = data["choices"][0]["message"]
                    # llama-v3p3-70b-instruct returns text in "content" only (no separate reasoning_content channel)
                    content = msg.get("content") or ""
                    return content
                except (KeyError, IndexError) as parse_err:
                    raise RuntimeError(f"Unexpected response structure from Fireworks API: {data}") from parse_err

            # Retry on rate limit (429) or transient server errors (500, 502, 503, 504)
            if response.status_code in [429, 500, 502, 503, 504]:
                if attempt < max_attempts - 1:
                    logger.warning(f"Fireworks API returned status {response.status_code}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2.0
                    continue

            # Non-transient errors or final attempt failure
            response.raise_for_status()
        except requests.RequestException as e:
            if attempt < max_attempts - 1:
                logger.warning(f"Fireworks API request failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2.0
            else:
                raise e

    raise RuntimeError("Failed to get completions from Fireworks after multiple attempts.")