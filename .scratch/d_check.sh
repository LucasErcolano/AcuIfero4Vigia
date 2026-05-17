#!/usr/bin/env bash
B=http://127.0.0.1:8000
echo "=== alert 2 full ==="
curl -s $B/api/alerts/2 | python3 -m json.tool | head -80
echo "=== operator-summary ==="
curl -s $B/api/sites/silverado-fixed-cam-usgs/operator-summary | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('current_level:',d.get('current_level'),'score:',d.get('current_score'))
la=d.get('latest_alert') or {}
print('alert.local_alarm_triggered:',la.get('local_alarm_triggered'))
print('latest_actuation:',d.get('latest_actuation'))
"
echo "=== CAP w/ proper params ==="
curl -s -X POST $B/api/cap/emit \
  -H 'Content-Type: application/json' \
  -d '{"site_id":"silverado-fixed-cam-usgs","lat":33.7471,"lon":-117.6416,"severity":"severe","headline":"Inundacion en curso - evacuar zonas bajas","summary":"Nivel critico confirmado por reporte ciudadano y nodo fijo."}' \
  -o /tmp/cap2.xml -w 'HTTP=%{http_code}\n'
grep -oE '<(severity|urgency|certainty|headline)>[^<]+' /tmp/cap2.xml
