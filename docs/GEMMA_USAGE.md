# Gemma 4 Usage

Concrete map of where Gemma 4 runs in this repo, which runtime is used, and how to verify it.

## Models

| Variant | Where | Runtime |
|---|---|---|
| `gemma4:e2b` (multimodal) | Backend (Acuifero node assessment, Vigia text structuring) | Ollama (dev), LiteRT-LM (edge target) |
| `gemma4:e4b` | Backend reasoning (optional, workstation/Pi 16GB) | Ollama |
| Gemma 3n E2B (`.task`) | Android Vigia app | MediaPipe LLM Inference |

Selection lives in [`backend/src/acuifero_vigia/core/settings.py`](../backend/src/acuifero_vigia/core/settings.py) (env vars `GEMMA_MODEL`, `GEMMA_RUNTIME`, `OLLAMA_HOST`).

## Where Gemma 4 is used

### 1. Edge node temporal assessment (Acuifero)
- Curates frames from fixed camera, builds temporal evidence pack, asks Gemma for `assessment_level / assessment_score / temporal_summary / reasoning_summary / reasoning_steps`.
- Files:
  - [`backend/src/acuifero_vigia/services/acuifero_assessment.py`](../backend/src/acuifero_vigia/services/acuifero_assessment.py)
  - [`backend/src/acuifero_vigia/adapters/video_assessment.py`](../backend/src/acuifero_vigia/adapters/video_assessment.py)
  - [`backend/src/acuifero_vigia/adapters/image_assessment.py`](../backend/src/acuifero_vigia/adapters/image_assessment.py)
  - [`backend/src/acuifero_vigia/adapters/llm.py`](../backend/src/acuifero_vigia/adapters/llm.py) (Ollama client + LiteRT stub)
  - [`scripts/pi_acuifero_node.py`](../scripts/pi_acuifero_node.py), [`scripts/node_guard.py`](../scripts/node_guard.py)

### 2. Vigia volunteer report understanding
- Structures free-form Rioplatense Spanish reports into typed observations.
- Files:
  - [`backend/src/acuifero_vigia/adapters/text_structuring_gemma_fewshot.py`](../backend/src/acuifero_vigia/adapters/text_structuring_gemma_fewshot.py)
  - [`backend/src/acuifero_vigia/services/report_structuring.py`](../backend/src/acuifero_vigia/services/report_structuring.py)
  - Android on-device path: [`android/app/src/main/java/com/acuifero/vigia/android/data/GemmaOnDevice.kt`](../android/app/src/main/java/com/acuifero/vigia/android/data/GemmaOnDevice.kt) (MediaPipe LLM Inference, no backend fallback).

### 3. Alert reasoning / audit trace
- Generates Spanish reasoning block for every non-green fused alert.
- Files:
  - [`backend/src/acuifero_vigia/services/reasoning.py`](../backend/src/acuifero_vigia/services/reasoning.py)
  - [`backend/src/acuifero_vigia/services/node_analysis.py`](../backend/src/acuifero_vigia/services/node_analysis.py)
  - [`backend/src/acuifero_vigia/services/actuators.py`](../backend/src/acuifero_vigia/services/actuators.py)

## Why this runtime

- **Ollama** for backend dev: simple model pull, multimodal in one process, matches Pi 16GB / workstation profile.
- **LiteRT-LM** target for the Pi 8GB demo profile: smaller footprint, on-device decode benchmarks live in [`docs/hackathon/`](hackathon/) (`litert-e2b-pi5-8gb-*.jsonl`). Runner stub: [`scripts/litert_benchmark.py`](../scripts/litert_benchmark.py), [`scripts/litert_smoke.py`](../scripts/litert_smoke.py).
- **MediaPipe LLM Inference** on Android: official Gemma path for on-device mobile, no silent network fallback (see [`android_gemma.md`](hackathon/android_gemma.md)).

## Prompt / schema

- Acuifero assessment schema: [`shared/`](../shared/) JSON schemas + `acuifero_assessment.py` prompt builder.
- Vigia few-shot prompt: `text_structuring_gemma_fewshot.py` (12-shot Rioplatense corpus from [`datasets/`](../datasets/)).
- Reasoning prompt: `services/reasoning.py` emits structured `reasoning_steps[]` plus `temporal_summary`.

## Inputs / outputs

| Path | Input | Output |
|---|---|---|
| Acuifero node | curated frames + metadata | `NodeAssessment` JSON (level, score, summaries, steps, audit artifacts) |
| Vigia text | free-form Spanish report | `LocalParsedObservation` (typed fields, confidence) |
| Reasoning | fused alert context | Spanish reasoning block + deterministic rule trace |

## Limitations (honest)

- Multimodal latency on Pi 8GB: see `e2b-e4b-ablation.md` and timeout logs. E4B reasoning is workstation/Pi 16GB territory.
- LiteRT-LM runner is currently a benchmark/stub path; production inference uses Ollama until LiteRT-LM ships a multimodal release we can pin.
- Few-shot Rioplatense corpus is 82 examples - small, but versioned and reproducible (`scripts/eval_rioplatense.py`).

## Verify it is not mock

```bash
# 1. Backend hitting real Ollama
docker compose --profile llm up
docker exec acuifero-ollama ollama pull gemma4:e2b
curl -s http://localhost:11434/api/tags | grep gemma4

# 2. Acuifero assessment end-to-end (real frames)
python scripts/demo.py

# 3. Rioplatense eval (real model vs labeled corpus)
python scripts/eval_rioplatense.py

# 4. Pi node demo runner
bash scripts/run_acuifero_pi8_multimodal_demo.sh
```

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for expected outputs.
