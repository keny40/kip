from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import httpx

import sys

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.collectors.kcycle_players import (  # noqa: E402
    DEFAULT_LIST_URL,
    KcyclePlayerCollector,
    KcyclePlayerCollectorError,
    KcyclePlayerQuery,
    export_kcycle_players_csv,
)


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "kcycle_players_fixture.html"
FIXED_TIME = datetime(2026, 7, 13, 4, 5, 6, tzinfo=timezone.utc)


class KcyclePlayerCollectorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_html = FIXTURE_PATH.read_text(encoding="utf-8")

    def _client(self, *, html: str | None = None, status: int = 200) -> httpx.Client:
        body = self.fixture_html if html is None else html

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status,
                request=request,
                text=body,
                headers={"content-type": "text/html; charset=utf-8"},
            )

        return httpx.Client(transport=httpx.MockTransport(handler))

    def _collect(self, *, page_size: int = 10):
        collector = KcyclePlayerCollector(client=self._client(), clock=lambda: FIXED_TIME)
        return collector.collect(KcyclePlayerQuery(page_size=page_size, max_pages=1))

    def test_extracts_master_fields_and_preserves_external_id_string(self) -> None:
        result = self._collect()

        self.assertEqual(result.total_cards, 5)
        self.assertEqual(result.cards_seen, 5)
        self.assertEqual(len(result.rows), 2)
        first = result.rows[0]
        self.assertEqual(first.external_id, "00120034")
        self.assertEqual(first.name, "가상선수 하나")
        self.assertEqual(first.period_number, 28)
        self.assertEqual(first.grade, "S1")
        self.assertEqual(first.region, "unknown")
        self.assertEqual(first.status, "active")
        self.assertEqual(first.detail_url, f"https://www.kcycle.or.kr/racer/info/{first.external_id}")
        self.assertEqual(first.source, "kcycle")
        self.assertEqual(first.collected_at, "2026-07-13T04:05:06Z")

    def test_duplicate_and_missing_fields_are_reported_without_fake_ids(self) -> None:
        result = self._collect()

        self.assertEqual(result.duplicates_skipped, 1)
        self.assertEqual(
            [issue.error_code for issue in result.issues],
            ["MISSING_EXTERNAL_ID", "MISSING_PLAYER_NAME"],
        )
        self.assertEqual({row.external_id for row in result.rows}, {"00120034", "20240002"})
        self.assertNotIn("28", {row.external_id for row in result.rows})

    def test_page_size_limits_normalization_and_single_page_ends(self) -> None:
        result = self._collect(page_size=2)

        self.assertEqual(result.total_cards, 5)
        self.assertEqual(result.cards_seen, 2)
        self.assertEqual(len(result.rows), 2)
        self.assertEqual(result.pages_fetched, 1)
        self.assertEqual(result.page_end_reason, "single_unpaged_response")

    def test_preview_csv_is_created_without_database_access(self) -> None:
        result = self._collect(page_size=2)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "preview.csv"
            database_marker = Path(temp_dir) / "kip.db"

            export_kcycle_players_csv(output, result.rows)

            self.assertTrue(output.exists())
            self.assertFalse(database_marker.exists())
            with output.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["external_id"], "00120034")
            self.assertEqual(len(rows), 2)

    def test_http_error_is_wrapped_without_response_body(self) -> None:
        collector = KcyclePlayerCollector(client=self._client(html="sensitive body", status=503))

        with self.assertRaisesRegex(KcyclePlayerCollectorError, "HTTP status 503") as raised:
            collector.collect(KcyclePlayerQuery())
        self.assertNotIn("sensitive body", str(raised.exception))

    def test_timeout_and_connection_failures_are_wrapped(self) -> None:
        def timeout_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout details", request=request)

        timeout_collector = KcyclePlayerCollector(
            client=httpx.Client(transport=httpx.MockTransport(timeout_handler))
        )
        with self.assertRaisesRegex(KcyclePlayerCollectorError, "request timed out"):
            timeout_collector.collect(KcyclePlayerQuery())

        def connection_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection details", request=request)

        connection_collector = KcyclePlayerCollector(
            client=httpx.Client(transport=httpx.MockTransport(connection_handler))
        )
        with self.assertRaisesRegex(KcyclePlayerCollectorError, "Unable to connect"):
            connection_collector.collect(KcyclePlayerQuery())

    def test_structure_change_without_cards_is_rejected(self) -> None:
        collector = KcyclePlayerCollector(
            client=self._client(html="<html><body><div>changed</div></body></html>")
        )

        with self.assertRaisesRegex(KcyclePlayerCollectorError, "list area was not found"):
            collector.collect(KcyclePlayerQuery())

    def test_unexpected_content_type_is_rejected(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                request=request,
                json={"items": []},
                headers={"content-type": "application/json"},
            )

        collector = KcyclePlayerCollector(client=httpx.Client(transport=httpx.MockTransport(handler)))
        with self.assertRaisesRegex(KcyclePlayerCollectorError, "unexpected response type"):
            collector.collect(KcyclePlayerQuery())

    def test_preview_limits_are_enforced(self) -> None:
        collector = KcyclePlayerCollector(client=self._client())

        with self.assertRaisesRegex(KcyclePlayerCollectorError, "page_size"):
            collector.collect(KcyclePlayerQuery(page_size=11))
        with self.assertRaisesRegex(KcyclePlayerCollectorError, "max_pages"):
            collector.collect(KcyclePlayerQuery(max_pages=2))

    def test_default_endpoint_is_official_player_info(self) -> None:
        self.assertEqual(DEFAULT_LIST_URL, "https://www.kcycle.or.kr/racer/info")


if __name__ == "__main__":
    unittest.main()
