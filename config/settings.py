import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Models
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Video Processing Settings
FRAME_COUNT = int(os.getenv("FRAME_COUNT", "5"))
ENABLE_SCENE_DETECTION = os.getenv("ENABLE_SCENE_DETECTION", "true").lower() == "true"
ENABLE_AUDIO = os.getenv("ENABLE_AUDIO", "false").lower() == "true"

# IO Paths
INPUT_TASKS_PATH = os.getenv("INPUT_TASKS_PATH", "/input/tasks.json")
OUTPUT_RESULTS_PATH = os.getenv("OUTPUT_RESULTS_PATH", "/output/results.json")
