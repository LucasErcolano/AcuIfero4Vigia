# Persona A claims/QC

## Real lines

- Raspberry Pi access can be verified with:
  `ssh raspi5-tail "hostname"`.
- The Pi answered as `raspi5`.
- The defended Pi 5 8GB runtime profile is E2B with `provider=litert`,
  text/reasoning `backend=gpu`, multimodal `cpu`, vision `cpu`, and
  `speculative_decoding=true`.
- The deterministic firewall implementation is pure PIL / Python and emits
  `cv_backend=pil-pure-python`, `waterline_ratio`, `rise_velocity`,
  `water_level`, and `crossed_critical_line`.
- Benchmark-card metrics are wall-clock and RSS peak only. TTFT, decode tok/s,
  output token counts, and token streaming are not measured.

## Replay lines

- `docs/demo/persona_a_replay.json` is a replay fixture for recording when the
  backend is unavailable.
- Replay output must remain labeled `mode=replay` or `source=replay`; do not cut
  away the label in the edit.
- Replay `sample-node-analysis` lines show the documented P1 evidence shape:
  `runner.mode=litert-multimodal-temporal`,
  `assessment_mode=gemma4-multimodal-v1`, and `frames_analyzed=1`.

## Demo-inject lines

- `cam=52` and `severity_score=0.52` are the Persona C Acto 2 demo payload from
  `scripts/demo_persona_c/02_acuifero_amarillo.sh`.
- Do not claim the Silverado sample clip necessarily produced exactly 0.52.
- The allowed bridge wording is:
  `Same edge-node channel feeds Persona C Acto 2 demo payload`.
- Keep this boundary visible:
  `cam=52 is the synchronized Acto 2 payload, not the Silverado sample score`.

## Blocked claims

- No "E4B GPU is the main Raspberry Pi 5 8GB profile".
- No "OpenCV" for the current firewall path.
- No TTFT, tok/s, streaming-token, accuracy, or lead-time claim.
- No real deployment, real hardware station, or real SINAGIR integration claim.
- No Vigia details inside Persona A except the one-line handoff to Persona C.
- No repository state, local branch names, dirty worktree output, untracked file
  lists, or other development-machine details in jury-facing video.
