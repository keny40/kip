from __future__ import annotations

import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

import app.models  # noqa: F401,E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_engine  # noqa: E402
from app.models.external_players import ExternalPlayer  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.services.external_player_import import (  # noqa: E402
    EXPECTED_COLUMNS,
    ExternalPlayerCSVImportService,
)


class ExternalPlayerImportTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.db"
        self.engine = get_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.service = ExternalPlayerCSVImportService()

    def tearDown(self) -> None:
        self.engine.dispose()
        self.tempdir.cleanup()

    def _write_csv(self, rows: list[dict[str, str]]) -> Path:
        path = Path(self.tempdir.name) / "external_players.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(EXPECTED_COLUMNS))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _row(self, **updates: str) -> dict[str, str]:
        row = {
            "external_id": "00120034",
            "name": "Masked Rider",
            "period_number": "06",
            "grade": "A1",
            "region": "unknown",
            "status": "active",
            "detail_url": "https://www.kcycle.or.kr/racer/info/00120034",
            "source": "kcycle",
            "collected_at": "2026-07-13T04:05:06Z",
        }
        row.update(updates)
        return row

    def test_first_apply_preserves_string_and_second_apply_skips(self) -> None:
        path = self._write_csv([self._row()])
        with self.SessionLocal() as db:
            first = self.service.import_csv(db, path, dry_run=False)
            db.commit()
            self.assertEqual((first.created, first.updated, first.skipped, first.failed), (1, 0, 0, 0))

        with self.SessionLocal() as db:
            stored = db.query(ExternalPlayer).one()
            self.assertEqual(stored.external_id, "00120034")
            self.assertIsInstance(stored.external_id, str)
            self.assertEqual(stored.period_number, "06")
            second = self.service.import_csv(db, path, dry_run=False)
            db.commit()
            self.assertEqual((second.created, second.updated, second.skipped), (0, 0, 1))
            self.assertEqual(db.query(ExternalPlayer).count(), 1)

    def test_changed_values_update_only_changed_fields(self) -> None:
        original = self._write_csv([self._row()])
        with self.SessionLocal() as db:
            self.service.import_csv(db, original, dry_run=False)
            db.commit()

        changed = self._write_csv([self._row(grade="S1", status="inactive")])
        with self.SessionLocal() as db:
            report = self.service.import_csv(db, changed, dry_run=False)
            db.commit()
            self.assertEqual((report.created, report.updated, report.skipped), (0, 1, 0))
            self.assertEqual(report.preview[0].changed_fields, ("grade", "status"))
            stored = db.query(ExternalPlayer).one()
            self.assertEqual((stored.grade, stored.status), ("S1", "inactive"))
            self.assertEqual(db.query(ExternalPlayer).count(), 1)

    def test_dry_run_and_players_table_remain_unchanged(self) -> None:
        path = self._write_csv([self._row()])
        with self.SessionLocal() as db:
            before_players = db.query(Player).count()
            report = self.service.import_csv(db, path, dry_run=True)
            db.commit()
            self.assertEqual(report.created, 1)
            self.assertEqual(db.query(ExternalPlayer).count(), 0)
            self.assertEqual(db.query(Player).count(), before_players)

    def test_validation_defaults_and_required_fields(self) -> None:
        rows = [
            self._row(external_id="123", name="Bad ID"),
            self._row(external_id="20240002", name=""),
            self._row(external_id="20240003", source="other"),
            self._row(
                external_id="20240004",
                grade="",
                region="",
                status="",
                detail_url="https://www.kcycle.or.kr/racer/info/20240004",
            ),
        ]
        path = self._write_csv(rows)
        with self.SessionLocal() as db:
            report = self.service.import_csv(db, path, dry_run=False)
            db.commit()
            self.assertEqual((report.created, report.failed), (1, 3))
            stored = db.query(ExternalPlayer).one()
            self.assertEqual((stored.grade, stored.region, stored.status), ("unknown", "unknown", "unknown"))

    def test_detail_url_must_match_external_id(self) -> None:
        path = self._write_csv(
            [self._row(detail_url="https://www.kcycle.or.kr/racer/info/99999999")]
        )
        with self.SessionLocal() as db:
            report = self.service.import_csv(db, path, dry_run=False)
            db.commit()
            self.assertEqual(report.failed, 1)
            self.assertEqual(db.query(ExternalPlayer).count(), 0)

    def test_duplicate_csv_rows_are_skipped_by_source_and_external_id(self) -> None:
        path = self._write_csv([self._row(), self._row(name="Conflicting Name")])
        with self.SessionLocal() as db:
            report = self.service.import_csv(db, path, dry_run=False)
            db.commit()
            self.assertEqual((report.created, report.duplicate_rows, report.skipped), (1, 1, 1))
            self.assertEqual(db.query(ExternalPlayer).count(), 1)
            self.assertEqual(db.query(ExternalPlayer).one().name, "Masked Rider")

    def test_database_unique_constraint(self) -> None:
        values = dict(
            source="kcycle",
            external_id="00120034",
            name="Masked Rider",
            period_number="06",
            grade="A1",
            region="unknown",
            status="active",
            detail_url=None,
            source_updated_at=None,
            collected_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
        )
        with self.SessionLocal() as db:
            db.add_all([ExternalPlayer(**values), ExternalPlayer(**values)])
            with self.assertRaises(IntegrityError):
                db.commit()
            db.rollback()


class ExternalPlayerMigrationTestCase(unittest.TestCase):
    def test_upgrade_and_downgrade_external_players(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "migration.db"
            env = os.environ.copy()
            env["DATABASE_URL"] = f"sqlite:///{db_path}"
            upgrade = subprocess.run(
                [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
                cwd=backend_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(upgrade.returncode, 0, upgrade.stdout + upgrade.stderr)
            connection = sqlite3.connect(db_path)
            try:
                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertIn("external_players", tables)
            finally:
                connection.close()

            downgrade = subprocess.run(
                [sys.executable, "-m", "alembic", "-c", "alembic.ini", "downgrade", "0004_admin_auth"],
                cwd=backend_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(downgrade.returncode, 0, downgrade.stdout + downgrade.stderr)
            connection = sqlite3.connect(db_path)
            try:
                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertNotIn("external_players", tables)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
