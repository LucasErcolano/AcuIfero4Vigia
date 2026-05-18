#!/usr/bin/env bash
curl -s -X POST http://127.0.0.1:8000/api/reports \
  -F site_id=silverado-fixed-cam-usgs \
  -F reporter_name=test -F reporter_role=brigadista \
  -F transcript_text='el agua ya paso la marca del puente, sube rapido y trae barro' \
  -F offline_created=true \
  -o /tmp/B.json -w 'HTTP=%{http_code} time=%{time_total}s\n' --max-time 600
python3 - <<'PY'
import json
d=json.load(open('/tmp/B.json'))
p=d['parsed']
print('parser:',p['parser_source'],'urgency:',p['urgency'],'water:',p['water_level_category'],'summary:',p.get('structured_json',{}).get('summary'))
PY
echo "=== log tail ==="
grep -iE 'litert|parser|generate_text' /tmp/uvicorn.log | tail -10
