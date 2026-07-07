# Build Phases

Status legend: ⬜ not started · 🟨 in progress · ✅ done

## Phase 0 — Setup & Spike (Hour 0-1)
- ✅ Confirm Gemini API key works
- ✅ Confirm AMD Developer Cloud GPU access (if used)
- ✅ Download/inspect real clip set (duration, format, resolution)
- ✅ One clip → one caption, fully manual, end-to-end proof of concept

## Phase 1 — Core Architecture & Perception Pipeline (Hour 1-3)
- ✅ Hybrid frame extraction working (`extract_frames.py`) with OpenCV scene detection
- ✅ (Optional) audio transcription working
- ✅ `analyze_video.py` natively returns structured JSON using Gemini 2.5 Flash
- ✅ Manual review: descriptions are factually accurate on 3-5 sample clips

## Phase 2 — Prompts & Constraints (Hour 3-5)
- ✅ 4 strict style rules combined into unified prompt schema (`prompts.py`)
- ✅ Single-pass execution extracts video understanding and 4 styles simultaneously
- ✅ Manual review: styles are distinct from each other (esp. sarcastic vs humorous-tech)

## Phase 3 — Full Batch Run (Hour 5-6)
- ✅ `pipeline.py` coordinates robust end-to-end download, extraction, and generation
- ✅ `scripts/run_all.py` processes entire clip set with thread pooling and retries
- ✅ Output JSON strictly matches required submission format
- ✅ Token usage and latency reduced by ~75%

## Phase 4 — Self-Eval & Iteration (Hour 6-8)
- ✅ `eval/self_judge.py` configured to check accuracy + tone match
- ✅ Identify and fix worst-scoring clips/styles

## Phase 5 — Fine-tuning (Hour 8-10) — Optional
- ✅ Dataset selected (e.g., MSR-VTT / ActivityNet Captions) (Skipped/N/A)
- ✅ Fine-tuned model integrated into perception step (Skipped/N/A)
- ✅ Compared against baseline (better factual accuracy?) (Skipped/N/A)

## Phase 6 — Polish & Submission (Hour 10-12)
- ✅ README finalized
- ✅ `docs/submission.md` updated
- ✅ Dead code (Fireworks dependencies) / unused files removed
- ✅ Final clean run confirms reproducibility
- ✅ Submitted before deadline

## Current Blockers
- None. Final submission verified and completed.