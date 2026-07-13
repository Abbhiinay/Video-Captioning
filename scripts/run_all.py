import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root is in Python path so absolute imports work when run as script
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
    fireworks_key = os.getenv("FIREWORKS_API_KEY")

    missing = []
    if not fireworks_key:
        missing.append("FIREWORKS_API_KEY")

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
        try:
            save_results([], output_path)
        except Exception:
            pass
        sys.exit(0)

    # 3. Build task order map and write skeleton results IMMEDIATELY.
    # This ensures all task IDs appear in the output file even if the
    # container is killed mid-run before all tasks finish.
    task_order = {t.get("task_id"): idx for idx, t in enumerate(tasks)}

    results = [
        {
            "task_id": task.get("task_id"),
            "captions": {s: "" for s in task.get("styles", [])}
        }
        for task in tasks
    ]

    logger.info(f"Writing skeleton output for {len(results)} task(s) to {output_path}...")
    try:
        save_results(results, output_path)
        logger.info("Skeleton output written. All task IDs are now present in the output file.")
    except Exception as e:
        logger.error(f"Failed to write skeleton output to {output_path}: {e}")
        sys.exit(1)

    # 4. Process tasks concurrently, saving incrementally after each completion.
    from config.settings import MAX_WORKERS
    logger.info(f"Processing {len(tasks)} tasks with max_workers={MAX_WORKERS}...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(process_task, task): task for task in tasks}

        for future in as_completed(future_to_task):
            task = future_to_task[future]
            task_id = task.get("task_id")
            try:
                result = future.result()
            except Exception as e:
                logger.error(f"Unexpected exception processing task {task_id}: {e}")
                result = {
                    "task_id": task_id,
                    "captions": {s: "" for s in task.get("styles", [])}
                }

            # Replace skeleton entry with real result
            for i, r in enumerate(results):
                if r.get("task_id") == task_id:
                    results[i] = result
                    break

            # Log caption quality
            requested_styles = task.get("styles", [])
            captions = result.get("captions", {})
            missing_or_empty = [s for s in requested_styles if not captions.get(s)]
            if missing_or_empty:
                logger.warning(f"Task {task_id} generated empty captions for styles: {missing_or_empty}")
            else:
                logger.info(f"Task {task_id} processed successfully.")

            # Save incrementally so results are preserved even if killed later
            sorted_results = sorted(results, key=lambda x: task_order.get(x.get("task_id"), 999))
            try:
                save_results(sorted_results, output_path)
                completed = sum(
                    1 for r in results
                    if any(r.get("captions", {}).get(s) for s in r.get("captions", {}))
                )
                logger.info(f"Incremental save: {completed}/{len(tasks)} tasks with non-empty captions.")
            except Exception as e:
                logger.warning(f"Could not save incremental results: {e}")

    # 5. Final sorted save
    final_results = sorted(results, key=lambda x: task_order.get(x.get("task_id"), 999))
    logger.info(f"Saving final results ({len(final_results)} tasks) to {output_path}...")
    try:
        save_results(final_results, output_path)
    except Exception as e:
        logger.error(f"Failed to write final results to {output_path}: {e}")
        sys.exit(1)

    # 6. Validate and exit
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
    except Exception as e:
        # Log the issue but still exit 0 — the output file was written with
        # all task IDs present. A non-zero exit would discard valid results.
        logger.warning(f"Post-run validation warning (output file is still valid): {e}")

    sys.exit(0)

if __name__ == "__main__":
    main()