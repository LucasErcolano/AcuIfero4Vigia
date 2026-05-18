#!/usr/bin/env python3
"""SFTP put/get via paramiko with password auth."""
import argparse
import paramiko

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="100.105.56.84")
    ap.add_argument("--user", default="hz")
    ap.add_argument("--password", default="1")
    ap.add_argument("--put", nargs=2, metavar=("LOCAL", "REMOTE"), action="append", default=[])
    ap.add_argument("--get", nargs=2, metavar=("REMOTE", "LOCAL"), action="append", default=[])
    args = ap.parse_args()

    t = paramiko.Transport((args.host, 22))
    t.connect(username=args.user, password=args.password)
    s = paramiko.SFTPClient.from_transport(t)
    for local, remote in args.put:
        print(f"put {local} -> {remote}")
        s.put(local, remote)
    for remote, local in args.get:
        print(f"get {remote} -> {local}")
        s.get(remote, local)
    s.close()
    t.close()

if __name__ == "__main__":
    main()
