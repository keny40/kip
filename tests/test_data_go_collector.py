from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

import httpx

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

import app.models  # noqa: F401,E402
from app.collectors.data_go import (  # noqa: E402
    DEFAULT_BASE_URL,
    DataGoCollectorError,
    DataGoKeirinPlayerCollector,
    DataGoQuery,
    collect_players_to_csv,
    import_players_csv,
)
from scripts.collect_players import import_players_safely  # noqa: E402
from scripts.collect_players import build_parser  # noqa: E402


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "data_go_keirin_players_fixture.xml"


def build_response_xml(*, total_count: int, items: list[dict[str, str]], result_code: str = "00") -> str:
    item_xml = []
    for item in items:
        children = "".join(f"<{key}>{value}</{key}>" for key, value in item.items())
        item_xml.append(f"<item>{children}</item>")
    return (
        "<response>"
        "<header>"
        f"<resultCode>{result_code}</resultCode>"
        "<resultMsg>NORMAL SERVICE</resultMsg>"
        "</header>"
        "<body>"
        f"<totalCount>{total_count}</totalCount>"
        f"<items>{''.join(item_xml)}</items>"
        "</body>"
        "</response>"
    )


class DataGoCollectorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_xml = FIXTURE_PATH.read_text(encoding="utf-8")

    def _build_client(self, payloads: dict[int, str]) -> httpx.Client:
        def handler(request: httpx.Request) -> httpx.Response:
            page_no = int(request.url.params.get("pageNo", "1"))
            payload = payloads.get(page_no)
            if payload is None:
                payload = build_response_xml(total_count=0, items=[])
            return httpx.Response(200, text=payload)

        return httpx.Client(transport=httpx.MockTransport(handler), base_url="https://apis.data.go.kr")

    def test_default_endpoint_uses_live_apis_domain(self) -> None:
        self.assertEqual(DEFAULT_BASE_URL, "https://apis.data.go.kr/B551014/SRVC_CRA_RACER_INFO/TODZ_CRA_RACER_INFO")

    def test_live_style_fixture_rejects_all_rows_without_racer_no(self) -> None:
        collector = DataGoKeirinPlayerCollector(client=self._build_client({1: self.fixture_xml}))
        result = collector.collect_players(DataGoQuery(service_key="test-key", page_size=10, max_pages=1), inspect=True)

        self.assertEqual(result.item_count, 10)
        self.assertEqual(len(result.rows), 0)
        self.assertEqual(result.duplicates_skipped, 0)
        self.assertNotIn("racer_no", result.observed_tags)
        self.assertIn("racer_nm", result.observed_tags)
        self.assertIn("period_no", result.observed_tags)
        self.assertIn("racer_grd_cd", result.observed_tags)
        self.assertEqual(len(result.issues), 10)
        self.assertTrue(all(issue.error_code == "MISSING_PLAYER_NUMBER" for issue in result.issues))
        self.assertEqual(result.normalized_preview, [])

    def test_missing_player_number_rejected_without_fake_generation(self) -> None:
        payload = build_response_xml(
            total_count=1,
            items=[{"racer_nm": "Player Missing Number", "racer_grd_cd": "A1"}],
        )
        collector = DataGoKeirinPlayerCollector(client=self._build_client({1: payload}))

        result = collector.collect_players(DataGoQuery(service_key="test-key", page_size=10, max_pages=1))

        self.assertEqual(len(result.rows), 0)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].error_code, "MISSING_PLAYER_NUMBER")
        self.assertEqual(result.issues[0].source_fields, {})

    def test_missing_player_name_has_specific_safe_error_code(self) -> None:
        payload = build_response_xml(
            total_count=1,
            items=[{"racer_no": "777", "racer_grd_cd": "A1"}],
        )
        collector = DataGoKeirinPlayerCollector(client=self._build_client({1: payload}))

        result = collector.collect_players(DataGoQuery(service_key="test-key", page_size=10, max_pages=1))

        self.assertEqual(len(result.rows), 0)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].error_code, "MISSING_PLAYER_NAME")
        self.assertEqual(result.issues[0].source_fields, {})

    def test_racer_no_is_used_as_player_number(self) -> None:
        payload = build_response_xml(
            total_count=1,
            items=[{"racer_no": "888", "racer_nm": "Player Eight Eight Eight", "racer_grd_cd": "B1"}],
        )
        collector = DataGoKeirinPlayerCollector(client=self._build_client({1: payload}))

        result = collector.collect_players(DataGoQuery(service_key="test-key", page_size=10, max_pages=1))

        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].player_number, 888)
        self.assertEqual(result.rows[0].name, "Player Eight Eight Eight")
        self.assertEqual(result.rows[0].grade, "B1")

    def test_api_error_response_raises(self) -> None:
        payload = build_response_xml(total_count=0, items=[], result_code="99")
        collector = DataGoKeirinPlayerCollector(client=self._build_client({1: payload}))

        with self.assertRaises(DataGoCollectorError):
            collector.collect_players(DataGoQuery(service_key="test-key"))

    def test_invalid_xml_raises_safe_collector_error(self) -> None:
        collector = DataGoKeirinPlayerCollector(client=self._build_client({1: "<not-closed>"}))

        with self.assertRaisesRegex(DataGoCollectorError, "Unable to parse XML response"):
            collector.collect_players(DataGoQuery(service_key="test-key"))

    def test_missing_result_code_raises_safe_collector_error(self) -> None:
        payload = "<response><body><totalCount>0</totalCount><items /></body></response>"
        collector = DataGoKeirinPlayerCollector(client=self._build_client({1: payload}))

        with self.assertRaisesRegex(DataGoCollectorError, "missing resultCode"):
            collector.collect_players(DataGoQuery(service_key="test-key"))

    def test_timeout_is_wrapped_without_request_url(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timed out", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        collector = DataGoKeirinPlayerCollector(client=client)

        with self.assertRaisesRegex(DataGoCollectorError, "request timed out") as raised:
            collector.collect_players(DataGoQuery(service_key="secret-test-key"))
        self.assertNotIn("secret-test-key", str(raised.exception))

    def test_connection_failure_is_wrapped_without_request_url(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection failed", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        collector = DataGoKeirinPlayerCollector(client=client)

        with self.assertRaisesRegex(DataGoCollectorError, "Unable to connect") as raised:
            collector.collect_players(DataGoQuery(service_key="secret-test-key"))
        self.assertNotIn("secret-test-key", str(raised.exception))

    def test_http_error_reports_only_status(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, request=request, text="upstream details")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        collector = DataGoKeirinPlayerCollector(client=client)

        with self.assertRaisesRegex(DataGoCollectorError, "HTTP status 503") as raised:
            collector.collect_players(DataGoQuery(service_key="secret-test-key"))
        self.assertNotIn("secret-test-key", str(raised.exception))
        self.assertNotIn("upstream details", str(raised.exception))

    def test_cli_uses_period_number_only(self) -> None:
        args = build_parser().parse_args(["--period-number", "22"])

        self.assertEqual(args.period_no, 22)

    def test_live_style_rows_do_not_reach_db_import(self) -> None:
        payload = self.fixture_xml
        collector = DataGoKeirinPlayerCollector(client=self._build_client({1: payload}))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            csv_path = temp_dir_path / "players.csv"
            result = collect_players_to_csv(csv_path, DataGoQuery(service_key="test-key", page_size=10, max_pages=1), collector=collector)

            self.assertTrue(csv_path.exists())
            self.assertEqual(len(result.rows), 0)
            self.assertEqual(len(result.issues), 10)

            test_db_path = temp_dir_path / "test.db"
            self.assertFalse(test_db_path.exists())

            report, skip_reason = import_players_safely(
                csv_path,
                database_url=f"sqlite:///{test_db_path}",
                dry_run=True,
            )

            self.assertEqual(report.created, 0)
            self.assertEqual(skip_reason, "NO_STABLE_PLAYER_IDENTIFIER")
            self.assertFalse(test_db_path.exists())

    def test_period_no_and_name_never_become_player_number(self) -> None:
        payload = build_response_xml(
            total_count=1,
            items=[{"racer_nm": "Same Name", "period_no": "29", "racer_grd_cd": "A1"}],
        )
        collector = DataGoKeirinPlayerCollector(client=self._build_client({1: payload}))

        result = collector.collect_players(DataGoQuery(service_key="test-key", period_no=29))

        self.assertEqual(result.rows, [])
        self.assertEqual(result.duplicates_skipped, 0)
        self.assertEqual(result.issues[0].error_code, "MISSING_PLAYER_NUMBER")
