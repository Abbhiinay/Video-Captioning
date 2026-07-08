import os
import sys
import json
import requests
import logging
from dotenv import load_dotenv

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def rate_caption_with_gemini(style: str, caption: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY missing"}
        
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = (
        "You are an AI evaluator. Evaluate whether the caption fits the requested style and accurately describes a scene.\n"
        "Output ONLY a valid JSON object with EXACTLY these keys:\n"
        "{\n"
        '  "caption_accuracy": <float 0.0 to 1.0>,\n'
        '  "style_match": <float 0.0 to 1.0>,\n'
        '  "overall": <float 0.0 to 1.0>,\n'
        '  "reason": "<brief note>"\n'
        "}\n\n"
        f"Style Requested: {style}\nCaption: {caption}"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    try:
        parsed = json.loads(text)
        return {
            "caption_accuracy": parsed.get("caption_accuracy", 0.0),
            "style_match": parsed.get("style_match", 0.0),
            "overall": parsed.get("overall", 0.0),
            "reason": parsed.get("reason", "unknown")
        }
    except Exception as e:
        return {"error": f"Failed to parse eval response: {e}"}

def main():
    results_path = os.getenv("OUTPUT_RESULTS_PATH", "data/outputs/results.json")
    if not os.path.exists(results_path):
        print(f"Results file not found at {results_path}")
        sys.exit(1)
        
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    print("=== Caption Self-Evaluation ===")
    for task in results:
        task_id = task.get("task_id")
        captions = task.get("captions", {})
        
        print(f"\nTask: {task_id}")
        for style, caption in captions.items():
            if not caption:
                print(f"  [{style}]: EMPTY")
                continue
                
            try:
                rating = rate_caption_with_gemini(style, caption)
                if "error" in rating:
                    print(f"  [{style}]: \"{caption}\"\n    -> Evaluation failed: {rating['error']}")
                else:
                    print(f"  [{style}]: \"{caption}\"\n"
                          f"    -> Acc: {rating['caption_accuracy']} | Style: {rating['style_match']} | Overall: {rating['overall']}\n"
                          f"    -> Reason: {rating['reason']}")
            except Exception as e:
                print(f"  [{style}]: \"{caption}\"\n    -> Evaluation failed: {e}")

if __name__ == "__main__":
    main()