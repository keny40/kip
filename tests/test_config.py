from __future__ import annotations

import sys
from pathlib import Path
import unittest

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.core.config import DEFAULT_CORS_ORIGINS, parse_cors_origins


class ConfigTestCase(unittest.TestCase):
    def test_default_cors_origins_are_local_development_hosts(self) -> None:
        self.assertEqual(parse_cors_origins(None), DEFAULT_CORS_ORIGINS)

    def test_cors_origins_trim_whitespace_and_remove_empty_items(self) -> None:
        self.assertEqual(
            parse_cors_origins(" http://localhost:5001 , , http://127.0.0.1:5001 "),
            ("http://localhost:5001", "http://127.0.0.1:5001"),
        )

    def test_empty_cors_origins_fall_back_to_defaults(self) -> None:
        self.assertEqual(parse_cors_origins(" , , "), DEFAULT_CORS_ORIGINS)


if __name__ == "__main__":
    unittest.main()
