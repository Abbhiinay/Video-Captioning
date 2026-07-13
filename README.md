# Video Captioning Agent

An AI agent that watches a video clip and generates captions in multiple styles.

Built on a **single unified Fireworks VLM API call** that performs visual
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
Fireworks VLM            (Single API call — structured JSON output)
     │
     ▼
JSON Validation & Repair (Key validation · Retry-on-bad-JSON · Graceful fallback)
     │
     ▼
results.json             { task_id, captions: { formal, sarcastic, … } }
```

### Single-Pass Design

The pipeline consolidates visual perception and all four caption styles into
one Fireworks VLM API call. This means:

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
- **JSON repair retry**: If the VLM returns malformed JSON, a targeted repair
  prompt is sent automatically. If that also fails, a safe default is returned gracefully.

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
FIREWORKS_API_KEY=your_fireworks_api_key_here
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1
FIREWORKS_VISION_MODEL=accounts/fireworks/models/minimax-m3
FIREWORKS_FALLBACK_VISION_MODEL=accounts/fireworks/models/qwen3p7-plus

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

### 1. Build the Docker Image
Ensure you are in the project root folder:
```bash
docker build -t video-captioning:latest .
```

### 2. Run the Container
Run the container without passing any environment variables or API keys, as they are baked directly into the image:
```powershell
docker run -v "${PWD}/data:/input" -v "${PWD}/data/outputs:/output" video-captioning:latest
```
*(Or on Linux/macOS, replace `${PWD}` with `$(pwd)`)*

### 3. Pull and Run from Docker Hub (Alternative)
If you wish to pull the pre-built, self-contained image directly from Docker Hub rather than building it locally:
```bash
# Pull the image
docker pull abbhiinay/video-captioning:latest

# Run the container (PowerShell)
docker run -v "${PWD}/data:/input" -v "${PWD}/data/outputs:/output" abbhiinay/video-captioning:latest
```

---

## Web Application (Frontend & Backend)

The project includes an interactive web application consisting of a React + Vite frontend and a FastAPI backend server.

### 1. Run the FastAPI Backend Server
Open a terminal in the project root directory, activate your virtual environment, install API dependencies, and run:
```powershell
# Activate environment (Windows)
.venv\Scripts\activate

# Install backend dependencies
pip install -r api/requirements.txt

# Start the API server
uvicorn main:app --app-dir api --host 127.0.0.1 --port 8000 --reload
```

### 2. Run the Vite Frontend Client
Open a second terminal window, navigate to the `web` folder, and start the development server:
```powershell
# Navigate to frontend folder
cd web

# Install frontend dependencies
npm install

# Start the development server
npm run dev
```

### 3. Access the Web App
Open your browser and navigate to `http://localhost:5173/`. 
The frontend proxies requests starting with `/api` to the backend server running at `http://127.0.0.1:8000`. You can upload video files (.mp4, .webm, etc.) through the web UI and see live generated captions across all four styles.

---

## Project Structure

```
Video-Captioning/
├── api/                         # FastAPI Backend
│   ├── frame_extractor.py       # Async OpenCV frame extractor
│   ├── gemini_service.py        # Gemini interaction layer
│   ├── main.py                  # API endpoints (health, caption)
│   └── requirements.txt         # Backend API dependencies
├── web/                         # React + Vite Frontend
│   ├── public/                  # Static assets
│   ├── src/                     # Source files (App.jsx, components)
│   ├── vite.config.js           # Vite dev config with API proxy
│   ├── package.json             # Frontend node dependencies
│   └── README.md                # Vite specific documentation
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
