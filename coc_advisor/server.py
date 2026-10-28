"""A loopback-only, dependency-free workbench server."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser

from .planner import analyze


MAX_REQUEST = 256 * 1024
WEB = Path(__file__).with_name("web")
ASSETS = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}


def _reject_constant(value):
    raise ValueError(f"Nonfinite JSON value: {value}.")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _allowed(self):
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        if host not in hosts or (origin is not None and origin != f"http://{host}"):
            self._json(403, {"error": "This workbench only accepts requests from its local page."})
            return False
        return True

    def _send(self, status, content, mime):
        self.send_response(status)
        self.send_header("Content-Type", f"{mime}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status, payload):
        self._send(status, json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8"), "application/json")

    def do_GET(self):
        if not self._allowed():
            return
        path = self.path.split("?", 1)[0]
        if path not in ASSETS:
            self._json(404, {"error": "Page not found."})
            return
        filename, mime = ASSETS[path]
        self._send(200, (WEB / filename).read_bytes(), mime)

    def do_POST(self):
        if not self._allowed():
            return
        if self.path != "/api/plan":
            self._json(404, {"error": "Endpoint not found."})
            return
        if self.headers.get("Transfer-Encoding"):
            self._json(400, {"error": "Chunked requests are not supported."})
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
            self._json(415, {"error": "Send application/json."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0:
                raise ValueError("Invalid request size.")
            if length > MAX_REQUEST:
                self._json(413, {"error": "Session annotations exceed the 256 KB request limit."})
                return
            self.connection.settimeout(5)
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError("The request was incomplete.")
            data = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)
            self._json(200, analyze(data))
        except (ValueError, UnicodeError, TypeError, TimeoutError) as exc:
            self._json(400, {"error": str(exc) or "Invalid session data."})


def create_server(port=8765):
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description="Offline Scouting Lab")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    try:
        server = create_server(args.port)
    except OSError as exc:
        parser.exit(1, f"Cannot start Scouting Lab: {exc}. Try --port 8766.\n")
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"Scouting Lab: {url}\nPress Ctrl+C to stop. Images stay in your browser.", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
