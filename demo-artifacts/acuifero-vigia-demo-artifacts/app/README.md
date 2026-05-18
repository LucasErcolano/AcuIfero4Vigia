# App builds

Place demo builds here before zipping the package:

- `vigia-demo.apk` — Android Vigía build with `DEMO_MODE=true` (loads
  `inputs/audio/*` and `outputs/logs/vigia_report_run.jsonl` instead of
  the live mic + radio channel).
- `acuifero-dashboard-demo.zip` — static dashboard build (`pnpm build`
  output of `frontend/`) configured to read `outputs/alerts/*.json`.

Both builds are **optional**. The Kaggle Notebook live demo does not depend
on them. They exist so judges with an Android device or a local web server
can poke the real UIs.

## Build commands (for the team, not the judge)

```bash
# Android
cd android && ./gradlew :app:assembleDemoRelease
cp app/build/outputs/apk/demoRelease/app-demoRelease.apk \
   ../demo-artifacts/acuifero-vigia-demo-artifacts/app/vigia-demo.apk

# Dashboard
cd frontend && pnpm install && pnpm build
cd dist && zip -r ../../demo-artifacts/acuifero-vigia-demo-artifacts/app/acuifero-dashboard-demo.zip .
```
