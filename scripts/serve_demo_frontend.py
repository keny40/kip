from __future__ import annotations

import argparse
import http.client
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class DemoHandler(SimpleHTTPRequestHandler):
    backend_port: int

    def list_directory(self, path):  # noqa: ANN001
        self.send_error(404, "Not found")
        return None

    def log_message(self, fmt: str, *args) -> None:  # noqa: ANN002
        print(f"FRONTEND_REQUEST method={self.command} path={urlsplit(self.path).path}")

    def do_GET(self) -> None:
        if self.path.startswith("/api/") or self.path == "/health":
            self._proxy()
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path.startswith("/api/"):
            self._proxy()
            return
        self.send_error(405, "Method not allowed")

    def _proxy(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() in {"accept", "authorization", "content-type"}
        }
        connection = http.client.HTTPConnection("127.0.0.1", self.backend_port, timeout=30)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            payload = response.read()
            self.send_response(response.status)
            self.send_header("Content-Type", response.getheader("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store" if self.path.startswith("/api/") else "no-cache")
            self.end_headers()
            self.wfile.write(payload)
        except OSError:
            payload = json.dumps({"detail": "Backend unavailable"}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        finally:
            connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--backend-port", type=int, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not (directory / "index.html").exists():
        raise SystemExit("Frontend build is missing.")
    handler = lambda *values, **kwargs: DemoHandler(  # noqa: E731
        *values, directory=str(directory), **kwargs
    )
    DemoHandler.backend_port = args.backend_port
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
