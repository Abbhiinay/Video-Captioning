# Video Captioning Agent

An AI agent that watches a video clip and generates captions in multiple styles.

Built on a **single unified Gemini 2.5 Flash API call** that performs visual
perception and multi-style caption generation simultaneously.

---

## Architecture Overview

```
Video Clip
     │
     ▼
Hybrid Frame Extraction  (OpenCV — uniform anchors + FPS-driven scene detection)
     │
     ▼
Gemini 2.5 Flash         (Single API call — structured JSON output)
     │
     ▼
JSON Validation & Repair (Key validation · Retry-on-bad-JSON · Graceful fallback)
     │
     ▼
results.json             { task_id, captions: { formal, sarcastic, … } }
```

### Single-Pass Design

The pipeline consolidates visual perception and all four caption styles into
one Gemini API call. This means:

- **Substantially fewer API calls** compared to a sequential per-style approach.
- **Reduced latency** — one network round-trip instead of a waterfall.
- **Reduced token usage** — video context is transmitted once, not once per style.


## Caption Styles

| Style | Description | Length |
|---|---|---|
| `formal` | Objective, factual, single sentence | 15–18 words (max 20) |
| `sarcastic` | Witty, dry, playful exaggeration | Max 20 words |
| `humorous_tech` | Software engineering metaphors anchored to visible content | Max 20 words |
| `humorous_non_tech` | Relatable everyday humor anchored to visible content | Max 20 words |

### Quality Guarantees

- **Anti-hallucination**: The prompt explicitly forbids inventing objects, people,
  locations, or actions not visible in the frames. Uncertain elements are described
  as "unknown".
- **Fact consistency**: All four captions describe the same scene — only tone
  differs. No style may introduce new facts or assumptions.
- **Grounded humor**: Humorous captions must reference at least one specific
  visible object or action from the video. Generic reusable jokes are rejected
  by prompt design.
- **Apparent emotion only**: The `apparent_emotion` field describes visible
  facial expressions or body language — never inferred internal states.
- **JSON repair retry**: If Gemini returns malformed JSON, a targeted repair
  prompt is sent automatically. If that also fails, an empty-caption result
  is returned gracefully — the batch never crashes.

---

## Setup

### Requirements
- Python **3.11+**
- `ffmpeg` installed and on system PATH (optional, used by some codecs)

### 1. Install dependencies
```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt
```

### 2. Configure environment
Copy `.env.example` to `.env` and fill in your values:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

FRAME_COUNT=5
ENABLE_SCENE_DETECTION=true
ENABLE_AUDIO=false
```

> [!IMPORTANT]
> **Security Reminder:**
> - Never commit your `.env` file to version control.
> - Use `.env.example` as a template for other environments.
> - Rotate your API keys immediately if they are ever exposed.
> - Do not print or log secrets in your application logs.


---

## Usage

### Batch Run (Production)

Reads from `/input/tasks.json`, writes to `/output/results.json`.

```bash
python scripts/run_all.py
```

Override paths:
```bash
$env:INPUT_TASKS_PATH="data/tasks.json"
$env:OUTPUT_RESULTS_PATH="data/outputs/results.json"
python scripts/run_all.py
```

### Output Format

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

```bash
# Build
docker build -t video-captioning:latest .

# Run
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
│   └── settings.py              # Centralised environment configuration
├── description/
│   ├── pipeline.py              # End-to-end task orchestrator
│   ├── style_engine/
│   │   └── prompts.py           # Unified JSON prompt builder + repair prompt
│   └── utils/
│       ├── gemini_client.py     # Gemini REST API wrapper (retries, JSON mode)
│       └── io.py                # Task loader, video downloader, result writer
├── src/
│   ├── perception/
│   │   └── analyze_video.py     # JSON parsing, retry, key validation, defaults
│   └── preprocessing/
│       └── extract_frames.py    # Hybrid FPS-driven scene detection & sampling
├── scripts/
│   └── run_all.py               # Batch entry point (ThreadPoolExecutor)
├── docs/
│   ├── architechture.md         # Architecture design decisions
│   ├── phases.md                # Build phase log
│   └── submission.md            # Integration walkthrough & verification
├── Dockerfile                   # Production Docker image
└── requirements.txt             # Python dependencies
```
