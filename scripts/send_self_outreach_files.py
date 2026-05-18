#!/usr/bin/env python3
"""Self-send the 6 new outreach Markdown files as attachments to ercolanolucas@gmail.com."""
import mimetypes
import smtplib
import socket
import sys
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
OUT_DIR = ROOT / "docs" / "outreach"
LOG_PATH = OUT_DIR / "self_send_log.md"

TO_ADDR = "ercolanolucas@gmail.com"
SUBJECT = "Acuifero 4 + Vigia - 6 listas outreach WhatsApp/tel (70 contactos nuevos)"
TIMEOUT = 180

FILES = [
    "whatsapp_radios_comunitarias.md",
    "whatsapp_asambleas_vecinales.md",
    "whatsapp_fomento_clubes_parroquias.md",
    "whatsapp_makerspaces_educacion.md",
    "whatsapp_legisladores_concejales.md",
    "whatsapp_empresas_hidricas.md",
]

BODY = """Lucas,

Adjunto 6 archivos generados por agentes paralelos. Total 70 contactos nuevos sobre los 41 ya contactados.

Resumen:
- radios_comunitarias.md: 15 (WhatsApp/tel)
- asambleas_vecinales.md: 11 tel + 1 FB (algunos numeros 2012-2014, verificar vigencia)
- fomento_clubes_parroquias.md: 14 (12 tel + 2 FB DM)
- makerspaces_educacion.md: 10 (7 tel + 3 email)
- legisladores_concejales.md: 11 (Twitter/X DM, sin WhatsApp publico)
- empresas_hidricas.md: 9 (B2B tel/email)

WhatsApp-ready directo: ~48. Resto Twitter/email/FB.

Cada entrada con URL fuente como comentario HTML, mensaje listo en bloque triple-backtick.
"""


def load_env(path: Path) -> dict:
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def main():
    env = load_env(ENV_PATH)
    user = env.get("GMAIL_USER")
    pwd = env.get("GMAIL_APP_PASSWORD")
    if not user or not pwd:
        print("ERROR: missing GMAIL_USER or GMAIL_APP_PASSWORD in .env", file=sys.stderr)
        sys.exit(2)

    msg = EmailMessage()
    msg["From"] = formataddr(("Lucas Ercolano", user))
    msg["To"] = TO_ADDR
    msg["Subject"] = SUBJECT
    msg["Reply-To"] = user
    msg.set_content(BODY)

    total_bytes = 0
    attached = []
    missing = []
    for name in FILES:
        path = OUT_DIR / name
        if not path.exists():
            missing.append(name)
            continue
        data = path.read_bytes()
        total_bytes += len(data)
        mime, _ = mimetypes.guess_type(str(path))
        maintype, subtype = (mime.split("/", 1) if mime else ("text", "markdown"))
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)
        attached.append(name)

    started = datetime.now()
    status = "sent"
    err = ""
    try:
        socket.setdefaulttimeout(TIMEOUT)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=TIMEOUT) as server:
            server.login(user, pwd)
            server.send_message(msg)
    except Exception as e:
        status = "failed"
        err = type(e).__name__ + ": " + str(e)
    ended = datetime.now()

    lines = [
        "# Self-send outreach files log",
        "",
        f"- Started: {started.isoformat(timespec='seconds')}",
        f"- Ended: {ended.isoformat(timespec='seconds')}",
        f"- From: {user}",
        f"- To: {TO_ADDR}",
        f"- Subject: {SUBJECT}",
        f"- Status: {status}",
        f"- Attached: {len(attached)} files, {total_bytes} bytes",
    ]
    if missing:
        lines.append(f"- Missing files (skipped): {', '.join(missing)}")
    if err:
        lines.append(f"- Error: {err}")
    lines.append("")
    lines.append("| File | Status |")
    lines.append("|------|--------|")
    for n in attached:
        lines.append(f"| {n} | attached |")
    for n in missing:
        lines.append(f"| {n} | MISSING |")
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Status: {status}")
    print(f"Attached: {len(attached)} files, {total_bytes} bytes")
    print(f"Log: {LOG_PATH}")
    if status == "failed":
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
