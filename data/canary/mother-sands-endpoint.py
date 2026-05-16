#!/usr/bin/env python3
"""Mother Sands programmable HTTP endpoint.

Serves data/canary/served.json (a copy of baseline.json unless mutated by a
scenario). The MODE env var controls HTTP-level behaviour injection:

  MODE=ok       (default) — 200 OK with JSON body
  MODE=timeout  — accept connection, never reply (simulate read timeout)
  MODE=404      — 404 Not Found
  MODE=503      — 503 Service Unavailable

ETag / Last-Modified are computed from the served file's mtime so that
conditional GETs (If-None-Match / If-Modified-Since) work correctly.

Usage:
  python3 data/canary/mother-sands-endpoint.py
  MODE=timeout python3 data/canary/mother-sands-endpoint.py
  PORT=9090 python3 data/canary/mother-sands-endpoint.py
"""
import hashlib
import http.server
import os
import select
import time
from email.utils import formatdate
from pathlib import Path

PORT = int(os.environ.get("PORT", "9191"))
MODE = os.environ.get("MODE", "ok")

SERVED_FILE = Path(__file__).parent / "served.json"
BASELINE_FILE = Path(__file__).parent / "baseline.json"


def _etag_and_lm(path: Path) -> tuple[str, str]:
    mtime = path.stat().st_mtime
    etag = '"' + hashlib.md5(str(mtime).encode()).hexdigest()[:16] + '"'
    last_modified = formatdate(mtime, usegmt=True)
    return etag, last_modified


class CanaryHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[canary] {self.address_string()} - {fmt % args}")

    def do_GET(self):
        mode = os.environ.get("MODE", "ok")

        if mode == "timeout":
            # Accept connection, never reply — caller's read timeout fires
            print("[canary] MODE=timeout: holding connection open")
            try:
                select.select([], [], [], 120)
            except Exception:
                pass
            return

        if mode == "404":
            self.send_error(404, "Not Found (canary injection)")
            return

        if mode == "503":
            self.send_error(503, "Service Unavailable (canary injection)")
            return

        # MODE=ok (default): serve the file with ETag support
        served = SERVED_FILE if SERVED_FILE.exists() else BASELINE_FILE
        body = served.read_bytes()
        etag, last_modified = _etag_and_lm(served)

        if_none_match = self.headers.get("If-None-Match")
        if_mod_since = self.headers.get("If-Modified-Since")

        if if_none_match and if_none_match == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Last-Modified", last_modified)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("ETag", etag)
        self.send_header("Last-Modified", last_modified)
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    if not SERVED_FILE.exists():
        import shutil
        shutil.copy(BASELINE_FILE, SERVED_FILE)

    print(f"[canary] Mother Sands endpoint on :{PORT}  MODE={MODE}")
    print(f"[canary] Serving: {SERVED_FILE}")
    server = http.server.HTTPServer(("0.0.0.0", PORT), CanaryHandler)
    server.serve_forever()
