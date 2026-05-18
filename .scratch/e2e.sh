#!/usr/bin/env bash
set +e
B=http://127.0.0.1:8000
echo "=== A: sample-node-analysis (silverado) ==="
curl -s -X POST "$B/api/sites/silverado-fixed-cam-usgs/sample-node-analysis" -o /tmp/A.json -w "HTTP=%{http_code} time=%{time_total}s\n"
python3 -c "import json; d=json.load(open('/tmp/A.json')); o=d.get('observation',{}); a=d.get('alert',{}); print('site:',o.get('site_id'),'frames:',o.get('frames_analyzed'),'mode:',o.get('assessment_mode'),'runner:',o.get('runner',{}).get('mode'),'level:',a.get('level'),'score:',a.get('score'))" 2>&1 | head -5

echo "=== B: volunteer report ==="
curl -s -X POST "$B/api/reports" \
  -F site_id=silverado-fixed-cam-usgs \
  -F reporter_name='Operador Demo' \
  -F reporter_role='brigadista' \
  -F transcript_text='el agua ya paso la marca del puente, sube rapido y trae barro' \
  -F offline_created=true -o /tmp/B.json -w "HTTP=%{http_code} time=%{time_total}s\n"
python3 -c "import json; d=json.load(open('/tmp/B.json')); r=d.get('report',{}); p=d.get('parsed',{}); a=d.get('alert',{}); print('report_id:',r.get('id'),'parser:',p.get('parser_source'),'urgency:',p.get('urgency'),'alert:',a.get('level'),'score:',a.get('score'))"

echo "=== C: alerts list ==="
curl -s "$B/api/alerts" -o /tmp/C.json -w "HTTP=%{http_code}\n"
python3 -c "import json; d=json.load(open('/tmp/C.json')); print('count:',len(d));
[print(' -',x.get('id'),x.get('site_id'),x.get('level'),'node=',x.get('node_score'),'report=',x.get('report_score'),'fused=',x.get('score')) for x in d[:5]]"

echo "=== D1: alert detail + actuators ==="
ALERT_ID=$(python3 -c "import json; d=json.load(open('/tmp/C.json')); print(d[0]['id'] if d else '')")
echo "ALERT=$ALERT_ID"
[ -n "$ALERT_ID" ] && curl -s "$B/api/alerts/$ALERT_ID" -o /tmp/D1.json -w "HTTP=%{http_code}\n" && python3 -c "import json; d=json.load(open('/tmp/D1.json')); print('actuators:',d.get('actuators') or d.get('dispatched_actuators') or 'n/a'); print('reasoning:',(d.get('reasoning_summary') or '')[:120])"

echo "=== D2: CAP emit ==="
[ -n "$ALERT_ID" ] && curl -s -X POST "$B/api/cap/emit" -H 'Content-Type: application/json' -d "{\"alert_id\":\"$ALERT_ID\"}" -o /tmp/D2.json -w "HTTP=%{http_code}\n" && head -c 800 /tmp/D2.json; echo

echo "=== D3: SINAGIR export ==="
[ -n "$ALERT_ID" ] && curl -s -X POST "$B/api/alerts/$ALERT_ID/export-sinagir" -o /tmp/D3.json -w "HTTP=%{http_code}\n" && head -c 800 /tmp/D3.json; echo
