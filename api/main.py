"""
main.py

FastAPI backend for the AI Video Caption Generator.

Endpoints:
  POST /api/caption  — Upload a video, extract frames, call Gemini, return captions.
  GET  /api/health   — Readiness check.
"""

import sys
import os

# Add project root to sys.path so sibling directories can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import logging
import tempfile
from datetime import datetime

import aiofiles
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from frame_extractor import extract_frames
from caption_service import generate_captions

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CaptionAI API",
    description="AI-powered multi-style video caption generator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
FRAME_COUNT = int(os.getenv("FRAME_COUNT", "5"))
MAX_UPLOAD_MB = 100
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "outputs")
STYLES = ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]


@app.get("/api/health")
async def health():
    """Readiness check."""
    return {
        "status": "ok",
        "model": os.getenv("FIREWORKS_VISION_MODEL", "accounts/fireworks/models/minimax-m3"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/caption")
async def caption_video(video: UploadFile = File(...)):
    """
    Upload a video file, extract frames, call Gemini for multi-style
    caption generation, save results, and return JSON.
    """
    # ── Validate file type ────────────────────────────────────────────
    allowed_types = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"}
    if video.content_type and video.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format: {video.content_type}. Accepted: MP4, WebM, MOV.",
        )

    # ── Save uploaded file to temp location using aiofiles ────────────
    suffix = ".mp4"
    if video.filename:
        _, ext = os.path.splitext(video.filename)
        if ext:
            suffix = ext

    video_path = None
    frame_paths: list[str] = []

    try:
        # Write upload to temp file asynchronously (non-blocking)
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        video_path = tmp.name
        tmp.close()

        total_bytes = 0
        async with aiofiles.open(video_path, "wb") as f:
            while True:
                chunk = await video.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {MAX_UPLOAD_MB}MB.",
                    )
                await f.write(chunk)

        logger.info(f"Uploaded {total_bytes / 1024 / 1024:.1f}MB to {video_path}")

        # ── Extract frames (runs in thread pool) ─────────────────────
        logger.info(f"Extracting {FRAME_COUNT} frames...")
        frame_paths = await extract_frames(video_path, n=FRAME_COUNT)
        logger.info(f"Extracted {len(frame_paths)} frame(s)")

        # ── Call Fireworks for captions ──────────────────────────────────
        logger.info("Calling Fireworks for caption generation...")
        result = generate_captions(frame_paths, styles=STYLES)

        captions = result.get("captions", {})
        video_understanding = result.get("video_understanding", {})

        # ── Save to results.json ─────────────────────────────────────
        try:
            os.makedirs(RESULTS_DIR, exist_ok=True)
            results_path = os.path.join(RESULTS_DIR, "results.json")

            result_entry = {
                "task_id": video.filename or "web_upload",
                "captions": captions,
                "video_understanding": video_understanding,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Append to or create results file
            existing = []
            if os.path.exists(results_path):
                try:
                    with open(results_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except (json.JSONDecodeError, IOError):
                    existing = []

            existing.append(result_entry)

            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            logger.info(f"Results saved to {results_path}")
        except Exception as save_err:
            logger.warning(f"Failed to save results.json: {save_err}")

        # ── Return to frontend ───────────────────────────────────────
        return {
            "captions": captions,
            "video_understanding": video_understanding,
            "filename": video.filename,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Caption generation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        # ── Cleanup temp files ───────────────────────────────────────
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except OSError:
                pass
        for fp in frame_paths:
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                except OSError:
                    pass
