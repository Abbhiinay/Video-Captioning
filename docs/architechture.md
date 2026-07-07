# Architecture

## Problem
Given a fixed set of short video clips (30s–2min), generate a caption for each clip in 4 distinct styles: formal, sarcastic, humorous-tech, humorous-non-tech.

## Design Principle
Perception (understanding the video) and Style Generation (tone) are fully decoupled.
This lets us debug independently: if a caption is wrong, we can tell whether it's a
factual/understanding error (perception) or a tone error (style engine).

## Pipeline
Video Clip
│
▼
Preprocessing (extract_frames.py, transcribe_audio.py)
│  → sampled frames + optional transcript
▼
Perception (describe_video.py)
│  → single neutral, factual description of the video
▼
Style Engine (generate_captions.py)
│  → 4 style-specific rewrites of the neutral description
▼
Output (pipeline.py → data/outputs/*.json)
→ { clip_id, formal, sarcastic, humorous_tech, humorous_non_tech }

## Components

| Component | Responsibility | Input | Output |
|---|---|---|---|
| `preprocessing/extract_frames.py` | Sample frames from video | video path | list of frame images |
| `preprocessing/transcribe_audio.py` | (Optional) speech-to-text | video path | transcript string |
| `perception/describe_video.py` | Generate neutral factual description | frames (+transcript) | plain-text description |
| `style_engine/generate_captions.py` | Rewrite description in 4 tones | description string | dict of 4 captions |
| `utils/fireworks_client.py` | Shared API wrapper (auth, retries) | prompt/payload | model response |
| `eval/self_judge.py` | Self-check accuracy + tone match | generated captions | scores/notes |

## Models Used
- Perception (visual): **Gemini 2.0 Flash** — Google multimodal model, handles inline base64 JPEG frames via REST API
- Perception (synthesis): **llama-v3p3-70b-instruct** (Fireworks) — synthesizes raw Gemini observations into a single neutral paragraph
- Style generation: **llama-v3p3-70b-instruct** (Fireworks) — rewrites the neutral description into 4 distinct tones

## Key Design Decisions
- Frame sampling rate: [fill in, e.g., 1 fps / scene-change detection]
- Why decoupled perception/style: independent debugging + easier tone iteration without re-running vision model
- Fallback if launch-day model lacks direct video input: frame-sampling becomes mandatory