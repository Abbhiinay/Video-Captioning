# Video Captioning Agent

An AI agent that watches a video clip and generates captions in multiple styles.

Recently **refactored for extreme efficiency**, this agent now leverages a **single unified Gemini 2.5 Flash API call** to perform both visual perception and multi-style caption generation simultaneously.

---

## ⚡ Architecture Improvements & Token Savings

The pipeline was redesigned to achieve:
- **~70% Token Reduction:** Eliminated redundant context windows (previously 5 API calls per video, now just 1).
- **Lower Latency:** One network request instead of a sequential waterfall of 5 requests.
- **Hybrid Scene Detection:** Uses OpenCV to calculate histogram differences, extracting both uniform intervals and distinct scene changes.
- **Strict JSON Enforcement:** Leverages Gemini's native `application/json` output to guarantee perfect schema adherence without intermediate parsers.

### How It Works (Before vs After)

**Before (Legacy Pipeline):**
```
Video → Extract 5 Frames → Gemini (Perception) → Fireworks (Neutral Summary)
                                                 → Fireworks (Formal)
                                                 → Fireworks (Sarcastic)
                                                 → Fireworks (Humorous Tech)
                                                 → Fireworks (Humorous Non-Tech)
```
*(Total: 1 Gemini call + 5 Fireworks calls)*

**After (New Pipeline):**
```
Video
  ↓
Hybrid Frame Extraction (OpenCV Scene Detection)
  ↓
Gemini 2.5 Flash (Single API Call with strict JSON schema)
  ↓
Structured Output { video_understanding, captions: { formal, sarcastic, ... } }
  ↓
/output/results.json
```
*(Total: 1 Gemini call)*

---

## Supported Caption Styles

| Style | Description | Length Limit |
|---|---|---|
| `formal` | Objective, factual, concise, no emojis | Max 25 words |
| `sarcastic` | Witty, dry, playful exaggeration | Max 20 words |
| `humorous_tech` | Software engineering references (Git, Docker, etc.) | Max 20 words |
| `humorous_non_tech` | Relatable everyday humor (office, family, etc.) | Max 20 words |

---

## Setup & Configuration

### 1. Requirements
- Python **3.11+**
- (Optional) `ffmpeg` installed and on system PATH

### 2. Install dependencies
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and configure:
```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Model Configurations
GEMINI_MODEL=gemini-2.5-flash

# Video Processing Settings
FRAME_COUNT=5
ENABLE_SCENE_DETECTION=true
ENABLE_AUDIO=false
```

---

## Usage

### Batch Run (Production)

This is the primary mode. It reads from `/input/tasks.json` and writes to `/output/results.json`.

**1. Run the batch script:**
```bash
python scripts/run_all.py
```

Override paths if needed:
```bash
$env:INPUT_TASKS_PATH="data/tasks.json"
$env:OUTPUT_RESULTS_PATH="data/outputs/results.json"
python scripts/run_all.py
```

### Output Format
The resulting `/output/results.json` strictly matches the required submission format:
```json
[
  {
    "task_id": "v1",
    "captions": {
      "formal": "...",
      "sarcastic": "...",
      "humorous_tech": "...",
      "humorous_non_tech": "..."
    }
  }
]
```

---

## Docker

### Build the image
```bash
docker build -t video-captioning:latest .
```

### Run the container locally
```bash
docker run \
  -e GEMINI_API_KEY=your_key_here \
  -v $(pwd)/data:/input \
  -v $(pwd)/data/outputs:/output \
  video-captioning:latest
```

---

## Project Structure

```
Video-Captioning/
├── config/
│   └── settings.py              # Centralized environment configuration
├── description/
│   ├── pipeline.py              # End-to-end task orchestrator
│   ├── style_engine/
│   │   └── prompts.py           # Unified JSON prompt builder
│   └── utils/
│       ├── gemini_client.py     # Gemini REST API wrapper (application/json)
│       └── io.py                # Task loader, video downloader, result writer
├── src/
│   ├── perception/
│   │   └── analyze_video.py     # Invokes Gemini for perception + captions
│   └── preprocessing/
│       └── extract_frames.py    # Hybrid scene detection & sampling
├── scripts/
│   └── run_all.py               # Batch entry point
├── Dockerfile                   # Production Docker image
└── requirements.txt             # Python dependencies
```
