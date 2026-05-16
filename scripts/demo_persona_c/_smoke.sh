#!/usr/bin/env bash
set -e
pkill -f "uvicorn acuifero_vigia.main:app" 2>/dev/null || true
sleep 2
cd /home/hz/work/AcuIfero4Vigia_local/backend
mkdir -p data
rm -f data/edge.db data/central.db data/acuifero.db
PYTHONPATH=src python3 -m acuifero_vigia.scripts.seed
nohup env ACUIFERO_ENABLE_DEMO_INJECT=1 PYTHONPATH=src python3 -m uvicorn acuifero_vigia.main:app --host 127.0.0.1 --port 8000 > /tmp/uvicorn.log 2>&1 &
sleep 6
echo "---health---"
curl -sS http://127.0.0.1:8000/api/health || curl -sS http://127.0.0.1:8000/api/runtime/health || echo no_health
echo ""
echo "---ACTO 1 verde---"
bash /home/hz/work/AcuIfero4Vigia_local/scripts/demo_persona_c/01_vigia_verde.sh
sleep 2
echo "---ACTO 2 amarillo---"
bash /home/hz/work/AcuIfero4Vigia_local/scripts/demo_persona_c/02_acuifero_amarillo.sh
sleep 2
echo "---ACTO 3 rojo---"
bash /home/hz/work/AcuIfero4Vigia_local/scripts/demo_persona_c/03_fusion_rojo.sh
