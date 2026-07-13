from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

import httpx
from sqlalchemy.orm import sessionmaker

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

import app.models  # noqa: F401,E402
from app.collectors.data_go_player_stats import (  # noqa: E402
    DataGoPlayerStatCollector,
    DataGoPlayerStatQuery,
)
from app.db.base import Base  # noqa: E402
from app.db.session import get_engine  # noqa: E402
from app.models.external_player_statistics import ExternalPlayerStatistic  # noqa: E402
from app.models.external_players import ExternalPlayer  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.services.external_player_stat_import import ExternalPlayerStatisticImportService  # noqa: E402
from app.services.player_match_candidates import PlayerMatchCandidateService  # noqa: E402


FIXED_TIME = datetime(2026, 7, 13, 5, 0, 0, tzinfo=timezone.utc)


def response_xml(items: list[dict[str, str]]) -> str:
    item_xml = "".join(
        "<item>" + "".join(f"<{key}>{value}</{key}>" for key, value in item.items()) + "</item>"
        for item in items
    )
    return (
        "<response><header><resultCode>00</resultCode></header><body>"
        f"<totalCount>{len(items)}</totalCount><items>{item_xml}</items></body></response>"
    )


def mock_client(xml: str) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, text=xml)
    return httpx.Client(transport=httpx.MockTransport(handler))


class DataGoPlayerStatisticCollectorTestCase(unittest.TestCase):
    def test_maps_all_stat_fields_and_preserves_null_and_zero(self) -> None:
        xml = response_xml([{
            "stnd_yr": "2025", "racer_nm": "Masked Rider", "period_no": "06",
            "racer_grd_cd": "A1", "run_cnt": "0", "run_day_tcnt": "12",
            "rank1_tcnt": "1", "rank2_tcnt": "2", "rank3_tcnt": "3",
            "rank4_tcnt": "4", "rank5_tcnt": "5", "rank6_tcnt": "6",
            "rank7_tcnt": "7", "rank8_tcnt": "8", "rank9_tcnt": "9",
            "elim_tcnt": "0", "win_rate": "0", "high_rate": "25.5",
        }])
        collector = DataGoPlayerStatCollector(client=mock_client(xml), clock=lambda: FIXED_TIME)
        result = collector.collect(DataGoPlayerStatQuery("key", "2025"))
        row = result.rows[0]
        self.assertEqual(row.standard_year, "2025")
        self.assertEqual(row.period_number, "06")
        self.assertEqual(row.run_count, 0)
        self.assertEqual(row.rank9_count, 9)
        self.assertEqual(row.eliminated_count, 0)
        self.assertEqual(row.win_rate, Decimal("0"))
        self.assertEqual(row.high_rate, Decimal("25.5"))
        self.assertIsNone(row.high_3_rate)
        self.assertFalse(hasattr(row, "player_number"))

    def test_invalid_numbers_missing_required_and_duplicate_are_reported(self) -> None:
        items = [
            {"stnd_yr": "2025", "racer_nm": "One", "period_no": "1", "run_cnt": "bad"},
            {"stnd_yr": "", "racer_nm": "Two"},
            {"stnd_yr": "2025", "racer_nm": "", "period_no": "2"},
            {"stnd_yr": "2025", "racer_nm": "Three", "period_no": "3", "win_rate": "bad"},
            {"stnd_yr": "2025", "racer_nm": "Four", "period_no": "4"},
            {"stnd_yr": "2025", "racer_nm": "Four", "period_no": "4"},
        ]
        collector = DataGoPlayerStatCollector(client=mock_client(response_xml(items)))
        result = collector.collect(DataGoPlayerStatQuery("key", "2025"))
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.parse_error_count, 2)
        self.assertEqual(result.duplicates_skipped, 1)
        self.assertEqual(
            [issue.error_code for issue in result.issues],
            ["INVALID_INTEGER", "MISSING_STANDARD_YEAR", "MISSING_PLAYER_NAME", "INVALID_RATE", "DUPLICATE_SOURCE_ROW"],
        )


class ExternalPlayerStatisticStorageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.engine = get_engine(f"sqlite:///{Path(self.tempdir.name) / 'test.db'}")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.service = ExternalPlayerStatisticImportService()

    def tearDown(self) -> None:
        self.engine.dispose()
        self.tempdir.cleanup()

    def _row(self, **changes):
        xml = response_xml([{
            "stnd_yr": "2025", "racer_nm": "Exact Rider", "period_no": "06",
            "racer_grd_cd": "A1", "run_cnt": str(changes.get("run_count", 10)),
        }])
        collector = DataGoPlayerStatCollector(client=mock_client(xml), clock=lambda: FIXED_TIME)
        return collector.collect(DataGoPlayerStatQuery("key", "2025")).rows[0]

    def test_dry_run_first_apply_second_skip_and_update(self) -> None:
        with self.SessionLocal() as db:
            before_players = db.query(Player).count()
            before_external = db.query(ExternalPlayer).count()
            dry = self.service.upsert(db, [self._row()], dry_run=True)
            db.commit()
            self.assertEqual(dry.created, 1)
            self.assertEqual(db.query(ExternalPlayerStatistic).count(), 0)
            first = self.service.upsert(db, [self._row()], dry_run=False)
            db.commit()
            self.assertEqual(first.created, 1)
            second = self.service.upsert(db, [self._row()], dry_run=False)
            db.commit()
            self.assertEqual(second.skipped, 1)
            changed = self.service.upsert(db, [self._row(run_count=11)], dry_run=False)
            db.commit()
            self.assertEqual(changed.updated, 1)
            self.assertEqual(changed.preview[0].changed_fields, ("run_count",))
            self.assertEqual(db.query(ExternalPlayerStatistic).count(), 1)
            self.assertEqual(db.query(Player).count(), before_players)
            self.assertEqual(db.query(ExternalPlayer).count(), before_external)

    def _external(self, external_id: str, name: str, period: str, grade: str) -> ExternalPlayer:
        return ExternalPlayer(
            source="kcycle", external_id=external_id, name=name, period_number=period,
            grade=grade, region="unknown", status="active", detail_url=None,
            source_updated_at=None, collected_at=FIXED_TIME,
        )

    def _stat(self, name: str, period: str | None, grade: str) -> ExternalPlayerStatistic:
        return ExternalPlayerStatistic(
            source="data_go", standard_year="2025", racer_name=name,
            period_number=period, grade=grade, collected_at=FIXED_TIME,
        )

    def test_all_candidate_statuses(self) -> None:
        with self.SessionLocal() as db:
            db.add_all([
                self._external("00000001", "Unique", "1", "A1"),
                self._external("00000002", "Multi", "2", "A1"),
                self._external("00000003", "Multi", "2", "A1"),
                self._external("00000004", "Mismatch", "3", "B1"),
                self._stat("Unique", "1", "A1"),
                self._stat("Nobody", "9", "A1"),
                self._stat("Multi", "2", "A1"),
                self._stat("No Period", None, "A1"),
                self._stat("Mismatch", "3", "S1"),
            ])
            db.commit()
            report = PlayerMatchCandidateService().build_report(db, year="2025")
            self.assertEqual(
                {item.match_status for item in report},
                {"UNIQUE_CANDIDATE", "NO_CANDIDATE", "MULTIPLE_CANDIDATES", "MISSING_PERIOD_NUMBER", "GRADE_MISMATCH"},
            )
            self.assertTrue(all("*" in item.masked_racer_name for item in report))


class ExternalPlayerStatisticMigrationTestCase(unittest.TestCase):
    def test_upgrade_and_downgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "migration.db"
            env = os.environ.copy(); env["DATABASE_URL"] = f"sqlite:///{db_path}"
            for command, expected in (("upgrade", True), ("downgrade", False)):
                target = "head" if command == "upgrade" else "0005_external_players"
                run = subprocess.run(
                    [sys.executable, "-m", "alembic", "-c", "alembic.ini", command, target],
                    cwd=backend_root, env=env, capture_output=True, text=True, check=False,
                )
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                connection = sqlite3.connect(db_path)
                try:
                    tables={r[0] for r in connection.execute("select name from sqlite_master where type='table'")}
                    self.assertEqual("external_player_statistics" in tables, expected)
                finally: connection.close()


if __name__ == "__main__":
    unittest.main()
