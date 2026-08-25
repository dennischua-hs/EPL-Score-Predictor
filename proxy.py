#!/usr/bin/env python3
"""Tiny zero-dependency local proxy + static server for the EPL Score Predictor.

    python3 proxy.py            -> serves http://localhost:8080
    python3 proxy.py 9000       -> serves on port 9000

Why this exists: the official Fantasy Premier League API does not send CORS
headers, so a browser can't fetch it directly from the HTML file. This relays
the two endpoints the app needs (adding a CORS header) and serves the page from
the same origin, so everything works with no build step, signup, or Node.js.
"""
import sys
import os
import posixpath
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROOT = os.path.dirname(os.path.abspath(__file__))

# Only these upstream paths may be proxied (no open relay).
FPL = {
    "/fpl/bootstrap": "https://fantasy.premierleague.com/api/bootstrap-static/",
    "/fpl/fixtures":  "https://fantasy.premierleague.com/api/fixtures/",
}

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js":   "text/javascript; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".ico":  "image/x-icon",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the console quiet
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in FPL:
            self.relay(FPL[path])
        else:
            self.serve_static(path)

    def relay(self, upstream):
        try:
            req = urllib.request.Request(
                upstream, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as up:
                body = up.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=60")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:  # noqa: BLE001
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(('{"error":"%s"}' % str(e).replace('"', "'")).encode())

    def serve_static(self, path):
        rel = "/index.html" if path == "/" else path
        rel = posixpath.normpath(rel).lstrip("/")
        full = os.path.join(ROOT, rel)
        if not os.path.abspath(full).startswith(ROOT) or not os.path.isfile(full):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return
        ext = os.path.splitext(full)[1]
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print("EPL Score Predictor running at  http://localhost:%d/" % PORT)
    print("Proxying FPL endpoints:", ", ".join(FPL))
    print("Press Ctrl+C to stop.")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
