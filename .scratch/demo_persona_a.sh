#!/usr/bin/env bash
# Persona A demo: Acuifero edge node — deterministic firewall (numpy+PIL)
# feeding LiteRT-LM Gemma 4 E4B multimodal verdict + backend dispatch.
# Designed for asciinema recording on a VM simulating a Pi-class node.
set +e
B=http://127.0.0.1:8000
SITE=silverado-fixed-cam-usgs

banner() {
  echo
  echo "=========================================="
  echo "$1"
  echo "=========================================="
  sleep 1
}

slow_cat() {
  while IFS= read -r line; do echo "$line"; sleep 0.04; done
}

banner "PERSONA A — Acuifero edge node (VM simulating Raspberry Pi 5)"
cat <<EOF | slow_cat
Hardware (simulated):
  Host           : Linux $(uname -r)
  CPU/RAM        : $(grep -c ^processor /proc/cpuinfo) core / $(awk '/MemTotal/ {printf "%.1f", $2/1024/1024}' /proc/meminfo) GB
  GPU (vision)   : $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
  Inference      : LiteRT-LM (Gemma 4 E4B) — multimodal GPU + speculative decoding
  Prefilter      : Deterministic CV firewall (numpy+PIL, anti-hallucination anchor)
EOF
sleep 2

banner "STEP 1 — Backend health + runtime config"
curl -s "$B/api/health" | python3 -m json.tool | slow_cat
curl -s "$B/api/settings/runtime" | python3 -c "
import json, sys
d = json.load(sys.stdin)['acuifero']
keep = {k: d.get(k) for k in [
    'multimodal_max_frames','max_curated_frames',
    'multimodal_frame_sample_seconds','node_enable_speculative_decoding','engine_ready',
]}
print(json.dumps(keep, indent=2))" | slow_cat
sleep 1

banner "STEP 2 — Tail uvicorn log filtered for firewall + LiteRT"
truncate -s 0 /tmp/demo_filtered.log 2>/dev/null
( tail -n 0 -F /tmp/uvicorn.log 2>/dev/null \
    | grep --line-buffered -E "deterministic_firewall|litert|runner.mode|speculative|POST /api/sites" \
    > /tmp/demo_filtered.log 2>&1 ) &
TAIL_PID=$!
sleep 1

banner "STEP 3 — POST sample-node-analysis (bundled Silverado camera clip)"
echo "+ curl -s -X POST $B/api/sites/$SITE/sample-node-analysis"
sleep 1
curl -s --max-time 180 -X POST "$B/api/sites/$SITE/sample-node-analysis" \
  -o /tmp/demo_resp.json \
  -w "HTTP=%{http_code} latency=%{time_total}s\n"

banner "STEP 4 — Deterministic firewall vector (pre-LLM, numpy+PIL)"
python3 - <<'PY' | slow_cat
import json
d = json.load(open('/tmp/demo_resp.json'))
fw = d['observation']['critical_evidence'].get('deterministic_prefilter', {})
print(json.dumps({
    "cv_backend": fw.get("cv_backend"),
    "opencv_used": fw.get("opencv_used"),
    "water_level": fw.get("water_level"),
    "waterline_ratio": fw.get("waterline_ratio"),
    "rise_velocity": fw.get("rise_velocity"),
    "crossed_critical_line": fw.get("crossed_critical_line"),
    "confidence": fw.get("confidence"),
}, indent=2))
PY

banner "STEP 5 — LiteRT-LM Gemma 4 multimodal verdict"
python3 - <<'PY' | slow_cat
import json
d = json.load(open('/tmp/demo_resp.json'))
obs = d['observation']
print(json.dumps({
    "runner.mode": obs['runner']['mode'],
    "runner.name": obs['runner']['name'],
    "assessment_mode": obs.get('assessment_mode'),
    "assessment_level": obs.get('assessment_level'),
    "assessment_score": obs.get('assessment_score'),
    "frames_analyzed": obs.get('frames_analyzed'),
    "temporal_summary": obs.get('temporal_summary'),
    "reasoning_summary": obs.get('reasoning_summary'),
}, indent=2))
PY

banner "STEP 6 — Fused alert score posted to backend"
python3 - <<'PY' | slow_cat
import json
d = json.load(open('/tmp/demo_resp.json'))
a = d['alert']
print(json.dumps({
    "level": a.get('level'),
    "score": a.get('score'),
    "trigger_source": a.get('trigger_source'),
    "local_alarm_triggered": a.get('local_alarm_triggered'),
}, indent=2))
PY

banner "STEP 7 — Captured log lines during inference"
sleep 1
kill $TAIL_PID 2>/dev/null
sed -n '1,30p' /tmp/demo_filtered.log

banner "DEMO COMPLETE — RTX 3060 12GB (simulating Pi 5) | LiteRT-LM GPU+CPU | Firewall: numpy+PIL"
