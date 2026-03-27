#!/usr/bin/env python3
"""
B737NG Flashcard Trainer - Lokale Server
Dubbelklik dit bestand (of run: python start_server.py)
Dan open je de app op iPad/Samsung via het getoonde adres.
"""
import http.server
import socketserver
import socket
import os
import webbrowser

PORT = 8080
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Geen spam in console

ip = get_local_ip()

print("=" * 55)
print("  B737NG Flashcard Trainer — Server gestart!")
print("=" * 55)
print()
print(f"  Op DEZE pc:     http://localhost:{PORT}")
print(f"  Op iPad/Samsung: http://{ip}:{PORT}")
print()
print("  iPad (Safari):")
print(f"    1. Open Safari → ga naar http://{ip}:{PORT}")
print(f"    2. Tik op Delen (□↑) → 'Zet op beginscherm'")
print()
print("  Samsung S24 (Chrome):")
print(f"    1. Open Chrome → ga naar http://{ip}:{PORT}")
print(f"    2. Menu (⋮) → 'Toevoegen aan startscherm'")
print()
print("  ⚠️  Zorg dat iPad/Samsung op hetzelfde wifi-netwerk zit!")
print("  Sluit dit venster om de server te stoppen.")
print("=" * 55)

webbrowser.open(f"http://localhost:{PORT}")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer gestopt.")
