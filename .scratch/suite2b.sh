#!/usr/bin/env bash
set +e
cd /home/hz/work/AcuIfero4Vigia_local
echo "=== Suite 2b: bump both frame caps + longer video ==="
# also bump curated + reduce sample interval so a short clip yields >1 frame
for K in ACUIFERO_MULTIMODAL_MAX_FRAMES ACUIFERO_MAX_CURATED_FRAMES; do
  if grep -q "^$K=" backend/.env; then sed -i "s/^$K=.*/$K=4/" backend/.env; else echo "$K=4" >> backend/.env; fi
done
if grep -q '^ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=' backend/.env; then
  sed -i 's/^ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=.*/ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=2/' backend/.env
else
  echo 'ACUIFERO_MULTIMODAL_FRAME_SAMPLE_SECONDS=2' >> backend/.env
fi
grep -E 'MAX_FRAMES|MAX_CURATED|FRAME_SAMPLE' backend/.env

# synth 12s video so 2s sampling yields ~4-6 candidate frames
ffmpeg -y -f lavfi -i "testsrc=duration=12:size=640x480:rate=10" -pix_fmt yuv420p /tmp/test12.mp4 -loglevel error
ls -la /tmp/test12.mp4

bash /tmp/start_backend.sh
sleep 12
curl -s --max-time 5 http://127.0.0.1:8000/api/settings/runtime | python3 -c "
import json,sys
d=json.load(sys.stdin)
a=d['acuifero']
print('multimodal_max_frames:',a.get('multimodal_max_frames'),'max_curated_frames:',a.get('max_curated_frames'),'frame_sample_s:',a.get('multimodal_frame_sample_seconds'))
print('engine_ready:',a.get('engine_ready'))"

echo "--- gpu before ---"
nvidia-smi --query-gpu=memory.used --format=csv,noheader

( nvidia-smi --query-gpu=memory.used --format=csv,noheader -l 1 > /tmp/gpu_s2b.log 2>&1 ) &
GPID=$!
echo "=== POST /api/node/analyze ==="
curl -s --max-time 600 -X POST http://127.0.0.1:8000/api/node/analyze \
  -F site_id=silverado-fixed-cam-usgs \
  -F "video=@/tmp/test12.mp4" \
  -o /tmp/N3.json -w "HTTP=%{http_code} time=%{time_total}s\n"
kill $GPID 2>/dev/null
python3 -c "
import json
d=json.load(open('/tmp/N3.json'))
o=d.get('observation',{})
print('frames_analyzed:',o.get('frames_analyzed'),'mode:',o.get('assessment_mode'),'runner:',o.get('runner',{}).get('mode'))
"
echo "--- gpu peak ---"
sort -un /tmp/gpu_s2b.log | tail -3

echo "=== real errors in log ==="
echo -n 'send_message failed: '; grep -c 'send_message failed' /tmp/uvicorn.log
echo -n 'OOM/oom-killer:    '; grep -ciE 'out of memory|oom-killer' /tmp/uvicorn.log
echo -n 'CUDA errors:       '; grep -ciE 'cuda.error|cuda.fail' /tmp/uvicorn.log
echo -n 'HTTP 500:          '; grep -c ' 500 Internal' /tmp/uvicorn.log
echo -n 'Timeouts (real):   '; grep -ciE 'TimeoutError|read timeout|connect timeout' /tmp/uvicorn.log
