import os
import sys
import json
import logging
from dotenv import load_dotenv
import requests

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def rate_caption_with_gemini(style: str, caption: str, video_context: str | None = None) -> dict:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY missing"}
        
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    headers = {"Content-Type": "application/json"}
    
    context_str = f"Scene Ground Truth Description: {video_context}\n" if video_context else ""
    
    prompt = (
        "You are an AI evaluator. Evaluate whether the caption fits the requested style and accurately describes the scene.\n"
        "Use the provided Scene Ground Truth Description to verify factual accuracy.\n"
        "Evaluate based on semantic match: if the primary physical actions, subjects, and objects in the caption match the ground truth "
        "description, award a high caption_accuracy score (0.9 to 1.0). Accept creative tech or everyday metaphors (e.g. comparing "
        "a kitten walking to a git push) as factually accurate since these are required for stylistic expression.\n"
        "Output ONLY a valid JSON object with EXACTLY these keys:\n"
        "{\n"
        '  "caption_accuracy": <float 0.0 to 1.0>,\n'
        '  "style_match": <float 0.0 to 1.0>,\n'
        '  "overall": <float 0.0 to 1.0>,\n'
        '  "reason": "<brief note>"\n'
        "}\n\n"
        f"{context_str}"
        f"Style Requested: {style}\n"
        f"Caption: {caption}"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        
        candidates = data.get("candidates") or []
        if not candidates:
            raise KeyError("candidates list is empty")
        content = candidates[0].get("content") or {}
        parts_res = content.get("parts") or []
        if not parts_res:
            raise KeyError("parts list is empty")
        text = parts_res[0].get("text", "").strip()

        # Clean potential markdown fences
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            
        parsed = json.loads(text)
        return {
            "caption_accuracy": parsed.get("caption_accuracy", 0.0),
            "style_match": parsed.get("style_match", 0.0),
            "overall": parsed.get("overall", 0.0),
            "reason": parsed.get("reason", "unknown")
        }
    except Exception as e:
        return {"error": f"Failed to call evaluation model: {e}"}

def main():
    results_path = os.getenv("OUTPUT_RESULTS_PATH", "data/outputs/results.json")
    if not os.path.exists(results_path):
        print(f"Results file not found at {results_path}")
        sys.exit(1)
        
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    print("=== Caption Self-Evaluation (Gemini) ===")
    for task in results:
        task_id = task.get("task_id")
        captions = task.get("captions", {})
        
        # Use the formal caption as the ground truth context for other styles
        video_context = captions.get("formal")
            
        print(f"\nTask: {task_id}")
        for style, caption in captions.items():
            if not caption:
                print(f"  [{style}]: EMPTY")
                continue
                
            try:
                # If evaluating the formal caption itself, pass it as both context and caption
                rating = rate_caption_with_gemini(style, caption, video_context)
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