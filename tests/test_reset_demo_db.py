from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.reset_demo_db import (
    backup_database,
    database_path_from_url,
    reset_demo_database,
    resolve_database_url,
)


class ResetDemoDbTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()
        os.environ.pop("DATABASE_URL", None)

    def _set_database_url(self, path: Path) -> str:
        url = f"sqlite:///{path}"
        os.environ["DATABASE_URL"] = url
        return url

    def test_dry_run_does_not_change_database(self) -> None:
        db_path = self.root / "dry_run.db"
        before_exists = db_path.exists()
        self._set_database_url(db_path)

        result = reset_demo_database(dry_run=True)

        self.assertIsNone(result)
        self.assertEqual(before_exists, db_path.exists())

    def test_backup_file_is_created(self) -> None:
        db_path = self.root / "source.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO demo (id) VALUES (1)")
        conn.commit()
        conn.close()

        backups_dir = self.root / "backups"
        backup_path = backup_database(db_path, backups_dir)

        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())
        self.assertGreater(backup_path.stat().st_size, 0)

    def test_reset_creates_demo_database(self) -> None:
        db_path = self.root / "demo.db"
        url = self._set_database_url(db_path)

        summary = reset_demo_database()

        self.assertIsNotNone(summary)
        self.assertEqual(database_path_from_url(url), db_path)
        self.assertTrue(db_path.exists())
        self.assertGreaterEqual(summary.tracks, 3)
        self.assertGreaterEqual(summary.players, 10)
        self.assertGreaterEqual(summary.races, 3)
        self.assertGreaterEqual(summary.entries, 15)
        self.assertGreaterEqual(summary.results, 8)
        self.assertTrue(summary.foreign_key_validation)
        self.assertTrue(summary.api_readable)

    def test_existing_database_absent_still_runs(self) -> None:
        db_path = self.root / "missing.db"
        self._set_database_url(db_path)

        summary = reset_demo_database()

        self.assertIsNotNone(summary)
        self.assertTrue(db_path.exists())

    def test_resolve_database_url_prefers_environment(self) -> None:
        expected = "sqlite:///example.db"
        os.environ["DATABASE_URL"] = expected
        self.assertEqual(resolve_database_url(), expected)
