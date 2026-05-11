# Backend

FastAPI service for the Acuifero 4 + Vigia backend.

## Key services

- Gemma-first fixed-camera temporal assessment through `AcuiferoAssessmentEngine`
- temporal evidence curation with OpenCV used only for sampling, ROI/band processing, overlays, and numeric hints
- persisted audit artifact packs for node analyses
- volunteer report parsing through a local Gemma-compatible endpoint with rule fallback
- live hydromet snapshots from Open-Meteo
- fused alert scoring and SQLite sync replication
- bundled sample clip analysis for the USGS Silverado demo site

## Runtime defaults

The fixed Acuifero node defaults to a Raspberry Pi 8 GB profile and a local
Ollama-compatible endpoint:

```bash
ACUIFERO_NODE_PROFILE=raspberry-pi-8gb-hybrid
ACUIFERO_DATA_DIR=/mnt/acuifero/data
ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_LLM_MODEL=gemma4:e2b
ACUIFERO_LLM_API_KEY=ollama
ACUIFERO_MULTIMODAL_ENABLED=false
ACUIFERO_MULTIMODAL_VERIFIER_ENABLED=true
ACUIFERO_MULTIMODAL_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_MULTIMODAL_MODEL=gemma4:e2b
ACUIFERO_MULTIMODAL_MIN_INTERVAL_SECONDS=300
ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=768
ACUIFERO_MULTIMODAL_NUM_CTX=2048
ACUIFERO_MAX_CURATED_FRAMES=3
ACUIFERO_ARTIFACT_RETENTION_DAYS=7
```

For this profile, Acuifero sends Gemma a compact text evidence pack produced
from fixed-camera frames. OpenCV remains the always-on visual worker. A separate
Gemma 4 multimodal verifier can inspect one optimized evidence frame every five
minutes or on critical events. Vigia is treated as a separate user/volunteer node
and is not sized by this Raspberry Pi fixed-node profile.

Use `../scripts/node_guard.py` on the Pi to record short clips from
`ACUIFERO_CAMERA_SOURCE` and submit them to `/api/node/analyze` on a fixed
interval. The backend decides whether the expensive multimodal verifier should
run for that analysis.

## Core node-assessment contract

The fixed-node pipeline now produces a node assessment package centered on:

- `assessment_level`
- `assessment_score`
- `temporal_summary`
- `reasoning_summary`
- `reasoning_steps`
- `critical_evidence`
- `runner_name`
- `runner_mode`
- `fallback_used`
- audit artifact references

The external API surface remains stable; these fields are added to the existing node-analysis responses.

## Seed and tests

```bash
PYTHONPATH=src python -m acuifero_vigia.scripts.seed
PYTHONPATH=src pytest -q
```
