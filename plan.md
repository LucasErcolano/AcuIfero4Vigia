# Acuifero 4 + Vigia - Historical MVP Plan

## Historical note

This file used to be the original MVP execution plan. It is now kept only as
historical context.

The current repo has moved beyond that OpenCV-first MVP framing in the
`Acuifero` area.

## Current architectural reality

- `Acuifero` is now a **Gemma-first temporal assessment engine**
- fixed-node analysis builds a **Temporal Evidence Pack**
- Gemma emits the node verdict and reasoning package
- OpenCV remains only for evidence curation, overlays, and numeric hints
- node analyses persist a rich audit pack through `AcuiferoAssessmentArtifact`
- the public backend facade remains stable while exposing additive node fields

## Current sources of truth

- [`README.md`](README.md)
- [`docs/architecture.md`](docs/architecture.md)
- [`backend/README.md`](backend/README.md)

If this file ever conflicts with those documents, treat this file as obsolete.
