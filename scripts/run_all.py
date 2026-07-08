import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root is in Python path so absolute imports work when run as script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env if present

from description.utils.io import load_tasks, save_results
from description.pipeline import process_task

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    # 1. Validate environment variables (fail fast)
    gemini_key = os.getenv("GEMINI_API_KEY")

    missing = []
    if not gemini_key:
        missing.append("GEMINI_API_KEY")

    if missing:
        logger.error(f"Initialization Failed: Missing required environment variable(s): {', '.join(missing)}")
        sys.exit(1)

    # 2. Get input and output paths (defaulting to standard locations)
    input_path = os.getenv("INPUT_TASKS_PATH", "/input/tasks.json")
    output_path = os.getenv("OUTPUT_RESULTS_PATH", "/output/results.json")

    logger.info(f"Loading tasks from {input_path}...")
    try:
        tasks = load_tasks(input_path)
    except Exception as e:
        logger.error(f"Failed to load tasks from {input_path}: {e}")
        sys.exit(1)

    if not tasks:
        logger.warning("No tasks found to process.")
        # Ensure we write a valid, empty JSON array to output file
        try:
            save_results([], output_path)
        except Exception:
            pass
        sys.exit(0)

    # 3. Process tasks with a thread pool to respect rate limits and 10-minute budget.
    from config.settings import MAX_WORKERS
    results = []

    logger.info(f"Processing {len(tasks)} tasks concurrently with max_workers={MAX_WORKERS}...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit tasks
        future_to_task = {executor.submit(process_task, task): task for task in tasks}
        
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            task_id = task.get("task_id")
            try:
                result = future.result()
                results.append(result)
                
                requested_styles = task.get("styles", [])
                captions = result.get("captions", {})
                
                # Check if all requested styles are present and non-empty for logging purposes
                missing_or_empty = []
                for s in requested_styles:
                    if not captions.get(s):
                        missing_or_empty.append(s)
                        
                if missing_or_empty:
                    logger.warning(f"Task {task_id} generated empty captions for styles: {missing_or_empty}")
                else:
                    logger.info(f"Task {task_id} processed successfully.")
            except Exception as e:
                logger.error(f"Unexpected exception processing task {task_id}: {e}")
                # Append fallback empty result structure
                results.append({
                    "task_id": task_id,
                    "captions": {s: "" for s in task.get("styles", [])}
                })

    # Sort results by the order of task_id in input to keep order consistent
    task_order = {t.get("task_id"): index for index, t in enumerate(tasks)}
    results.sort(key=lambda x: task_order.get(x.get("task_id"), 999))

    # 4. Save results (best effort)
    logger.info(f"Saving final results to {output_path}...")
    try:
        save_results(results, output_path)
    except Exception as e:
        logger.error(f"Failed to write results file to {output_path}: {e}")
        sys.exit(1)

    # 5. Exit with correct code
    # Validate the written results.json file meets structure requirements
    import json
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        if not isinstance(saved_data, list):
            raise ValueError("results.json root is not a list")
            
        task_map = {t.get("task_id"): t for t in tasks}
        for item in saved_data:
            if not isinstance(item, dict):
                raise ValueError("Result item is not a dictionary")
            if "task_id" not in item or "captions" not in item:
                raise ValueError("Result item missing 'task_id' or 'captions'")
            
            tid = item["task_id"]
            if tid not in task_map:
                raise ValueError(f"Unknown task_id in results: {tid}")
                
            requested_styles = task_map[tid].get("styles", [])
            captions = item["captions"]
            if not isinstance(captions, dict):
                raise ValueError(f"captions for {tid} is not a dictionary")
                
            for style in requested_styles:
                if style not in captions:
                    raise ValueError(f"Missing requested style '{style}' in captions for {tid}")
                    
        logger.info("Batch processing completed successfully. All outputs validated.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Validation of results.json failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()