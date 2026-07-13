import os
import sys
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def rate_caption_with_fireworks(style: str, caption: str, video_context: str | None = None) -> dict:
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        return {"error": "FIREWORKS_API_KEY missing"}
        
    base_url = os.getenv("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")
    model = os.getenv("FIREWORKS_VISION_MODEL", "accounts/fireworks/models/minimax-m3")
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
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
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        text = response.choices[0].message.content.strip()
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
        
    print("=== Caption Self-Evaluation (Fireworks) ===")
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
                rating = rate_caption_with_fireworks(style, caption, video_context)
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