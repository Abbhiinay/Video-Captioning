# Integration Walkthrough - Video Captioning Pipeline

This document details the completed implementation and verification steps across each build phase of the video captioning integration.

## Implemented Steps by Phase

### Phase 0 — Setup & Spike
* Installed required python packages (`ffmpeg-python`, `opencv-python`, `requests`, `pyyaml`, `dotenv`, `openai`, `pytest`).
* Set up the local development environment configurations and created a `.env` file to hold API keys and model specifications.
* Configured environment variables:
  * `GEMINI_API_KEY`: [Configured]
  * `FIREWORKS_API_KEY`: [Configured]
  * `GEMINI_MODEL`: `gemini-2.5-flash`
  * `FIREWORKS_LLM_MODEL`: `accounts/fireworks/models/gpt-oss-120b` (Chosen as it handles strict formatting constraints without emitting reasoning thoughts in the output).

### Phase 1 — Perception Pipeline
* **Frame Extraction (`extract_frames.py`)**: Implemented robust extraction sampling 5 frames evenly spaced. Includes `ffmpeg-python` check and a full fallback to `OpenCV` to handle local development environment compatibility.
* **Gemini Client (`gemini_client.py`)**: Created standard REST wrapper using raw HTTP POST requests to inline base64 image data to the Gemini API, equipped with a 4-attempt exponential backoff retry system.
* **Video Description Synthesis (`describe_video.py`)**: Coordinates step-by-step:
  1. Sends frame list to Gemini to get visual observations.
  2. Sends observations to Fireworks to synthesize a single neutral, factual, plain-text summary paragraph.

### Phase 2 — Style Engine
* **Prompt Builder (`prompts.py`)**: Parses style rules from `config/styles.yaml` and constructs clean, concise system and user prompts.
* **Style Engine (`generate_captions.py`)**: Handles style generation requests independently. Generates only the styles defined in the input task, catching errors per-style to ensure a single style generation failure doesn't ruin the entire batch output.

### Phase 3 — Full Batch Run
* **Pipeline Orchestrator (`pipeline.py`)**: Manages the end-to-end task run (downloading -> frame extraction -> perception -> styling) and guarantees temporary video and frame file clean-up in a `finally` block.
* **Concurrency Coordinator (`scripts/run_all.py`)**: Entry point loading tasks from `/input/tasks.json` and processing them in parallel using a ThreadPoolExecutor (max workers=3) to respect rate limits and keep the runtime within 10 minutes.
* **Dockerfile Setup**: Configured a `python:3.11-slim` container installing system `ffmpeg`, installing package dependencies, and running the `run_all.py` script.

### Phase 4 — Self-Eval & Iteration
* **Sanity Checks (`eval/self_judge.py`)**: Implemented an automated judge script calling the Fireworks LLM to score the generated captions (1-5 scale) on how well they align with the requested style.
* **Style Prompt Iteration**: Prompt formatting was tightened to ensure the LLM strictly emits the final caption string without introductory preambles or planning thoughts.

---

## Verification Results

The pipeline successfully executed on the three specified test videos. The output JSON file `data/outputs/results.json` was generated matching the submission format:

```json
[
  {
    "task_id": "v1",
    "captions": {
      "formal": "Daytime urban street view showing a multi‑lane road bordered by yellow‑orange foliage, with a building displaying “KOREA ILLIES ENGINEERING” and nearby “FASPARK” and “INSURANCE” signage...",
      "sarcastic": "Because nothing says “exciting urban life” like a green light that never changes and a parade of cars that actually move.",
      "humorous_tech": "Green light = build passed, orange car = hot‑fix deployed to prod, red bus = background job rolling out, and the rest of the traffic? Just async noise from a runaway while‑loop.",
      "humorous_non_tech": "Watching that orange car zip by while the red bus takes its sweet time—my daily commute in a nutshell."
    }
  },
  {
    "task_id": "v2",
    "captions": {
      "formal": "An orange, long‑haired kitten walks across a sun‑dappled forest floor; the five‑frame sequence captures the animal’s progressive steps—alternating front paws—while its gaze remains toward the camera...",
      "sarcastic": "Groundbreaking discovery: an orange kitten struts across a sunny patch of dirt. Who could've imagined such cinematic innovation?",
      "humorous_tech": "Kitten v0.1 boots up, enters an infinite walk() loop, never triggers a segfault, and leaks cuteness into the stack trace of the forest.",
      "humorous_non_tech": "Me, strutting like it’s a runway, but really I’m just racing toward the treat bowl."
    }
  },
  {
    "task_id": "v3",
    "captions": {
      "formal": "A professional woman is seated at a white office desk framed by green plants and circular overhead lights...",
      "sarcastic": "In a jaw‑dropping moment of workplace intrigue, a woman actually sits at a desk, squints at a screen, and—gasp!—uses the keyboard.",
      "humorous_tech": "She’s doing a git merge in real life—master on the monitor, feature branch on the plants, and her hands are the conflict resolver.",
      "humorous_non_tech": "When you’re typing like a pro but your brain’s already planning what to eat for dinner."
    }
  }
]
```

### Self-Judge Results
All generated captions scored exceptionally high under self-evaluation:
* **Formal style**: 4/5 or 5/5 (Detailed, professional, objective).
* **Sarcastic style**: 5/5 (Used mock dramatic/ironic expressions).
* **Humorous (Tech)**: 5/5 (Cleverly integrated git, thread, loop, and hot-fix metaphors).
* **Humorous (Non-Tech)**: 4/5 or 5/5 (Relatable everyday jokes on commuting, cat food, and office dinner planning).
