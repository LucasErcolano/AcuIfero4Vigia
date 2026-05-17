#!/usr/bin/env bash
set +e
echo "=== A LiteRT ==="
curl -s -X POST http://127.0.0.1:8000/api/sites/silverado-fixed-cam-usgs/sample-node-analysis \
  -o /tmp/A2.json -w 'HTTP=%{http_code} time=%{time_total}s\n' --max-time 600
python3 - <<'PY'
import json
d=json.load(open('/tmp/A2.json'))
o=d.get('observation',{}); a=d.get('alert',{})
print('frames:',o.get('frames_analyzed'),'mode:',o.get('assessment_mode'))
print('runner:',o.get('runner'))
print('alert level:',a.get('level'),'score:',a.get('score'))
print('summary:',(o.get('temporal_summary') or '')[:300])
print('multimodal:',o.get('multimodal_assessment'))
PY
