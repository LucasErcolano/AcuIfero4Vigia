#!/usr/bin/env bash
set +e
cd /home/hz/work/AcuIfero4Vigia_local
echo "=== Suite 2: multimodal stress MAX_FRAMES=4 ==="
echo "--- gpu before ---"
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader

# Patch env, restart
sed -i 's/^ACUIFERO_MULTIMODAL_MAX_FRAMES=.*/ACUIFERO_MULTIMODAL_MAX_FRAMES=4/' backend/.env
grep -q '^ACUIFERO_MULTIMODAL_MAX_FRAMES=' backend/.env || echo 'ACUIFERO_MULTIMODAL_MAX_FRAMES=4' >> backend/.env
echo "env MAX_FRAMES=$(grep ^ACUIFERO_MULTIMODAL_MAX_FRAMES backend/.env)"

bash /tmp/start_backend.sh
sleep 12
curl -s --max-time 5 http://127.0.0.1:8000/api/health || { echo "backend dead"; exit 1; }

# Find/create test video
VID=""
for c in backend/data/fixtures/*.mp4 backend/data/samples/*.mp4 fixtures/video/*.mp4 backend/data/*.mp4; do
  [ -f "$c" ] && VID="$c" && break
done
if [ -z "$VID" ]; then
  echo "no fixture mp4, synthesizing 6s 480p test video via ffmpeg"
  ffmpeg -y -f lavfi -i "testsrc=duration=6:size=640x480:rate=10" -pix_fmt yuv420p /tmp/test_node.mp4 -loglevel error
  VID=/tmp/test_node.mp4
fi
ls -la "$VID"

echo "--- gpu after engine load ---"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

# fire 1: warm
echo "=== POST /api/node/analyze (call 1) ==="
( nvidia-smi --query-gpu=memory.used --format=csv,noheader -l 2 > /tmp/gpu_call1.log 2>&1 ) &
GPID=$!
T0=$(date +%s)
curl -s --max-time 300 -X POST http://127.0.0.1:8000/api/node/analyze \
  -F site_id=silverado-fixed-cam-usgs \
  -F "video=@$VID" \
  -o /tmp/N1.json -w "HTTP=%{http_code} time=%{time_total}s\n"
T1=$(date +%s)
kill $GPID 2>/dev/null
python3 -c "
import json
d=json.load(open('/tmp/N1.json'))
o=d.get('observation',{})
a=d.get('alert',{})
print('frames_analyzed:',o.get('frames_analyzed'),'runner:',o.get('runner',{}).get('mode'),'level:',a.get('level') if isinstance(a,dict) else 'n/a','score:',a.get('score') if isinstance(a,dict) else 'n/a')
"
echo "--- gpu peak during call 1 ---"
sort -u /tmp/gpu_call1.log | tail -5

echo
echo "=== POST /api/node/analyze (call 2, warm) ==="
curl -s --max-time 300 -X POST http://127.0.0.1:8000/api/node/analyze \
  -F site_id=silverado-fixed-cam-usgs \
  -F "video=@$VID" \
  -o /tmp/N2.json -w "HTTP=%{http_code} time=%{time_total}s\n"

echo
echo "=== buffer/timeout/oom check in logs ==="
grep -ciE 'buffer.overflow|out of memory|cuda.error|oom-killer|conversation_send_message failed|timeout' /tmp/uvicorn.log

echo
echo "--- gpu final ---"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

# restore default
sed -i 's/^ACUIFERO_MULTIMODAL_MAX_FRAMES=.*/ACUIFERO_MULTIMODAL_MAX_FRAMES=1/' backend/.env
