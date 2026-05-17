#!/usr/bin/env python3
"""Run command on VM via paramiko with password auth, stream stdout."""
import argparse
import sys
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="100.105.56.84")
    ap.add_argument("--user", default="hz")
    ap.add_argument("--password", default="1")
    ap.add_argument("--cmd", required=True)
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(args.host, username=args.user, password=args.password, timeout=15)
    stdin, stdout, stderr = c.exec_command(args.cmd, timeout=args.timeout, get_pty=True)
    stdin.close()
    for line in iter(stdout.readline, ""):
        sys.stdout.write(line)
        sys.stdout.flush()
    err = stderr.read().decode(errors="replace")
    if err.strip():
        sys.stderr.write(err)
    rc = stdout.channel.recv_exit_status()
    c.close()
    sys.exit(rc)

if __name__ == "__main__":
    main()
