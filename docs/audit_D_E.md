# Audit Persona D (Storytelling) + Persona E (Integration & Polish)

Fecha: 2026-05-16 (sábado). Deadline: lunes 18-may. Filmación: hoy.
Branch: develop. Branches activas: feat/video-demo (merged), feat/central-system (merged).

## Estado por tarea

| Tarea | Estado | Evidencia | Próxima acción |
|---|---|---|---|
| D-P3 Video 3 min, 4 actos | en-curso (preprod completa) | `docs/hackathon/video/` — timeline.md (8 bloques 3:00), narration.md, shot_list.md, captions.srt, edl.json, 7 hf_*.mp4 renderizados en raw/ (~4.6 MB total), narration.wav generado, ui_scenes/*.html (9 escenas) + screenshots PNG | Filmar talking-head (B02/B05), capturar screencast B05 con `scripts/capture_demo_connectivity.py`, ensamblar con `video-use` desde `edit/edl.json` |
| D-P6 Writeup 1500 palabras | no-empezada | Sin archivo `writeup.md` ni equivalente; existen insumos en `README.md`, `docs/architecture.md`, `MAIN_IDEA.md`, `docs/hackathon/vigia.md`, `docs/raspberry-pi-acuifero-node.md` | Crear `docs/hackathon/writeup.md` siguiendo estructura: Problema → Arquitectura → Anti-alucinación → Compliance → Diferenciación |
| D-P7 Sección anti-alucinación | parcial | `docs/hackathon/video/claims_guardrail.md` (A/B/C claims, MVP framing). `docs/hackathon/thinking-mode.md` (Gemma 4 thinking off). `docs/hackathon/android_gemma.md` ("no silent backend fallback") | Consolidar en sección del writeup: rule trace determinista + reasoning summary + claims guardrail |
| D-P9 Diferenciación competidores | no-empezada | Cero menciones de FarmWise / Flood Hub / PetaBencana en el repo | Investigar y redactar sección comparativa (offline-first, edge Gemma, SINAGIR, Spanish reasoning) |
| D apoyo P2 CAP español | hecho-base | Backend emite CAP v1.2 (README.md L54), reasoning summary en español confirmado | Revisar textos al ensamblar writeup |
| E-P11 Compliance AR | en-curso (agente bg) | `docs/compliance_argentina.md` ya existe (Ley 25.326, AAIP, Res 38/2024, 126/2024, SINAGIR) | NO duplicar — esperar agente bg |
| E-P12 Outreach Defensa Civil | hecho | `docs/outreach/` (3 batch summaries + linkedin_outreach.md + CSVs), `contacts_aquifero_outreach.csv` en raíz, `form_fill_results.json` | Confirmado por usuario |
| E-P13 Repo limpio + docker-compose + README | en-curso (agente bg) | `README.md` 14 KB (completo, no skeleton), `docker-compose.yml` funcional (backend + ollama profile), `.env.example`, LICENSE, .gitignore. PDFs sueltos en raíz + `_division.txt` + `_priorizado.txt` + `screenshots/` + `tools/` ensucian | NO duplicar — esperar agente bg; sugerir mover PDFs a `docs/hackathon-pdfs/` (ya hay copia ahí), borrar `_*.txt` |
| E-P14 Ablation E2B vs E4B | no-empezada | Cero scripts/notebooks de ablation. `scripts/eval_rioplatense.py` existe pero es eval de texto, no comparativa E2B/E4B | Esperar benchmarks de Persona A; crear `scripts/ablation_e2b_e4b.py` |
| E backstop LiteRT-LM | parcial | README menciona "LiteRT-LM (stub runner target)". Ruta backup vía Ollama/MediaPipe ya funciona | Sin acción si A entrega |
| E Demo E2E | listo | `scripts/demo_connectivity.py` + `scripts/demo.py` + `scripts/demo.ps1` + `docs/demo-script.md` | Ensayar antes de filmar B05 |
| Clip argentino (P4) | no-confirmado | No hay video crudo argentino en `raw/` (solo hf_*.mp4 sintéticos). `visual_prompts.md` describe B-roll AI | Filmar hoy o usar B-roll AI/stock con disclaimer |

## Arranque priorizado (hoy sábado, orden estricto)

1. Filmar B02+B05 talking-head (perecedero — requiere luz/locación)
2. Capturar screencast B05 (`capture_demo_connectivity.py`) con backend+frontend corriendo
3. Conseguir/filmar 1 clip argentino real para B01/B02 (riesgo si falta)
4. Escribir `docs/hackathon/writeup.md` (D-P6) — esqueleto + secciones 1+2 hoy, 3+4+5 mañana
5. Sección anti-alucinación (D-P7) — consolidar desde claims_guardrail + thinking-mode
6. Sección diferenciación (D-P9) — research + 200-300 palabras
7. Ensamblar video con `video-use` (domingo)
8. Ablation E2B vs E4B (E-P14) — solo si A entrega benchmarks domingo

## Riesgos

- **Clip argentino real**: no hay evidencia en repo. Si no se filma hoy, fallback es B-roll AI/stock con watermark "simulated scenario" (ya contemplado en claims_guardrail).
- **Writeup 1500 palabras**: cero borrador a 48 h del deadline. Bloqueante alto.
- **Diferenciación competidores**: cero research previo. ~2 h de trabajo.
- **Ablation E2B vs E4B**: depende de Persona A; si A no entrega, omitir y declararlo en roadmap.
- **Limpieza raíz**: PDFs y `_*.txt` sueltos + `screenshots/` + `tools/` (venvs) hacen el repo ver desprolijo — agente bg P13 debe atacarlo.
- **CAP español payload**: D debe revisar textos antes del freeze; aún no validado.

## Insumos del repo que sirven a D para el writeup

- Sección **Problema/Producto**: `MAIN_IDEA.md`, `HACKATHON.md`, `README.md` (intro + diferenciación)
- Sección **Arquitectura técnica (C)**: `docs/architecture.md`, `docs/central-integration-plan.md`, `README.md` (diagrama L36-51), `backend/` source
- Sección **Pi/Edge (A)**: `docs/raspberry-pi-acuifero-node.md`, `docs/edge-notes.md`, `scripts/pi_acuifero_node.py`, `scripts/run_acuifero_pi*.sh`
- Sección **Vigía/Android**: `docs/hackathon/vigia.md`, `docs/hackathon/android_gemma.md`
- Sección **Anti-alucinación (P7)**: `docs/hackathon/video/claims_guardrail.md`, `docs/hackathon/thinking-mode.md`, `docs/hackathon/multimodal-comparison.md`
- Sección **Compliance (E)**: `docs/compliance_argentina.md` (en expansión por agente bg)
- Sección **Eval**: `docs/hackathon/rioplatense_eval.md`, `datasets/`, `scripts/eval_rioplatense.py`
- Sección **SINAGIR**: `docs/hackathon/sinagir-mapping.md`
- **Demo narrativa**: `docs/demo-script.md`, `docs/hackathon/video/timeline.md`, `narration.md`
