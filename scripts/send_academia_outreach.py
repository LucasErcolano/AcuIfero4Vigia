#!/usr/bin/env python3
"""Send outreach emails to academic contacts from docs/outreach/whatsapp_academia.md.

Uses Gmail SMTP with credentials from .env (GMAIL_USER, GMAIL_APP_PASSWORD).
Idempotent: writes a send log; excludes recipients in EXCLUDED set.
"""
import os
import re
import smtplib
import socket
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
ACADEMIA_PATH = ROOT / "docs" / "outreach" / "whatsapp_academia.md"
LOG_PATH = ROOT / "docs" / "outreach" / "academia_send_log.md"

EXCLUDED = {
    "ivillanueva@ihlla.org.ar",
    "rovai@unifei.edu.br",
    "shampa_iwfm@iwfm.buet.ac.bd",
}

SUBJECT = "Acuifero 4 + Vigia - feedback breve (demo academica)"
SEND_TIMEOUT = 180  # seconds per send


def load_env(path: Path) -> dict:
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def parse_contacts(md_path: Path):
    """Yield dicts with name, email, message for each numbered contact."""
    text = md_path.read_text(encoding="utf-8")
    # Split on top-level "## N. ..." headers
    blocks = re.split(r"\n## (\d+)\.\s+", text)
    # blocks: [preamble, "1", body1, "2", body2, ...]
    for i in range(1, len(blocks) - 1, 2):
        idx = blocks[i]
        body = blocks[i + 1]
        # Stop at next "##" or "---"
        # Section ends at next "## " or end of block already
        # Skip non-numeric ids
        if not idx.isdigit():
            continue
        n = int(idx)
        if n > 12:
            continue
        # Title is first line
        title = body.splitlines()[0].strip()
        # Extract Email line(s)
        m_email = re.search(r"\*\*Email:\*\*\s*(.+)", body)
        if not m_email:
            continue
        email_line = m_email.group(1)
        # Pull all emails on that line
        emails = re.findall(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email_line)
        if not emails:
            continue
        # Extract message block (first ``` ... ```)
        m_msg = re.search(r"\*\*Mensaje:\*\*\s*\n+```\s*\n(.*?)\n```", body, re.DOTALL)
        if not m_msg:
            continue
        message = m_msg.group(1).strip()
        yield {
            "idx": n,
            "title": title,
            "emails": emails,
            "message": message,
        }


def send_one(smtp_user, smtp_pass, to_emails, subject, body, timeout):
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("Lucas Ercolano", smtp_user))
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg["Reply-To"] = smtp_user
    msg.attach(MIMEText(body, "plain", "utf-8"))

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=timeout) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_emails, msg.as_string())
    finally:
        socket.setdefaulttimeout(old_timeout)


def main():
    env = load_env(ENV_PATH)
    user = env.get("GMAIL_USER")
    pwd = env.get("GMAIL_APP_PASSWORD")
    if not user or not pwd:
        print("ERROR: missing GMAIL_USER or GMAIL_APP_PASSWORD in .env", file=sys.stderr)
        sys.exit(2)

    contacts = list(parse_contacts(ACADEMIA_PATH))
    print(f"Parsed {len(contacts)} contacts from {ACADEMIA_PATH.name}")

    results = []
    sent = failed = skipped = 0
    started = datetime.now()

    for c in contacts:
        # Filter excluded
        recipients = [e for e in c["emails"] if e.lower() not in EXCLUDED]
        excluded_here = [e for e in c["emails"] if e.lower() in EXCLUDED]
        if not recipients:
            results.append({"idx": c["idx"], "title": c["title"], "emails": c["emails"],
                            "status": "skipped", "reason": "all emails excluded"})
            skipped += 1
            print(f"[{c['idx']:02d}] SKIP all excluded: {c['emails']}")
            continue

        try:
            send_one(user, pwd, recipients, SUBJECT, c["message"], SEND_TIMEOUT)
            results.append({"idx": c["idx"], "title": c["title"], "emails": recipients,
                            "status": "sent", "reason": ""})
            sent += 1
            print(f"[{c['idx']:02d}] SENT -> {recipients}")
        except Exception as e:
            err = type(e).__name__ + ": " + str(e)
            # Do not log credentials; smtplib errors do not embed password
            results.append({"idx": c["idx"], "title": c["title"], "emails": recipients,
                            "status": "failed", "reason": err})
            failed += 1
            print(f"[{c['idx']:02d}] FAIL -> {recipients}: {err}")

        # Small pacing to avoid Gmail rate limits
        time.sleep(2)

    ended = datetime.now()

    # Write log
    lines = []
    lines.append("# Academia - email send log")
    lines.append("")
    lines.append(f"- Started: {started.isoformat(timespec='seconds')}")
    lines.append(f"- Ended: {ended.isoformat(timespec='seconds')}")
    lines.append(f"- Sender: {user}")
    lines.append(f"- Source: docs/outreach/whatsapp_academia.md")
    lines.append(f"- Subject: {SUBJECT}")
    lines.append(f"- Totals: sent={sent}, failed={failed}, skipped={skipped}")
    lines.append("")
    lines.append("| # | Contact | Recipients | Status | Reason |")
    lines.append("|---|---------|------------|--------|--------|")
    for r in results:
        title = r["title"].replace("|", "/")
        recips = ", ".join(r["emails"])
        reason = r["reason"].replace("|", "/").replace("\n", " ")
        lines.append(f"| {r['idx']} | {title} | {recips} | {r['status']} | {reason} |")
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nLog written: {LOG_PATH}")
    print(f"Totals: sent={sent} failed={failed} skipped={skipped}")


if __name__ == "__main__":
    main()
