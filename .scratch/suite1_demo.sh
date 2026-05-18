#!/usr/bin/env bash
cd /home/hz/work/AcuIfero4Vigia_local
START=$(date +%s)
backend/.venv/bin/python scripts/demo_connectivity.py 2>&1 | tail -30
END=$(date +%s)
echo "recovery_seconds=$((END-START))"
