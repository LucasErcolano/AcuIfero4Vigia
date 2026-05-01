# ACUIFERO 4 + VIGIA - Hackathon Final Push Agent Brief

## Status note

This brief is now **historical context**. The backend has already been
restructured so that `Acuifero` is a **Gemma-first temporal assessment engine**
and not an OpenCV-first scorer anymore.

## Updated product background

- **Product**: "Acuifero 4 + Vigia" - hybrid flood early-warning system.
  - `Acuifero` = fixed-camera node with temporal evidence curation + Gemma-first node assessment + local actuation hooks.
  - `Vigia` = volunteer mobile app, offline-first, photo + voice + observation -> structured JSON.
  - Both feed a local decision engine that produces a `FusedAlert` with transparent reasoning.
- **Users**: civil defense volunteers and municipal coordinators in flood-prone towns along Argentina's Parana, Salado, and Paraguay rivers.
- **Acuifero node target**: fixed-camera Raspberry Pi 5, 8 GB RAM, 64-bit OS, SSD-backed `backend/data`, Gemma 4 E2B via local Ollama, text-first temporal evidence by default.
- **Vigia target**: separate volunteer/user node; do not size the fixed Acuifero Raspberry profile around Vigia.

## Updated architectural claim

The strongest novelty claim is now:

1. `Acuifero` builds a bounded **temporal evidence pack** from fixed-camera video.
2. Gemma consumes that temporal pack and emits the node assessment package:
   - `assessment_level`
   - `assessment_score`
   - `temporal_summary`
   - `reasoning_summary`
   - `reasoning_steps`
   - `critical_evidence`
3. The backend persists a rich audit artifact pack with curated frames, runner metadata, fallback status, and JSON manifests.
4. OpenCV remains only as an evidence-curation utility, not the main semantic judge.

## P2 note (superseded)

Older versions of this brief described Gemma on evidence frames as
"explanatory only" while CV remained the authoritative severity signal. That is
no longer the intended story for `Acuifero`.

Current story:

- the **node verdict** is Gemma-first and temporal
- the **evidence-frame overlay** is still useful in the demo, but it is now a
  secondary artifact derived from the temporal assessment pipeline

## P0/P1/P2 references

When reading any older hackathon notes in this repo, interpret them through the
new architecture:

- `docs/architecture.md` is the current source of truth
- `README.md` is the current public narrative
- `docs/hackathon/multimodal-comparison.md` should be read as support material
  for the temporal assessment story, not as proof that OpenCV is still the main
  scorer
