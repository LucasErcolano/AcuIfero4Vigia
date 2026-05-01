# Architecture

## System shape

```text
[ Fixed Camera Clip ] ----> [ Temporal Evidence Builder ] ----> [ Gemma Assessment Runner ] ----> [ Acuifero Assessment Pack ]
[ Bundled USGS Clip ] ----> [ sample-node-analysis ] --------------------------------------------^
[ Volunteer PWA ] --------> [ FastAPI Backend ] -------------------------------------------------> [ edge.db ] -> [ sync queue ] -> [ central.db ]
[ Open-Meteo APIs ] ------> [ Hydromet Snapshot ]
[ Local Gemma via Ollama ] -> [ Acuifero Node Assessment + Alert Reasoning ]
[ Separate Vigia App ] ----> [ Volunteer Reports / User Node ]
```

## Responsibilities

### Acuifero fixed-node assessment

- input: uploaded video clip from a fixed camera or a bundled per-site sample clip
- processing:
  - sample roughly 1 FPS
  - apply the stored ROI mask
  - curate a bounded temporal frame bundle around the highest-risk window
  - preserve non-semantic hints such as motion, contrast, edge strength, and waterline ratio hints
  - hand the compact temporal evidence pack to Gemma for the actual node verdict
- output:
  - `assessment_level`
  - `assessment_score`
  - `temporal_summary`
  - `reasoning_summary`
  - `reasoning_steps`
  - `critical_evidence`
  - persisted audit artifacts

### Volunteer report flow

- input: site, operator metadata, transcript, optional photo/audio attachments
- PWA stores reports offline first in IndexedDB
- backend persists the report, structures it with local Gemma when available, and falls back to deterministic rules otherwise
- output: `VolunteerReport`, `ParsedObservation`, and a recomputed `FusedAlert`

## Backend Module Boundaries

`backend/src/acuifero_vigia/main.py` is intentionally thin. It creates the
FastAPI app, mounts static assets, and includes routers.

- `api/routers/acuifero.py`: fixed-camera node analysis, sample-node analysis,
  frame explanation, and Acuifero assessment artifact creation.
- `api/routers/vigia.py`: volunteer report submission and report listing.
- `api/routers/sites.py`: shared site registry, calibration, and hydromet
  snapshots.
- `api/routers/alerts.py`: shared fused-alert reads, recomputation, and SINAGIR
  export.
- `api/routers/runtime.py`: health, runtime status, and connectivity toggle.
- `api/routers/sync.py`: edge-to-central queue flush.
- `api/deps.py`: shared runtime singletons such as the LLM client, Acuifero
  engine, image assessor, text structurer, external-data service, and sync queue
  helper.
- `api/serializers.py`: API response shaping for sites, hydromet snapshots, and
  node observations.

Team ownership guideline:

- Acuifero work should prefer `services/acuifero_assessment.py`,
  `adapters/video_assessment.py`, and `api/routers/acuifero.py`.
- Vigia work should prefer `services/report_structuring.py`, text adapters,
  `api/routers/vigia.py`, and the Android/PWA report queues.
- `services/decision_engine.py`, `api/routers/alerts.py`, domain models, and
  shared docs are integration surfaces. Coordinate changes there before merging.

### Live hydromet context

- provider: Open-Meteo weather forecast API + Open-Meteo flood API
- lookup key: site latitude/longitude
- output: `HydrometSnapshot`
- used to enrich site detail pages and to boost fused risk when weather and river conditions support escalation

### Alert fusion

- takes the strongest available site signal as the base score
- uses the Gemma-first node assessment package as the node input
- adds a boost when multiple sources support the same escalation
- produces a `FusedAlert` and decides whether a local alarm should be triggered

## Runtime model contract

The fixed `Acuifero` node expects an OpenAI-compatible chat endpoint:

- base URL: `ACUIFERO_LLM_BASE_URL`
- model name: `ACUIFERO_LLM_MODEL`
- endpoints used: `/v1/models`, `/v1/chat/completions`, and Ollama native `/api/chat` when available

Default local runtime for the fixed Acuifero node:

- Ollama installed under `tools/ollama`
- `gemma4:e2b` as the default model for a Raspberry Pi 5 with 8 GB RAM
- `ACUIFERO_NODE_PROFILE=raspberry-pi-8gb`
- `ACUIFERO_DATA_DIR=/mnt/acuifero/data` on SSD/NVMe
- `ACUIFERO_MAX_CURATED_FRAMES=3`
- `ACUIFERO_ARTIFACT_RETENTION_DAYS=7`
- `ACUIFERO_MULTIMODAL_ENABLED=false`
- repo helper scripts: `scripts/install_ollama_local.sh` and `scripts/run_gemma_local.sh`
- LiteRT runner kept as an explicit future target, not the current default implementation

On Raspberry Pi 8 GB, Acuifero is text-first: OpenCV curates frames and numeric
temporal hints locally, while Gemma receives the bounded evidence summary. Inline
multimodal image prompting is intentionally disabled by default for RAM and
latency. Bigger x86/GPU nodes may opt in with `ACUIFERO_MULTIMODAL_ENABLED=true`.

`Vigia` is not part of this fixed-node hardware target. It remains a separate
volunteer/user node and can run on Android/PWA/client hardware independently.

## Persistence

### edge.db

Operational local state:

- `Site`
- `SiteCalibration`
- `NodeObservation`
- `AcuiferoAssessmentArtifact`
- `VolunteerReport`
- `ParsedObservation`
- `HydrometSnapshot`
- `FusedAlert`
- `SyncQueueItem`

`NodeObservation` is the compatibility-facing projection. `AcuiferoAssessmentArtifact` stores the richer audit pack for demos and review.

### central.db

Receives synced copies of queued entities from `edge.db`.

## UI surfaces

- `Dashboard`: current alerts + site access
- `Site Detail`: hydromet refresh, reference frame preview, bundled sample analysis, upload analysis, temporal summary, runner metadata, and evidence artifacts
- `Calibration`: save ROI and threshold lines against a stored site frame
- `Report`: volunteer observation form with offline-first queueing
- `Queue`: flush locally stored reports
- `Runtime`: local Gemma endpoint + hydromet connectivity status
