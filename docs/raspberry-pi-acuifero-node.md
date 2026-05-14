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
export ACUIFERO_LLM_ENABLED=true
export ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11434/v1
export ACUIFERO_LLM_MODEL=gemma4:e2b
export ACUIFERO_LLM_API_KEY=ollama
export ACUIFERO_MULTIMODAL_ENABLED=true
export ACUIFERO_MULTIMODAL_BASE_URL=http://127.0.0.1:11434/v1
export ACUIFERO_MULTIMODAL_MODEL=gemma4:e2b
export ACUIFERO_MULTIMODAL_MAX_FRAMES=1
export ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=300
export ACUIFERO_MULTIMODAL_IMAGE_MAX_SIDE=512
export ACUIFERO_MULTIMODAL_NUM_CTX=1024
export ACUIFERO_MULTIMODAL_TIMEOUT_SECONDS=300
```

This mode extracts one small frame from each short clip using ffmpeg, optimizes
it with Pillow, and sends it directly to Gemma 4 multimodal. There is no OpenCV
visual analysis in this path.

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

- `llm.reachable=true` means Ollama is reachable.
- `runner.mode=ollama-multimodal-temporal` means Gemma 4 read the image(s).
- `fallback_used=true` means frames were prepared, but Gemma was down, timed out,
  or returned invalid JSON.
- Evidence images and JSON manifests are stored under `ACUIFERO_UPLOAD_DIR`.
