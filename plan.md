# Acuifero 4 + Vigia MVP Implementation Plan

## 0. Agent Brief

You are implementing a full, demoable MVP from an empty repository.

Read this file first and execute it as written unless you discover a hard blocker.

Hard rules:

- Optimize for a working end-to-end MVP on this exact machine, not for a perfect contest-final architecture.
- Do not make Android Studio, Java, Docker, CUDA, native LoRa hardware, GPIO hardware, or local fine-tuning mandatory.
- Keep Google AI Edge / LiteRT alignment in the architecture, but do not let LiteRT-LM integration block the MVP.
- If any optional AI Edge integration takes more than 60 minutes to make usable, stub it behind an adapter and continue.
- Prefer CPU-friendly, offline-capable, low-RAM choices.
- The repository is effectively empty at the start. You must create the structure.

## 1. Goal

Build one unified system, not two separate products:

`Acuifero 4 + Vigia = hybrid flood early-warning MVP with fixed node + volunteer reports + local decision engine`

The MVP must demonstrate these three flows:

1. A fixed node ingests a video clip or webcam stream, analyzes a 60 second temporal window, estimates whether water crossed a critical threshold, and triggers a local alarm action.
2. A volunteer uses a mobile-friendly offline-first app to submit a photo, an audio note or transcript, and a site observation. The system converts that into structured JSON and stores it locally.
3. When connectivity is "restored", queued data syncs into a central store and a fused alert timeline becomes visible.

This is the MVP definition. If these three flows work reliably on this machine, the MVP is successful.

## 2. Real Machine Constraints

This plan is for the current machine:

- OS: Windows 10 Home 64-bit
- CPU: AMD Ryzen 5 7530U
- Logical processors: 12
- RAM: about 7.85 GB
- GPU: AMD Radeon integrated graphics only
- CUDA: not available
- Python: 3.12.0
- Node: 24.14.0
- npm: 11.9.0
- uv: 0.10.12
- ffmpeg: installed and available
- Java: not installed
- WSL: present, but default distro is `docker-desktop`

Implications:

- Do not depend on Android emulator or Android Studio.
- Do not depend on local training, LoRA fine-tuning, or large multimodal GPU inference.
- Do not assume local Gemma 4 E4B multimodal inference is practical on this laptop.
- Keep memory pressure low and avoid heavyweight background services.
- Prefer a browser-based mobile UI plus a Python backend over native Android for the first MVP.

## 3. Product Framing

The system is one product with two inputs:

- `Acuifero 4`: fixed river/bridge monitoring node
- `Vigia`: volunteer field reporting app

Both feed a shared local decision engine with:

- structured observations
- threshold logic
- alert explanations
- offline queueing
- delayed sync

The product story is:

`When internet fails, local observation and local action still work.`

## 4. Non-Negotiable Scope

Implement these features in the mandatory MVP:

- Local SQLite persistence
- Offline-first volunteer report queue
- Video analysis pipeline for fixed-node ingestion
- Alert severity scoring
- Explainable decision trace
- Local alarm action simulation
- Central sync simulation
- Demo dashboard

Do not make these features mandatory in the first pass:

- Real LoRaWAN hardware
- Real GPIO relay hardware
- Real SINAGIR production integration
- Native Android APK
- Fine-tuned Gemma
- Full on-device multimodal Gemma inference

## 5. Recommended Architecture

Use a simple two-part stack:

- Frontend: `React + TypeScript + Vite + PWA`
- Backend: `FastAPI + SQLite + SQLModel or SQLAlchemy + OpenCV`

Why this stack:

- It fits the installed toolchain.
- It is fast to scaffold from an empty repo.
- It works well on Windows with 8 GB RAM.
- It gives a mobile-friendly experience without requiring Android Studio.
- It supports offline storage and sync simulation cleanly.

## 6. Mandatory Repo Structure

Create this structure:

```text
backend/
  pyproject.toml
  src/acuifero_vigia/
    __init__.py
    main.py
    api/
    core/
    db/
    models/
    schemas/
    services/
    adapters/
    utils/
  data/
    .gitkeep
  tests/

frontend/
  package.json
  vite.config.ts
  tsconfig.json
  public/
  src/
    app/
    components/
    features/
    lib/
    pages/
    stores/
    types/

shared/
  schemas/
    volunteer-report.schema.json
    node-event.schema.json
    fused-alert.schema.json

fixtures/
  media/
  generated/

scripts/
  setup.ps1
  dev.ps1
  demo.ps1
  seed.ps1

docs/
  architecture.md
  demo-script.md
  edge-notes.md

README.md
plan.md
```

Keep all code/package names ASCII even if the product name in UI uses `Acuifero 4` and `Vigia`.

## 7. Core Functional Design

### 7.1 Fixed Node Flow

Input:

- local video file, webcam feed, or RTSP URL

Behavior:

- sample 1 frame per second over a rolling 60 second window
- analyze only a configured region of interest
- estimate waterline relative to a manually calibrated critical line
- ignore noise such as vegetation motion when possible
- store evidence and the computed decision
- trigger a local alarm when threshold is exceeded

MVP implementation guidance:

- Use classical CV, not a large multimodal model.
- Add a calibration step where the user uploads or freezes one frame and marks:
  - the monitored ROI
  - the critical line
  - an optional reference line below it
- Persist calibration per site in SQLite.

Suggested CV approach:

- Convert ROI to grayscale and HSV.
- Use temporal median smoothing across frames.
- Use edge detection plus connected components or horizontal line estimation to infer a stable water boundary.
- Compute:
  - `waterline_ratio`
  - `crossed_critical_line`
  - `rise_velocity`
  - `confidence`
- Build a human-readable explanation such as:
  - `critical line crossed in 8 of last 10 frames`
  - `rise velocity exceeds configured threshold`
  - `confidence reduced because camera motion was detected`

Do not over-engineer this. A robust calibrated heuristic is enough for the MVP.

### 7.2 Volunteer Report Flow

Input:

- selected site
- photo
- audio note or transcript
- optional quick toggles for road status / bridge status / urgency

Behavior:

- work offline in the browser
- persist draft and queued submissions in IndexedDB
- create a structured observation JSON
- sync later when "online"

Mandatory UX requirements:

- mobile-first layout
- installable PWA
- explicit offline status badge
- "saved locally" confirmation
- queue page with retry button
- transcript text field must always be available as fallback

Important constraint:

- Audio processing must not be a blocker. The app must accept manual transcript entry if local ASR is unavailable or too slow.

### 7.3 Local Decision Engine

Input sources:

- node observations
- volunteer structured reports

Output:

- site alert level
- explanation trace
- pending actions

Mandatory alert levels:

- green
- yellow
- orange
- red

Use deterministic logic first:

- compare current node severity against configured hard thresholds
- compare current severity against a rolling baseline
- boost severity when volunteer report contains critical phrases or critical toggles
- produce a plain-language reasoning summary

### 7.4 Sync Simulation

Implement two SQLite databases:

- `edge.db`: local state used by the node and volunteer app
- `central.db`: simulated central backend store

When the app is "offline":

- store outgoing sync payloads in a queue table

When the app is "online":

- flush queued payloads into `central.db`
- mark them as synced

This gives a real offline/online demo without requiring cloud deployment.

### 7.5 Local Action Simulation

Implement actuators behind interfaces:

- `AlarmActuator`
- `RadioActuator`
- `NotificationActuator`

Provide concrete MVP adapters:

- `winsound` or WAV playback siren
- log-to-file "LoRa payload" writer
- in-app emergency banner / toast

Do not wait for hardware. Simulate it cleanly.

## 8. Data Model

Implement at least these entities:

- `Site`
- `SiteCalibration`
- `NodeObservation`
- `VolunteerReport`
- `ParsedObservation`
- `FusedAlert`
- `SyncQueueItem`
- `DeviceConfig`
- `ActuationEvent`

Suggested fields:

### Site

- `id`
- `name`
- `region`
- `lat`
- `lng`
- `description`
- `is_active`

### SiteCalibration

- `id`
- `site_id`
- `roi_polygon`
- `critical_line`
- `reference_line`
- `created_at`

### NodeObservation

- `id`
- `site_id`
- `source_type`
- `video_path`
- `started_at`
- `ended_at`
- `frames_analyzed`
- `waterline_ratio`
- `rise_velocity`
- `crossed_critical_line`
- `confidence`
- `decision_trace`
- `severity_score`
- `evidence_frame_path`

### VolunteerReport

- `id`
- `site_id`
- `created_at`
- `reporter_name`
- `reporter_role`
- `photo_path`
- `audio_path`
- `transcript_text`
- `offline_created`
- `sync_status`

### ParsedObservation

- `id`
- `volunteer_report_id`
- `water_level_category`
- `trend`
- `road_status`
- `bridge_status`
- `homes_affected`
- `urgency`
- `confidence`
- `structured_json`
- `decision_trace`

### FusedAlert

- `id`
- `site_id`
- `created_at`
- `level`
- `score`
- `trigger_source`
- `summary`
- `decision_trace`
- `local_alarm_triggered`
- `sync_status`

## 9. JSON Contract

Do not claim official SINAGIR compliance unless you verify it later. For the MVP, produce a `SINAGIR-ready` normalized schema that is easy to map later.

Use a JSON payload like this:

```json
{
  "site_id": "puente-arroyo-01",
  "observed_at": "2026-04-17T10:15:00Z",
  "source": "volunteer",
  "media": {
    "photo_path": "uploads/reports/rep-001.jpg",
    "audio_path": "uploads/reports/rep-001.wav"
  },
  "hydrology": {
    "water_level_category": "above_bridge_mark",
    "trend": "fast_rising",
    "crossed_critical_threshold": true
  },
  "infrastructure": {
    "bridge_status": "at_risk",
    "road_status": "partially_blocked",
    "homes_affected": false
  },
  "severity": {
    "level": "red",
    "score": 0.92
  },
  "explanation": [
    "transcript contains 'paso la marca del puente'",
    "trend classified as fast rising",
    "road status marked as partially blocked"
  ],
  "sync": {
    "status": "pending"
  }
}
```

## 10. Inference and Parsing Strategy

This machine cannot be the baseline target for heavy multimodal local inference. Design the system so AI is replaceable.

Create these adapters:

- `TextStructuringAdapter`
- `AudioTranscriptionAdapter`
- `ImageAssessmentAdapter`
- `VideoAssessmentAdapter`

Required MVP implementations:

- `RuleBasedTextStructuringAdapter`
- `OptionalWhisperAdapter` or `OptionalFasterWhisperAdapter`
- `HeuristicImageAssessmentAdapter`
- `CalibratedVideoCVAdapter`

### Text Structuring

Implement a rule-based parser first.

Support colloquial rioplatense/litoral phrases such as:

- `paso la marca`
- `esta subiendo rapido`
- `ya toca el puente`
- `ya tapo la calle`
- `entro agua`
- `esta estable`
- `bajo un poco`

Map them into normalized enums.

### Audio

Recommended path:

- try CPU-friendly transcription with a small model
- cap clip duration at 30 seconds
- cache the transcription model on first use
- if transcription fails, require transcript text

Do not chase perfect ASR. Good-enough transcription plus manual fallback is acceptable.

### Image

Do not attempt a sophisticated VLM.

For the MVP, image handling should do two things:

- preserve photo evidence
- optionally derive coarse visual tags such as:
  - visible water
  - water near road edge
  - obstructed structure

This can be heuristic, manual-assisted, or both.

## 11. Preferred AI Edge Strategy

Keep the codebase AI Edge ready, but make it optional.

### Mandatory AI Edge Alignment

Implement architecture hooks for:

- tool-calling style actuation
- structured outputs
- replaceable local model adapters
- future LiteRT-LM integration

### Optional AI Edge Experiment Order

If there is time after the mandatory MVP works:

1. Try `FunctionGemma 270M` for text-to-JSON structuring and tool-call style actions.
2. Try `Gemma 4 E2B` for text-only structured reasoning.
3. Do not make `Gemma 4 E4B` mandatory on this machine.

Reason:

- Official Google material confirms Gemma 4 E2B/E4B and LiteRT-LM support on edge devices, but this laptop has only 8 GB RAM, no CUDA, no Java, and no proven Android workflow.
- The MVP must be finishable here even if LiteRT-LM setup is awkward.

Document all AI Edge attempts in `docs/edge-notes.md`.

## 12. Frontend Pages

Create these pages:

- `/` dashboard
- `/report` new volunteer report
- `/queue` offline queue
- `/sites/:id` site detail
- `/sites/:id/calibrate` calibration UI
- `/settings` connectivity toggle and local config

### Dashboard requirements

- list sites
- show latest node observation
- show latest volunteer report
- show current alert level
- show connectivity state
- show queued item count
- manual "analyze demo clip" button

### Report page requirements

- site selector
- photo upload or capture
- audio upload or record if browser allows
- transcript textarea
- structured preview card
- save offline button
- submit/sync button

### Calibration page requirements

- show reference frame
- let user draw or click ROI
- let user place critical line
- persist calibration

## 13. Backend API

Implement these endpoints at minimum:

- `GET /api/health`
- `GET /api/sites`
- `POST /api/sites`
- `GET /api/sites/{site_id}`
- `POST /api/sites/{site_id}/calibration`
- `POST /api/node/analyze`
- `POST /api/reports`
- `GET /api/reports`
- `POST /api/alerts/recompute`
- `GET /api/alerts`
- `POST /api/sync/flush`
- `POST /api/settings/connectivity`
- `GET /api/settings/connectivity`

Behavior requirements:

- all write endpoints return stored objects, not only `ok`
- all alert endpoints include `decision_trace`
- sync endpoints show queued, flushed, and failed counts

## 14. Alert Scoring Logic

Use a transparent scoring model.

Suggested approach:

- `node_score = 0.55 * waterline_ratio + 0.25 * rise_velocity_norm + 0.20 * crossed_flag`
- `report_score = severity_from_text + infra_boost + urgency_boost`
- `fused_score = max(node_score, report_score) + corroboration_bonus`

Then map:

- `< 0.25` -> green
- `0.25 to < 0.5` -> yellow
- `0.5 to < 0.75` -> orange
- `>= 0.75` -> red

Also allow hard overrides:

- if `crossed_critical_line = true` and confidence is above threshold, at least orange
- if volunteer report says `paso la marca` or `tapo la calle`, at least orange
- if both node and volunteer indicate critical escalation, red

Always store the explanation trace as a list of rule firings.

## 15. Mandatory Scripts

Create these PowerShell scripts:

### `scripts/setup.ps1`

Responsibilities:

- create backend virtual environment or use `uv`
- install backend dependencies
- install frontend dependencies
- create local data directories
- seed demo fixtures if missing

### `scripts/dev.ps1`

Responsibilities:

- run backend dev server
- run frontend dev server
- print URLs clearly

### `scripts/seed.ps1`

Responsibilities:

- create demo sites
- create default calibration
- create baseline records
- optionally create synthetic media fixtures

### `scripts/demo.ps1`

Responsibilities:

- execute the main demo flow in sequence
- analyze a demo node clip
- submit or seed a volunteer report
- toggle offline then online
- flush sync
- print where to view the result

## 16. Fixtures

If real field media is unavailable, generate synthetic fixtures.

Minimum fixtures:

- one "normal water level" clip
- one "rising / crossed threshold" clip
- one volunteer report image
- one volunteer transcript sample

Audio fixture is optional if generation is annoying. The report form must still support manual transcript entry.

Store them under:

- `fixtures/media/`
- `fixtures/generated/`

## 17. Testing

You must add tests. This is still an MVP, but it cannot be a demo held together only by UI.

Backend tests:

- parser unit tests for colloquial phrases
- alert scoring unit tests
- sync queue tests
- calibration persistence tests
- API integration tests for report submission and sync

Frontend tests:

- queue store tests
- offline state tests
- structured preview rendering smoke tests

Avoid heavy browser E2E unless it is trivial. The machine is small.

## 18. Recommended Dependency Set

Backend likely needs:

- `fastapi`
- `uvicorn`
- `sqlmodel` or `sqlalchemy`
- `pydantic`
- `opencv-python-headless`
- `numpy`
- `python-multipart`
- `aiofiles`
- `httpx`
- `orjson`
- `pytest`
- `pytest-asyncio`

Optional backend dependencies:

- `faster-whisper` or another lightweight CPU ASR option
- `ffmpeg-python`

Frontend likely needs:

- `react`
- `typescript`
- `vite`
- `react-router-dom`
- `zustand` or equivalent small state store
- `idb` or Dexie for IndexedDB
- `zod`
- `vite-plugin-pwa`
- `vitest`

Keep dependencies lean.

## 19. Build Order

Follow this order exactly:

1. Scaffold backend, frontend, scripts, and README.
2. Implement SQLite schema and seed flow.
3. Implement basic dashboard and report form.
4. Implement offline queue in frontend.
5. Implement backend report ingestion and structured JSON generation.
6. Implement calibration storage and calibration UI.
7. Implement video analysis pipeline and alert generation.
8. Implement local alarm simulation.
9. Implement central sync simulation.
10. Add tests and fix the obvious failures.
11. Add optional AI Edge adapter hooks.
12. Only then try LiteRT-LM or Gemma experiments.

Do not reorder this unless forced.

## 20. Definition of Done

The MVP is done only if all of this is true:

- `scripts/setup.ps1` works on this machine
- `scripts/dev.ps1` starts frontend and backend
- at least one site can be calibrated
- a demo node clip can generate a node observation and fused alert
- a volunteer report can be created offline and remains queued after page reload
- restoring connectivity flushes queued items into `central.db`
- the dashboard shows current alert level and reasoning trace
- local alarm simulation runs for red alerts
- tests pass or, if some fail, all failures are documented with a concrete reason
- `README.md` explains how to run the project

## 21. Explicit Non-Goals

Do not spend time on these unless everything else already works:

- Android native packaging
- map visualization
- user auth
- role permissions
- cloud deployment
- live public RTSP ingestion at scale
- real LoRa transmission
- real GPIO switching
- training custom LoRA
- benchmark chasing

## 22. Notes for Competitive Positioning

Even though the MVP uses CPU-friendly heuristics first, preserve these narrative anchors in docs and naming:

- autonomous edge alerting
- offline-first resilience
- structured field reports from colloquial language
- explainable local decision engine
- future LiteRT-LM / Gemma-ready adapter design

Do not fake capabilities that are not implemented.

## 23. README Requirements

The final `README.md` must include:

- one paragraph describing the product
- local setup instructions
- architecture diagram or concise text diagram
- demo flow steps
- known limitations
- future AI Edge integration notes

## 24. External Reference Notes

Use these as guidance, not as excuses to overcomplicate the MVP:

- Google Gemma release notes show Gemma 4 was released on March 31, 2026 in E2B and E4B sizes.
- Google AI Edge states LiteRT-LM is the open-source LLM runtime for edge deployment.
- Google AI Edge blog states Gemma 4 supports edge agent workflows and LiteRT-LM adds structured decoding and tool use support.
- Google AI Edge blog states Gemma 3n audio support initially supports batch clips up to 30 seconds.

Useful official links:

- https://ai.google.dev/gemma/docs/releases
- https://ai.google.dev/edge/litert/genai/overview
- https://developers.googleblog.com/bring-state-of-the-art-agentic-skills-to-the-edge-with-gemma-4/
- https://developers.googleblog.com/en/google-ai-edge-gallery-now-with-audio-and-on-google-play/

## 25. Final Instruction

Finish the working MVP first.

Then make it cleaner.

Then, only if there is time and the system is already solid, add AI Edge experiments.
