# Persona C Demo Recording — Backend / Fusion / CAP / Function Calling

Self-contained script. Follow top to bottom for a 90-second demo recording.

---

## What this demo shows

Persona C's deliverables, end-to-end, through the operator console:

1. **Fusion** of node + citizen signals (handled by `fusion/engine.py`).
2. **Auditable Gemma reasoning trace** attached to the fused alert.
3. **CAP v1.2 emission** via the real backend endpoint `POST /api/cap/emit`.
4. **SINAGIR JSON export** via `POST /api/alerts/{alert_id}/export-sinagir`.
5. **Offline / sync behavior** via `POST /api/settings/connectivity` and `GET /api/sync/status`.
6. **Demo-simulated actuation** (siren, LoRa, notify) — explicitly labeled as sim.

What is *not* demoed: live talking-head, B-roll, screencast B05 ensemble. Those belong to D+E.

---

## Pre-flight

```bash
# repo root
docker compose up backend     # or python -m acuifero_vigia
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Open `http://localhost:5173`.

Confirm:
- Top bar shows `Acuifero 4 + Vigia` with green `Online` pill.
- Bottom nav has `Dashboard / Report / Queue / Runtime`.

---

## Recording sequence (~90 s)

### Beat 1 — Site context (0:00–0:10)
- Dashboard → click any site → land on Site Detail.
- Read aloud: site name, region, hydromet card (signal score, rain, river discharge).

### Beat 2 — Run analysis (0:10–0:25)
- Scroll to **Analyze fixed-camera clip**.
- Click `Analyze bundled sample` (no upload needed — uses repo demo clip).
- Wait for response (~5–10 s).
- Point to **Node metrics** (waterline ratio, rise velocity, confidence, critical-line crossed).

### Beat 3 — Fusion + auditable reasoning (0:25–0:45)
- In **Resulting alert** panel, expand `Razonamiento de Gemma (gemma4:e2b)`.
- Show the reasoning summary + numbered chain — this is the audit trail.
- Mention fusion rules implemented (`fusion/engine.py`): single-source → moderate cap; cross-source within 500 m / 10 min → can escalate to severe.

### Beat 4 — CAP emission (0:45–1:00)
- Scroll to **Command center**.
- Click `Emit CAP`.
- Expand `CAP XML payload`. Show:
  - OASIS namespace `urn:oasis:names:tc:emergency:cap:1.2`
  - Severity, area polygon, headline in Spanish.
  - SHA-256 signature parameter.

### Beat 5 — SINAGIR export (1:00–1:10)
- Click `Export SINAGIR`.
- Expand the JSON. Mention this is the SINAGIR-ready handoff for Defensa Civil.

### Beat 6 — Action guard / simulated actuation (1:10–1:20)
- Click `Trigger siren (sim)` → action log appends `SIMULADO` line.
- Click `Send LoRa (sim)` and `Notify operator (sim)`.
- Explain: real backend has `action_guard.py` rejecting tool calls without evidence and rate-limiting per zone. The buttons here are explicit demo simulations.

### Beat 7 — Offline / sync (1:20–1:30)
- Click `Online` pill in header → toggles to `Offline`. Red `SIN CONECTIVIDAD` banner appears, pulsing.
- Navigate to `Runtime`. Show **Sync status** panel: pending / synced / failed counters.
- Click `Online` again → flash `Sincronizado` strip appears.

End.

---

## Talk track cheatsheet

- "El backend hace la fusión espacial y temporal entre nodo y reporte ciudadano."
- "Cada alerta lleva el razonamiento de Gemma como traza auditable."
- "CAP XML válido contra OASIS v1.2, listo para SINAGIR."
- "Tool calls pasan por action_guard: schema estricto, rate limit, rechazo si la severidad excede la evidencia."
- "Offline-first: la cola sigue funcionando sin red, sincroniza al volver conectividad."

---

## Endpoints hit during the demo

| UI action | Method | Path |
|-----------|--------|------|
| Load site | GET | `/api/sites/{id}` |
| Load hydromet | GET | `/api/sites/{id}/external-snapshot` |
| Analyze bundled clip | POST | `/api/sites/{id}/sample-node-analysis` |
| Emit CAP | POST | `/api/cap/emit` |
| Export SINAGIR | POST | `/api/alerts/{alert_id}/export-sinagir` |
| Toggle connectivity | POST | `/api/settings/connectivity` |
| Sync status | GET | `/api/sync/status` |
| Flush queue | POST | `/api/sync/flush` |

Siren / LoRa / Notify are explicitly **not** wired to backend endpoints — they push a `SIMULADO` line into the on-screen action log.

---

## Known caveats to mention briefly if asked

- Talking-head and final video ensemble are D+E deliverables, not in this clip.
- Latency E2E numbers in `docs/writeup.md` are still `[TODO]` until A finalizes Pi benchmarks.
- LiteRT-LM is the future runtime target; demo runs Gemma 4 through Ollama as the local backend.
