# Build Phases

Status legend: ⬜ not started · 🟨 in progress · ✅ done

## Phase 0 — Setup & Spike (Hour 0-1)
- ✅ Confirm Gemini API key works
- ✅ Download/inspect real clip set (duration, format, resolution)
- ✅ One clip → one caption, fully manual, end-to-end proof of concept

## Phase 1 — Core Architecture & Perception Pipeline (Hour 1-3)
- ✅ Hybrid frame extraction working (`extract_frames.py`) with OpenCV scene detection
- ✅ (Optional) audio transcription hook wired in pipeline
- ✅ `analyze_video.py` returns structured JSON via Gemini 2.5 Flash
- ✅ Manual review: descriptions are factually accurate on 3-5 sample clips

## Phase 2 — Prompts & Constraints (Hour 3-5)
- ✅ 4 strict style rules combined into unified prompt schema (`prompts.py`)
- ✅ Single-pass execution extracts video understanding and 4 styles simultaneously
- ✅ Manual review: styles are distinct from each other (esp. sarcastic vs humorous-tech)

## Phase 3 — Full Batch Run (Hour 5-6)
- ✅ `pipeline.py` coordinates robust end-to-end download, extraction, and generation
- ✅ `scripts/run_all.py` processes entire clip set with thread pooling and retries
- ✅ Output JSON strictly matches required submission format
- ✅ Substantially fewer API calls and reduced latency vs legacy multi-call approach

## Phase 4 — Self-Eval & Iteration (Hour 6-8)
- ✅ `eval/self_judge.py` configured to check accuracy + tone match
- ✅ Identify and fix worst-scoring clips/styles

## Phase 5 — Production Hardening (Final Pass)
- ✅ Robust JSON parsing: parse → repair-prompt retry → graceful empty fallback
- ✅ Key validation: all required caption and video_understanding fields guaranteed
- ✅ Anti-hallucination prompt: never invent objects, people, or locations
- ✅ Fact consistency: all 4 captions describe the same scene (tone-only variation)
- ✅ Grounded humor: jokes must reference a visible object or action from the video
- ✅ Formal captions: 15–18 words, hard max 20, single sentence
- ✅ One sentence per caption enforced across all styles
- ✅ Clean output: no markdown, emojis, bullets, hashtags, or labels in captions
- ✅ camera_motion: always present, constrained to allowed vocabulary
- ✅ apparent_emotion: replaces emotion; describes visible expression only
- ✅ FPS-driven frame sampling: ~0.5 s interval scales with actual video FPS
- ✅ Improved logging: frame indices, scene-change indices, retry attempts logged
- ✅ Defensive coding: all dict accesses use .get(), no KeyError crashes
- ✅ Unverified quantitative claims removed from documentation
- ✅ All docs updated to reflect hardened pipeline

## Phase 6 — Polish & Submission
- ✅ README finalised
- ✅ `docs/submission.md` updated
- ✅ Dead code removed
- ✅ Final clean run confirms reproducibility
- ✅ Submitted before deadline

## Current Blockers
- None. Final submission verified and completed.