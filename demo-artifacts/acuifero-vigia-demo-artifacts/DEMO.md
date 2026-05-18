# Acuífero + Vigía — Demo Reproduction Guide

This package replays the hardware pipeline so a judge can verify the demo
without owning the Raspberry Pi camera node.

## Option A — Replay demo without hardware (recommended)

1. Open the Kaggle Notebook:
   `https://www.kaggle.com/code/<team>/acuifero-vigia-live-hardware-replay-demo`

2. Click **Run all**.

3. The notebook loads from this package:
   - `inputs/video/river_nominal.mp4` and frames
   - `inputs/video/river_warning.mp4`
   - `inputs/video/river_critical.mp4` and frames
   - `inputs/audio/report_bridge_water.wav` plus its transcript
   - `inputs/reports/report_bridge_water.txt`
   - `config/thresholds.json`, `config/model_config.json`,
     `config/prompt_templates.md`

4. Expected progression:

   ```
   NOMINAL  ->  WARNING  ->  URGENT / CRITICAL
   ```

5. Compare the notebook outputs against `eval/expected_outputs.json`. They
   must match `outputs/logs/*.jsonl` and `outputs/alerts/*.json` in this
   package.

## Option B — Real Raspberry Pi deployment

Hardware:

- Raspberry Pi 4 (8 GB) or Pi 5
- Pi Camera module v2/v3 or USB camera
- Local Gemma 4 runtimes per tier:
  - Acuífero node: LiteRT serving `google/gemma-4-E4B-it` (int4)
  - Vigía app:     LiteRT serving `google/gemma-4-E2B-it` (int4)
  - Central node:  Ollama serving `google/gemma-4-26B-A4B-it` (q4_K_M)
- Optional: Android device with `app/vigia-demo.apk` installed

Commands:

```bash
git clone https://github.com/LucasErcolano/AcuIfero4Vigia.git
cd AcuIfero4Vigia
bash scripts/setup.sh
bash scripts/run_acuifero_pi8_multimodal_demo.sh

# Replay one of the captured cases through the live node:
python scripts/demo.py --case demo-artifacts/acuifero-vigia-demo-artifacts/inputs/video/river_critical.mp4
```

Expected stdout:

```
final_state=CRITICAL
evidence_count=4
cloud_required=false
```

## What "live demo" proves

- Local node detects water-level change against thresholds in
  `config/thresholds.json` (deterministic firewall, no LLM).
- Vigía citizen report is transcribed and passed to `gemma-4-E2B-it` on the
  handset with the prompt in `config/prompt_templates.md`.
- Acuífero node classifies camera frames with `gemma-4-E4B-it` (LiteRT, int4).
- Central node fuses node telemetry + citizen evidence with
  `gemma-4-26B-A4B-it` (Ollama, q4_K_M), returns structured JSON
  (severity, evidence, recommended_action, uncertainty).
- Final alert is written to `outputs/alerts/` and surfaced on the dashboard
  (`outputs/screenshots/dashboard_urgent.png`) and the Vigía app
  (`outputs/screenshots/mobile_queue.png`).
- No cloud dependency. Offline queue path captured in
  `outputs/logs/vigia_report_run.jsonl`.
