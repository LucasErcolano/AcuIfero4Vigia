# P0 — Reconnaissance

Date: 2026-04-20. Branch: `develop`.

## Git state

```
d02b5ec Fix hydromet refresh serialization and error handling
4778906 Add Android MVP app on develop
ef5c6b6 Stabilize local Gemma parsing and Linux dev startup
45f68af Document reproducible local smoke test
2947400 Build browser-first MVP with local Gemma runtime
8a4050d Initial MVP implementation
```

Branches: `develop` (active, up-to-date with `origin/develop`), `main`. Status clean except untracked `Hackathon-agent-brief.md`.

## Repo tree (develop)

- `backend/` — FastAPI + SQLModel + OpenCV (Python 3.10+).
- `frontend/` — React 18 + TypeScript + Vite + PWA.
- `android/` — Kotlin + Jetpack Compose (Gradle).
- `shared/schemas/` — JSON Schema for `volunteer-report`, `node-event`, `fused-alert`.
- `scripts/` — bash + powershell setup/demo helpers.
- `fixtures/media/` — bundled USGS Silverado clip.

## Android stack (identified)

- **Framework**: Kotlin + Jetpack Compose (native).
- **Gradle**: Kotlin DSL. `compileSdk=34`, `minSdk=26`, `targetSdk=34`, JVM target 17.
- **Key deps**: Compose BOM `2024.10.01`, Retrofit `2.11.0`, Room `2.6.1`, WorkManager `2.9.1`, Coil `2.7.0`, Navigation Compose `2.8.4`, KSP for Room.
- **Source layout**: `android/app/src/main/java/com/acuifero/vigia/android/{data,ui}/` — thin MVP: `MainActivity`, `AcuiferoApp` composable, `MainViewModel`, Retrofit `AcuiferoApi`, Room `AppDatabase`, `SyncQueuedReportsWorker`.
- **Backend URL**: `http://10.0.2.2:8000/api/` (emulator default) overrideable from in-app Settings.

### Gemma runtime on Android — **BLOCKER / P7 HIGHEST PRIORITY GAP**

- No MediaPipe LLM Inference integration.
- No LiteRT / LiteRT-LM binding.
- No `.task` or `.gguf` asset referenced anywhere.
- No model-loading code in `android/`.
- Android currently relies fully on **backend** for LLM structuring via Retrofit.

This is the single highest-priority gap identified by the brief for the LiteRT Prize.

## Backend LLM adapter inventory

Path: `backend/src/acuifero_vigia/adapters/`.

- `llm.py` — `OpenAICompatibleLLM` class. Single concrete adapter exposing:
  - `health() -> LLMHealth` (polls `/models`).
  - `structure_observation(transcript_text, site_context) -> dict | None` (calls Ollama native `/api/chat` JSON mode first, falls back to OpenAI-compatible `/chat/completions`).
- **No per-interface adapter modules** (no `text_structuring.py`, no `image_assessment.py`, no `audio_transcription.py`). The brief's P1/P2 file paths must therefore be created; P4 file path too.
- Called from:
  - `services/report_structuring.py::structure_report` — text structuring path with rule-based fallback (`_fallback_parse`).
  - `main.py` — single module-level `llm_client` instance.

## Decision engine / alerting

- No `services/alerting.py` — brief reference. Actual alert fusion lives in `services/decision_engine.py::recompute_site_alert`.
- Fusion picks `max(node.severity_score, parsed.severity_score, hydromet.signal_score)` and adds a small corroboration bonus. Persists `FusedAlert` with `level`, `score`, `trigger_source`, `summary`, `decision_trace` (JSON-encoded list of strings), `local_alarm_triggered`.

## Current `decision_trace` (real)

Seeded DB + volunteer report "El agua ya paso la marca critica, esta subiendo rapido, cortamos la ruta." on `silverado-fixed-cam-usgs`:

```
LEVEL: red  SCORE: 1.0
TRACE: ["volunteer=1.00", "supporting_sources=1"]
SUMMARY: Volunteer report: water=critical, trend=rising, road=open, bridge=unknown
```

Trace is deterministic-only — no LLM reasoning chain. **This is exactly what P1 must fix.**

## Test status

- Backend: `PYTHONPATH=src pytest -q` → **10 passed** in 1.85s.
- Frontend: `npm test` (vitest) → **2 passed**. `npm run lint` → clean.
- Frontend build: not re-run here (assumed green from last commit).
- Android: no JUnit tests in `android/app/src/test/` / `androidTest/`. Gradle not invoked (no Android SDK on dev machine).

## Schema adaptations required vs brief

- Brief says "new file `services/reasoning.py`" — OK, greenfield.
- Brief says "`services/alerting.py`" → map to `services/decision_engine.py::recompute_site_alert`.
- Brief says "new adapter `adapters/image_assessment_gemma.py` implementing existing `ImageAssessmentAdapter` interface" — **interface does not exist yet**; will create it plus adapter.
- Brief expects Android native Gemma — stack is Kotlin/Compose (good: MediaPipe LLM Inference has native Kotlin API).

## Blockers

- **Android SDK / Android Studio not verified on dev machine** — P7 bundling + APK build may need Colab or a second machine. Will proceed by writing the Kotlin integration code and a build/benchmark doc; the developer runs gradle themselves if they want an APK.
- **Ollama availability** not verified at recon time. All LLM paths must therefore keep deterministic fallback (P1 spec already requires this).
- **Gemma 4 E4B VRAM** not confirmed. P2 will auto-fall back to E2B.

Status: **recon complete**, proceeding to P1.
