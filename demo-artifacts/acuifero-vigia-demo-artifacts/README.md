# Acuífero + Vigía — Demo Artifacts

Reproducible demo package for the Kaggle Gemma 4 Good Hackathon submission.

The production deployment runs on a Raspberry Pi 4/5 camera node plus the Vigía
Android app. This package lets a judge verify the full alerting pipeline
**without** owning the physical hardware: captured node inputs, citizen audio
reports, telemetry logs, model and runtime configuration, expected outputs, and
demo builds for the dashboard and mobile app.

## Contents

```
acuifero-vigia-demo-artifacts/
  README.md                  - this file
  DEMO.md                    - step-by-step reproduction guide
  manifest.json              - machine-readable index of every artifact

  inputs/                    - what the Raspberry Pi node / Vigía app captured
    video/                   - water-level evidence (nominal / warning / critical)
    audio/                   - resident voice reports
    reports/                 - .txt transcripts (skip STT if needed)

  outputs/                   - what the system produced from those inputs
    logs/                    - JSONL telemetry from each node run
    alerts/                  - final alert payloads
    screenshots/             - dashboard + mobile UI evidence

  app/                       - installable demo builds (optional)
    vigia-demo.apk           - Android Vigía build (demo mode)
    acuifero-dashboard-demo.zip - static dashboard build

  config/                    - everything needed to prove the run is real
    model_config.json        - Gemma 4 three-tier model setup (E4B node / E2B mobile / 26B-A4B central)
    thresholds.json          - water-level / severity thresholds
    runtime_config.yaml      - node + backend runtime config
    lite_rt_config.json      - on-device LiteRT config
    prompt_templates.md      - exact prompts used by Vigía / Acuífero

  eval/                      - reproducibility evidence
    expected_outputs.json    - canonical outputs per case
    replay_results.json      - what this package's replay produced
```

## How to verify the demo

See `DEMO.md`. Two paths:

- **Option A — replay without hardware**: run the Kaggle Notebook linked from
  the submission. It loads the files in `inputs/` and produces the artifacts
  shown in `outputs/`.
- **Option B — real Raspberry Pi deployment**: clone the repo, follow the
  hardware deployment section.

## Notes

- Gemma 4 weights are **not** bundled. The system runs three Gemma 4 variants,
  one per tier (see `config/model_config.json`):
  - `google/gemma-4-E4B-it` on the Acuífero Raspberry Pi camera node (LiteRT, int4)
  - `google/gemma-4-E2B-it` on the Vigía Android app (LiteRT, int4)
  - `google/gemma-4-26B-A4B-it` on the central server (Ollama, q4_K_M)
  The package ships configuration and prompts only.
- All inputs are real captures from the Acuífero node and Vigía app, not
  synthetic. Filenames map 1:1 to entries in `manifest.json`.
