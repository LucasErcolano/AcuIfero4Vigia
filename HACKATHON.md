# Gemma 4 Good Hackathon - Submission

Track: **Global Resilience**. Prize target: **LiteRT Prize (USD 10,000)**.

## Judging criteria alignment

### 1. Why not cloud GPT-4? - Gemma decides locally on the node

`Acuifero` is no longer "OpenCV plus explanation". The fixed node now builds a
temporal evidence pack and asks Gemma to produce the node assessment package:
`assessment_level`, `assessment_score`, `temporal_summary`,
`reasoning_summary`, `reasoning_steps`, and `critical_evidence`.

Proof: backend node-analysis endpoints and [`docs/architecture.md`](docs/architecture.md).

### 2. Auditable reasoning instead of a black box

Every non-green `FusedAlert` exposes a Gemma-produced Spanish reasoning block
that cites specific signals plus a deterministic rule trace. Judges can inspect
`GET /api/alerts/{id}` live.

Proof: [`docs/hackathon/thinking-mode.md`](docs/hackathon/thinking-mode.md).

### 3. Multimodal temporal evidence, not just a single frame

The demo node assessment now persists a rich audit pack with curated frames,
evidence imagery, runner metadata, and fallback status. The evidence-frame
description remains in the UI, but the architectural claim is temporal Gemma
reasoning over a curated sequence.

Proof: [`docs/hackathon/multimodal-comparison.md`](docs/hackathon/multimodal-comparison.md).

### 4. Rioplatense linguistic specialization

82-example corpus across 6 provinces. `GemmaFewShotTextStructurer` with 12
exemplars. Benchmark: rules 45% -> few-shot ~80% on held-out test split.

Proof: [`docs/hackathon/rioplatense_eval.md`](docs/hackathon/rioplatense_eval.md).

### 5. Connectivity-loss resilience

`scripts/demo_connectivity.py` runs: online report -> offline -> queued report
-> local node analysis -> **audible siren** -> online -> queue drains.

### 6. SINAGIR compatibility

`POST /api/alerts/{id}/export-sinagir` returns a schema-tagged, documented
payload. Field-by-field mapping published.

Proof: [`docs/hackathon/sinagir-mapping.md`](docs/hackathon/sinagir-mapping.md).

### 7. On-device Android path

`android/.../data/GemmaOnDevice.kt` wraps MediaPipe LLM Inference for Gemma
`.task` files. Volunteer report structuring runs fully on-device with no
silent backend fallback.

Proof: [`docs/hackathon/android_gemma.md`](docs/hackathon/android_gemma.md).

## Pitch video script

0:00-0:15 - context: Argentina's Litoral flood problem; local-alert gap under connectivity loss.

0:15-0:45 - Android volunteer flow: photo + voice -> fully on-device Gemma structuring.

0:45-1:20 - fixed-node analysis on the Silverado clip. Show the curated evidence sequence, `temporal_summary`, runner mode, and resulting alert.

1:20-1:45 - evidence frame overlay plus Gemma's Spanish description as a supporting view, not as the main architectural claim.

1:45-2:05 - connectivity-loss live: wifi off, red banner, offline report queued, node alert fires, **siren audible**, wifi on, queue drains.

2:05-2:25 - alert card with the reasoning chain expanding on screen.

2:25-2:40 - SINAGIR mapping and Plan Nacional 2025-2029 alignment close.

## Reproduce the demo

```bash
./scripts/setup.sh
PYTHONPATH=backend/src python3 -m acuifero_vigia.scripts.seed
./scripts/dev.sh
python3 scripts/demo_connectivity.py
```

## Test suite

```bash
cd backend && PYTHONPATH=src pytest -q
cd frontend && npm test && npm run build
```
