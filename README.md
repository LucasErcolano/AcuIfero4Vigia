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

## Overview

The system has three real signal paths:

- `Acuifero`: Gemma-first fixed-node temporal assessment over real clips
- `Vigia`: volunteer field reports stored offline-first in the PWA
- live hydrometeorological enrichment from Open-Meteo APIs

The fixed `Acuifero` node is now sized for a Raspberry Pi 8 GB edge box with
local storage. It uses OpenCV locally to curate compact temporal evidence, then
asks a local OpenAI-compatible Gemma runtime for a text verdict over those
numeric/temporal hints. `Vigia` remains a separate volunteer/user node.

## What is real in this repo

- Node analysis samples fixed-camera video, curates a temporal evidence bundle, and asks Gemma to emit the node assessment package.
- OpenCV still runs locally, but only for frame curation, ROI/band processing, overlays, and numeric hints passed into Gemma.
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
- 128 GB or larger USB SSD/NVMe for `backend/data`
- fixed camera input uploaded to the backend or bound as per-site sample media
- local SQLite for `edge.db`, audit artifacts, and the sync queue

The Raspberry profile is the default:

```bash
ACUIFERO_NODE_PROFILE=raspberry-pi-8gb
ACUIFERO_DATA_DIR=/mnt/acuifero/data
ACUIFERO_MAX_CURATED_FRAMES=3
ACUIFERO_ARTIFACT_RETENTION_DAYS=7
ACUIFERO_MULTIMODAL_ENABLED=false
```

On this profile, Acuifero still curates frames locally, but the Gemma call is
text-first over the temporal evidence pack. Inline multimodal frame prompting is
disabled by default to keep RAM and latency inside a Raspberry Pi 8 GB budget.
Set `ACUIFERO_MULTIMODAL_ENABLED=true` only for a stronger node.

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

Default backend env:

```bash
ACUIFERO_LLM_ENABLED=true
ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_LLM_MODEL=gemma4:e2b
ACUIFERO_LLM_API_KEY=ollama
```

Practical recommendation for the Raspberry Pi 8 GB Acuifero node:

- start with `gemma4:e2b`
- keep `ACUIFERO_MULTIMODAL_ENABLED=false`
- keep `ACUIFERO_MAX_CURATED_FRAMES=3`
- store `ACUIFERO_DATA_DIR` on SSD/NVMe, not on the boot microSD

On bigger x86/GPU nodes, you can raise curated frames and enable multimodal
prompting, but that is not the default Acuifero deployment target.

Install and start the local runtime from the repo root:

```bash
./scripts/install_ollama_local.sh
./scripts/run_gemma_local.sh
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
for the Pi environment, Ollama startup, sample data, and camera capture flow.

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

With Ollama running locally and `gemma4:e2b` already pulled:

```bash
./tools/ollama/bin/ollama list
```

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

- `/api/settings/runtime` returns `llm.reachable=true`, `model=gemma4:e2b`, and `acuifero.node_profile=raspberry-pi-8gb`
- sample-node analysis returns `frames_analyzed=126`, `assessment_mode=temporal-gemma-v1`, and `alert_level=red` for the bundled USGS clip
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
- The default LiteRT runner is a stub target; the implemented fixed-node runtime today is the Ollama runner with deterministic fallback.
- Hydromet data is real but model-based; it is not a replacement for a local gauging station.
- Raspberry Pi 8 GB is a text-first Acuifero node target. Multimodal Gemma over inline images should be treated as an optional stronger-node mode.
