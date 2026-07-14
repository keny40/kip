from __future__ import annotations

import argparse
import http.client
import json
import shutil
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


CLIENT_DISCONNECT_ERRNOS = {32, 104, 10053, 10054}
CLIENT_DISCONNECT_EXCEPTIONS = (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)


def is_client_disconnect(exc: BaseException) -> bool:
    if isinstance(exc, CLIENT_DISCONNECT_EXCEPTIONS):
        return True
    return isinstance(exc, OSError) and getattr(exc, "errno", None) in CLIENT_DISCONNECT_ERRNOS


class DemoThreadingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):  # noqa: ANN001
        exc = sys.exc_info()[1]
        if exc is not None and is_client_disconnect(exc):
            return
        super().handle_error(request, client_address)


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

    def copyfile(self, source, outputfile) -> None:  # noqa: ANN001
        try:
            shutil.copyfileobj(source, outputfile)
        except OSError as exc:
            if is_client_disconnect(exc):
                return
            raise

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
            self._send_payload(
                response.status,
                payload,
                response.getheader("Content-Type", "application/json"),
                "no-store" if self.path.startswith("/api/") else "no-cache",
            )
        except OSError as exc:
            if is_client_disconnect(exc):
                return
            payload = json.dumps({"detail": "Backend unavailable"}).encode()
            self._send_payload(502, payload, "application/json", None)
        finally:
            connection.close()

    def _send_payload(
        self,
        status: int,
        payload: bytes,
        content_type: str,
        cache_control: str | None,
    ) -> None:
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            if cache_control:
                self.send_header("Cache-Control", cache_control)
            self.end_headers()
            self.wfile.write(payload)
        except OSError as exc:
            if is_client_disconnect(exc):
                return
            raise


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
    server = DemoThreadingHTTPServer(("127.0.0.1", args.port), handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
