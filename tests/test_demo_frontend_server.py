from __future__ import annotations

import contextlib
import io
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from scripts.serve_demo_frontend import (
    DemoHandler,
    DemoThreadingHTTPServer,
    is_client_disconnect,
)


class DemoFrontendServerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tempdir.name)
        (self.root / "index.html").write_text("demo index", encoding="utf-8")
        (self.root / "asset.txt").write_text("asset", encoding="utf-8")

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _start_server(self) -> tuple[DemoThreadingHTTPServer, threading.Thread, int]:
        handler = lambda *values, **kwargs: DemoHandler(  # noqa: E731
            *values, directory=str(self.root), **kwargs
        )
        DemoHandler.backend_port = 9
        server = DemoThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread, server.server_address[1]

    def _request(self, port: int, path: str) -> bytes:
        with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
            client.sendall(f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n".encode())
            chunks = []
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)

    def test_index_response_is_200(self) -> None:
        server, thread, port = self._start_server()
        try:
            response = self._request(port, "/")
            self.assertIn(b"200 OK", response)
            self.assertIn(b"demo index", response)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_directory_listing_is_blocked(self) -> None:
        (self.root / "nested").mkdir()
        server, thread, port = self._start_server()
        try:
            response = self._request(port, "/nested/")
            self.assertIn(b"404", response)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_path_traversal_is_not_served(self) -> None:
        outside = self.root.parent / "outside-secret.txt"
        outside.write_text("secret", encoding="utf-8")
        server, thread, port = self._start_server()
        try:
            response = self._request(port, "/../outside-secret.txt")
            self.assertNotIn(b"secret", response)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_client_disconnect_errors_are_classified(self) -> None:
        self.assertTrue(is_client_disconnect(BrokenPipeError()))
        self.assertTrue(is_client_disconnect(ConnectionAbortedError()))
        self.assertTrue(is_client_disconnect(ConnectionResetError()))
        self.assertTrue(is_client_disconnect(OSError(10053, "aborted")))
        self.assertFalse(is_client_disconnect(OSError(2, "missing")))
        self.assertFalse(is_client_disconnect(RuntimeError("boom")))

    def test_client_disconnect_handle_error_does_not_print_traceback(self) -> None:
        server = DemoThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)

        def raise_disconnect() -> None:
            try:
                raise ConnectionAbortedError("client disconnected")
            except ConnectionAbortedError:
                server.handle_error(None, ("127.0.0.1", 12345))

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            raise_disconnect()
        server.server_close()
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertNotIn("ConnectionAbortedError", stderr.getvalue())

    def test_unexpected_handle_error_still_prints_traceback(self) -> None:
        server = DemoThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)

        def raise_unexpected() -> None:
            try:
                raise RuntimeError("unexpected server failure")
            except RuntimeError:
                server.handle_error(None, ("127.0.0.1", 12345))

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            raise_unexpected()
        server.server_close()
        self.assertIn("Traceback", stderr.getvalue())
        self.assertIn("RuntimeError", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
