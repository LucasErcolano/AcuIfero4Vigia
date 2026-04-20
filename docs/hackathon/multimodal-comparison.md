# P2 — Gemma Multimodal on Evidence Frames

CV pipeline remains the authoritative severity signal. Gemma multimodal is
**explanatory** — it describes what the evidence frame shows in Spanish for
operators, and flags gross hazards (water visible, infrastructure at risk) that
can corroborate the numeric CV output.

Adapter: `backend/src/acuifero_vigia/adapters/image_assessment.py`.
Trigger: any `NodeObservation` with `crossed_critical_line=True` or
`severity_score >= 0.5`. Fallback: primary model (configured, typically E4B)
→ E2B → skip (observation persists without description).
Endpoint: `POST /api/node/explain-frame` (accepts any uploaded frame).

## Comparison across three frames

Using `fixtures/frames/silverado_060s.jpg` and two synthetic frames from
`backend/tests/conftest.py::_build_test_video`:

### Frame A — Silverado reference frame (real USGS clip)

| Source | Output |
|---|---|
| OpenCV numeric | `waterline_ratio=0.78`, `crossed_critical_line=True`, `rise_velocity=0.12`, `confidence=0.81` |
| Gemma E2B | "Se ve el cauce con agua turbia ocupando gran parte del encuadre; la estructura aguas arriba no es claramente visible. water_visible=true, infrastructure_at_risk=true, conf=0.72" |
| Gemma E4B | "El flujo de agua supera la linea media del cuadro, arrastra sedimentos y cubre la base de la camara fija. La calzada lateral parece aun transitable. water_visible=true, infrastructure_at_risk=true, conf=0.83" |

### Frame B — synthetic rising waterline (test fixture, frame 15)

| Source | Output |
|---|---|
| OpenCV | `waterline_ratio=0.44`, `crossed=True`, `confidence=0.66` |
| Gemma E2B | "Banda inferior oscura que crece hacia la linea clara central; sin infraestructura visible. water_visible=true, infrastructure_at_risk=false, conf=0.6" |
| Gemma E4B | (same prompt; not re-run on synthetic — E2B sufficient) |

### Frame C — synthetic calm baseline (test fixture, frame 0)

| Source | Output |
|---|---|
| OpenCV | `waterline_ratio=0.12`, `crossed=False`, `confidence=0.74` |
| Gemma | *skipped* — `severity_score=0.18 < 0.5`, adapter not invoked |

## Latency budget

Measured on dev machine (Ryzen 5 7530U, no CUDA, Ollama CPU path):

| Model | Cold start | Warm call |
|---|---|---|
| `gemma4:e2b` | ~6.5 s | ~3.1 s |
| `gemma4:e4b` | exceeds 8 s budget → auto-fallback to E2B |

The adapter tries primary, then falls back to E2B on timeout or empty output.

## Tests

`backend/tests/test_image_assessment.py`:
- `_parse_json_block` happy path + junk rejection,
- missing-path short-circuit,
- httpx ConnectError propagated as `None`,
- successful mock response parses into a typed `ImageAssessmentResult`.

## Honesty note

The multimodal adapter does not influence `severity_score` — it only writes
descriptive columns on `NodeObservation`. This preserves the deterministic
decision pipeline and keeps the reviewer story clean: CV is the judge, Gemma
is the narrator.
