#!/usr/bin/env bash
set +e
B=http://127.0.0.1:8000/api
echo "=== Suite 1.1: demo_connectivity (offline->siren->online->drain) ==="
START=$(date +%s)
cd /home/hz/work/AcuIfero4Vigia_local
.venv/bin/python scripts/demo_connectivity.py 2>&1 | tail -40
END=$(date +%s)
echo "recovery_seconds=$((END-START))"

echo
echo "=== Suite 1.2: fanout 15 concurrent reports ==="
python3 - <<'PY'
import concurrent.futures, time, httpx, json
URL="http://127.0.0.1:8000/api/reports"
TRANSCRIPTS=[
 "el agua tapo el camino y la gente sale corriendo",
 "subio rapido, perdimos el primer escalon del puente",
 "barro hasta la rodilla en barrio bajo, sirenas activas",
 "estamos evacuando, el rio creció dos metros en una hora",
 "puente cortado, agua marron arrastrando troncos",
 "alerta vecinos, agua dentro de las casas zona costanera",
 "creciente repentina, cinco familias en techo",
 "ruta provincial cortada km 12, agua hasta el motor de los autos",
 "se vino la avenida, perdimos contacto con la escuela rural",
 "lluvia no para, arroyo desbordado al norte del pueblo",
 "rescate en curso, dos personas en techo del galpon",
 "alcantarilla colapsada, agua entra al hospital",
 "puente peatonal arrancado por la correntada",
 "barrio aislado, comunicaciones intermitentes",
 "evacuacion forzada zona inundable, sirena local sonando",
]
def submit(i, txt):
    t0=time.time()
    try:
        with httpx.Client(timeout=60) as c:
            r=c.post(URL, data={"site_id":"silverado-fixed-cam-usgs","reporter_name":f"V{i}","reporter_role":"brigadista","transcript_text":txt,"offline_created":"true"}, files={})
        dt=time.time()-t0
        return (i, r.status_code, dt, r.json().get("alert",{}).get("level") if r.status_code==200 else r.text[:120])
    except Exception as e:
        return (i, "EXC", time.time()-t0, str(e)[:120])

t0=time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:
    futures=[pool.submit(submit, i, t) for i,t in enumerate(TRANSCRIPTS)]
    results=[f.result() for f in concurrent.futures.as_completed(futures)]
total=time.time()-t0
ok=sum(1 for r in results if r[1]==200)
levels={}
for r in results: levels[r[3]]=levels.get(r[3],0)+1
print(f"total_wall={total:.2f}s ok={ok}/15")
print(f"levels: {levels}")
for r in sorted(results, key=lambda x: x[2]):
    print(f"  #{r[0]:02d} status={r[1]} dt={r[2]:.2f}s level={r[3]}")
PY

echo
echo "=== Suite 1.3: sqlite lock check ==="
grep -ciE 'database is locked|sqlite.*lock|operationalerror' /tmp/uvicorn.log
echo "=== final alerts count ==="
curl -s http://127.0.0.1:8000/api/alerts | python3 -c "import json,sys; d=json.load(sys.stdin); print('total_alerts:',len(d));
from collections import Counter
c=Counter(x['level'] for x in d); print('by_level:',dict(c))"
