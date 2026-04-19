# Backend

FastAPI service for the Acuifero 4 + Vigia MVP.

## Key services

- real fixed-camera video analysis via OpenCV
- volunteer report parsing through a local Gemma-compatible endpoint with rule fallback
- live hydromet snapshots from Open-Meteo
- fused alert scoring and SQLite sync replication
- bundled sample clip analysis for the USGS Silverado demo site

## Runtime defaults

The backend defaults to a local Ollama-compatible endpoint:

```bash
ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11434/v1
ACUIFERO_LLM_MODEL=gemma4:e2b
ACUIFERO_LLM_API_KEY=ollama
```

Override them if you want to point at another OpenAI-compatible runner.

## Seed and tests

```bash
PYTHONPATH=src python -m acuifero_vigia.scripts.seed
PYTHONPATH=src pytest -q
```
