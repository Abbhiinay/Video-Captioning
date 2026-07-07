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

    # 3. Process tasks with a small thread pool to respect rate limits and 10-minute budget.
    # A concurrency of 3 tasks keeps parallel requests reasonable for API limits.
    max_workers = 3
    results = []
    failed_any = False

    logger.info(f"Processing {len(tasks)} tasks concurrently with max_workers={max_workers}...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks
        future_to_task = {executor.submit(process_task, task): task for task in tasks}
        
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            task_id = task.get("task_id")
            try:
                result = future.result()
                results.append(result)
                
                # Check if this task produced empty results for all requested styles (indicates failure)
                requested_styles = task.get("styles", [])
                captions = result.get("captions", {})
                if requested_styles and all(captions.get(s) == "" for s in requested_styles):
                    failed_any = True
                    logger.warning(f"Task {task_id} failed to generate any captions.")
                else:
                    logger.info(f"Task {task_id} processed successfully.")
            except Exception as e:
                failed_any = True
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
    if failed_any:
        logger.error("Batch processing finished with some failures. Exiting non-zero.")
        sys.exit(1)
    else:
        logger.info("Batch processing completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()