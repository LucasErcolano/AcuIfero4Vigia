#!/usr/bin/env bash
python3 - <<'PY'
import json
d=json.load(open('/tmp/B.json'))
sj=json.loads(d['parsed']['structured_json'])
print('parser_source:', d['parsed']['parser_source'])
print('summary:', sj.get('summary'))
print('confidence:', sj.get('confidence'))
PY
echo "=== litert text errors ==="
grep -c 'send_message failed' /tmp/uvicorn.log
