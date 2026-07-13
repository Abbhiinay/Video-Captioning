import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "")

# ── Models ────────────────────────────────────────────────────────────────────
FIREWORKS_BASE_URL = os.getenv("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1")
FIREWORKS_VISION_MODEL = os.getenv("FIREWORKS_VISION_MODEL", "accounts/fireworks/models/minimax-m3")
FIREWORKS_FALLBACK_VISION_MODEL = os.getenv(
    "FIREWORKS_FALLBACK_VISION_MODEL", "accounts/fireworks/models/qwen3p7-plus"
)

# ── Video Processing Settings ──────────────────────────────────────────────────
FRAME_COUNT = int(os.getenv("FRAME_COUNT", "5"))
ENABLE_SCENE_DETECTION = os.getenv("ENABLE_SCENE_DETECTION", "true").lower() == "true"
ENABLE_AUDIO = os.getenv("ENABLE_AUDIO", "false").lower() == "true"
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "3"))

# ── Generation Settings ────────────────────────────────────────────────────────
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
TOP_P = float(os.getenv("TOP_P", "0.8"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))

# ── IO Paths ───────────────────────────────────────────────────────────────────
INPUT_TASKS_PATH = os.getenv("INPUT_TASKS_PATH", "/input/tasks.json")
OUTPUT_RESULTS_PATH = os.getenv("OUTPUT_RESULTS_PATH", "/output/results.json")
