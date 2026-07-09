# Architecture

## Problem

Given a set of short video clips (30s–2min), generate a caption for each clip
in 4 distinct styles: formal, sarcastic, humorous-tech, humorous-non-tech.

---

## Design Principle: Single-Pass Inference

The pipeline extracts frames once, passes them to Gemini once, and receives both
the visual understanding *and* all requested captions in a single structured JSON
payload. This approach means:

- **Substantially fewer API calls** compared to sequential per-style generation.
- **Reduced latency** — one network round-trip rather than a sequential waterfall.
- **Reduced token usage** — the video frame context is transmitted once rather
  than once per style.

---

## Pipeline Architecture

The system supports two execution paths sharing the same core visual perception and styling engine:

1. **Batch Pipeline (CLI / Production)**: Processes multiple remote video tasks specified in `tasks.json` concurrently using a thread pool, downloading clips and producing a single structured `results.json` file.
2. **Interactive Web Pipeline (Web UI / API)**: Supports single-pass real-time upload of local videos from a browser, handling processing asynchronously and returning styling results dynamically back to the interface.

```
[ Batch Flow ]
Video Tasks (tasks.json) ──> Concurrency coordinator (run_all.py) ──> Batch Pipeline (pipeline.py)
                                                                             │
[ Web Flow ]                                                                 ▼
Video File (Web App) ──> API Server (api/main.py) ──> extract_frames.py ──> gemini_client.py ──> output
```

---

## Components

| Component | Layer / Area | Responsibility | Input | Output |
|---|---|---|---|---|
| `extract_frames.py` / `frame_extractor.py` | Preprocessing | Sample frames (hybrid uniform + scene-change) | Video path / file | List of local JPEG paths |
| `analyze_video.py` / `gemini_service.py` | Perception | Sends frames to Gemini, parses JSON, retries, validates | Base64 frames + prompts | Validated structure dict |
| `prompts.py` | Prompt Engine | Build unified styling prompt + JSON repair instructions | Target styles list | Formatted prompt string |
| `pipeline.py` | Batch Orchestrator | Coordinates download -> extract -> analyze sequence | Task dict | Result output dict |
| `run_all.py` | Batch Runner | CLI entry point running thread-pooled tasks | tasks.json | results.json |
| `api/main.py` | Web API Backend | FastAPI endpoints (`/api/health`, `/api/caption`) | Uploaded video file | JSON captions payload |
| `web/src/App.jsx` | Web Frontend | React + Vite client UI, upload handlers, styling view | User action (upload) | Interactive dashboard |

- **Gemini 2.5 Flash** — Google multimodal model.
  Receives inline base64 JPEG frames via REST API.
  Outputs schema-constrained JSON via `responseMimeType: "application/json"`.

---

## Key Design Decisions

### Frame Sampling Rate — Hybrid FPS-Driven

Candidate frames for scene-detection are sampled at approximately one frame
per 0.5 seconds of video, scaled to the actual video FPS. This approach:
- Scales correctly from slow 12 fps footage to 60 fps high-speed clips.
- Prevents over-sampling very short clips (too many near-identical frames).
- Prevents under-sampling long clips (missing genuine scene changes).

Fixed 3 anchor frames are always included regardless of scene detection results,
guaranteeing temporal coverage across the full clip.

### JSON Robustness — Retry + Repair

Even with `responseMimeType: "application/json"`, Gemini occasionally returns
malformed output (e.g. trailing commas, partial fences). The pipeline:
1. Attempts to parse the response normally.
2. On failure, sends a targeted repair prompt explicitly showing the bad response
   and requesting a clean JSON-only retry.
3. On a second failure, returns graceful empty captions — the batch continues.

This prevents a single malformed API response from killing the entire run.

### Key Validation — Safe Defaults

After parsing, every required key (`captions.formal`, `captions.sarcastic`,
`captions.humorous_tech`, `captions.humorous_non_tech`, `video_understanding.*`)
is checked. Missing keys are filled with empty strings or sensible defaults.
No `KeyError` exceptions propagate.

### Anti-Hallucination Prompt Design

The prompt explicitly forbids:
- Inventing objects, people, or locations not visible in the frames.
- Inferring unseen actions or events.
- Assuming identities from appearance.
- Guessing locations without visible evidence.

Uncertain elements must be described as "unknown". This reduces confident
confabulation in clips with ambiguous or sparse visual content.

### Grounded Humor

Humorous captions frequently drift toward generic one-liners that could apply
to any video. The prompt requires every humorous caption to reference at least
one specific visible object or visible action from the video. This anchors the
joke to the actual content and improves output quality and relevance.

### Fact Consistency Across Styles

All four captions describe the same scene. Style-specific rules only govern
*tone* — no style may introduce new facts, new objects, new people, or new
assumptions. This ensures the captions remain faithful to the observed video
regardless of the requested style.

### apparent_emotion (not emotion)

The `apparent_emotion` field replaces the generic `emotion` field. Gemini is
instructed to describe only visible facial expressions or body language — never
to infer internal emotional states. If no person is visible, or expression is
ambiguous, the field returns "unknown".

### camera_motion — Constrained Vocabulary

The `camera_motion` field is constrained to:
`static | pan | tilt | zoom | tracking | handheld | unknown`.
Any value outside this set is normalised to "unknown" by the post-parse
validation step.

---

## Security Considerations

- **API Keys**: Never commit `.env` or other files containing credentials to version control.
- **Environment Templates**: Use `.env.example` to document required configuration variables without sharing secrets.
- **Key Rotation**: Rotate your API keys immediately if they are ever accidentally exposed in logs or commits.
- **Log Sanitation**: Do not print, log, or otherwise expose secrets or API keys in standard output or files.