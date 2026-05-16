# Persona C demo — continuation brief (load into fresh Claude session)

Drop this file into a new Claude Code session along with the instruction
"continuamos iterando sobre la demo de Persona C, este es el estado actual".
Everything below is verified working as of 2026-05-16.

## TL;DR

End-to-end pipeline that records a 1440×900 webm of the Acuífero 4 + Vigía
**Command Center** dashboard while a real backend fuses live signals through
3 actos: verde → amarillo → rojo. Output: `outputs/persona_c_demo_v3.webm`.

All inference, fusion, CAP emission and decision tracing is real. Only the
parser (Gemma transcript → severity_score) is bypassed via gated `inject`
endpoints so the escalada is deterministic for video recording.

## Architecture

```
Local Windows                          VM hz@100.105.56.84
─────────────                          ─────────────────────
Claude Code (you)                       /home/hz/work/AcuIfero4Vigia_local/
  │                                       backend/  (FastAPI :8000)
  │ plink/pscp                            frontend/ (Vite dev :5173)
  ├──── sync src + scripts ──────►        ollama (gemma4:26b, gemma4:e2b) :11434
  │                                       playwright + chromium headless
  └──── run record_demo.py ──────►        record_demo.py
          ◄────── webm + xml ─────        /tmp/persona_c_demo.webm
                                          /tmp/cap_alert_<id>.xml
```

## VM access (Windows host only — these paths are local to my machine)

```
plink:  C:\Users\76hz\AppData\Local\Temp\plink.exe
pscp:   C:\Users\76hz\AppData\Local\Temp\pscp.exe
host:   100.105.56.84
user:   hz
pw:     1
hostkey:SHA256:vb8YLf6AX8WEY0jyyuLzG42mJZl6gesBDbrdUZhXTVA
repo:   /home/hz/work/AcuIfero4Vigia_local
```

PowerShell invocation template (Bash cannot reach the VM from this sandbox):

```powershell
$PLINK = "C:\Users\76hz\AppData\Local\Temp\plink.exe"
$PSCP  = "C:\Users\76hz\AppData\Local\Temp\pscp.exe"
$HKEY  = "SHA256:vb8YLf6AX8WEY0jyyuLzG42mJZl6gesBDbrdUZhXTVA"
$VM    = "hz@100.105.56.84"
& $PLINK -ssh -batch -no-antispoof -hostkey $HKEY -l hz -pw 1 100.105.56.84 "<remote cmd>"
& $PSCP  -batch -hostkey $HKEY -pw 1 "<local>" "${VM}:<remote>"
```

Multiline remote commands → write to a `.sh` file locally, pscp it over, then
plink-run it. Heredocs through plink corrupt quoting.

## Files that matter

| Path | Role |
|---|---|
| `backend/src/acuifero_vigia/api/routers/demo_inject.py` | Gated debug router. `/api/demo/inject-volunteer-report` + `/api/demo/inject-node-observation`. Bypasses parser, calls real `recompute_site_alert`. |
| `backend/src/acuifero_vigia/main.py` | Conditional include of demo_inject when `ACUIFERO_ENABLE_DEMO_INJECT=1`. |
| `frontend/src/pages/Dashboard.tsx` | Command Center page. `liveSignals` + `liveAudit` derive from `activeAlert.decision_trace` (decision-trace-v2 schema). Falls back to `DEMO_FUSION` / `DEMO_AUDIT` only when `alerts.length === 0`. |
| `frontend/src/components/CommandCenter.tsx` | UI atoms. `SignalInput` interface has optional `model` field rendered as `modelo: gemma4:e4b` etc. |
| `scripts/demo_persona_c/record_demo.py` | Playwright recorder. Pre-injects baseline verde, then drives 3 actos via HTTP, scrolls page, dumps DOM checks. |
| `scripts/demo_persona_c/_rec_full.sh` | Full pipeline: kill+restart uvicorn with env flag, wipe DB, seed, ensure vite up, run recorder. |
| `scripts/demo_persona_c/_restart_frontend.sh` | Kill vite, npm install, restart on :5173. |
| `scripts/demo_persona_c/_snap_final.py` | Single screenshot of dashboard current state at 1440×900 full_page=True. Sanity check tool. |
| `scripts/demo_persona_c/00_reset.sh` `01_*.sh` `02_*.sh` `03_*.sh` | Standalone curl runners (no Playwright). Useful for manual rehearsal in a terminal. |

## Demo deterministic targets (verified)

| Acto | Source | severity_score input | Fused result | Banner text |
|------|--------|---------------------|--------------|-------------|
| 1 | volunteer (rutina aguas arriba) | 0.20 | green 0.20 | NOMINAL |
| 2 | node (cámara fija puente, cota elevada) | 0.52 | yellow 0.52 | VIGILANCIA |
| 3 R1 | volunteer (junto al puente, marca pasada) | 0.78 | red 0.86 | CRÍTICO |
| 3 R2 | volunteer (plaza, calle cortada) | 0.74 | red 0.86 | CRÍTICO |
| 3 R3 | volunteer (barrio bajo, agua en casas) | 0.88 | red 0.96 | CRÍTICO |

Geografía narrativa: aguas arriba → puente → plaza → barrio bajo. Refleja el
recorrido físico del agua río abajo, así el operador entiende por qué los
reportes llegan en ese orden.

Per-source model labels (cosmetic only, not actually orchestrated): cámara
`gemma4:e4b`, vigía `gemma4:e2b`, hydromet `open-meteo`.

## Why deterministic inject instead of real Vigía POST

The real `/api/reports` runs the transcript through `structure_observation`
which calls Gemma. Gemma sometimes rates "rutina" as critical (hallucination).
For a recorded demo we need fixed severity per acto. The inject endpoints
write the same `VolunteerReport` + `ParsedObservation` (or `NodeObservation`)
rows the real ingest would, with controlled `severity_score`, then call the
exact same `recompute_site_alert`. Fusion, reasoning, CAP emit, audit trace
are 100% real — only the parser is skipped.

## Critical gotchas (lost time on these)

1. **DB path is `data/edge.db`, not `data/acuifero.db`.** Settings reads
   `ACUIFERO_EDGE_DB_PATH` env or defaults to `data_dir / "edge.db"`. If you
   `rm data/acuifero.db`, you reset nothing and Acts read stale rows from the
   prior 45-minute evidence window.

2. **Dashboard does NOT poll.** `fetchAlerts` runs once on mount via
   `useEffect`. Recorder must `page.reload()` between acts or you get a static
   frame. (Could add `setInterval` in store; we chose reload to keep frontend
   diff small.)

3. **`DEMO_FUSION` / `DEMO_AUDIT` constants in Dashboard.tsx.** The old
   Dashboard always rendered those constants even with live alerts. We patched
   to derive `liveSignals` and `liveAudit` from `activeAlert.decision_trace`
   (decision-trace-v2 schema: `evidence[]`, `rules_fired[]`). Demo fallback
   only kicks in when `alerts.length === 0`.

4. **Pre-inject Act 1 BEFORE first page.goto.** Otherwise dashboard shows the
   `DEMO_ALERT` static CRÍTICO 87% fallback for the first ~5s of the video.

5. **Playwright recording is viewport-only.** A 1440×900 viewport on a
   1440×~1900 page cuts off the lower half. Two options: taller viewport
   (uglier, everything shrinks) or scrolling (what we use). We chose scrolling
   with `scroll_to(y, steps, dwell)` in the recorder.

6. **`set -e` + piped `head` causes SIGPIPE abort.** Affected
   `03_fusion_rojo.sh` Act 4 — write to file first, then `head` it.

7. **`fused_score` saturates fast.** After R1 (severity 0.78) the score is
   already 0.86. R2/R3 don't change it much. The narrative drama is in the
   banner color change and in the *third* tile (vol_report) growing 20 → 78 →
   88, not in the fused score moving.

8. **VM frontend can lag behind local repo.** First time I recorded, the VM
   had an old Dashboard.tsx without the Command Center. pscp the whole
   `frontend/src/` recursively after any UI edit. Vite hot-reloads, so no
   restart needed for source-only changes; restart only after `package.json`
   changes.

## Iteration recipes

### Change a transcript or severity

Edit `scripts/demo_persona_c/record_demo.py` constants at the top:
`ACT1`, `ACT2`, `ACT3_REPORTS`. Re-pscp the script, run `_rec_full.sh`. No
backend or frontend restart needed.

### Change scroll choreography

Recorder has `scroll_to(y_px, dwell_ms)` calls per acto. Page heights to
remember (Command Center 1440-wide):
- 0–300 px: RiskBanner + top of first section
- 420 px: SignalFusionRow tiles centered
- 600–900 px: Frame de evidencia (Gemma narration)
- 900–1100 px: Razonamiento de Gemma
- 1100–1400 px: Traza de auditoría determinística
- 1400–1600 px: Línea de tiempo del incidente
- 1600+: Sitios monitoreados (auxiliary, OK to skip)

### Add a per-source UI affordance

`SignalInput` interface is in `frontend/src/components/CommandCenter.tsx`.
Render in tile body inside `SignalFusionRow`. Dashboard fills the field
inside `liveSignals` useMemo.

### Verify DOM consistency without re-recording

Run only `_snap_final.py` after `_rec_full.sh` — it screenshots the dashboard
in its terminal state (red). The recorder also has `dump_dom_check(label)`
which `page.evaluate`s and prints big numbers + mono badges to stdout. Compare
to `curl /api/alerts | jq` on the VM.

### Switch the demo site

Default `puente-arroyo-01`. Other seeded sites: `calle-baja-02`,
`silverado-fixed-cam-usgs` (latter has a bundled USGS video clip so you can
use `/api/sites/silverado-fixed-cam-usgs/sample-node-analysis` instead of the
inject endpoint for a real CV pass — slow on RTX 3060 with Gemma offload).

### Bring real Gemma back into the picture

Remove `record_demo.py`'s use of `inject-volunteer-report` and switch to real
`/api/reports` multipart POST. Accept that severity will be Gemma-rated and
non-deterministic. Useful for showcasing the LLM parser but bad for repeatable
recordings.

## Standard workflow

```powershell
# 1. Edit a .py / .tsx locally
# 2. pscp it to the VM (frontend hot-reloads, backend needs uvicorn restart)
& $PSCP -batch -hostkey $HKEY -pw 1 `
  "C:\Users\76hz\Documents\GitHub\AcuIfero4Vigia\<file>" `
  "hz@100.105.56.84:/home/hz/work/AcuIfero4Vigia_local/<file>"

# 3. Run the full pipeline
& $PLINK -ssh -batch -no-antispoof -hostkey $HKEY -l hz -pw 1 100.105.56.84 `
  "bash /home/hz/work/AcuIfero4Vigia_local/scripts/demo_persona_c/_rec_full.sh 2>&1 | tail -30"

# 4. Pull artifacts
& $PSCP -batch -hostkey $HKEY -pw 1 `
  "hz@100.105.56.84:/tmp/persona_c_demo.webm" `
  "C:\Users\76hz\Documents\GitHub\AcuIfero4Vigia\outputs\persona_c_demo.webm"
```

## Recording timings (current cut, ~45–60 s)

Per acto in `record_demo.py`:
- Act 1: 2.5 s dwell on banner + 2.0 s on tiles
- Act 2: refresh + scroll banner (2 s) + tiles (2.2 s) + evidence (2 s)
- Act 3 × 3: refresh + 3 scrolls (1.4 + 1.6 + 1.4 s) each report
- Act 4: audit (2.5 s) + cap card (2.5 s) + cap card after emit (2.2 s) + timeline (2.5 s) + back to banner (2 s)

To shorten the cut, drop dwell on intermediate Act 3 reports (R1 and R2 are
narratively redundant after R3 saturates). To lengthen, raise dwell on the
banner-color-change frames.

## What's NOT done yet (potential next iterations)

- Backend orchestration of two distinct Gemma models per source. Today's
  `gemma4:e4b` / `gemma4:e2b` labels are cosmetic; backend uses one
  `llm_client`. Real split needs an `image_assessor` adapter switch + a second
  `OpenAICompatibleLLM` instance with a different `ACUIFERO_LLM_MODEL`.
- Caption / subtitle overlay on the recorded video. Today the video is silent
  and uncaptioned. Could add a CSS overlay div with timed visibility per acto
  and screen-record that, or add a post-processing ffmpeg `drawtext` pass.
- Audio narration sync. Recorder is silent.
- Direct mp4 output. We emit webm because Playwright records webm natively.
  Convert in post with `ffmpeg -i in.webm -c:v libx264 -crf 18 out.mp4`.
- Frontend store polling. Currently we reload the whole page after each
  inject. A 3-second polling interval in `store.ts` would let the dashboard
  update smoothly without reloads, which would look more "real" on video.
- Action rail buttons. The four operator buttons (Emitir CAP / Sirena / LoRa /
  Defensa Civil) are pure UI in the current commit — they log to a stdout
  panel and push to the local timeline state, but they don't hit the backend.
  Wiring them to `/api/alerts/{id}/export-sinagir` etc. is documented in
  `DEMO_RECORDING_PERSONA_C.md` section 3 as a known follow-up.

## Outputs (in `outputs/`)

- `persona_c_demo_v3.webm` — current best take, 1440×900, ~8.9 MB, scroll
  choreography, live signals, per-source models, location narrative.
- `persona_c_demo_v2.webm` — taller viewport (1440×1800), no scrolling, looks
  shrunken. Kept for diff.
- `persona_c_demo.webm` — first take, old Dashboard, pre-fix. Reference of
  what NOT to ship.
- `dashboard_snap.png` / `dashboard_snap_v2.png` — full-page screenshots of
  the dashboard in its terminal (red) state.
- `persona_c_cap_alert.xml` — sample CAP v1.2 XML emitted in Acto 4.

## Quick sanity invocation

```powershell
# One-liner to verify the whole pipeline still works
& $PLINK -ssh -batch -no-antispoof -hostkey $HKEY -l hz -pw 1 100.105.56.84 `
  "bash /home/hz/work/AcuIfero4Vigia_local/scripts/demo_persona_c/_rec_full.sh 2>&1 | grep -E 'ACTO|verify|level=|score=|saved'"
```

Expected output: green 0.20 → yellow 0.52 → red 0.86 → red 0.96 → CAP saved.
DOM verify lines should show `bigNums` matching those scores.

## Open questions for the operator (you, in next session)

- Do we want the action rail buttons wired to real backend POSTs for the
  recording? If yes, this is the highest-leverage next change.
- Do we want subtitles / lower-third overlays burnt into the video, or are we
  going to add them in post in a video editor?
- Is the 1440×900 viewport the final delivery resolution, or do we need to
  re-encode for a specific platform (vertical for socials, 1080p for jury)?
