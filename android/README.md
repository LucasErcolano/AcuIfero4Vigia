# Android MVP

Android app for the Acuifero Vigia MVP.

Current scope:
- dashboard with runtime, alerts and sites
- site detail with sample-node analysis and hydromet refresh
- volunteer report submission
- offline Room queue with manual flush and startup sync worker
- numeric calibration form
- configurable backend base URL for emulator or device

Default backend URL:
- emulator: `http://10.0.2.2:8000/api/`

To use on a real device, replace it from the Settings screen with your machine LAN URL, for example:
- `http://192.168.1.20:8000/api/`

Expected backend stack:
- `./scripts/dev.sh`
- or backend + Ollama + frontend started separately

Android tooling note:
- The official Android tools page says the Android CLI is designed to work with agents and that projects can then be opened in Android Studio for visual tools and debugging.
- This module is structured to be opened directly in Android Studio under `android/`.
