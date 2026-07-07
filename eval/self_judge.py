import os
import sys
import json
import logging
from dotenv import load_dotenv

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

load_dotenv()

from description.utils.fireworks_client import complete

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

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
                
            system_prompt = (
                "You are an AI evaluator. Evaluate whether the caption fits the requested style on a scale of 1-5. "
                "Output ONLY a single line in the following format: [Score: X/5] - Reason: <brief note>"
            )
            user_prompt = f"Style Requested: {style}\nCaption: {caption}"
            
            try:
                rating = complete(system_prompt, user_prompt, max_tokens=256)
                print(f"  [{style}]: \"{caption}\"\n    -> {rating.strip()}")
            except Exception as e:
                print(f"  [{style}]: \"{caption}\"\n    -> Evaluation failed: {e}")

if __name__ == "__main__":
    main()