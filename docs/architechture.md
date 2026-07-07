# Architecture

## Problem
Given a fixed set of short video clips (30s–2min), generate a caption for each clip in 4 distinct styles: formal, sarcastic, humorous-tech, humorous-non-tech.

## Design Principle
Highly optimized **Single-Pass Inference**. We extract the frames, pass them to a vision-language model once alongside strict output formatting rules, and receive both the visual understanding and the requested captions in a single structured JSON payload. This drastically reduces API calls, latency, and token usage compared to sequential generation.

## Pipeline
```
Video Clip
│
▼
Preprocessing (extract_frames.py, transcribe_audio.py)
│  → sampled frames (hybrid uniform + scene detection) + optional transcript
▼
Unified Perception & Styling (analyze_video.py)
│  → single prompt requesting structured video metadata AND 4 distinct captions
▼
Output (pipeline.py → data/outputs/*.json)
→ { clip_id, formal, sarcastic, humorous_tech, humorous_non_tech }
```

## Components

| Component | Responsibility | Input | Output |
|---|---|---|---|
| `preprocessing/extract_frames.py` | Sample frames from video | video path | list of frame images |
| `preprocessing/transcribe_audio.py` | (Optional) speech-to-text | video path | transcript string |
| `perception/analyze_video.py` | Generate JSON with description + styles | frames (+transcript) | JSON dict object |
| `utils/gemini_client.py` | Shared API wrapper (auth, retries, JSON enforcement) | prompt/payload | model response |
| `eval/self_judge.py` | Self-check accuracy + tone match | generated captions | scores/notes |

## Models Used
- Unified Perception & Style: **Gemini 2.5 Flash** — Google multimodal model, handles inline base64 JPEG frames via REST API, natively enforces `application/json` structured output.

## Key Design Decisions
- **Frame sampling rate:** Hybrid. Extracts 3 evenly-spaced frames, plus 2 scene-change frames using OpenCV histogram differences to capture sudden cuts or changes in action.
- **Why Single-Pass:** Consolidating perception and style generation into a single API call removes the need to constantly re-pass the video's textual description back into the LLM 4 separate times. This saves ~75% of context token usage and drastically drops latency.
- **Strict JSON Enforcement:** Using `responseMimeType: "application/json"` guarantees that the model will output keys exactly matching the required output format without needing manual regex parsing or risking hallucinations.