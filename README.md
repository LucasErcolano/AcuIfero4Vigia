# Acuifero 4 + Vigia

Hybrid flood early-warning system for Argentina's Litoral: a Gemma-first
fixed-node assessment engine (`Acuifero`) plus offline-first volunteer reports
(`Vigia`) feeding a local, auditable alert pipeline. Submitted to the Gemma 4
Good Hackathon (Global Resilience track, LiteRT Prize).

## What makes this different

1. **Gemma-first temporal node reasoning**: `Acuifero` curates a temporal evidence pack from fixed-camera video and asks Gemma to emit the node assessment package: `assessment_level`, `assessment_score`, `temporal_summary`, `reasoning_summary`, `reasoning_steps`, and audit artifacts.
2. **Auditable reasoning chain**: every non-green `FusedAlert` carries a Spanish-language reasoning block alongside the deterministic rule trace. See [`docs/hackathon/thinking-mode.md`](docs/hackathon/thinking-mode.md).
3. **Rich audit pack for demos and review**: each node analysis persists curated frames, evidence imagery, runner metadata, fallback status, and JSON artifacts instead of only a heuristic score.
4. **Rioplatense hydro understanding**: 82-example labeled corpus + 12-shot prompt beats rule-based baseline on Litoral colloquial phrases. See [`docs/hackathon/rioplatense_eval.md`](docs/hackathon/rioplatense_eval.md).
5. **SINAGIR-ready export**: `POST /api/alerts/{id}/export-sinagir` emits a documented schema mapped to Argentina's national disaster registry. See [`docs/hackathon/sinagir-mapping.md`](docs/hackathon/sinagir-mapping.md).
6. **On-device Android volunteer flow**: MediaPipe LLM Inference wrapper parses reports fully on-device (no silent backend fallback). See [`docs/hackathon/android_gemma.md`](docs/hackathon/android_gemma.md).

Connectivity-loss demo: [`scripts/demo_connectivity.py`](scripts/demo_connectivity.py) runs the full `wifi-off -> local alert -> siren -> wifi-on -> queue drain` narrative in under 90 s.

## Where Gemma 4 is used

Gemma 4 is used in three places (full map: [`docs/GEMMA_USAGE.md`](docs/GEMMA_USAGE.md)):

1. Edge node temporal reasoning - [`backend/src/acuifero_vigia/services/acuifero_assessment.py`](backend/src/acuifero_vigia/services/acuifero_assessment.py), [`backend/src/acuifero_vigia/adapters/video_assessment.py`](backend/src/acuifero_vigia/adapters/video_assessment.py), [`backend/src/acuifero_vigia/adapters/llm.py`](backend/src/acuifero_vigia/adapters/llm.py)
2. Vigia report understanding - [`backend/src/acuifero_vigia/adapters/text_structuring_gemma_fewshot.py`](backend/src/acuifero_vigia/adapters/text_structuring_gemma_fewshot.py), on-device Android [`android/app/src/main/java/com/acuifero/vigia/android/data/GemmaOnDevice.kt`](android/app/src/main/java/com/acuifero/vigia/android/data/GemmaOnDevice.kt)
3. Alert reasoning + audit trace - [`backend/src/acuifero_vigia/services/reasoning.py`](backend/src/acuifero_vigia/services/reasoning.py), [`backend/src/acuifero_vigia/services/node_analysis.py`](backend/src/acuifero_vigia/services/node_analysis.py)

Runtimes: Ollama (backend dev / Pi 16GB), LiteRT-LM (Pi 8GB target, benchmarks in [`docs/hackathon/`](docs/hackathon/)), MediaPipe LLM Inference (Android).

Reproducibility (versions, commands, expected outputs, anti-mock checks): [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md). Hardware deployment: [`docs/raspberry-pi-acuifero-node.md`](docs/raspberry-pi-acuifero-node.md).

## Repository layout

```
backend/    FastAPI service (Python 3.10+, uv): node analysis, alerts, sync
frontend/   PWA dashboard (Vite + TS): operator UI for sites and queue
android/    Volunteer Android app (Compose + MediaPipe LLM Inference)
scripts/    Pi node runners, demo, setup, dev, fetch assets
shared/     Cross-component JSON schemas
fixtures/   Demo media/frames (gitignored, fetched on demand)
datasets/   Rioplatense eval corpus
docs/       Architecture, hackathon notes, demo script, PDF summaries
docker-compose.yml  Dev orchestration for backend + optional Ollama
.env.example        Copy to .env, fill local secrets (never commit .env)
```

## Architecture (high-level)

```
   +----------------+        +-------------------+        +-------------+
   | Fixed camera   | ffmpeg | Acuifero edge (Pi)|  HTTP  |  Backend    |
   | (RTSP/USB)     +------->| node_guard.py     +------->|  FastAPI    |
   +----------------+        | + Gemma 4 (Ollama)|        |  + SQLite   |
                             +-------------------+        |  + DecisionE|
                                                          +------+------+
   +----------------+        +-------------------+               |
   | Volunteer      |  PWA   | Android (Compose) |  HTTP/queue   |
   | (Vigia)        +------->| MediaPipe LLM     +-------------->|
   +----------------+        | (Gemma E2B/E4B)   |               |
                             +-------------------+        +------v------+
                                                          | Alerts/CAP  |
                                                          | SINAGIR exp |
                                                          +-------------+
```

Stack: Gemma 4 (E2B/E4B) via Ollama and MediaPipe LLM Inference, LiteRT-LM
(stub runner target), FastAPI, SQLite, React/Vite PWA, Jetpack Compose, CAP v1.2.

## Quick start (Docker)

```bash
cp .env.example .env
docker compose --profile llm up
# Backend at http://localhost:8000, Ollama at http://localhost:11434
# docker-compose.yml sets ACUIFERO_LLM_MODEL=gemma4:26b for vision + tools;
# gemma4:e2b is text-only and rejects /api/chat tools, so pull 26b for this stack.
docker exec acuifero-ollama ollama pull gemma4:26b
```

For native dev per component, see the sections below.

## Overview

The system has three real signal paths:

- `Acuifero`: Gemma-first fixed-node temporal assessment over real clips
- `Vigia`: volunteer field reports stored offline-first in the PWA
- live hydrometeorological enrichment from Open-Meteo APIs

The fixed `Acuifero` node is now sized in two modes: a minimum Raspberry Pi 8 GB
demo and a Raspberry Pi 16 GB / workstation production profile. Both use Gemma 4
multimodal directly over curated frames; OpenCV is not part of the Acuifero
visual decision path. `Vigia` remains a separate volunteer/user node.

## What is real in this repo

- Node analysis samples fixed-camera video with ffmpeg, curates image evidence, and asks Gemma 4 multimodal to emit the node assessment package.
- Acuifero does not use OpenCV for the fixed-node visual decision path; Gemma 4 reads the selected images directly.
- Every node analysis persists an audit artifact pack with curated frames, evidence frame, temporal summary, runner metadata, fallback status, and JSON manifests.
- Volunteer reports are parsed into structured observations with a local Gemma adapter and a deterministic fallback.
- Fused alerts are recomputed from node, volunteer, and hydromet signals.
- Hydromet context is fetched from real public APIs using site coordinates.
- Edge-to-central sync still uses local SQLite databases, but the queue and replication flow are real.
- The repo includes a real fixed-camera demo site based on the public-domain USGS Silverado clip.

## Acuifero fixed node target

The current production target for the fixed-camera `Acuifero` node is:

- Raspberry Pi 5, 8 GB RAM
- Raspberry Pi OS 64-bit
- system `ffmpeg` available for frame extraction
- 128 GB or larger USB SSD/NVMe for `backend/data`
- fixed camera input uploaded to the backend or bound as per-site sample media
- local SQLite for `edge.db`, audit artifacts, and the sync queue

The Raspberry Pi 8 GB demo profile is the first deploy target. Use an external
SSD/NVMe path for `ACUIFERO_DATA_DIR`; `/mnt/acuifero/data` is the example used
below.

```bash
ACUIFERO_NODE_PROFILE=raspberry-pi-8gb-multimodal-demo
ACUIFERO_DATA_DIR=/mnt/acuifero/data
ACUIFERO_UPLOAD_DIR=/mnt/acuifero/data/uploads
ACUIFERO_NODE_PROVIDER=litert
ACUIFERO_NODE_MODEL_PATH=/mnt/acuifero/data/models/gemma-4-E2B-it.litertlm
ACUIFERO_NODE_BACKEND=gpu
ACUIFERO_NODE_MULTIMODAL_BACKEND=cpu
ACUIFERO_NODE_MULTIMODAL_VISION_BACKEND=cpu
ACUIFERO_NODE_CACHE_DIR=/mnt/acuifero/data/litert-cache
ACUIFERO_NODE_ENABLE_SPECULATIVE_DECODING=true
ACUIFERO_NODE_MAX_OUTPUT_TOKENS=1024
ACUIFERO_NODE_MULTIMODAL_MAX_OUTPUT_TOKENS=2048
ACUIFERO_MAX_CURATED_FRAMES=1
ACUIFERO_ARTIFACT_RETENTION_DAYS=3
ACUIFERO_MULTIMODAL_ENABLED=true
ACUIFERO_MULTIMODAL_VERIFIER_ENABLED=false
ACUIFERO_MULTIMODAL_MODEL=gemma-4-E2B-it.litertlm
ACUIFERO_MULTIMODAL_MAX_FRAMES=1
ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=300
ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=512
ACUIFERO_MULTIMODAL_NUM_CTX=1024
```

On this profile, Acuifero extracts one optimized frame from each short clip and
asks Gemma 4 multimodal for the verdict. It is intentionally sparse so we can
learn the real latency and memory ceiling of the 8 GB Pi without changing the
production code path.

`Vigia` is intentionally out of this hardware profile: volunteer reports and
phone/user-side operation are treated as a separate node/application.

## Team module boundaries

The backend API is split by ownership so Acuifero and Vigia can move in parallel:

- Acuifero fixed-node work: `api/routers/acuifero.py`,
  `services/acuifero_assessment.py`, `adapters/video_assessment.py`
- Vigia volunteer/user work: `api/routers/vigia.py`,
  `services/report_structuring.py`, text adapters, Android/PWA report queues
- Shared integration: `api/routers/alerts.py`, `services/decision_engine.py`,
  `models/domain.py`, runtime settings, and sync

Use `develop` as the shared baseline for these boundaries, then branch from it
for feature work.

## Local Gemma runtime

Default Vigia/dev backend env for local report-structuring experiments:

```bash
ACUIFERO_LLM_ENABLED=true
ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_LLM_MODEL=gemma4:e2b
ACUIFERO_LLM_API_KEY=ollama
```

Production Acuifero node env on Raspberry Pi 8 GB:

- use LiteRT-LM with the upstream `gemma-4-E2B-it.litertlm` artifact
- keep `ACUIFERO_NODE_PROVIDER=litert`
- keep `ACUIFERO_NODE_BACKEND=gpu` for text/reasoning smoke checks
- keep `ACUIFERO_NODE_MULTIMODAL_BACKEND=cpu`
- keep `ACUIFERO_NODE_MULTIMODAL_VISION_BACKEND=cpu`
- keep `ACUIFERO_NODE_ENABLE_SPECULATIVE_DECODING=true`
- keep `ACUIFERO_NODE_MAX_OUTPUT_TOKENS=1024`
- keep `ACUIFERO_NODE_MULTIMODAL_MAX_OUTPUT_TOKENS=2048`
- keep `ACUIFERO_MULTIMODAL_ENABLED=true`
- keep `ACUIFERO_MULTIMODAL_MAX_FRAMES=1`
- keep `ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=512`
- use `ACUIFERO_GUARD_INTERVAL_SECONDS=300` for a frame/clip every five minutes
- store `ACUIFERO_DATA_DIR` on SSD/NVMe, not on the boot microSD

Measured Pi 5 status on this branch:

- LiteRT text smoke inference works with `backend=gpu`
- LiteRT one-image smoke inference works on the Pi with
  `ACUIFERO_NODE_BACKEND=gpu`,
  `ACUIFERO_NODE_MULTIMODAL_BACKEND=cpu`,
  `ACUIFERO_NODE_MULTIMODAL_VISION_BACKEND=cpu`,
  `ACUIFERO_NODE_MULTIMODAL_MAX_OUTPUT_TOKENS=2048`, and speculative decoding
  enabled
- the GPU vision path fails on Pi 5 because the WebGPU path lands on Mesa
  `llvmpipe` and exhausts the available buffer budget
- the current Pi profile therefore keeps text/reasoning on GPU and uses a
  CPU-only LiteRT engine for multimodal image inference

Measured end-to-end Acuifero endpoint evidence on Raspberry Pi 5:

- `/api/settings/runtime` returned `acuifero.provider=litert`,
  `acuifero.backend=gpu`, `acuifero.multimodal_backend=cpu`,
  `acuifero.multimodal_vision_backend=cpu`,
  `acuifero.speculative_decoding=true`, `acuifero.engine_ready=true`, and
  `acuifero.p1_runtime_ready=true`
- `POST /api/sites/silverado-fixed-cam-usgs/sample-node-analysis` returned
  `assessment_mode=gemma4-multimodal-v1`,
  `runner.mode=litert-multimodal-temporal`, `frames_analyzed=1`, and
  `alert.level=green`
- this endpoint result is the Acuifero full-flow P1 proof; the
  `litert_smoke.py --image` command is only a one-image runtime smoke test

Benchmark and ablation evidence:

- `docs/hackathon/benchmark-card.md` records the measured Pi 5 8 GB LiteRT-LM
  E2B runs. The current Python response path does not expose reliable token
  counts or streaming callbacks, so TTFT and decode tok/s are documented as not
  measured instead of estimated.
- Reusing the same GPU text engine in one process produced
  `RuntimeError: litert_lm_conversation_send_message failed`; the runtime now
  resets that cached engine and retries once. This avoids a direct fallback, but
  the retry path can add latency and increase process RSS.
- `docs/hackathon/e2b-e4b-ablation.md` keeps E2B as the Pi 5 8 GB operating
  profile. E4B GPU text/reasoning failed with WebGPU buffer/command errors on
  this hardware; E4B CPU and multimodal CPU/CPU are recorded only as fallback or
  Pi 16 GB / workstation candidates.
- Production actuator selection with `ACUIFERO_NODE_PROVIDER=litert` no longer
  calls Ollama. The current path is strict JSON structured tool selection
  through LiteRT, not native LiteRT function calling exposed by this wrapper.
  Real Pi smoke did not confirm parseable actuator JSON before external
  timeouts, so orange/red alerts retain deterministic recommended-actuator
  fallback for continuity.

For local development only, Acuifero can also be forced onto the old Ollama
path with `ACUIFERO_NODE_PROVIDER=ollama`. That mode is not a production Pi
runtime and is never used as an automatic fallback from LiteRT.

For the Raspberry Pi 16 GB / workstation production profile, use
`scripts/run_acuifero_pi16_multimodal_prod.sh`; it raises frames, image size,
context, timeout, retention, and analysis cadence while keeping the same
Gemma-first multimodal code path.

On Raspberry Pi OS, install the system video dependency first:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

Install and probe the LiteRT node runtime from the repo root:

```bash
export REPO_DIR=/opt/acuifero-vigia
cd "$REPO_DIR"
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -e backend/.[dev]
python3 scripts/fetch_litert_model.py
python3 scripts/fetch_demo_assets.py
python3 scripts/litert_smoke.py
./scripts/run_acuifero_pi8_multimodal_demo.sh
```

Run the fixed-camera guard loop from another terminal on the Pi:

```bash
cd backend
source .venv/bin/activate
ACUIFERO_CAMERA_SOURCE=/dev/video0 \
ACUIFERO_GUARD_SITE_ID=silverado-fixed-cam-usgs \
ACUIFERO_GUARD_INTERVAL_SECONDS=300 \
ACUIFERO_GUARD_CLIP_SECONDS=12 \
PYTHONPATH=src python3 ../scripts/node_guard.py
```

For local Linux development with one command, use:

```bash
./scripts/dev.sh
```

## Demo assets

Fetch or refresh the bundled demo clip and calibration frames:

```bash
python3 scripts/fetch_demo_assets.py
```

Bundled sample site:

- site id: `silverado-fixed-cam-usgs`
- source: USGS Silverado fixed camera clip
- local clip: `fixtures/media/usgs_silverado_fire_2015_fixed_cam.mp4`
- reference frame: `fixtures/frames/silverado_060s.jpg`

## Raspberry Pi fixed-node probe

For the real Raspberry Pi 8 GB node, use the operator probe script:

```bash
python3 scripts/pi_acuifero_node.py --site-id puente-arroyo-01 --synthetic
python3 scripts/pi_acuifero_node.py --site-id puente-arroyo-01 --camera /dev/video0 --duration 12
```

It checks backend/Gemma health, captures or generates a short fixed-camera clip,
uploads it to `POST /api/node/analyze`, and prints the assessment/alert summary.
See [`docs/raspberry-pi-acuifero-node.md`](docs/raspberry-pi-acuifero-node.md)
for the Pi environment, LiteRT bootstrap, sample data, and camera capture flow.

## Local setup

Bootstrap completo desde Linux:

```bash
./scripts/setup.sh
```

### Backend

Requirements:

- Python 3.10+
- `uv`

Install and seed:

```bash
cd backend
uv venv
. .venv/bin/activate
uv pip install -e .[dev]
python -m acuifero_vigia.scripts.seed
```

Run backend:

```bash
cd backend
PYTHONPATH=src uvicorn acuifero_vigia.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### Android

There is now an Android app module under `android/`.

Current Android scope:

- Compose app with dashboard, alerts, sites and detail screens
- sample-node analysis against the real backend
- volunteer report submission
- offline Room queue with manual flush and startup sync worker
- numeric calibration form
- configurable backend base URL for emulator or physical device

## Demo flow

1. Start backend and frontend.
2. Optionally start the local Gemma runtime with `./scripts/run_gemma_local.sh`.
3. Open `http://localhost:5173`.
4. Open the `Silverado Fixed Cam (USGS)` site.
5. Run `Analyze bundled sample` to execute the real fixed-camera clip through the backend.
6. Inspect the returned evidence frame, `temporal_summary`, runner info, and alert level.
7. Refresh the hydromet snapshot.
8. Adjust calibration on the calibration page if needed.
9. Submit a volunteer report from the `Report` page.
10. Toggle offline/online and flush the queue from the `Queue` page.

Smoke demo once the API is live:

```bash
python scripts/demo.py
```

## Reproducible smoke test

Start the stack in two terminals:

```bash
cd backend
PYTHONPATH=src python3 -m acuifero_vigia.scripts.seed
PYTHONPATH=src python3 -m uvicorn acuifero_vigia.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Then validate the live stack from a third terminal:

```bash
curl -sf http://127.0.0.1:8000/api/settings/runtime | jq
curl -sf http://127.0.0.1:8000/api/sites | jq '.[] | {id,name}'
curl -sf -X POST http://127.0.0.1:8000/api/sites/silverado-fixed-cam-usgs/sample-node-analysis | jq '{site_id: .observation.site_id, frames_analyzed: .observation.frames_analyzed, assessment_mode: .observation.assessment_mode, runner: .observation.runner.mode, alert_level: .alert.level}'
curl -sf -X POST http://127.0.0.1:8000/api/reports \
  -F site_id=silverado-fixed-cam-usgs \
  -F reporter_name='Operador Demo' \
  -F reporter_role='brigadista' \
  -F transcript_text='El agua ya cruzo la marca critica y trae barro, evacuar zona baja.' \
  -F offline_created=true | jq '{report_id: .report.id, parser_source: .parsed.parser_source, urgency: .parsed.urgency, alert_level: .alert.level}'
```

Expected on a healthy setup:

- `/api/settings/runtime` returns `acuifero.provider=litert`, `acuifero.backend=gpu`, `acuifero.multimodal_backend=cpu`, `acuifero.multimodal_vision_backend=cpu`, `acuifero.speculative_decoding=true`, `acuifero.engine_ready=true`, `acuifero.p1_runtime_ready=true`, `acuifero.model_path`, `acuifero.node_profile=raspberry-pi-8gb-multimodal-demo`, and `acuifero.multimodal_enabled=true`
- sample-node analysis returns `frames_analyzed>=1`, `assessment_mode=gemma4-multimodal-v1`, and `runner.mode=litert-multimodal-temporal`
- report submission returns `200 OK` and creates a fused red alert for the sample site

## Main API routes

- `GET /api/health`
- `GET /api/settings/runtime`
- `GET /api/sites`
- `GET /api/sites/{site_id}`
- `GET|POST /api/sites/{site_id}/calibration`
- `GET /api/sites/{site_id}/external-snapshot`
- `POST /api/sites/{site_id}/external-snapshot/refresh`
- `POST /api/node/analyze`
- `POST /api/sites/{site_id}/sample-node-analysis`
- `POST /api/reports`
- `GET /api/alerts`
- `POST /api/alerts/recompute`
- `POST /api/sync/flush`
- `GET|POST /api/settings/connectivity`

## Test status

Backend coverage includes:

- health and connectivity endpoints
- volunteer report structuring + sync
- persisted report attachments
- Gemma-first fixed-node temporal assessment on a synthetic upload clip
- bundled sample-node analysis endpoint

Run checks with:

```bash
cd backend && PYTHONPATH=src pytest -q
cd frontend && npm run build
cd frontend && npm test
cd frontend && npm run lint
```

## Current limitations

- Calibration is numeric and rectangular in the UI, not click-to-draw.
- The temporal evidence builder is still tuned for fixed cameras with stable framing; moving cameras are out of scope.
- The fixed-node runtime now targets LiteRT-LM via the Python API; the generic upstream artifact wired here is `gemma-4-E2B-it.litertlm`.
- Hydromet data is real but model-based; it is not a replacement for a local gauging station.
- Raspberry Pi 8 GB remains a constrained profile, so the default path keeps a single curated frame, uses GPU for text/reasoning checks, and uses CPU for LiteRT multimodal image inference with speculative decoding enabled.
- LiteRT-LM benchmark output currently lacks reliable TTFT and decode tok/s
  because this wrapper receives only final responses; wall-clock and RSS are the
  measured quantitative evidence.
- E4B is not the Pi 5 8 GB production profile. It is documented as an ablation
  with GPU failures and CPU fallback measurements.
- LiteRT actuator selection is structured JSON prompting, not native function
  calling through a public wrapper API; deterministic fallback preserves
  orange/red actuation when model selection times out or returns malformed JSON.
