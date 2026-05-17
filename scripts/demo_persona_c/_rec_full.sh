#!/usr/bin/env bash
# Full pipeline: kill+restart backend, reset DB, ensure frontend up, run recorder.
set -e
cd /home/hz/work/AcuIfero4Vigia_local/backend
pkill -f "uvicorn acuifero_vigia.main:app" 2>/dev/null || true
sleep 2
rm -f data/edge.db data/central.db data/acuifero.db
PYTHONPATH=src python3 -m acuifero_vigia.scripts.seed
nohup env ACUIFERO_ENABLE_DEMO_INJECT=1 PYTHONPATH=src python3 -m uvicorn acuifero_vigia.main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn.log 2>&1 &
sleep 6

# Make sure frontend is up
if ! curl -sf http://127.0.0.1:5173 > /dev/null; then
  echo "[rec] starting frontend dev server..."
  cd /home/hz/work/AcuIfero4Vigia_local/frontend
  nohup npm run dev -- --host 127.0.0.1 --port 5173 > /tmp/frontend.log 2>&1 &
  sleep 8
fi

curl -sS http://127.0.0.1:8000/api/health
echo
curl -sf http://127.0.0.1:5173 > /dev/null && echo "[rec] frontend OK"

cd /home/hz/work/AcuIfero4Vigia_local/scripts/demo_persona_c
python3 record_demo.py --out /tmp/persona_c_demo.webm
