# Architecture

## System shape

```text
[ Fixed Camera Clip ] ----> [ FastAPI Backend ] ----> [ edge.db ] ----> [ sync queue ] ----> [ central.db ]
[ Bundled USGS Clip ] ----> [ sample-node-analysis ]
[ Volunteer PWA ] --------> [ FastAPI Backend ]
[ Open-Meteo APIs ] -----> [ Hydromet Snapshot ]
[ Local Gemma via Ollama ] -> [ Structured Report Parser ]
```

## Responsibilities

### Fixed-node analysis

- input: uploaded video clip from a fixed camera or a bundled per-site sample clip
- processing:
  - sample roughly 1 FPS
  - apply the stored ROI mask
  - search only inside the calibrated band between reference and critical lines
  - score the highest-risk temporal window instead of the clip-wide median
- output: `NodeObservation` plus a recomputed `FusedAlert`

### Volunteer report flow

- input: site, operator metadata, transcript, optional photo/audio attachments
- PWA stores reports offline first in IndexedDB
- backend persists the report, structures it with local Gemma when available, and falls back to deterministic rules otherwise
- output: `VolunteerReport`, `ParsedObservation`, and a recomputed `FusedAlert`

### Live hydromet context

- provider: Open-Meteo weather forecast API + Open-Meteo flood API
- lookup key: site latitude/longitude
- output: `HydrometSnapshot`
- used to enrich site detail pages and to boost fused risk when weather and river conditions support escalation

### Alert fusion

- takes the strongest available site signal as the base score
- adds a boost when multiple sources support the same escalation
- produces a `FusedAlert` and decides whether a local alarm should be triggered

## Runtime model contract

The backend expects an OpenAI-compatible chat endpoint:

- base URL: `ACUIFERO_LLM_BASE_URL`
- model name: `ACUIFERO_LLM_MODEL`
- endpoints used: `/v1/models` and `/v1/chat/completions`

Default local runtime for this repo:

- Ollama installed under `tools/ollama`
- `gemma4:e2b` as the default model for 12 GB VRAM systems
- repo helper scripts: `scripts/install_ollama_local.sh` and `scripts/run_gemma_local.sh`

## Persistence

### edge.db

Operational local state:

- `Site`
- `SiteCalibration`
- `NodeObservation`
- `VolunteerReport`
- `ParsedObservation`
- `HydrometSnapshot`
- `FusedAlert`
- `SyncQueueItem`

### central.db

Receives synced copies of queued entities from `edge.db`.

## UI surfaces

- `Dashboard`: current alerts + site access
- `Site Detail`: hydromet refresh, reference frame preview, bundled sample analysis, upload analysis
- `Calibration`: save ROI and threshold lines against a stored site frame
- `Report`: volunteer observation form with offline-first queueing
- `Queue`: flush locally stored reports
- `Runtime`: local Gemma endpoint + hydromet connectivity status
