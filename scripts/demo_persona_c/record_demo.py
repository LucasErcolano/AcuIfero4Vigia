"""Playwright recorder for Persona C escalada.

Launches Chromium headless at 1440x900, opens the operator dashboard, and fires
the 3 actos via direct HTTP calls to the backend. Records a webm of the entire
session. Convert to mp4 in post with ffmpeg if needed.

Usage on VM:
  cd /home/hz/work/AcuIfero4Vigia_local/scripts/demo_persona_c
  bash 00_reset.sh
  python3 record_demo.py --out /tmp/persona_c_demo.webm
"""
from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

import httpx
from playwright.async_api import async_playwright


API = os.environ.get("API", "http://127.0.0.1:8000")
FRONTEND = os.environ.get("FRONTEND", "http://127.0.0.1:5173")
SITE = os.environ.get("SITE", "puente-arroyo-01")

# Geografia coherente: rio baja desde aguas-arriba (Act 1 vigia rutina) hacia el
# puente (Acto 2 camara fija) y luego desborda hacia el barrio bajo (Acto 3
# vigias criticos). Cada summary deja la ubicacion explicita para que el
# operador entienda la trayectoria del evento.
ACT1 = {
    "site_id": SITE,
    "reporter_name": "Vecino Mendez (aguas arriba)",
    "reporter_role": "ciudadano",
    "transcript_text": "Aguas arriba: llueve fuerte pero el canal corre normal, sin riesgo todavia.",
    "severity_score": 0.20,
    "water_level_category": "low",
    "trend": "stable",
    "road_status": "open",
    "urgency": "low",
    "summary": "Vigia aguas arriba: lluvia fuerte, canal corre normal sin desborde.",
}

ACT2 = {
    "site_id": SITE,
    "severity_score": 0.52,
    "waterline_ratio": 0.62,
    "rise_velocity": 0.05,
    "crossed_critical_line": False,
    "confidence": 0.81,
    "assessment_level": "elevated",
    "temporal_summary": "Camara fija sobre el puente: cota supera linea de referencia, sin cruzar critica.",
}

ACT3_REPORTS = [
    {
        "reporter_name": "Vecino Lopez (junto al puente)",
        "reporter_role": "ciudadano",
        "transcript_text": "Junto al puente: el agua paso la marca pintada.",
        "severity_score": 0.78, "water_level_category": "high", "trend": "rising",
        "road_status": "open", "homes_affected": False, "urgency": "critical",
        "summary": "Vigia puente: marca de agua superada, nivel sigue subiendo.",
    },
    {
        "reporter_name": "Voluntario Sosa (plaza centro)",
        "reporter_role": "brigadista",
        "transcript_text": "Plaza centro: se taparon las calles, intransitable.",
        "severity_score": 0.74, "water_level_category": "high", "trend": "rising",
        "road_status": "blocked", "homes_affected": False, "urgency": "critical",
        "summary": "Vigia plaza: calles cortadas, transito interrumpido.",
    },
    {
        "reporter_name": "Vecina Diaz (barrio bajo)",
        "reporter_role": "ciudadano",
        "transcript_text": "Barrio bajo: el agua esta entrando a las casas, familias evacuadas.",
        "severity_score": 0.88, "water_level_category": "critical", "trend": "rising",
        "road_status": "blocked", "homes_affected": True, "urgency": "critical",
        "summary": "Vigia barrio bajo: agua dentro de viviendas, evacuacion en curso.",
    },
]


async def post(client: httpx.AsyncClient, path: str, payload: dict) -> dict:
    r = await client.post(f"{API}{path}", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


async def emit_cap(client: httpx.AsyncClient, alert: dict) -> None:
    sev_map = {"red": "severe", "orange": "severe", "yellow": "moderate", "green": "minor"}
    payload = {
        "site_id": alert["site_id"],
        "lat": -32.9468,
        "lon": -60.6393,
        "severity": sev_map.get(alert["level"], "minor"),
        "headline": f"Alerta {alert['level'].upper()} en {alert['site_id']}",
        "summary": alert["summary"],
        "instruction": "Activar protocolo de Defensa Civil y evacuar zonas anegadas.",
        "areaDesc": alert["site_id"],
    }
    r = await client.post(f"{API}/cap/emit", json=payload, timeout=30)
    r.raise_for_status()
    out = Path("/tmp") / f"cap_alert_{alert['id']}.xml"
    out.write_bytes(r.content)
    print(f"  CAP -> {out}")


async def run(out_path: Path, chromium_path: str | None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    video_dir = out_path.parent / f"_video_tmp_{os.getpid()}"
    video_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        launch_kwargs = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path
        browser = await pw.chromium.launch(**launch_kwargs)
        VIEW_W, VIEW_H = 1440, 900
        context = await browser.new_context(
            viewport={"width": VIEW_W, "height": VIEW_H},
            record_video_dir=str(video_dir),
            record_video_size={"width": VIEW_W, "height": VIEW_H},
        )
        page = await context.new_page()

        # Pre-inject Act 1 BEFORE opening the dashboard so the very first paint
        # already shows the live green alert (no DEMO_ALERT CRITICO fallback).
        async with httpx.AsyncClient() as client:
            print("[rec] PRE-INJECT verde (baseline)")
            r0 = await post(client, "/api/demo/inject-volunteer-report", ACT1)
            print(f"  -> {r0['alert']['level']} score={r0['alert']['score']}")

        print(f"[rec] open {FRONTEND}")
        await page.goto(FRONTEND, wait_until="networkidle")
        await page.wait_for_timeout(5000)

        async def refresh():
            await page.reload(wait_until="networkidle")
            await page.wait_for_timeout(1500)

        async def scroll_to(y: int, steps: int = 12, dwell: int = 1200):
            """Smooth scroll to absolute y over `steps` increments, then dwell."""
            current = await page.evaluate("window.scrollY")
            delta = (y - current) / max(1, steps)
            for i in range(steps):
                await page.evaluate(f"window.scrollTo({{top: {current + delta * (i + 1)}, behavior: 'instant'}})")
                await page.wait_for_timeout(80)
            await page.wait_for_timeout(dwell)

        async def dump_dom_check(label: str) -> dict:
            """Pull live tile + banner text from DOM for consistency check."""
            data = await page.evaluate("""() => {
                const pick = (sel) => Array.from(document.querySelectorAll(sel)).map(e => e.innerText.replace(/\\s+/g,' ').trim());
                return {
                    banner: pick('header, [class*="risk"], [class*="Risk"]').slice(0, 3),
                    bigNums: pick('.text-3xl').slice(0, 6),
                    monoBadges: pick('.font-mono').slice(0, 12),
                };
            }""")
            print(f"[verify {label}] bigNums={data['bigNums']} mono={data['monoBadges'][:6]}")
            return data

        async with httpx.AsyncClient() as client:
            # === ACTO 1: baseline verde, ya pre-inyectado ===
            print("[rec] ACTO 1 verde (baseline already on screen)")
            await scroll_to(0, dwell=2500)              # banner verde + top
            await dump_dom_check("act1_top")
            await scroll_to(420, dwell=2000)            # tiles fusion
            await dump_dom_check("act1_fusion")

            # === ACTO 2: camara fija detecta cota elevada ===
            print("[rec] ACTO 2 amarillo")
            r2 = await post(client, "/api/demo/inject-node-observation", ACT2)
            print(f"  -> {r2['alert']['level']} score={r2['alert']['score']}")
            await refresh()
            await scroll_to(0, dwell=2000)              # banner pasa a amarillo
            await scroll_to(420, dwell=2200)            # tile camara sube
            await dump_dom_check("act2_fusion")
            await scroll_to(820, dwell=2000)            # frame evidencia camara
            await dump_dom_check("act2_evidence")

            # === ACTO 3: 3 vigia criticos ===
            print("[rec] ACTO 3 rojo")
            for i, rep in enumerate(ACT3_REPORTS, 1):
                rep_full = {"site_id": SITE, **rep}
                r3 = await post(client, "/api/demo/inject-volunteer-report", rep_full)
                print(f"  R{i} -> {r3['alert']['level']} score={r3['alert']['score']}")
                await refresh()
                await scroll_to(0, dwell=1400)          # banner rojo
                await scroll_to(420, dwell=1600)        # tiles
                await scroll_to(900, dwell=1400)        # razonamiento
                await dump_dom_check(f"act3_r{i}")

            # === ACTO 4: razonamiento + traza + acciones operador ===
            await scroll_to(1100, dwell=2500)           # traza auditoria
            await dump_dom_check("act4_audit")
            await scroll_to(0, dwell=1200)              # back to top, right column
            # right column has CAP + actions; viewport 1440 wide shows both cols
            await scroll_to(300, dwell=2500)            # CAP card + action rail

            print("[rec] ACTO 4 CAP emit")
            alerts = (await client.get(f"{API}/api/alerts", timeout=30)).json()
            target = next(a for a in alerts if a["site_id"] == SITE)
            await emit_cap(client, target)
            await refresh()
            await scroll_to(300, dwell=2200)
            await dump_dom_check("act4_cap")
            await scroll_to(1500, dwell=2500)           # timeline final
            await dump_dom_check("act4_timeline")
            await scroll_to(0, dwell=2000)              # close on banner critico

        # finalize: close page -> video flushed
        video = page.video
        await context.close()
        await browser.close()
        if video is not None:
            src = Path(await video.path())
            if src.exists():
                shutil.move(str(src), str(out_path))
                print(f"[rec] saved {out_path} ({out_path.stat().st_size/1024:.1f} KB)")
        for leftover in video_dir.glob("*"):
            leftover.unlink()
        video_dir.rmdir()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="/tmp/persona_c_demo.webm")
    p.add_argument("--chromium", default=None, help="Path to system chromium binary")
    args = p.parse_args()
    out = Path(args.out)
    try:
        asyncio.run(run(out, args.chromium))
    except Exception as exc:
        print(f"[rec] FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
