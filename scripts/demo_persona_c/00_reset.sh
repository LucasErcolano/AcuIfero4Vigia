#!/usr/bin/env bash
# Limpieza pre-demo: borra DB + uploads, re-siembra sitios.
# Necesario para empezar cada toma desde estado verde limpio.
set -euo pipefail

BACKEND_DIR="${BACKEND_DIR:-/home/hz/work/AcuIfero4Vigia_local/backend}"

cd "$BACKEND_DIR"
rm -f data/edge.db data/central.db data/acuifero.db
rm -rf data/uploads/* 2>/dev/null || true
PYTHONPATH=src python3 -m acuifero_vigia.scripts.seed
echo "[reset] DB re-seeded. Listo para grabar."
