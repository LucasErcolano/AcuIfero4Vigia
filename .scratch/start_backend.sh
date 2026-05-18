#!/usr/bin/env bash
set -e
cd /home/hz/work/AcuIfero4Vigia_local/backend
pkill -f "acuifero_vigia.main:app" 2>/dev/null || true
sleep 1
set -a
source .env
set +a
nohup env PYTHONPATH=src .venv/bin/python -m uvicorn acuifero_vigia.main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn.log 2>&1 &
echo "PID=$!"
disown
