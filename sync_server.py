#!/usr/bin/env python3
"""
B737NG Flashcard Trainer - Sync Server
Draait permanent op de Home Assistant mini PC (poort 8765).
Serveert de app-bestanden EN beheert de sync-data voor alle apparaten.

Installatie op HA mini PC: zie INSTALLATIE_HA.md
"""
import http.server
import socketserver
import json
import os
import sys
from pathlib import Path

PORT = 8765
BASE_DIR = Path(__file__).parent
SYNC_FILE = BASE_DIR / "sync_data.json"


class FlashcardHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    # ── CORS headers ──────────────────────────────────────────────────────
    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    # ── GET ───────────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path == "/api/sync":
            self._get_sync()
        elif self.path == "/api/status":
            self._send_json(200, {"status": "ok", "server": "B737 Sync", "version": "1.0"})
        else:
            super().do_GET()

    def _get_sync(self):
        if SYNC_FILE.exists():
            data = SYNC_FILE.read_bytes()
            self.send_response(200)
            self.send_cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self._send_json(404, {"error": "no sync data yet"})

    # ── POST ──────────────────────────────────────────────────────────────
    def do_POST(self):
        if self.path == "/api/sync":
            self._post_sync()
        else:
            self.send_error(404)

    def _post_sync(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)   # valideer JSON
            SYNC_FILE.write_bytes(body)
            self._send_json(200, {"status": "saved", "cards": len(data.get("cards", []))})
        except Exception as e:
            self._send_json(400, {"error": str(e)})

    # ── helpers ───────────────────────────────────────────────────────────
    def _send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass   # stille server (geen log-spam)


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    print(f"B737NG Sync Server gestart op poort {PORT}")
    print(f"App beschikbaar op: http://<IP>:{PORT}")
    with socketserver.TCPServer(("", PORT), FlashcardHandler) as httpd:
        httpd.allow_reuse_address = True
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server gestopt.")
