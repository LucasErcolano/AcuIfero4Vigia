# Acuifero 4 + Vigia

Browser-first flood early-warning MVP with three real signal paths:

- fixed-node video analysis using OpenCV over real clips
- volunteer field reports stored offline-first in the PWA
- live hydrometeorological enrichment from Open-Meteo APIs

The backend is wired for a local Gemma runtime through an OpenAI-compatible endpoint. By default it now targets a local Ollama server.

## What is real in this MVP

- Node analysis samples fixed-camera video and scores the highest-risk window instead of mocking detections.
- Volunteer reports are parsed into structured observations with a local Gemma adapter and a deterministic fallback.
- Fused alerts are recomputed from node, volunteer, and hydromet signals.
- Hydromet context is fetched from real public APIs using site coordinates.
- Edge-to-central sync still uses local SQLite databases, but the queue and replication flow are real.
- The repo includes a real fixed-camera demo site based on the public-domain USGS Silverado clip.

## Local Gemma runtime

Default backend env:

```bash
ACUIFERO_LLM_ENABLED=true
ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_LLM_MODEL=gemma4:e2b
ACUIFERO_LLM_API_KEY=ollama
```

Practical recommendation for a 12 GB VRAM RTX 3060:

- start with `gemma4:e2b`
- move to `gemma4:e4b` only if VRAM headroom and latency stay acceptable
- keep video analysis in OpenCV; use Gemma for text structuring and operator-facing reasoning

Install and start the local runtime from the repo root:

```bash
./scripts/install_ollama_local.sh
./scripts/run_gemma_local.sh
```

That installs Ollama under `tools/ollama`, starts the local API, and pulls `gemma4:e2b` by default.

For local Linux development with one command, use:

```bash
./scripts/dev.sh
```

That script starts or reuses Ollama, seeds the backend, launches backend and frontend, writes logs under `backend/data/logs`, and stops both app servers on `Ctrl+C`.

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

## Local setup

Bootstrap completo desde Linux:

```bash
./scripts/setup.sh
```

Ese script instala dependencias, baja el clip demo, aplica el seed idempotente y deja el frontend listo.

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

Optional env bootstrap:

```bash
cp backend/.env.example backend/.env
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

## Demo flow

1. Start backend and frontend.
2. Optionally start the local Gemma runtime with `./scripts/run_gemma_local.sh`.
3. Open `http://localhost:5173`.
4. Open the `Silverado Fixed Cam (USGS)` site.
5. Run `Analyze bundled sample` to execute the real fixed-camera clip through the backend.
6. Inspect the returned evidence frame and alert level.
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

Or start everything at once:

```bash
./scripts/dev.sh
```

Then validate the live stack from a third terminal:

```bash
curl -sf http://127.0.0.1:8000/api/settings/runtime | jq
curl -sf http://127.0.0.1:8000/api/sites | jq '.[] | {id,name}'
curl -sf -X POST http://127.0.0.1:8000/api/sites/silverado-fixed-cam-usgs/sample-node-analysis | jq '{site_id: .observation.site_id, frames_analyzed: .observation.frames_analyzed, waterline_ratio: .observation.waterline_ratio, alert_level: .alert.level}'
curl -sf -X POST http://127.0.0.1:8000/api/reports \
  -F site_id=silverado-fixed-cam-usgs \
  -F reporter_name='Operador Demo' \
  -F reporter_role='brigadista' \
  -F transcript_text='El agua ya cruzo la marca critica y trae barro, evacuar zona baja.' \
  -F offline_created=true | jq '{report_id: .report.id, parser_source: .parsed.parser_source, urgency: .parsed.urgency, alert_level: .alert.level}'
```

Expected on a healthy setup:

- `/api/settings/runtime` returns `llm.reachable=true` and `model=gemma4:e2b`
- sample-node analysis returns `frames_analyzed=126` and `alert_level=red` for the bundled USGS clip
- report submission returns `200 OK` and creates a fused red alert for the sample site

Notes:

- Run the seed before the smoke test, otherwise `silverado-fixed-cam-usgs` will not exist.
- The first local LLM request can be noticeably slower while Ollama warms the model.
- With local Ollama, the backend first uses the native `/api/chat` JSON mode for Gemma and then falls back to the OpenAI-compatible endpoint.
- `parser_source` should normally be `llm` on a healthy local Gemma setup, and falls back to `rules` only if the model times out or returns unusable output.

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
- fixed-node analysis on a synthetic upload clip
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
- The fixed-node analyzer is heuristic and tuned for fixed cameras with stable framing.
- Hydromet data is real but model-based; it is not a replacement for a local gauging station.
- `gemma4:e4b` may be too tight on some 12 GB systems depending on concurrent GPU load.
