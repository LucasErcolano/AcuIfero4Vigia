# Persona A recording runbook

Goal: record a 30-45 s terminal-first clip for Persona A, the behind-the-scenes
Acuifero edge node on the real Raspberry Pi. The clip should prove the Pi
hardware and LiteRT runtime, then hand off honestly to the camera signal Persona
C injects in Acto 2.

## Preconditions

- Raspberry Pi access check:

```bash
ssh raspi5-tail "hostname"
```

Expected output: `raspi5`.

Do not show repository state in the jury-facing recording. Branch names,
untracked files, local paths, and development-machine status are internal
operator details, not part of the hackathon proof.

## Primary recording: real terminal on the Pi

This is the preferred take when the request is "the terminal GIF, but on the
real Raspberry Pi." Record the SSH session or a terminal already open on the Pi.
Keep it plain and legible: commands plus real output, not an editorial evidence
card.

Suggested command sequence:

```powershell
ssh raspi5-tail
```

```bash
hostname
cat /proc/device-tree/model
free -h
cd ~/AcuIfero4Vigia-litert
ls -lh backend/data/models/gemma-4-E2B-it.litertlm
backend/.venv/bin/python -c "import litert_lm; print('litert_lm ok')"
ACUIFERO_NODE_PROVIDER=litert \
ACUIFERO_NODE_MODEL_PATH=backend/data/models/gemma-4-E2B-it.litertlm \
ACUIFERO_NODE_BACKEND=gpu \
ACUIFERO_NODE_MULTIMODAL_BACKEND=cpu \
ACUIFERO_NODE_MULTIMODAL_VISION_BACKEND=cpu \
PYTHONPATH=backend/src \
backend/.venv/bin/python scripts/litert_smoke.py --reasoning
printf '\nPersona C Acto 2 uses synchronized cam=52 demo payload.\n'
printf 'This Pi run validates the real edge LiteRT runtime behind that narrative.\n'
```

Expected visible proof:

- `hostname` returns `raspi5`
- board line says `Raspberry Pi 5 Model B Rev 1.1`
- model file is `gemma-4-E2B-it.litertlm`
- `litert_lm ok`
- smoke exits with `smoke_exit_code=0` or equivalent successful command exit
- benchmark block shows real `elapsed_seconds`, `rss_mb`, `backend=gpu`,
  `multimodal_backend=cpu`, and `multimodal_vision_backend=cpu`

If the backend is already running and there is enough time, optionally add this
before the final bridge line:

```bash
curl -s --max-time 5 http://127.0.0.1:8000/api/settings/runtime
```

Do not block the main recording on the backend endpoint. The smoke proof is the
minimum defensible Pi runtime evidence.

## Scripted/replay recording: fallback only

Use this only if a controlled local terminal output is needed for editing or if
the Pi/backend is unavailable during the recording window. Keep `mode=replay`
or `source=replay` visible; do not cut away that label.

Live backend through SSH tunnel, if the Pi backend is already running:

Terminal 1, keep the tunnel open:

```powershell
ssh -N -L 18000:127.0.0.1:8000 raspi5-tail
```

Terminal 2, preview from the local worktree:

```powershell
cd C:\Users\joaco\Documents\IA\Personal\AcuIfero4Vigia
python docs\demo\persona_a_terminal_demo.py --api http://127.0.0.1:18000
```

Replay from the local worktree:

```powershell
cd C:\Users\joaco\Documents\IA\Personal\AcuIfero4Vigia
python docs\demo\persona_a_terminal_demo.py --force-replay
```

Only if these `docs/demo/persona_a_*` artifacts have intentionally been copied
to the Pi, the equivalent Pi command is:

```bash
cd /home/joaco/AcuIfero4Vigia-litert
backend/.venv/bin/python docs/demo/persona_a_terminal_demo.py --api http://127.0.0.1:8000
```

## Shot timing

1. Hold title for 3 s:
   `PERSONA A — Acuífero edge node (Raspberry Pi 5)`.
2. Runtime config, 6-8 s:
   `provider=litert`, `backend=gpu`, `multimodal_backend=cpu`,
   `vision_backend=cpu`, `speculative_decoding=true`, E2B model.
3. Firewall, 6-8 s:
   if shown, say `pure-Python/PIL visual prefilter`, not OpenCV.
4. Backend proof, 10-15 s:
   main proof is the real Pi LiteRT smoke. Live endpoint is optional and should
   be shown only if it is reachable during the take.
5. Bridge, 5-7 s:
   `Acto 2 demo payload` from
   `scripts/demo_persona_c/02_acuifero_amarillo.sh`: `severity_score=0.52`.
   On-screen line: `Same edge-node channel feeds Persona C Acto 2 demo payload`.
   Keep this boundary visible: `cam=52 is the synchronized Acto 2 payload, not the Silverado sample score`.
6. Final overlay:
   `Hardware: Raspberry Pi 5 8GB | LiteRT-LM | text GPU + image CPU/CPU | RSS peak from benchmark-card`.

## Editing notes

- Do not say E4B is the Pi 5 8GB primary profile.
- Do not say OpenCV. Say `pure-Python/PIL visual prefilter`.
- Do not show TTFT, tok/s, or token streaming.
- Do not imply real SINAGIR integration or deployment.
- Mention Vigia only as Persona C's later fusion step.
