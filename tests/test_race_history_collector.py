from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest

import httpx

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.collectors.race_history import (  # noqa: E402
    DEFAULT_LINEUP_ENDPOINT,
    DEFAULT_RESULT_ENDPOINT,
    RaceHistoryPreviewCollector,
    RaceHistoryQuery,
    _merge_items,
    _normalize_service_key,
    _normalize_race_date,
    _numeric_compare_key,
    _parse_items,
    _split_rank_value,
)


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class RaceHistoryCollectorTest(unittest.TestCase):
    def test_parse_data_go_lineup_fixture_preserves_fields_without_fake_ids(self) -> None:
        items = _parse_items((FIXTURE_DIR / "data_go_race_entries_fixture.xml").read_text(encoding="utf-8"))
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["race_ymd"], "20250103")
        self.assertEqual(items[0]["race_no"], "02")
        self.assertEqual(items[0]["back_no"], "2")
        self.assertEqual(items[0]["racer_nm"], "가상선수B")
        self.assertNotIn("racer_no", {key.lower() for key in items[0]})

    def test_parse_data_go_result_fixture_extracts_rank_values(self) -> None:
        lineup = _parse_items((FIXTURE_DIR / "data_go_race_entries_fixture.xml").read_text(encoding="utf-8"))
        results = _parse_items((FIXTURE_DIR / "data_go_race_results_fixture.xml").read_text(encoding="utf-8"))
        races = _merge_items(lineup, results, 10, query=RaceHistoryQuery(date_from=date(2025, 1, 1), date_to=date(2025, 1, 31), standard_year="2025"))
        self.assertEqual(len(races), 1)
        self.assertIsNone(races[0]["external_race_id"])
        self.assertEqual(races[0]["race_date"], "2025-01-03")
        self.assertEqual(races[0]["result_coverage_type"], "top3_only")
        self.assertIsNone(races[0]["entries"][0]["external_player_id"])
        self.assertEqual(races[0]["entries"][0]["entry_number"], "2")
        self.assertEqual(races[0]["entries"][0]["player_name"], "가상선수B")
        self.assertEqual(len(races[0]["results"]), 3)
        self.assertEqual(races[0]["results"][0]["result_rank"], 1)
        self.assertEqual(races[0]["results"][0]["entry_number"], "2")
        self.assertEqual(races[0]["results"][0]["player_name"], "가상선수B")

    def test_service_key_missing_blocks_live_call(self) -> None:
        collector = RaceHistoryPreviewCollector()
        preview = collector.collect_preview(
            RaceHistoryQuery(
                date_from=date(2025, 1, 1),
                date_to=date(2025, 1, 31),
                service_key="",
            )
        )
        self.assertFalse(preview.live_called)
        self.assertEqual(preview.issues[0].error_code, "SERVICE_KEY_MISSING")

    def test_default_endpoints_are_official_data_go_gateway_urls(self) -> None:
        self.assertEqual(
            DEFAULT_LINEUP_ENDPOINT,
            "https://apis.data.go.kr/B551014/SRVC_OD_API_CRA_RACE_ORGAN/TODZ_API_CRA_RACE_ORGAN_I",
        )
        self.assertEqual(
            DEFAULT_RESULT_ENDPOINT,
            "https://apis.data.go.kr/B551014/SRVC_TODZ_CRA_RACE_RESULT/TODZ_API_CRA_RACE_RESULT",
        )

    def test_encoded_service_key_is_decoded_once_without_logging_value(self) -> None:
        self.assertEqual(_normalize_service_key("abc%2Bdef%3D"), "abc+def=")
        self.assertEqual(_normalize_service_key('"abc%2Fdef"'), "abc/def")

    def test_compact_rank_value_and_race_date_are_normalized_safely(self) -> None:
        self.assertEqual(_split_rank_value("2신동인"), ("2", "신동인"))
        self.assertEqual(_split_rank_value("②신동인"), ("2", "신동인"))
        self.assertEqual(_split_rank_value("⑥정덕이"), ("6", "정덕이"))
        self.assertEqual(_split_rank_value("⑤이기한"), ("5", "이기한"))
        self.assertEqual(_split_rank_value("\ufeff2신동인"), ("2", "신동인"))
        self.assertEqual(_split_rank_value("[6정덕이]"), ("6", "정덕이"))
        self.assertEqual(_split_rank_value("5\xa0이기한"), ("5", "이기한"))
        self.assertEqual(_split_rank_value("2번 신동인"), ("2", "신동인"))
        self.assertEqual(_split_rank_value("신동인"), (None, "신동인"))
        self.assertEqual(_normalize_race_date("0103", "2025"), "2025-01-03")
        self.assertEqual(_normalize_race_date("20250103", None), "2025-01-03")
        self.assertEqual(_normalize_race_date("2025.01.03", None), "2025-01-03")

    def test_joined_preview_counts_result_item_and_normalized_results_separately(self) -> None:
        lineup_xml = (FIXTURE_DIR / "data_go_race_entries_fixture.xml").read_text(encoding="utf-8")
        result_xml = (FIXTURE_DIR / "data_go_race_results_fixture.xml").read_text(encoding="utf-8")

        def handler(request: httpx.Request) -> httpx.Response:
            if "RACE_RESULT" in str(request.url):
                return httpx.Response(200, text=result_xml)
            return httpx.Response(200, text=lineup_xml)

        collector = RaceHistoryPreviewCollector(client=httpx.Client(transport=httpx.MockTransport(handler)))
        preview = collector.collect_preview(
            RaceHistoryQuery(
                date_from=date(2025, 1, 1),
                date_to=date(2025, 1, 31),
                mode="joined-preview",
                service_key="test",
                standard_year="2025",
                meet_name="광명",
                week_count="01",
                day_count="1",
                race_number="02",
            )
        )
        self.assertEqual(preview.lineup_item_count, 3)
        self.assertEqual(preview.lineup_race_count, 1)
        self.assertEqual(preview.selected_lineup_entry_count, 3)
        self.assertEqual(preview.result_item_count, 1)
        self.assertEqual(preview.normalized_result_count, 3)
        self.assertEqual(preview.matched_result_count, 3)
        self.assertEqual(preview.unmatched_result_count, 0)
        self.assertEqual(preview.result_coverage_type, "top3_only")

    def test_joined_preview_lineup_request_uses_broad_filters_only(self) -> None:
        captured_urls: list[str] = []
        lineup_xml = (FIXTURE_DIR / "data_go_race_entries_fixture.xml").read_text(encoding="utf-8")
        result_xml = (FIXTURE_DIR / "data_go_race_results_fixture.xml").read_text(encoding="utf-8")

        def handler(request: httpx.Request) -> httpx.Response:
            captured_urls.append(str(request.url))
            if "RACE_RESULT" in str(request.url):
                return httpx.Response(200, text=result_xml)
            return httpx.Response(200, text=lineup_xml)

        collector = RaceHistoryPreviewCollector(client=httpx.Client(transport=httpx.MockTransport(handler)))
        collector.collect_preview(
            RaceHistoryQuery(
                date_from=date(2025, 1, 3),
                date_to=date(2025, 1, 3),
                mode="joined-preview",
                service_key="test",
                standard_year="2025",
                meet_name="광명",
                week_count="01",
                day_count="1",
                race_number="02",
            )
        )
        lineup_url = next(url for url in captured_urls if "RACE_ORGAN" in url)
        result_url = next(url for url in captured_urls if "RACE_RESULT" in url)
        self.assertIn("stnd_yr=2025", lineup_url)
        self.assertIn("meet_nm=", lineup_url)
        self.assertNotIn("week_tcnt", lineup_url)
        self.assertNotIn("day_tcnt", lineup_url)
        self.assertNotIn("race_no", lineup_url)
        self.assertIn("week_tcnt=01", result_url)
        self.assertIn("day_tcnt=1", result_url)
        self.assertIn("race_no=02", result_url)

    def test_numeric_compare_normalizes_zero_padding_without_changing_payload(self) -> None:
        self.assertEqual(_numeric_compare_key("01"), _numeric_compare_key("1"))
        self.assertEqual(_numeric_compare_key("02"), _numeric_compare_key(2))

    def test_joined_preview_collects_target_race_entries_across_pages(self) -> None:
        page1 = """
        <response><header><resultCode>00</resultCode></header><body><pageNo>1</pageNo><totalCount>7</totalCount><numOfRows>3</numOfRows><items>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>1</back_no><racer_nm>이재봉</racer_nm><period_no>12</period_no><racer_grd_cd>A1</racer_grd_cd></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>2</back_no><racer_nm>신동인</racer_nm><period_no>29</period_no><racer_grd_cd>A1</racer_grd_cd></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>3</back_no><racer_nm>김경태</racer_nm><period_no>5</period_no><racer_grd_cd>A2</racer_grd_cd></item>
        </items></body></response>
        """
        page2 = """
        <response><header><resultCode>00</resultCode></header><body><pageNo>2</pageNo><totalCount>7</totalCount><numOfRows>3</numOfRows><items>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>4</back_no><racer_nm>가상선수D</racer_nm><period_no>20</period_no><racer_grd_cd>B1</racer_grd_cd></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>5</back_no><racer_nm>이기한</racer_nm><period_no>22</period_no><racer_grd_cd>A2</racer_grd_cd></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>6</back_no><racer_nm>정덕이</racer_nm><period_no>31</period_no><racer_grd_cd>B1</racer_grd_cd></item>
        </items></body></response>
        """
        page3 = """
        <response><header><resultCode>00</resultCode></header><body><pageNo>3</pageNo><totalCount>7</totalCount><numOfRows>3</numOfRows><items>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>03</race_no><back_no>1</back_no><racer_nm>다음경주</racer_nm><period_no>1</period_no><racer_grd_cd>A1</racer_grd_cd></item>
        </items></body></response>
        """
        result_xml = """
        <response><header><resultCode>00</resultCode></header><body><pageNo>1</pageNo><totalCount>1</totalCount><numOfRows>1</numOfRows><items>
          <item><stnd_yr>2025</stnd_yr><race_ymd>0103</race_ymd><meet_nm>광명</meet_nm><race_no>02</race_no><rank1>2신동인</rank1><rank2>6정덕이</rank2><rank3>5이기한</rank3><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt></item>
        </items></body></response>
        """
        seen_lineup_pages: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if "RACE_RESULT" in url:
                return httpx.Response(200, text=result_xml)
            page_no = request.url.params.get("pageNo")
            seen_lineup_pages.append(page_no)
            return httpx.Response(200, text={"1": page1, "2": page2, "3": page3}[page_no])

        collector = RaceHistoryPreviewCollector(client=httpx.Client(transport=httpx.MockTransport(handler)))
        preview = collector.collect_preview(
            RaceHistoryQuery(
                date_from=date(2025, 1, 3),
                date_to=date(2025, 1, 3),
                mode="joined-preview",
                service_key="test",
                standard_year="2025",
                meet_name="광명",
                week_count="01",
                day_count="1",
                race_number="02",
                max_races=10,
            )
        )
        self.assertEqual(seen_lineup_pages, ["1", "2", "3"])
        self.assertEqual(preview.selected_lineup_entry_count, 6)
        selected_numbers = {entry["entry_number"] for entry in preview.races[0]["entries"]}
        self.assertTrue({"2", "5", "6"}.issubset(selected_numbers))
        self.assertEqual([result["entry_number"] for result in preview.races[0]["results"]], ["2", "6", "5"])
        self.assertEqual(preview.normalized_result_count, 3)
        self.assertEqual(preview.matched_result_count, 3)
        self.assertEqual(preview.unmatched_result_count, 0)
        self.assertEqual(preview.player_mismatch_count, 0)

    def test_result_entry_numbers_survive_final_preview_serialization(self) -> None:
        lineup_xml = """
        <response><header><resultCode>00</resultCode></header><body><pageNo>1</pageNo><totalCount>7</totalCount><numOfRows>10</numOfRows><items>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>1</back_no><racer_nm>이재봉</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>2</back_no><racer_nm>신동인</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>3</back_no><racer_nm>김경태</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>4</back_no><racer_nm>가상선수D</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>5</back_no><racer_nm>이기한</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>6</back_no><racer_nm>정덕이</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>7</back_no><racer_nm>가상선수G</racer_nm></item>
        </items></body></response>
        """
        result_xml = """
        <response><header><resultCode>00</resultCode></header><body><pageNo>1</pageNo><totalCount>1</totalCount><numOfRows>1</numOfRows><items>
          <item><stnd_yr>2025</stnd_yr><race_ymd>0103</race_ymd><meet_nm>광명</meet_nm><race_no>02</race_no><rank1>2신동인</rank1><rank2>6정덕이</rank2><rank3>5이기한</rank3><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt></item>
        </items></body></response>
        """

        def handler(request: httpx.Request) -> httpx.Response:
            if "RACE_RESULT" in str(request.url):
                return httpx.Response(200, text=result_xml)
            return httpx.Response(200, text=lineup_xml)

        preview = RaceHistoryPreviewCollector(client=httpx.Client(transport=httpx.MockTransport(handler))).collect_preview(
            RaceHistoryQuery(
                date_from=date(2025, 1, 3),
                date_to=date(2025, 1, 3),
                mode="joined-preview",
                service_key="test",
                standard_year="2025",
                meet_name="광명",
                week_count="01",
                day_count="1",
                race_number="02",
            )
        )
        self.assertEqual(preview.result_entry_numbers, ["2", "6", "5"])
        self.assertEqual([item["entry_number"] for item in preview.races[0]["results"]], ["2", "6", "5"])
        self.assertEqual(preview.matched_result_count, 3)
        self.assertEqual(preview.unmatched_result_count, 0)
        self.assertEqual(preview.player_mismatch_count, 0)
        self.assertFalse(any(issue.error_code == "LINEUP_MISSING" for issue in preview.issues))

    def test_circled_digit_rank_values_survive_final_preview_serialization(self) -> None:
        lineup_xml = """
        <response><header><resultCode>00</resultCode></header><body><pageNo>1</pageNo><totalCount>7</totalCount><numOfRows>10</numOfRows><items>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>1</back_no><racer_nm>이재봉</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>2</back_no><racer_nm>신동인</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>3</back_no><racer_nm>김경태</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>4</back_no><racer_nm>가상선수D</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>5</back_no><racer_nm>이기한</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>6</back_no><racer_nm>정덕이</racer_nm></item>
          <item><meet_nm>광명</meet_nm><stnd_yr>2025</stnd_yr><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt><race_ymd>20250103</race_ymd><race_no>02</race_no><back_no>7</back_no><racer_nm>가상선수G</racer_nm></item>
        </items></body></response>
        """
        result_xml = """
        <response><header><resultCode>00</resultCode></header><body><pageNo>1</pageNo><totalCount>1</totalCount><numOfRows>1</numOfRows><items>
          <item><stnd_yr>2025</stnd_yr><race_ymd>0103</race_ymd><meet_nm>광명</meet_nm><race_no>02</race_no><rank1>②신동인</rank1><rank2>⑥정덕이</rank2><rank3>⑤이기한</rank3><week_tcnt>01</week_tcnt><day_tcnt>1</day_tcnt></item>
        </items></body></response>
        """

        def handler(request: httpx.Request) -> httpx.Response:
            if "RACE_RESULT" in str(request.url):
                return httpx.Response(200, text=result_xml)
            return httpx.Response(200, text=lineup_xml)

        preview = RaceHistoryPreviewCollector(client=httpx.Client(transport=httpx.MockTransport(handler))).collect_preview(
            RaceHistoryQuery(
                date_from=date(2025, 1, 3),
                date_to=date(2025, 1, 3),
                mode="joined-preview",
                service_key="test",
                standard_year="2025",
                meet_name="광명",
                week_count="01",
                day_count="1",
                race_number="02",
            )
        )
        self.assertEqual(preview.result_entry_numbers, ["2", "6", "5"])
        self.assertEqual([item["entry_number"] for item in preview.races[0]["results"]], ["2", "6", "5"])
        self.assertEqual([item["player_name"] for item in preview.races[0]["results"]], ["신동인", "정덕이", "이기한"])
        self.assertEqual(preview.matched_result_count, 3)
        self.assertEqual(preview.invalid_rank_value_count, 0)
        self.assertFalse(any(issue.error_code == "LINEUP_MISSING" for issue in preview.issues))


if __name__ == "__main__":
    unittest.main()
