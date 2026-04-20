# P7 — On-device Gemma on Android

## Stack

Confirmed by P0 recon: Kotlin + Jetpack Compose, `compileSdk=34`, `minSdk=26`,
Retrofit for backend API, Room for offline queue. Gemma runtime is added via
**MediaPipe LLM Inference** (`com.google.mediapipe:tasks-genai`) — the Kotlin
API that ships Gemma as `.task` files with GPU/NNAPI acceleration.

Alternatives considered:

- **LiteRT-LM** — newer; Kotlin bindings still maturing, picked MediaPipe for stability.
- **llama.cpp via JNI** — works with `.gguf` but requires ABI-specific native builds. Deferred.

## Files added

- `android/app/src/main/java/com/acuifero/vigia/android/data/GemmaOnDevice.kt`
  — thin wrapper over `LlmInference`. Loaded reflectively so the module
  compiles in environments without Google Maven access; runtime-activates
  when the dependency is present.
- `android/app/build.gradle.kts` — `com.google.mediapipe:tasks-genai:0.10.14`
  declared but commented out. Uncomment after bundling a real `.task` asset.

## Model choice

`gemma4-e2b.task` (Q4 weights, ~1.4 GB). E4B exceeds comfort on mid-range
Android (Snapdragon 7-gen), so E2B is the production target. E4B can be
a stretch profile for flagships; same `GemmaOnDevice` code path works.

Download-on-first-launch flow (not bundled in APK — APK stays <50 MB):

```
GET https://your-cdn/gemma4-e2b.task  →  context.filesDir/gemma4-e2b.task
```

Verified via SHA-256 checksum stored alongside.

## Volunteer report flow

1. User fills transcript on `Report` screen.
2. `MainViewModel.submitReport` calls `gemma.structureReport(transcript)` if
   `gemma.isAvailable()`; otherwise shows an explicit error banner
   ("Modelo local no disponible, reintentá o usá sincronización con servidor")
   and requires the user to confirm backend sync.
3. On success, the parsed JSON goes into the local Room DB **labeled
   `parser_source = "gemma-android"`**.
4. UI displays a small chip: `Analizado con Gemma en este dispositivo` vs
   `Analizado en servidor` depending on `parser_source`.

## Latency budget

Target: **<12 s** combined text+image on mid-range device. Expected profile:

| Phase | Mid-range (Snapdragon 7-gen, 8GB) | Flagship (SD 8-gen) |
|---|---|---|
| Cold load `.task` → VRAM | 3.8 s | 1.9 s |
| Text structure (220 tokens, E2B) | 4.2 s | 1.6 s |
| Image assessment (frame, E2B) | 5.8 s | 2.3 s |

On emulator (no GPU) cold load can spike to ~18 s; document and fall back to
backend sync in that case.

## Build & run

1. Put `gemma4-e2b.task` at `android/app/src/main/assets/gemma4-e2b.task`
   (or wire download into the `AcuiferoApplication.onCreate`).
2. Uncomment the MediaPipe dep in `build.gradle.kts`.
3. `./gradlew :app:assembleDebug`.
4. Install: `adb install app/build/outputs/apk/debug/app-debug.apk`.

## Limitations (honest)

- No physical Android device was available on the dev machine for end-to-end
  validation; all latency numbers in this doc are projections from public
  MediaPipe benchmarks, not measurements on our APK.
- The reflective loader is a convenience for hackathon CI — production would
  hard-depend on `tasks-genai` and fail-fast at `Application.onCreate`.
- No silent backend fallback: this is deliberate. If the on-device claim fails
  on a given device, the user sees an explicit error.
- Image multimodal path on MediaPipe Kotlin is scoped for the v2 pitch.
  For now the image assessment stays backend-only when Android is used.
