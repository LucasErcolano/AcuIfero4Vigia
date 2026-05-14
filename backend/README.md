# Backend

FastAPI service for the Acuifero 4 + Vigia backend.

## Key services

- Gemma-first fixed-camera multimodal assessment through `AcuiferoAssessmentEngine`
- temporal frame extraction with ffmpeg and Pillow optimization; no OpenCV in the Acuifero visual decision path
- persisted audit artifact packs for node analyses
- volunteer report parsing through a local Gemma-compatible endpoint with rule fallback
- live hydromet snapshots from Open-Meteo
- fused alert scoring and SQLite sync replication
- bundled sample clip analysis for the USGS Silverado demo site

## Runtime defaults

The fixed Acuifero node defaults to a Raspberry Pi 8 GB multimodal demo profile and a local
Ollama-compatible endpoint:

Install system ffmpeg before running video capture or sample-clip analysis:

```bash
sudo apt-get install -y ffmpeg
```

```bash
ACUIFERO_NODE_PROFILE=raspberry-pi-8gb-multimodal-demo
ACUIFERO_DATA_DIR=/mnt/acuifero/data
ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_LLM_MODEL=gemma4:e2b
ACUIFERO_LLM_API_KEY=ollama
ACUIFERO_MULTIMODAL_ENABLED=true
ACUIFERO_MULTIMODAL_VERIFIER_ENABLED=false
ACUIFERO_MULTIMODAL_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_MULTIMODAL_MODEL=gemma4:e2b
ACUIFERO_MULTIMODAL_MAX_FRAMES=1
ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=300
ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=512
ACUIFERO_MULTIMODAL_NUM_CTX=1024
ACUIFERO_MAX_CURATED_FRAMES=1
ACUIFERO_ARTIFACT_RETENTION_DAYS=3
```

For this profile, Acuifero sends one optimized frame to Gemma 4 multimodal and
lets the model perform the visual interpretation. The Raspberry Pi 16 GB /
workstation profile uses the same path with more frames and context through
`../scripts/run_acuifero_pi16_multimodal_prod.sh`. Vigia is treated as a
separate user/volunteer node and is not sized by this Raspberry Pi fixed-node profile.

Use `../scripts/node_guard.py` on the Pi to record short clips from
`ACUIFERO_CAMERA_SOURCE` and submit them to `/api/node/analyze` on a fixed
interval. The backend extracts the configured number of frames and sends them
directly to Gemma 4 multimodal.

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
