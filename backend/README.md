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

The fixed Acuifero node now defaults to a Raspberry Pi 8 GB multimodal demo profile and an
embedded LiteRT-LM runtime:

Install system ffmpeg before running video capture or sample-clip analysis:

```bash
sudo apt-get install -y ffmpeg
```

```bash
ACUIFERO_NODE_PROFILE=raspberry-pi-8gb-multimodal-demo
ACUIFERO_DATA_DIR=/mnt/acuifero/data
ACUIFERO_NODE_PROVIDER=litert
ACUIFERO_NODE_MODEL_PATH=backend/data/models/gemma-4-E2B-it.litertlm
ACUIFERO_NODE_BACKEND=gpu
ACUIFERO_NODE_MULTIMODAL_BACKEND=cpu
ACUIFERO_NODE_MULTIMODAL_VISION_BACKEND=cpu
ACUIFERO_NODE_CACHE_DIR=backend/data/litert-cache
ACUIFERO_NODE_ENABLE_SPECULATIVE_DECODING=true
ACUIFERO_NODE_MAX_OUTPUT_TOKENS=1024
ACUIFERO_NODE_MULTIMODAL_MAX_OUTPUT_TOKENS=2048
ACUIFERO_MULTIMODAL_ENABLED=true
ACUIFERO_MULTIMODAL_VERIFIER_ENABLED=false
ACUIFERO_MULTIMODAL_MODEL=gemma-4-E2B-it.litertlm
ACUIFERO_MULTIMODAL_MAX_FRAMES=1
ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=300
ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=512
ACUIFERO_MULTIMODAL_NUM_CTX=1024
ACUIFERO_MAX_CURATED_FRAMES=1
ACUIFERO_ARTIFACT_RETENTION_DAYS=3
```

For this profile, Acuifero prepares one optimized frame and attempts Gemma 4
multimodal through LiteRT-LM. On the measured Raspberry Pi 5 setup in this
branch, text and reasoning smoke inference work with `gpu` and speculative
decoding enabled. The GPU vision path fails on the software WebGPU stack, but
one-image LiteRT multimodal smoke succeeds on the Pi with the CPU multimodal
engine and a 2048-token engine budget. With 1024 or fewer multimodal tokens the
image path can fail before inference because the vision patches exceed the
token cap.
The Raspberry Pi 16 GB / workstation profile
uses the same path with more frames and context through
`../scripts/run_acuifero_pi16_multimodal_prod.sh`. Vigia is treated as a
separate user/volunteer node and is not sized by this Raspberry Pi fixed-node
profile.

For local development only, the fixed node can still use Ollama by setting
`ACUIFERO_NODE_PROVIDER=ollama`. That path is explicit dev mode only; LiteRT
never falls back to Ollama automatically in production.

Download the model once before the first real run:

```bash
python ../scripts/fetch_litert_model.py
python ../scripts/fetch_demo_assets.py
python ../scripts/litert_smoke.py
```

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
