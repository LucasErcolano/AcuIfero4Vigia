# P0 - Reconnaissance

## Historical note

This file is a **historical reconnaissance snapshot** taken before the
Gemma-first redesign of `Acuifero`.

At the time of that recon, the repo still described:

- `Acuifero` as a FastAPI + SQLModel + OpenCV MVP
- Gemma as a supporting component around the node pipeline
- the fixed-node score as primarily heuristic

## What changed after recon

The current source of truth is now:

- [`README.md`](../../README.md)
- [`docs/architecture.md`](../architecture.md)
- backend implementation under `backend/src/acuifero_vigia/services/acuifero_assessment.py`

The important architectural correction is:

- `Acuifero` now means a **Gemma-first temporal assessment engine**
- OpenCV is retained only for temporal evidence curation and numeric hints
- node analysis persists a rich audit pack through `AcuiferoAssessmentArtifact`

## Why this note exists

Several hackathon notes referenced this recon as if it were the current
architecture. It is not. Keep it only as repo history and migration context.
