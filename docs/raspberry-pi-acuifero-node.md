# Raspberry Pi Acuifero fixed node

This guide prepares the fixed Acuifero camera node for the new Gemma 4
multimodal-only plan. The Raspberry Pi 8 GB profile is a minimal demo; the
Raspberry Pi 16 GB / workstation profile is the production code path we can
exercise locally before buying or deploying the larger Pi.

## Pi 8 demo profile

```bash
export ACUIFERO_NODE_PROFILE=raspberry-pi-8gb-multimodal-demo
export ACUIFERO_DATA_DIR=/mnt/acuifero/data
export ACUIFERO_UPLOAD_DIR=/mnt/acuifero/data/uploads
export ACUIFERO_NODE_PROVIDER=litert
export ACUIFERO_NODE_MODEL_PATH=/mnt/acuifero/data/models/gemma-4-E2B-it.litertlm
export ACUIFERO_NODE_BACKEND=gpu
export ACUIFERO_NODE_VISION_BACKEND=gpu
export ACUIFERO_NODE_CACHE_DIR=/mnt/acuifero/data/litert-cache
export ACUIFERO_NODE_ENABLE_SPECULATIVE_DECODING=true
export ACUIFERO_NODE_MAX_OUTPUT_TOKENS=1024
export ACUIFERO_MULTIMODAL_ENABLED=true
export ACUIFERO_MULTIMODAL_MODEL=gemma-4-E2B-it.litertlm
export ACUIFERO_MULTIMODAL_MAX_FRAMES=1
export ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=300
export ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=512
export ACUIFERO_MULTIMODAL_NUM_CTX=1024
export ACUIFERO_MULTIMODAL_TIMEOUT_SECONDS=300
```

This mode extracts one small frame from each short clip using ffmpeg, optimizes
it with Pillow, and sends it directly to Gemma 4 multimodal. There is no OpenCV
visual analysis in this path.

Measured Raspberry Pi 5 status on this branch:

- `ACUIFERO_NODE_BACKEND=gpu` works for LiteRT text inference.
- `ACUIFERO_NODE_BACKEND=cpu` fails during engine creation on this device.
- `litert-lm-api==0.11.0` is installed in `backend/.venv`.
- Verified model path: `~/AcuIfero4Vigia-litert/backend/data/models/gemma-4-E2B-it.litertlm`.
- Verified sample clip path:
  `~/AcuIfero4Vigia-litert/fixtures/media/usgs_silverado_fire_2015_fixed_cam.mp4`.
- Gemma 4 E2B multimodal still fails on Pi 5 because LiteRT picks Mesa
  `llvmpipe` WebGPU and the vision encoder exceeds the available buffer size.
- Generic cold text smoke is real LiteRT inference but slow on this Pi:
  `elapsed_seconds=130` in the measured run.
- On the Windows verification machine, `ACUIFERO_NODE_BACKEND=gpu` plus
  `ACUIFERO_NODE_ENABLE_SPECULATIVE_DECODING=true` works for text, reasoning,
  and one-image multimodal smoke. The one-image smoke requires at least
  `ACUIFERO_NODE_MAX_OUTPUT_TOKENS=512`; the full temporal Acuifero prompt needs
  the current 1024-token budget. At 256 tokens LiteRT rejects the simple image
  input with `Input token ids are too long. Exceeding the maximum number of tokens allowed: 300 >= 256`.
- Acuifero alert reasoning text now has a Pi-short prompt. A previous measured
  Pi run with a 256-token engine produced `reasoning_model=gemma-4-E2B-it.litertlm`
  in `350.18s` with about `3120 MB` max RSS. This is real LiteRT-LM inference,
  but too slow to claim stable operational latency on Raspberry Pi 5 8 GB. The
  current profile uses 1024 tokens so the same engine budget can also admit the
  full one-frame temporal multimodal prompt.
- Result today: `sample-node-analysis` reaches conservative fallback
  (`runner.mode=multimodal-unavailable-fallback`) on this exact hardware/model
  pairing.

## Pi 16 / workstation production profile

```bash
export ACUIFERO_NODE_PROFILE=raspberry-pi-16gb-multimodal-prod
export ACUIFERO_MULTIMODAL_MAX_FRAMES=4
export ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=60
export ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=960
export ACUIFERO_MULTIMODAL_NUM_CTX=4096
export ACUIFERO_MULTIMODAL_TIMEOUT_SECONDS=240
```

Use `scripts/run_acuifero_pi16_multimodal_prod.sh` on a workstation now, and on
a 16 GB Pi later. It keeps the exact same backend flow as the Pi 8 demo, just
with more visual evidence per analysis.

## LiteRT bootstrap

From the repo root, after creating `backend/.venv`:

```bash
source backend/.venv/bin/activate
python -m pip install -e backend/.[dev]
python scripts/fetch_litert_model.py
python scripts/fetch_demo_assets.py
python scripts/litert_smoke.py
```

This project uses the Python API (`litert-lm-api==0.11.0`) for production node
inference. Ollama remains acceptable only as an explicit development path for
Vigia or local experimentation, not as the Acuifero production engine on the Pi.

## Reproduce measured LiteRT inference on the Pi

From `~/AcuIfero4Vigia-litert`:

```bash
export PYTHONPATH=$PWD/backend/src
export ACUIFERO_NODE_PROVIDER=litert
export ACUIFERO_NODE_MODEL_PATH=$PWD/backend/data/models/gemma-4-E2B-it.litertlm
export ACUIFERO_NODE_BACKEND=gpu
export ACUIFERO_NODE_VISION_BACKEND=gpu
export ACUIFERO_NODE_CACHE_DIR=$PWD/backend/data/litert-cache
export ACUIFERO_NODE_ENABLE_SPECULATIVE_DECODING=true
export ACUIFERO_NODE_MAX_OUTPUT_TOKENS=1024
backend/.venv/bin/python scripts/litert_smoke.py --reasoning
```

Expected success signal:

- first JSON: `health.reachable=true`, `health.provider=litert`, `health.backend=gpu`
- second JSON: `result.model_name=gemma-4-E2B-it.litertlm`
- `benchmark.elapsed_seconds` is measured wall-clock time for the call

This command does not start or query Ollama. If LiteRT fails, the result is
`model_name=rule-fallback`; that is a failure to count as P1 evidence, not an
automatic production fallback to Ollama.

## First boot

From the repo root:

```bash
chmod +x scripts/run_acuifero_pi8_multimodal_demo.sh
./scripts/run_acuifero_pi8_multimodal_demo.sh
```

For the production profile:

```bash
chmod +x scripts/run_acuifero_pi16_multimodal_prod.sh
./scripts/run_acuifero_pi16_multimodal_prod.sh
```

## Probe without a camera

```bash
python3 scripts/pi_acuifero_node.py \
  --api-base http://127.0.0.1:8000/api \
  --site-id puente-arroyo-01 \
  --synthetic
```

## Probe a real camera

```bash
python3 scripts/node_guard.py
```

Useful env:

```bash
export ACUIFERO_CAMERA_SOURCE=/dev/video0
export ACUIFERO_GUARD_INTERVAL_SECONDS=300
export ACUIFERO_GUARD_CLIP_SECONDS=12
export ACUIFERO_GUARD_FPS=2
```

The guard records a short MJPEG AVI with ffmpeg and posts it to
`POST /api/node/analyze`.

## What to check

- `acuifero.provider=litert` means the node is configured for LiteRT-LM.
- `acuifero.engine_ready=true` means the LiteRT runtime and model file are ready.
- `acuifero.speculative_decoding=true` means the LiteRT engine is created with
  speculative decoding enabled.
- `acuifero.counts_for_p1=true` means the configured Acuifero node inference path
  is LiteRT-LM and the engine is ready; Ollama dev mode reports `false`.
- `runner.mode=litert-multimodal-temporal` means Gemma 4 read the image(s) through LiteRT-LM.
- `runner.mode=multimodal-unavailable-fallback` is the current expected result on
  the measured Pi 5 + Gemma 4 E2B setup until the vision path fits the device.
- `fallback_used=true` means frames were prepared, but Gemma was down, timed out,
  or returned invalid JSON.
- Evidence images and JSON manifests are stored under `ACUIFERO_UPLOAD_DIR`.
