#!/usr/bin/env bash
set +e
B=http://127.0.0.1:8000
echo "=========================================="
echo "Suite 3: fault injection"
echo "=========================================="

echo
echo "=== 3.1 Ollama DOWN mid-request ==="
sudo systemctl stop ollama 2>&1 || pkill -9 ollama
sleep 2
echo "ollama_alive: $(curl -s -o /dev/null -w '%{http_code}' --max-time 2 http://127.0.0.1:11434/api/version)"
curl -s --max-time 60 -X POST "$B/api/reports" \
  -F site_id=silverado-fixed-cam-usgs \
  -F reporter_name='Fault31' -F reporter_role='brigadista' \
  -F transcript_text='agua cortando la ruta, evacuamos a familias' \
  -F offline_created=true -o /tmp/F31.json -w "HTTP=%{http_code} time=%{time_total}s\n"
python3 -c "
import json
d=json.load(open('/tmp/F31.json'))
p=d.get('parsed',{})
a=d.get('alert',{})
print('parser_source:',p.get('parser_source'),'(expect rules fallback)')
print('alert_level:',a.get('level'),'score:',a.get('score'))
print('reasoning_summary_present:', bool(d.get('alert',{}).get('reasoning_summary')))
"

echo
echo "=== 3.2 Ollama DOWN — actuator dispatch path ==="
curl -s --max-time 60 -X POST "$B/api/sites/silverado-fixed-cam-usgs/sample-node-analysis" \
  -o /tmp/F32.json -w "HTTP=%{http_code} time=%{time_total}s\n"
python3 -c "
import json
d=json.load(open('/tmp/F32.json'))
print('runner:',d.get('observation',{}).get('runner',{}).get('mode'))
print('level:',d.get('alert',{}).get('level'))
"

echo
echo "Restart ollama"
sudo systemctl start ollama 2>&1 || nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 6
echo "ollama_alive: $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:11434/api/version)"
# ensure model warmed
curl -s --max-time 30 http://127.0.0.1:11434/api/generate -d '{"model":"gemma4:e2b","prompt":"hi","stream":false}' >/dev/null

echo
echo "=== 3.3 Malformed JSON via stubbed proxy ==="
# Spin a tiny HTTP server that returns garbage in OpenAI shape, point backend at it
python3 - <<'PY' &
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        l=int(self.headers.get('Content-Length','0')); self.rfile.read(l)
        self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
        # malformed: claim JSON content but ship truncated tool-call garbage
        body=json.dumps({"choices":[{"message":{"role":"assistant","content":"{\"foo\":\"bar","tool_calls":[{"function":{"name":"trigger_alarm","arguments":"{not-json"}}]}}]})
        self.wfile.write(body.encode())
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'{"object":"list","data":[]}')
    def log_message(self,*a,**k): pass
HTTPServer(('127.0.0.1',11499), H).serve_forever()
PY
PROXY=$!
sleep 1

# patch env, restart backend pointed at stub
cd /home/hz/work/AcuIfero4Vigia_local
cp backend/.env /tmp/env.bak
sed -i 's|^ACUIFERO_LLM_BASE_URL=.*|ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11499/v1|' backend/.env
grep -q '^ACUIFERO_LLM_BASE_URL=' backend/.env || echo 'ACUIFERO_LLM_BASE_URL=http://127.0.0.1:11499/v1' >> backend/.env
bash /tmp/start_backend.sh
sleep 8

curl -s --max-time 30 -X POST "$B/api/reports" \
  -F site_id=silverado-fixed-cam-usgs \
  -F reporter_name='Fault33' -F reporter_role='brigadista' \
  -F transcript_text='puente cortado, gente sobre techos' \
  -F offline_created=true -o /tmp/F33.json -w "HTTP=%{http_code} time=%{time_total}s\n"
python3 -c "
import json
d=json.load(open('/tmp/F33.json'))
p=d.get('parsed',{})
print('parser_source:',p.get('parser_source'),'(expect rules — malformed json caught)')
print('alert_level:',d.get('alert',{}).get('level'))
"

# restore real env
cp /tmp/env.bak backend/.env
kill $PROXY 2>/dev/null
bash /tmp/start_backend.sh
sleep 8

echo
echo "=== 3.4 Concurrency 5x sample-node-analysis (LiteRT engine lock) ==="
python3 - <<'PY'
import concurrent.futures, time, httpx
URL="http://127.0.0.1:8000/api/sites/silverado-fixed-cam-usgs/sample-node-analysis"
def hit(i):
    t0=time.time()
    try:
        with httpx.Client(timeout=300) as c:
            r=c.post(URL)
        return (i, r.status_code, time.time()-t0, r.json().get('observation',{}).get('runner',{}).get('mode') if r.status_code==200 else r.text[:120])
    except Exception as e:
        return (i, "EXC", time.time()-t0, str(e)[:120])
t0=time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as p:
    res=[f.result() for f in concurrent.futures.as_completed([p.submit(hit,i) for i in range(5)])]
print(f"wall={time.time()-t0:.2f}s")
ok=sum(1 for r in res if r[1]==200)
print(f"ok={ok}/5")
for r in sorted(res, key=lambda x: x[2]):
    print(f"  #{r[0]} status={r[1]} dt={r[2]:.2f}s runner={r[3]}")
PY

echo
echo "=== final error tally ==="
echo -n 'HTTP 500:           '; grep -c ' 500 Internal' /tmp/uvicorn.log
echo -n 'send_message failed:'; grep -c 'send_message failed' /tmp/uvicorn.log
echo -n 'JSONDecodeError:    '; grep -c 'JSONDecodeError' /tmp/uvicorn.log
echo -n 'actuator parse fail:'; grep -c 'actuator response parsing failed' /tmp/uvicorn.log
