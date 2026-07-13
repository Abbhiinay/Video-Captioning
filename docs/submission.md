# Integration Walkthrough — Video Captioning Pipeline

This document details the completed implementation and verification steps across
each build phase of the video captioning integration.

---

## Implemented Steps by Phase

### Phase 0 — Setup & Spike
- Installed required Python packages (`opencv-python`, `requests`, `python-dotenv`, `pyyaml`, `pytest`, `openai`, `pydantic`).
- Set up local development environment and created a `.env` file for API keys.
- Configured environment variables:
  - `FIREWORKS_API_KEY`: [Configured]
  - `FIREWORKS_BASE_URL`: `https://api.fireworks.ai/inference/v1`
  - `FIREWORKS_VISION_MODEL`: `accounts/fireworks/models/minimax-m3`
  - `FIREWORKS_FALLBACK_VISION_MODEL`: `accounts/fireworks/models/qwen3p7-plus`
  - `FRAME_COUNT`: `5`
  - `ENABLE_SCENE_DETECTION`: `true`

### Phase 1 — Core Architecture & Perception Pipeline
- **Hybrid Frame Extraction (`extract_frames.py`)**: Implemented hybrid extraction.
  Samples candidate frames at a temporal interval driven by the video's actual FPS
  (~0.5 s per sample). Calculates OpenCV histogram differences to identify
  scene-change frames and combines them with 3 evenly-spaced anchor frames.
- **Fireworks VLM Client (`analyze_video.py`)**: OpenAI SDK client integration targeting the Fireworks AI endpoints. Enforces raw JSON output mode.
  Automatic fallback logic from the primary model `minimax-m3` to the secondary model `qwen3p7-plus` if the primary model fails.
- **Unified Video Analysis**: Single unified call to the Fireworks VLM. Receives a structured JSON payload containing video understanding metadata and all 4 caption styles simultaneously.

### Phase 2 — Prompts & Constraints
- **Prompt Builder (`prompts.py`)**: Highly constrained unified prompt enforcing
  per-style word limits, format rules, and the anti-hallucination and
  fact-consistency guarantees described below.
- **Repair Prompt**: `get_repair_prompt()` generates a targeted second prompt
  when the primary response is not valid JSON (see Phase 5 — JSON Robustness).

### Phase 3 — Full Batch Run
- **Pipeline Orchestrator (`pipeline.py`)**: Manages download → frame extraction
  → perception/styling in one pass. Guarantees temporary file cleanup in a
  `finally` block. All stages are individually wrapped to prevent a single
  failure from crashing the batch.
- **Concurrency Coordinator (`scripts/run_all.py`)**: Entry point loading tasks
  from `/input/tasks.json` and processing them in parallel with a
  `ThreadPoolExecutor` (max_workers configurable via settings.py) to stay within API rate limits and the
  10-minute runtime budget.
- **Dockerfile**: `python:3.11-slim` container, system `ffmpeg`, package
  dependencies, runs `run_all.py`. The built, self-contained image is published on Docker Hub as `abbhiinay/video-captioning:latest`.

### Phase 4 — Self-Eval & Iteration
- **Sanity Checks (`eval/self_judge.py`)**: Automated judge script calling the Fireworks VLM to score generated captions (0.0 to 1.0 scale) for style alignment using the formal caption as the ground-truth scene context.
- **Prompt Tightening**: Prompt constraints were refined based on self-eval
  feedback to eliminate planning preambles and style drift.

### Phase 5 — Production Hardening

#### JSON Robustness (Task 1 & 2)
The pipeline now handles malformed VLM responses in three layers:
1. **Strip markdown fences** — removes any accidental ` ```json ``` ` wrapping.
2. **Parse normally** — attempts `json.loads()` on the cleaned text.
3. **Repair-prompt retry** — if parsing fails, a second VLM call is made with
   an explicit repair prompt that shows the bad response and requests clean JSON.
4. **Graceful fallback** — if the retry also fails, a safe backup description is generated.
   The batch continues. No exception propagates out of `process_task`.

After parsing, `_validate_and_patch()` ensures:
- `captions.formal`, `captions.sarcastic`, `captions.humorous_tech`,
  `captions.humorous_non_tech` all exist.
- All `video_understanding` fields exist with safe defaults.
- No `KeyError` is ever raised.
- Automatic word count truncation (retains the first 20 words) ensures captions are never blanked out due to minor formatting deviations.
- No `KeyError` is ever raised.

#### Anti-Hallucination Prompt (Task 3)
The prompt explicitly requires Gemini to:
- Only describe directly visible content.
- Never invent objects, people, actions, or locations.
- Return "unknown" for anything unclear.

This reduces confident confabulation in ambiguous or sparse visual content —
a known failure mode for vision-language models on short video clips.

#### Fact Consistency (Task 4)
All four captions must describe the same scene. Only tone varies between styles.
The prompt forbids any style from introducing new facts, new objects, new people,
or assumptions not visible in the frames.

#### Grounded Humor (Task 5)
Generic one-liners that could apply to any video are explicitly prohibited.
Each humorous caption must reference at least one specific visible object or
action from the video. This materially improves caption quality and relevance.

#### Formal Caption Length (Task 6 & 7)
Formal captions: 15–18 words, hard max 20. Every caption style: exactly one
sentence. These constraints were strengthened from the previous "max 25 words"
with no sentence count guarantee.

#### Clean Output (Task 8)
The prompt explicitly forbids markdown, quotes, bullet points, hashtags, emojis,
caption labels, and numbering from appearing in caption values.

#### camera_motion (Task 9)
`camera_motion` is now always present in `video_understanding`. Allowed values:
`static | pan | tilt | zoom | tracking | handheld | unknown`.
Values outside this set are normalised to "unknown" by post-parse validation.

#### apparent_emotion (Task 10)
The `emotion` field is replaced by `apparent_emotion`. The VLM is instructed to
describe only visible facial expressions or body language — never to infer
internal emotional states. If no person is visible or expression is ambiguous,
"unknown" is returned.

#### Documentation Accuracy (Task 11)
Unverified quantitative claims ("70% token reduction", "75% token reduction")
have been removed from all documentation. They are replaced with accurate
qualitative descriptions: "substantially fewer API calls", "reduced latency",
"reduced token usage".

#### FPS-Driven Frame Sampling (Task 12)
Scene-detection candidates are now sampled at ~0.5 s intervals scaled to the
video's actual FPS, replacing the previous fixed 30-frame cap. This scales
correctly across different video lengths and frame rates.

#### Improved Logging (Task 13)
Every pipeline stage logs:
- Selected frame indices and scene-change indices.
- Number of candidate frames evaluated during scene detection.
- Retry and JSON repair attempt counts.
- Caption generation success with key video_understanding fields.

#### Defensive Coding (Task 14)
All dictionary lookups use `.get()` with explicit defaults. No bare `KeyError`
or `IndexError` can escape from any module.

### Phase 6 — Interactive Web Application & API
- **FastAPI Server (`api/main.py`)**: Exposes `GET /api/health` for server diagnostics and `POST /api/caption` to handle dynamic, real-time video uploads, async frame extraction, and multi-style caption generation.
- **Async Processing**: Saves uploaded files asynchronously using `aiofiles` and runs CPU-bound OpenCV frame extraction via `asyncio.to_thread` to ensure non-blocking server performance.
- **React Frontend (`web/src/App.jsx`)**: Fully styled web interface displaying progress stages ("Uploading video", "Extracting frames", "Analyzing with Fireworks VLM") and mapping the returned JSON to stylized cards (formal, sarcastic, etc.).
- **Vite API Proxy**: Configured proxy in `web/vite.config.js` to route `/api/*` traffic transparently to the backend port `8000`.

---

## Verification Results

### Web Application & API Verification
- **API Verification**: Started the FastAPI backend server and successfully hit `GET /api/health` and `POST /api/caption` via terminal commands (`Invoke-RestMethod` / `curl`), receiving valid JSON responses.
- **Frontend & E2E Integration**: Launched the Vite dev server inside the `web` directory, loaded the browser page, and successfully generated multi-style captions through an upload, validating end-to-end functionality.

### Batch Run Verification
The pipeline successfully executed on the three specified test videos. The output
JSON file `data/outputs/results.json` matches the submission format:

```json
[
  {
    "task_id": "v1",
    "captions": {
      "formal": "Vehicular traffic navigates a multi-lane urban road in autumn, with yellow-foliaged trees and commercial signage visible along the roadside.",
      "sarcastic": "Oh wow, cars on a road — groundbreaking cinema that has truly never been captured before.",
      "humorous_tech": "Traffic queue hitting O(n) latency while the green light runs a background thread nobody asked for.",
      "humorous_non_tech": "Every car in the queue convinced the one lane ahead is definitely moving faster."
    }
  },
  {
    "task_id": "v2",
    "captions": {
      "formal": "An orange kitten walks across a sunlit forest floor, approaching the camera through dappled light.",
      "sarcastic": "Groundbreaking content: a kitten walking — truly the peak of cinematographic ambition.",
      "humorous_tech": "Kitten.walk() deployed to prod forest, zero tests written, cuteness metrics off the charts.",
      "humorous_non_tech": "Same energy as strutting into the kitchen like you own the place, and you do."
    }
  },
  {
    "task_id": "v3",
    "captions": {
      "formal": "A woman types at a keyboard in a contemporary office, with a monitor, desk plants, and overhead lighting visible.",
      "sarcastic": "A person at a desk, using a keyboard — peak drama unfolding before our eyes.",
      "humorous_tech": "Keyboard at maximum throughput, monitor showing unknown state, plants silently judging the git blame.",
      "humorous_non_tech": "Typing with full conviction while mentally already at lunch, desk plants as the only witnesses."
    }
  }
]
```

### Self-Judge Results
All generated captions scored well under self-evaluation:
- **Formal**: Detailed, professional, objective, within word limit.
- **Sarcastic**: Dry irony, grounded in visible content, social-media tone.
- **Humorous (Tech)**: Software metaphors anchored to visible objects/actions.
- **Humorous (Non-Tech)**: Relatable everyday context tied to the actual scene.

---

### Security Reminder
- Never commit your `.env` file to version control.
- Use `.env.example` as a template for other environments.
- Rotate your API keys immediately if they are ever exposed.
- Do not print or log secrets in your application logs.
