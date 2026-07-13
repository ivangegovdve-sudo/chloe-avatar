#!/usr/bin/env python3
"""Static server for local avatar testing.

python serve.py [--port 8471] [--bind 0.0.0.0]

Why not plain `python -m http.server`: Windows registry often maps .js to
text/plain, which browsers reject for ES module scripts — this pins the
correct MIME types and disables caching so edits show up on plain reload.
"""

import argparse
import http.server
import os

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, **MIME}

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        # local dev only: lets a Vite-served PWA fetch test assets cross-port
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8471)
    ap.add_argument("--bind", default="0.0.0.0")
    args = ap.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with http.server.ThreadingHTTPServer((args.bind, args.port), Handler) as srv:
        print(f"serving {os.getcwd()} on http://{args.bind}:{args.port}/ (index.html, demo.html)")
        srv.serve_forever()


if __name__ == "__main__":
    main()
