# Acuifero LiteRT Migration Tracker

## Goal

Migrate the fixed-node `Acuifero` LLM runtime on `develop` from Ollama to LiteRT-LM using `gemma-4-E2B-it.litertlm` as the node model target, while keeping `Vigia` out of scope.

## Decisions Locked

- Base branch: `origin/develop`
- Work branch: `codex/acuifero-litert-e2b-q4-node`
- Node model target: `Gemma 4 E2B` in `.litertlm` format
- Pi target strategy: measured Pi 5 defaults to GPU for LiteRT text; multimodal vision still blocked on current stack
- Scope in: Acuifero runner, node image verifier, alert reasoning
- Scope out: Vigia parsing / report structuring
- Ollama remains allowed only as an explicit development mode, not the Pi production path

## Done

- Created isolated worktree from `origin/develop`
- Confirmed shared-code boundaries between `Acuifero` and `Vigia`
- Confirmed current demo/test data shape:
  - seeded demo site `silverado-fixed-cam-usgs`
  - synthetic test assets in backend tests
- Confirmed missing real local fixture assets in this checkout
- Confirmed Raspberry Pi 5 access and current system baseline
- Confirmed LiteRT-LM docs/release/model sources for CLI + Python
- Added dedicated Acuifero LiteRT runtime/config wiring in backend
- Split Acuifero runtime wiring from Vigia wiring in API deps
- Added initial unit coverage for LiteRT runtime, verifier, and reasoning integration
- Validated real LiteRT API/package shape against `litert-lm-api==0.11.0`
- Validated full backend test suite locally: `56 passed`
- Downloaded real demo assets + LiteRT model on Raspberry Pi worktree
- Fixed Pi ffmpeg extraction portability by switching extracted intermediates to PNG
- Fixed short-clip extraction fallback when `frame_sample_seconds` exceeds clip duration

## In Progress

- Make LiteRT runtime fail closed into Acuifero fallback when dependency/model is unavailable
- Reconcile local/backend test baseline vs new runtime path
- Characterize Raspberry Pi runtime limits for Gemma 4 E2B LiteRT-LM

## Next

- Re-run targeted API tests after fallback fix
- Add LiteRT package dependency / bootstrap docs
- Replace node runner (`OllamaGemmaRunner`) with LiteRT-LM-backed runner
- Replace node frame verifier with LiteRT-LM-backed image assessment
- Replace alert reasoning generation for node path with LiteRT-LM-backed text generation
- Download required demo assets and LiteRT model if missing
- Validate smoke path on local worktree and Raspberry Pi

## Notes

- `origin/develop` differs materially from `main`; implementation must follow `develop` shapes, not the older `main` ones.
- In `develop`, the real node path already uses a dedicated multimodal runner through `AcuiferoAssessmentEngine`.
- `image_assessment.py` is shared today by both Acuifero and Vigia, so changes there must preserve a clean separation by dependency injection or provider split.
- Existing local checkout outside this worktree is dirty; do not use it for implementation work.
- Real fixture files are referenced by docs/seed but are not currently present in disk in this environment.
- Baseline before migration work: `backend/tests` already had 2 failing tests on `origin/develop`
  - `test_ollama_runner_multimodal_mode_parses_json_payload`
  - `test_node_analysis_with_image_media`
- User asked to target “Gemma 4 E2B Q4”; the actual generic LiteRT-LM file currently exposed upstream is `gemma-4-E2B-it.litertlm`, so implementation should use that concrete filename unless a Pi-specific Q4 artifact is verified later.
- Raspberry Pi finding on 2026-05-15:
  - `backend=gpu` works for text smoke inference
  - `backend=cpu` fails at engine creation even for text-only
  - `backend=gpu` + vision fails on Pi GPU buffer limit (`134217728` max buffer vs `152409600` requested)
  - `sample-node-analysis` now completes end-to-end after ffmpeg fixes, but lands on `multimodal-unavailable-fallback`
  - in the measured sample flow, the fallback verdict stayed `yellow` and the fused alert stayed `green`, so reasoning was skipped with `reasoning_model=rule-skip-green`
  - non-green reasoning prompt attempts on LiteRT GPU still timed out or aborted on this Pi, so alert reasoning currently falls back to deterministic summaries
  - result: multimodal node runner remains blocked on this exact Pi/model combination, and non-trivial text reasoning is not yet production-stable there either

## If We Need To Pause

- Re-open this file first.
- Then inspect current diff with `git status --short` and `git diff --stat`.
- Re-verify which runtime is wired in `backend/src/acuifero_vigia/api/deps.py`.
