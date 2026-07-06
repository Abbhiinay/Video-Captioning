# Build Phases

Status legend: ⬜ not started · 🟨 in progress · ✅ done

## Phase 0 — Setup & Spike (Hour 0-1)
- ⬜ Confirm Fireworks API key works (test curl/API call)
- ⬜ Confirm AMD Developer Cloud GPU access (if used)
- ⬜ Download/inspect real clip set (duration, format, resolution)
- ⬜ One clip → one caption, fully manual, end-to-end proof of concept

## Phase 1 — Perception Pipeline (Hour 1-3)
- ⬜ Frame extraction working (`extract_frames.py`)
- ⬜ (Optional) audio transcription working
- ⬜ `describe_video.py` returns a neutral description for any clip
- ⬜ Manual review: descriptions are factually accurate on 3-5 sample clips

## Phase 2 — Style Engine (Hour 3-5)
- ⬜ 4 prompt templates drafted in `config/styles.yaml`
- ⬜ `generate_captions.py` returns all 4 styles from a description
- ⬜ Manual review: styles are distinct from each other (esp. sarcastic vs humorous-tech)

## Phase 3 — Full Batch Run (Hour 5-6)
- ⬜ `pipeline.py` connects perception → style engine → output
- ⬜ `scripts/run_all.py` processes entire clip set
- ⬜ Output JSON matches required submission format

## Phase 4 — Self-Eval & Iteration (Hour 6-8)
- ⬜ `eval/self_judge.py` scores accuracy + tone match
- ⬜ Identify and fix worst-scoring clips/styles

## Phase 5 — Fine-tuning (Hour 8-10) — Optional
- ⬜ Dataset selected (e.g., MSR-VTT / ActivityNet Captions)
- ⬜ Fine-tuned model integrated into perception step
- ⬜ Compared against baseline (better factual accuracy?)

## Phase 6 — Polish & Submission (Hour 10-12)
- ⬜ README finalized
- ⬜ `docs/submission.md` written
- ⬜ Dead code / unused files removed
- ⬜ Final clean run confirms reproducibility
- ⬜ Submitted before deadline

## Current Blockers
- [list anything blocking progress here, update live during hackathon]