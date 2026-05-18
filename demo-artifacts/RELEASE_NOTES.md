# v0.1-gemma4good-submission

Reproducible demo artifacts for Acuífero + Vigía.

The full deployment runs on a Raspberry Pi camera node plus the Vigía Android
app. This release ships a hardware-replay package so judges can verify the
demo without owning the physical hardware: captured visual inputs, resident
audio reports, telemetry logs, model and runtime configuration, expected
outputs, and Android / dashboard demo builds where available.

## Assets

- `acuifero-vigia-demo-artifacts.zip` — the full package
  (`inputs/`, `outputs/`, `app/`, `config/`, `eval/`, `DEMO.md`, `manifest.json`).
- `vigia-demo.apk` (optional) — standalone Android Vigía demo build.
- `acuifero-dashboard-demo.zip` (optional) — static dashboard demo build.
- `SHA256SUMS.txt` — checksums for the above.

## How to use

1. Download `acuifero-vigia-demo-artifacts.zip`.
2. Follow `DEMO.md` inside the zip — Option A (Kaggle Notebook replay) or
   Option B (Raspberry Pi deployment).

## Project Links

- Repo: https://github.com/LucasErcolano/AcuIfero4Vigia
- Kaggle Notebook (live demo): `Acuifero + Vigia — Live Hardware Replay Demo`
- Kaggle Dataset (inputs/configs only): `acuifero-vigia-demo-artifacts`
- This release: `v0.1-gemma4good-submission`
