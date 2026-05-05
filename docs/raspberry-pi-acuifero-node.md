# Raspberry Pi Acuifero fixed node

This guide prepares the fixed Acuifero camera node for a Raspberry Pi 5 with
8 GB RAM, Raspberry Pi OS 64-bit, and local SSD/NVMe storage.

## Runtime profile

Export these values before starting the backend:

```bash
export ACUIFERO_NODE_PROFILE=raspberry-pi-8gb
export ACUIFERO_DATA_DIR=/mnt/acuifero/data
export ACUIFERO_UPLOAD_DIR=/mnt/acuifero/data/uploads
export ACUIFERO_LLM_ENABLED=true
export ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11434/v1
export ACUIFERO_LLM_MODEL=gemma4:e2b
export ACUIFERO_LLM_API_KEY=ollama
export ACUIFERO_MULTIMODAL_ENABLED=false
export ACUIFERO_MAX_CURATED_FRAMES=3
export ACUIFERO_ARTIFACT_RETENTION_DAYS=7
```

The Raspberry profile is text-first: OpenCV curates the video frames and
numeric temporal hints locally, then Gemma receives the compact evidence pack.
Inline image prompting stays disabled by default to keep memory pressure low.

## First boot

From the repo root:

```bash
./scripts/install_ollama_local.sh
./scripts/run_gemma_local.sh gemma4:e2b
```

In a second terminal:

```bash
cd backend
uv venv
. .venv/bin/activate
uv pip install -e .[dev]
python -m acuifero_vigia.scripts.seed
PYTHONPATH=src uvicorn acuifero_vigia.main:app --host 0.0.0.0 --port 8000
```

## Probe without a camera

Use the synthetic rising-water clip to validate the full backend path on the Pi:

```bash
python3 scripts/pi_acuifero_node.py \
  --api-base http://127.0.0.1:8000/api \
  --site-id puente-arroyo-01 \
  --synthetic
```

The output includes runtime health, frames analyzed, assessment level, runner
mode, fallback status, alert level, and the evidence frame URL.

## Probe the bundled sample

After fetching demo assets:

```bash
python3 scripts/fetch_demo_assets.py
python3 scripts/pi_acuifero_node.py \
  --api-base http://127.0.0.1:8000/api \
  --site-id silverado-fixed-cam-usgs \
  --sample-site
```

## Probe a real camera

For a UVC camera exposed as `/dev/video0`:

```bash
python3 scripts/pi_acuifero_node.py \
  --api-base http://127.0.0.1:8000/api \
  --site-id puente-arroyo-01 \
  --camera /dev/video0 \
  --duration 12 \
  --width 640 \
  --height 480 \
  --fps 4
```

The default capture command uses `ffmpeg` and writes an MJPEG AVI file before
uploading it to `POST /api/node/analyze`.

For a Raspberry Pi camera module or a different capture pipeline, pass a custom
command template:

```bash
python3 scripts/pi_acuifero_node.py \
  --site-id puente-arroyo-01 \
  --capture-command "ffmpeg -y -f v4l2 -framerate {fps} -video_size {width}x{height} -t {duration} -i {camera} -c:v mjpeg {output}"
```

Available placeholders are `{output}`, `{duration}`, `{duration_ms}`, `{width}`,
`{height}`, `{fps}`, and `{camera}`.

## What to check

- `llm.reachable=true` in the runtime block means Ollama is reachable.
- `runner.mode=text-only-temporal` means Gemma produced the temporal verdict.
- `fallback_used=true` means the node still produced a deterministic assessment,
  but Gemma was down, timed out, or returned invalid JSON.
- Evidence images and JSON manifests are stored under `ACUIFERO_UPLOAD_DIR`.

