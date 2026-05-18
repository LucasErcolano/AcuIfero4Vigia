# Kaggle Live Hardware Replay Demo

## Purpose

Use the notebook `notebooks/acuifero_vigia_live_hardware_replay_demo.ipynb` as
the Kaggle Live Demo link for Acuifero + Vigia.

This is a reproducible hardware replay demo. It lets judges run the alert
orchestration on captured/synthetic-safe Raspberry Pi node inputs and Vigia
citizen reports without requiring the physical Raspberry Pi, backend, frontend,
Docker, internet downloads, or GPU access.

Default mode is `RUN_GEMMA = False`. In that mode, the notebook uses
`golden_fixture_output`; it does not claim to run LiteRT-LM or live Gemma
inference. The real Raspberry Pi 5 + LiteRT-LM deployment evidence is documented
separately in the repository docs, benchmark card, and demo video artifacts.

## Kaggle Dataset

Create a Kaggle Dataset with slug:

```text
acuifero-vigia-fixtures
```

Upload the contents of:

```text
fixtures/kaggle_live_demo/
```

The dataset root must expose this exact layout:

```text
/kaggle/input/acuifero-vigia-fixtures/
  manifest.json
  sensor_readings.csv
  vigia_reports.jsonl
  frames/
    00_nominal.jpg
    01_vigilance.jpg
    02_urgent.jpg
    03_critical.jpg
  transcripts/
    report_01.txt
  expected_outputs/
    alert_trace.json
```

In the Kaggle notebook, use **Add Data** and attach the
`acuifero-vigia-fixtures` dataset. The notebook first checks
`/kaggle/input/acuifero-vigia-fixtures/`, then falls back to the repo-local
fixture paths for local development.

## Project Links Text

Title:

```text
Acuifero + Vigia — Live Hardware Replay Demo
```

Description:

```text
Reproducible hardware replay demo that lets judges run the alert orchestration on captured/synthetic-safe Raspberry Pi node inputs and Vigía citizen reports, without requiring access to the physical device. The real Raspberry Pi 5 + LiteRT-LM deployment evidence is documented separately in the repository.
```

## Checklist

- Kaggle Dataset is public or attached to the notebook.
- Notebook is public.
- Save & Run All has been executed.
- Output JSON is visible in `/kaggle/working/acuifero_vigia_alert_trace.json`.
- Notebook link is pasted in Project Links -> Live Demo.
- Disclaimer is visible in the first notebook screen.

## Honesty Boundaries

- The default notebook mode is hardware replay, not a live Raspberry stream.
- The default output is `golden_fixture_output`, not live Gemma inference.
- The notebook demonstrates the same data contract, same prompt contract, and
  same alert orchestration.
- The SINAGIR/CAP-shaped export is a preview only and is not submitted to
  SINAGIR production endpoints.
