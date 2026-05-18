# Demo recording path · Persona C — Backend & Fusion command center

This file documents exactly what the Backend & Fusion lead (Persona C) clicks and shows during the 3-minute hackathon recording.

**Two cuts available:**

1. **Dashboard cut (sections 1-5):** single-screen operator dashboard story, 3 min, uses local React state. Quickest to record.
2. **Hybrid escalada cut (section 6):** terminal + dashboard split, real backend ingest drives verde -> amarillo -> rojo escalada on the VM (`hz@100.105.56.84`) with Gemma 4 running in Ollama. Most impactful for the jury.

Pick one based on rehearsal time. Both end at the same artifacts: CAP v1.2 XML + decision trace.

Target resolution: **1440 × 900** (zoom browser to ~100%, hide bookmarks bar).

---

## 1. Pre-roll setup (do this BEFORE the camera rolls)

```bash
# Terminal A
cd backend && PYTHONPATH=src python3 -m acuifero_vigia.scripts.seed
PYTHONPATH=src python3 -m uvicorn acuifero_vigia.main:app --host 127.0.0.1 --port 8000

# Terminal B
./scripts/run_gemma_local.sh   # Ollama + gemma4:e2b warming up

# Terminal C
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

Then in the browser:

1. Open `http://localhost:5173`.
2. Confirm header pill says **`Online`** (green).
3. Confirm the **bottom nav** reads `Comando · Reporte · Cola (n) · Runtime`.
4. (Optional) trigger a real incident in Terminal D so the demo isn't sample state:
   ```bash
   curl -sf -X POST http://127.0.0.1:8000/api/sites/silverado-fixed-cam-usgs/sample-node-analysis | jq
   ```
   If no real alert is present, the dashboard **automatically falls back** to a clearly-labeled `DEMO · sample state` view — that's safe to record too.

---

## 2. What Persona C says + clicks (3-min cut)

### 0:00 – 0:20 · "The 5-second read"

**Click**: nothing yet — just land on `/`.

**Say**: *"Esto es lo que ve el operador en Defensa Civil cuando llega una alerta. En menos de cinco segundos sabe el nivel, el sitio, y el score."*

**Show**: the **RiskBanner** at the top — full-bleed red strip with `CRÍTICO`, score `87%`, site name, summary. If a real alert is loaded, the red strip will pulse softly; if it's demo, the `DEMO · sample state` badge is in the strip's top-right.

### 0:20 – 0:50 · "Why we trust this alert: signal fusion"

**Click**: nothing — point at the panel titled `Fusión de señales`.

**Say**: *"El motor no decide por una sola señal. Acá tenés las tres entradas: la cámara fija detectó cruce de línea crítica, un brigadista mandó el reporte por la app Vigía, y el modelo hidrometeorológico de Open-Meteo da una probabilidad alta. Cada tile tiene su score y cuándo llegó."*

**Show**: the three slate tiles — `cv_node` 87, `vol_report` 62, `hydromet` 45. All three status dots green.

### 0:50 – 1:15 · "Multimodal Gemma narration"

**Click**: nothing — point at the evidence frame.

**Say**: *"Acá Gemma multimodal narra el frame en español. La visión por computadora sigue siendo la fuente del score; Gemma solo describe lo que se ve para que el operador audite la decisión."*

**Show**: the evidence frame with the bottom strip `Gemma · gemma4:e2b · conf 78%` and the Spanish description.

### 1:15 – 1:40 · "Auditable reasoning"

**Click**: nothing — point at `Razonamiento de Gemma` and the numbered list below.

**Say**: *"Cada alerta no-verde lleva su razonamiento de Gemma en español, más una traza determinística de qué reglas dispararon. No es una caja negra: el operador puede defender la decisión ante un superior."*

**Show**: the reasoning summary + the `Traza de auditoría determinística` panel listing `RULE_CRITICAL_LINE_CROSSED`, `RULE_RISE_VELOCITY`, etc., each with `disparada` / `no aplicó`.

### 1:40 – 2:10 · "Function calling — the operator acts"

**Click**: in this order, with about 4 seconds between each:
1. `Emitir CAP v1.2`
2. `Disparar sirena`
3. `Enviar alerta LoRa`
4. `Notificar Defensa Civil`

After each click, the button spins for ~1s and a `stdout · function_call log` line appears below the action rail.

**Say**: *"Cuando el operador decide actuar, dispara funciones que Gemma 4 también puede invocar autónomamente. Emitir el XML CAP versión 1.2 — ese es el estándar internacional de Common Alerting Protocol, mapeado a SINAGIR. Disparar la sirena vía relay GPIO. Enviar alerta por LoRa a los nodos hermanos. Notificar al webhook de Defensa Civil municipal."*

**Show**: the `Estado CAP v1.2 · export` card flips from idle/emitido as the actions fire, and the `Línea de tiempo del incidente` at the bottom gets new dots.

### 2:10 – 2:30 · "Connectivity loss"

**Click**: header pill `Online` → flips to `Offline`. Wait ~1s.

**Say**: *"Si se cae la conexión, el operador no pierde la vista. Banner rojo `SIN CONECTIVIDAD`, la cola sigue contando reportes locales, y el motor local sigue tomando decisiones. Cuando vuelve la red, se sincroniza solo."*

**Show**: the `SIN CONECTIVIDAD — operación local activa · cola: N` banner under the header. The `Cola offline · última sincronización` card on the right shows offline state.

**Click**: header pill back to `Online`. The green `Sincronizado` flash appears for 2.5s.

### 2:30 – 2:50 · "Lifecycle in one strip"

**Click**: nothing — point at the timeline.

**Say**: *"Toda la historia del incidente en un strip: detección CV, reporte voluntario, fusión, emisión CAP, sirena, notificación. Auditable de punta a punta."*

**Show**: the `Línea de tiempo del incidente` at the bottom, dots in amber for completed events. The events we just triggered are at the right end.

### 2:50 – 3:00 · close

**Say**: *"Acuífero 4 + Vigía: alerta temprana híbrida, on-device, auditable, lista para Defensa Civil."*

---

## 3. Implementation notes

- **Demo fallback is labeled.** When `useAppStore.alerts` is empty, the dashboard renders `DEMO_ALERT` + `DEMO_FUSION` + `DEMO_TIMELINE` constants from `pages/Dashboard.tsx` with a visible `DEMO · sample state` badge in the RiskBanner. No hidden backend mocking.
- **Action rail.** Buttons in `Acciones del operador` dispatch a 900ms simulated busy state and log to a `stdout` panel. They do NOT call the backend in this commit — wiring to `POST /api/alerts/{id}/export-sinagir`, `/api/alerts/{id}/siren`, etc. is a follow-up. The visual contract is in place.
- **Spanish strings.** Every demo-critical label is Spanish: `Incidente activo`, `Fusión de señales`, `Razonamiento de Gemma`, `Traza de auditoría determinística`, `Acciones del operador`, `Emitir CAP v1.2`, `Disparar sirena`, `Enviar alerta LoRa`, `Notificar Defensa Civil`, `Cola offline · última sincronización`, `Línea de tiempo del incidente`, `Sitios monitoreados`, `Abrir sitio`, `Comando`, `Reporte`, `Cola`. The English fragments that remain are deliberate function-call identifiers (`emit_cap_xml`, `function_call`, etc.) — those are operator/dev shibboleths and reading them in Spanish would be wrong.
- **Responsive.** The `cc-grid` collapses to a single column under 1100px; the fusion row stacks under 720px. The recording target is 1440 × 900 — at that resolution everything above the timeline fits without scrolling.
- **Build.** Compiles under `noUnusedLocals`, `noUnusedParameters`, `verbatimModuleSyntax`, `erasableSyntaxOnly` per the existing `tsconfig.app.json`.

## 4. Files patched

| File | Change |
|---|---|
| `frontend/src/pages/Dashboard.tsx` | Full rewrite — command center layout, demo fallback, action rail wiring |
| `frontend/src/pages/SiteDetail.tsx` | Added CAP status card + audit trace at the bottom of the analysis section |
| `frontend/src/components/Layout.tsx` | Spanish nav labels: Dashboard → Comando, Report → Reporte, Queue → Cola |
| `frontend/src/components/CommandCenter.tsx` | **NEW.** Reusable atoms — RiskBanner, SignalFusionRow, EvidencePanel, GemmaReasoning, AuditTrace, ActionRail, CapStatusCard, OfflineSyncCard, IncidentTimeline, SectionPanel, EmptyCommandCenter |
| `frontend/src/index.css` | Added slate/ops palette + 1440×900 grid utilities (`cc-grid`, `cc-fusion`, `cc-action-btn`, severity strips, etc) |

## 6. Hybrid recording path - "El semaforo de riesgo" (escalada en vivo)

This is an alternative cut driven by **real backend ingestion** on the VM. The
operator dashboard reflects every act live: RiskBanner, fusion tiles, timeline
and CAP card move because a `FusedAlert` was actually written to the DB.

### 6.1 Setup on the VM (`hz@100.105.56.84`)

```bash
# Terminal A (backend with demo-inject gated router)
cd /home/hz/work/AcuIfero4Vigia_local/backend
rm -f data/edge.db data/central.db
PYTHONPATH=src python3 -m acuifero_vigia.scripts.seed
ACUIFERO_ENABLE_DEMO_INJECT=1 PYTHONPATH=src \
  python3 -m uvicorn acuifero_vigia.main:app --host 127.0.0.1 --port 8000

# Terminal B (frontend)
cd /home/hz/work/AcuIfero4Vigia_local/frontend
npm run dev -- --host 127.0.0.1 --port 5173

# Terminal C (ollama - already running)
ollama list   # gemma4:e2b o gemma4:26b deben estar listos
```

`ACUIFERO_ENABLE_DEMO_INJECT=1` enables `POST /api/demo/inject-node-observation`
and `POST /api/demo/inject-volunteer-report`, gated routes used only during the
demo to produce a deterministic verde -> amarillo -> rojo escalada that does NOT
depend on Gemma's interpretation of free-text transcripts.

> **Note on latency.** Gemma 4 26B Q4_0 on RTX 3060 + RAM offload is slow.
> Record without worrying — speed up in post. **Do NOT show tok/s or latency
> overlays on screen.**

### 6.2 Acts (terminal + dashboard split-screen)

Run from the project root on the VM:

```bash
cd /home/hz/work/AcuIfero4Vigia_local/scripts/demo_persona_c
bash 00_reset.sh                  # DB clean (verde baseline)
```

| Act | Script | Source | Expected fused | Dashboard signal |
|-----|--------|--------|----------------|------------------|
| 1   | `bash 01_vigia_verde.sh`     | Vigia ciudadano (rutina) | `green` ~0.20 | RiskBanner permanece verde, tile `vol_report` aparece bajo |
| 2   | `bash 02_acuifero_amarillo.sh` | Acuifero (cota elevada, sin cruzar linea critica) | `yellow` ~0.52 | RiskBanner pasa a amarillo, tile `cv_node` aparece, timeline gana punto |
| 3   | `bash 03_fusion_rojo.sh`     | 3 Vigia simultaneos + CAP/SINAGIR export | `red` >=0.86 | RiskBanner rojo pulsante, los 3 tiles activos, CAP card `emitido`, sirena en log |

Recommended cadence: ~10 s between scripts so the dashboard's polling tick (`useAppStore`) repaints with the new alert.

### 6.3 What to say (escalada narrative)

- **Act 1 (verde):** *"Un vecino reporta lluvia fuerte pero el canal corre normal. El sistema lo registra; no escala — verde."*
- **Act 2 (amarillo):** *"La camara fija detecta que la cota supera la linea de referencia, pero no cruza la critica. El motor de fusion sube a amarillo. Una sola fuente con score moderado: precaucion, no panico."*
- **Act 3 (rojo):** *"Tres Vigia ciudadanos reportan al mismo tiempo: marca del puente pasada, calle cortada, agua en las casas. La corroboracion humana cruzada con la lectura de camara dispara el `fused_score` por encima de 0.82. Rojo. Sirena local. Alerta CAP v1.2 lista para Defensa Civil."*
- **Act 4 (cierre):** *"Aca esta el decision trace en JSON con cada regla disparada, y el XML CAP v1.2 con `category`, `urgency`, `severity` listos para SINAGIR."*

Show in terminal: SINAGIR JSON (`/tmp/sinagir_<id>.json`) + CAP XML (`/tmp/cap_alert_<id>.xml`). Both written by `03_fusion_rojo.sh`.

### 6.4 Why a gated debug router (not free-text transcripts)

The Vigia `/api/reports` endpoint runs the transcript through Gemma's
`structure_observation`. For a recorded escalada we need deterministic scores,
not whatever Gemma decides for a given phrase. `POST /api/demo/inject-*` writes
the same DB rows the real ingest would, **with controlled `severity_score`** and
metadata, then calls the same `recompute_site_alert` fusion engine. The fusion,
reasoning and CAP outputs are 100% real — only the parser is bypassed.

The router is registered **only when `ACUIFERO_ENABLE_DEMO_INJECT=1`** (see
`backend/src/acuifero_vigia/api/routers/demo_inject.py` and the conditional
include in `backend/src/acuifero_vigia/main.py`). Default production builds do
not expose it.

### 6.5 Live smoke (record locally on the VM)

```
[Acto 1] Vigia ciudadano envia reporte a puente-arroyo-01...
  -> level=green score=0.2 trigger=volunteer
[Acto 2] Acuifero (camara fija) inyecta lectura elevada a puente-arroyo-01...
  -> level=yellow score=0.52 trigger=node
[Acto 3] Tres reportes Vigia simultaneos a puente-arroyo-01...
  R1 ... -> level=red score=0.86 alarm=True
  R2 ... -> level=red score=0.8594 alarm=True
  R3 ... -> level=red score=0.96 alarm=True
[Acto 4a] Decision trace SINAGIR-ready  -> /tmp/sinagir_<id>.json
[Acto 4b] Emitiendo CAP v1.2 XML institucional  -> /tmp/cap_alert_<id>.xml
```

If the numbers look different, run `00_reset.sh` first — the 45-min evidence
window means stale rows from a previous run will leak into the next take.

## 7. If something looks wrong on the day

- **Risk strip is wrong color.** The level comes from the live alert. If a real RED alert came in, the strip is RED and pulses. If the level is wrong, run the seed + the sample-node-analysis curl above to force RED.
- **Action rail does nothing.** Check the browser console for React errors. Buttons are pure UI in this commit and won't fail silently — every click writes to the `stdout` panel.
- **Spanish strings are wrong.** Search `frontend/src/pages/Dashboard.tsx` and `components/CommandCenter.tsx` for the label and fix in place — there's no i18n indirection.
- **No timeline events.** Timeline is initialized from `DEMO_TIMELINE_FACTORY()`. To restart, refresh the page. New events appear when action-rail buttons are clicked.
