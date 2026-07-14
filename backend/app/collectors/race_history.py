from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import os
import re
import unicodedata
from urllib.parse import unquote
import xml.etree.ElementTree as ET

import httpx


DATA_GO_LINEUP_DOC_URL = "https://www.data.go.kr/data/15107830/openapi.do"
DATA_GO_RESULT_DOC_URL = "https://www.data.go.kr/data/15107816/openapi.do"
DEFAULT_LINEUP_ENDPOINT = "https://apis.data.go.kr/B551014/SRVC_OD_API_CRA_RACE_ORGAN/TODZ_API_CRA_RACE_ORGAN_I"
DEFAULT_RESULT_ENDPOINT = "https://apis.data.go.kr/B551014/SRVC_TODZ_CRA_RACE_RESULT/TODZ_API_CRA_RACE_RESULT"


@dataclass(frozen=True)
class RaceHistoryQuery:
    date_from: date
    date_to: date
    mode: str = "lineup"
    max_races: int = 10
    service_key: str | None = None
    lineup_endpoint: str = DEFAULT_LINEUP_ENDPOINT
    result_endpoint: str = DEFAULT_RESULT_ENDPOINT
    meet_name: str | None = None
    standard_year: str | None = None
    week_count: str | None = None
    day_count: str | None = None
    race_number: str | None = None


@dataclass(frozen=True)
class RaceHistoryIssue:
    error_code: str
    page: int | None = None
    row: int | None = None
    message: str = ""


@dataclass
class RaceHistoryPreview:
    source: str = "data_go"
    races_seen: int = 0
    races: list[dict[str, object]] = field(default_factory=list)
    issues: list[RaceHistoryIssue] = field(default_factory=list)
    live_called: bool = False
    source_notes: list[str] = field(default_factory=list)
    lineup_item_count: int = 0
    result_item_count: int = 0
    identifier_status: dict[str, str] = field(default_factory=dict)
    normalized_result_count: int = 0
    matched_result_count: int = 0
    unmatched_result_count: int = 0
    result_coverage_type: str = "unverified"
    observed_result_tags: list[str] = field(default_factory=list)
    lineup_race_count: int = 0
    selected_lineup_entry_count: int = 0
    player_mismatch_count: int = 0
    available_lineup_keys: list[dict[str, object]] = field(default_factory=list)
    lineup_pages_fetched: int = 0
    selected_lineup_entry_numbers: list[str] = field(default_factory=list)
    result_entry_numbers: list[str] = field(default_factory=list)
    invalid_rank_value_count: int = 0


class RaceHistoryCollectorError(RuntimeError):
    pass


@dataclass(frozen=True)
class _ParsedPage:
    items: list[dict[str, str]]
    total_count: int | None
    page_no: int | None
    num_of_rows: int | None


class RaceHistoryPreviewCollector:
    """Small, dry-run-oriented collector for official race-history source checks.

    Endpoint URLs are intentionally configurable because the public data.go
    catalog page exposes the product identifiers, while deployment keys and
    concrete service paths can differ by issued API. The collector never writes
    to the application database.
    """

    def __init__(self, *, client: httpx.Client | None = None, timeout: float = 20.0) -> None:
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "RaceHistoryPreviewCollector":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def collect_preview(self, query: RaceHistoryQuery) -> RaceHistoryPreview:
        preview = RaceHistoryPreview(
            source_notes=[
                f"lineup_catalog={DATA_GO_LINEUP_DOC_URL}",
                f"result_catalog={DATA_GO_RESULT_DOC_URL}",
                f"lineup_endpoint={DEFAULT_LINEUP_ENDPOINT}",
                f"result_endpoint={DEFAULT_RESULT_ENDPOINT}",
                "KCYCLE public pages: /race/card/decision and /race/result/general",
            ],
            identifier_status={
                "race": "NO_STABLE_IDENTIFIER",
                "player": "NO_STABLE_IDENTIFIER",
                "entry": "CROSS_SOURCE_MAPPING_REQUIRED",
            },
        )
        service_key = _normalize_service_key(
            query.service_key if query.service_key is not None else os.getenv("DATA_GO_KR_SERVICE_KEY")
        )
        if not service_key:
            preview.issues.append(RaceHistoryIssue(error_code="SERVICE_KEY_MISSING", message="DATA_GO_KR_SERVICE_KEY is not set."))
            return preview
        if not query.lineup_endpoint or not query.result_endpoint:
            preview.issues.append(
                RaceHistoryIssue(
                    error_code="ENDPOINT_NOT_CONFIGURED",
                    message="Set explicit lineup/result endpoint URLs after confirming the issued data.go service paths.",
                )
            )
            return preview

        preview.live_called = True
        lineup_items: list[dict[str, str]] = []
        result_items: list[dict[str, str]] = []
        if query.mode in {"lineup", "joined-preview"}:
            if query.mode == "joined-preview":
                lineup_items, preview.lineup_pages_fetched = self._fetch_joined_lineup_items(query.lineup_endpoint, service_key, query)
            else:
                lineup_items = self._fetch_items(query.lineup_endpoint, service_key, query, page=1, kind="lineup")
                preview.lineup_pages_fetched = 1
        if query.mode == "result":
            if not _has_required_result_filters(query):
                preview.issues.append(
                    RaceHistoryIssue(
                        "RESULT_REQUIRED_FILTERS_MISSING",
                        message="Result API requires stnd_yr, meet_nm, week_tcnt, day_tcnt, and race_no.",
                    )
                )
                return preview
            result_items = self._fetch_items(query.result_endpoint, service_key, query, page=1, kind="result")
        elif query.mode == "joined-preview" and _has_required_result_filters(query):
            result_items = self._fetch_items(query.result_endpoint, service_key, query, page=1, kind="result")
        elif query.mode == "joined-preview":
            preview.issues.append(
                RaceHistoryIssue(
                    "RESULT_REQUIRED_FILTERS_MISSING",
                    message="Joined preview skipped result API because stnd_yr, meet_nm, week_tcnt, day_tcnt, and race_no were not all provided.",
                )
            )
        preview.lineup_item_count = len(lineup_items)
        preview.result_item_count = len(result_items)
        preview.races = _merge_items(lineup_items, result_items, query.max_races, query=query)
        preview.races_seen = len(preview.races)
        preview.lineup_race_count = len(_group_lineup_keys(lineup_items, query=query))
        preview.selected_lineup_entry_count = sum(len(race.get("entries", [])) for race in preview.races)
        preview.selected_lineup_entry_numbers = [
            str(entry.get("entry_number"))
            for race in preview.races
            for entry in race.get("entries", [])
            if entry.get("entry_number") is not None
        ]
        preview.result_entry_numbers = [
            str(result.get("entry_number"))
            for race in preview.races
            for result in race.get("results", [])
            if result.get("entry_number") is not None
        ]
        preview.invalid_rank_value_count = sum(
            1
            for race in preview.races
            for result in race.get("results", [])
            if result.get("entry_number") is None or not result.get("player_name")
        )
        for _ in range(preview.invalid_rank_value_count):
            preview.issues.append(RaceHistoryIssue("INVALID_RESULT_RANK_VALUE", page=1, row=None))
        preview.available_lineup_keys = _group_lineup_keys(lineup_items, query=query)[:10]
        if query.mode == "joined-preview" and lineup_items and preview.selected_lineup_entry_count == 0:
            preview.issues.append(
                RaceHistoryIssue(
                    "TARGET_LINEUP_RACE_NOT_FOUND",
                    message="No lineup race matched the requested local natural-key filters.",
                )
            )
        preview.normalized_result_count = sum(len(race.get("results", [])) for race in preview.races)
        preview.result_coverage_type = _result_coverage_type(result_items)
        preview.observed_result_tags = sorted({tag for item in result_items for tag in item})
        lineup_keys = {
            (
                race.get("race_date"),
                race.get("track_code"),
                _numeric_compare_key(race.get("race_number")),
                _numeric_compare_key(entry.get("entry_number")),
                entry.get("player_name"),
            )
            for race in preview.races
            for entry in race.get("entries", [])
        }
        matched = 0
        unmatched = 0
        mismatches = 0
        for race in preview.races:
            race_base = (race.get("race_date"), race.get("track_code"), _numeric_compare_key(race.get("race_number")))
            entry_names = {_numeric_compare_key(entry.get("entry_number")): entry.get("player_name") for entry in race.get("entries", [])}
            for result in race.get("results", []):
                result_entry_number = _numeric_compare_key(result.get("entry_number"))
                result_key = (*race_base, result_entry_number, result.get("player_name"))
                if result_key in lineup_keys:
                    matched += 1
                elif result_entry_number in entry_names:
                    unmatched += 1
                    mismatches += 1
                    preview.issues.append(RaceHistoryIssue("PLAYER_DATA_MISMATCH", page=1, row=None))
                elif race.get("entries"):
                    unmatched += 1
                    preview.issues.append(RaceHistoryIssue("LINEUP_MISSING", page=1, row=None))
        preview.matched_result_count = matched
        preview.unmatched_result_count = unmatched
        preview.player_mismatch_count = mismatches
        for index, race in enumerate(preview.races, start=1):
            if not race.get("race_date"):
                preview.issues.append(RaceHistoryIssue("MISSING_RACE_DATE", page=1, row=index))
            if not race.get("track_code"):
                preview.issues.append(RaceHistoryIssue("MISSING_TRACK", page=1, row=index))
            if not race.get("race_number"):
                preview.issues.append(RaceHistoryIssue("MISSING_RACE_NUMBER", page=1, row=index))
            preview.issues.append(RaceHistoryIssue("MISSING_RACE_IDENTIFIER", page=1, row=index))
            for entry_index, entry in enumerate(race.get("entries", []), start=1):
                if not entry.get("external_player_id"):
                    preview.issues.append(RaceHistoryIssue("MISSING_PLAYER_IDENTIFIER", page=1, row=entry_index))
                if not entry.get("player_name"):
                    preview.issues.append(RaceHistoryIssue("MISSING_PLAYER_NAME", page=1, row=entry_index))
        return preview

    def _fetch_items(self, endpoint: str, service_key: str, query: RaceHistoryQuery, *, page: int, kind: str) -> list[dict[str, str]]:
        return self._fetch_page(endpoint, service_key, query, page=page, kind=kind).items

    def _fetch_joined_lineup_items(self, endpoint: str, service_key: str, query: RaceHistoryQuery) -> tuple[list[dict[str, str]], int]:
        collected: list[dict[str, str]] = []
        page = 1
        target_seen = False
        next_race_seen_after_target = False
        max_pages = 100
        while page <= max_pages:
            parsed = self._fetch_page(endpoint, service_key, query, page=page, kind="lineup")
            if not parsed.items:
                break
            for item in parsed.items:
                collected.append(item)
                if _matches_joined_selection(item, query):
                    target_seen = True
                elif target_seen:
                    next_race_seen_after_target = True
            if next_race_seen_after_target:
                break
            if parsed.total_count is not None and len(collected) >= parsed.total_count:
                break
            if parsed.num_of_rows is not None and len(parsed.items) < parsed.num_of_rows:
                break
            page += 1
        return collected, page

    def _fetch_page(self, endpoint: str, service_key: str, query: RaceHistoryQuery, *, page: int, kind: str) -> _ParsedPage:
        params = {
            "serviceKey": service_key,
            "pageNo": page,
            "numOfRows": min(max(query.max_races, 1), 10),
            "resultType": "XML",
        }
        if query.meet_name:
            params["meet_nm"] = query.meet_name
        if query.standard_year:
            params["stnd_yr"] = query.standard_year
        if kind == "lineup" and query.mode == "joined-preview":
            pass
        elif query.week_count is not None:
            params["week_tcnt"] = query.week_count
        if kind == "result":
            params["day_tcnt"] = query.day_count
            params["race_no"] = query.race_number
        try:
            response = self._client.get(endpoint, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RaceHistoryCollectorError("OpenAPI request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise RaceHistoryCollectorError(
                    "OpenAPI authentication failed with HTTP status 401. "
                    "Check that DATA_GO_KR_SERVICE_KEY is valid and that this API is approved for the key."
                ) from exc
            raise RaceHistoryCollectorError(f"OpenAPI returned HTTP status {exc.response.status_code}.") from exc
        except httpx.RequestError as exc:
            raise RaceHistoryCollectorError("Unable to connect to the OpenAPI service.") from exc
        return _parse_page(response.text)


def _parse_items(xml_text: str) -> list[dict[str, str]]:
    return _parse_page(xml_text).items


def _parse_page(xml_text: str) -> _ParsedPage:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RaceHistoryCollectorError("Unable to parse XML response.") from exc
    result_code = _find_text(root, "resultCode")
    if result_code and result_code not in {"00", "0", "NORMAL_SERVICE"}:
        raise RaceHistoryCollectorError(f"OpenAPI returned error code {result_code}.")
    items: list[dict[str, str]] = []
    for item in root.iter():
        if _local_name(item.tag).lower() != "item":
            continue
        row: dict[str, str] = {}
        for child in list(item):
            text = "".join(child.itertext()).strip()
            if text:
                row[_local_name(child.tag)] = text
        if row:
            items.append(row)
    return _ParsedPage(
        items=items,
        total_count=_parse_int(_find_text(root, "totalCount")),
        page_no=_parse_int(_find_text(root, "pageNo")),
        num_of_rows=_parse_int(_find_text(root, "numOfRows")),
    )


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip()
    return int(text) if text.isdigit() else None


def _normalize_service_key(service_key: str | None) -> str:
    if service_key is None:
        return ""
    value = service_key.strip().strip('"').strip("'")
    if "%" in value:
        return unquote(value)
    return value


def _merge_items(lineup_items: list[dict[str, str]], result_items: list[dict[str, str]], max_races: int, *, query: RaceHistoryQuery | None = None) -> list[dict[str, object]]:
    result_by_key = {_race_key(item, query=query): item for item in result_items}
    races_by_key: dict[tuple[str | None, str | None, str | None], dict[str, object]] = {}
    seen_entries: set[tuple[tuple[str | None, str | None, str | None], str | None]] = set()
    for item in lineup_items:
        if query and query.mode == "joined-preview" and not _matches_joined_selection(item, query):
            continue
        key = _race_key(item, query=query)
        if len(races_by_key) >= max_races and key not in races_by_key:
            continue
        race = races_by_key.setdefault(key, _race_payload(item, query=query, status="preview"))
        entry_number = _first(item, "back_no", "backNo", "entryNo", "entry_no", "laneNo", "lane_no")
        entry_key = (key, entry_number)
        if entry_key in seen_entries:
            continue
        seen_entries.add(entry_key)
        race["entries"].append(
            {
                "external_player_id": _first(item, "racerNo", "racer_no", "playerNo", "player_no", "player_id"),
                "player_name": _first(item, "racerName", "racer_nm", "playerName", "player_nm"),
                "period_number": _first(item, "periodNo", "period_no"),
                "grade": _first(item, "grade", "racerGrdCd", "racer_grd_cd"),
                "entry_number": entry_number,
            }
        )
    for key, result_item in result_by_key.items():
        if len(races_by_key) >= max_races and key not in races_by_key:
            continue
        race = races_by_key.setdefault(key, _race_payload(result_item, query=query, status="result_preview"))
        race["results"] = _extract_rank_results(result_item)
        if race["results"]:
            race["result_coverage_type"] = "top3_only"
    return list(races_by_key.values())


def _race_payload(item: dict[str, str], *, query: RaceHistoryQuery | None, status: str) -> dict[str, object]:
    standard_year = _first(item, "stnd_yr") or (query.standard_year if query else None)
    raw_date = _first(item, "race_ymd", "raceDate", "race_date", "race_dt", "rcDate", "rc_date")
    track_code = _first(item, "meet_nm", "trackCode", "track_code", "meet", "meetName", " 시행처")
    return {
        "source": "data_go",
        "external_race_id": None,
        "standard_year": standard_year,
        "meet_name": track_code,
        "week_count": _first(item, "week_tcnt") or (query.week_count if query and query.week_count is not None else None),
        "day_count": _first(item, "day_tcnt") or (query.day_count if query and query.day_count is not None else None) or "1",
        "race_date": _normalize_race_date(raw_date, standard_year),
        "track_code": track_code,
        "race_number": _first(item, "race_no", "raceNo", "raceNumber", "rcNo"),
        "status": status,
        "result_coverage_type": "unverified",
        "entries": [],
        "results": [],
    }


def _race_key(item: dict[str, str], *, query: RaceHistoryQuery | None = None) -> tuple[str | None, str | None, str | None]:
    standard_year = _first(item, "stnd_yr") or (query.standard_year if query else None)
    raw_date = _first(item, "race_ymd", "raceDate", "race_date", "race_dt", "rcDate", "rc_date")
    return (
        _normalize_race_date(raw_date, standard_year),
        _first(item, "meet_nm", "trackCode", "track_code", "meet", "meetName"),
        _numeric_compare_key(_first(item, "race_no", "raceNo", "raceNumber", "rcNo")),
    )


def _has_required_result_filters(query: RaceHistoryQuery) -> bool:
    return bool(
        query.standard_year
        and query.meet_name
        and query.week_count is not None
        and query.day_count is not None
        and query.race_number
    )


def _matches_joined_selection(item: dict[str, str], query: RaceHistoryQuery) -> bool:
    standard_year = _first(item, "stnd_yr")
    if query.standard_year and standard_year and standard_year.strip() != query.standard_year.strip():
        return False
    meet_name = _first(item, "meet_nm", "trackCode", "track_code", "meet", "meetName")
    if query.meet_name and meet_name and meet_name.strip() != query.meet_name.strip():
        return False
    item_week = _first(item, "week_tcnt", "weekCount")
    if query.week_count is not None and item_week and _numeric_compare_key(item_week) != _numeric_compare_key(query.week_count):
        return False
    item_day = _first(item, "day_tcnt", "dayCount")
    if query.day_count is not None and item_day and _numeric_compare_key(item_day) != _numeric_compare_key(query.day_count):
        return False
    if query.race_number and _numeric_compare_key(_first(item, "race_no", "raceNo", "raceNumber", "rcNo")) != _numeric_compare_key(query.race_number):
        return False
    item_date = _normalize_race_date(_first(item, "race_ymd", "raceDate", "race_date", "race_dt", "rcDate", "rc_date"), standard_year or query.standard_year)
    if item_date and not (query.date_from.isoformat() <= item_date <= query.date_to.isoformat()):
        return False
    return True


def _group_lineup_keys(lineup_items: list[dict[str, str]], *, query: RaceHistoryQuery | None = None) -> list[dict[str, object]]:
    grouped: dict[tuple, dict[str, object]] = {}
    for item in lineup_items:
        standard_year = _first(item, "stnd_yr") or (query.standard_year if query else None)
        race_date = _normalize_race_date(_first(item, "race_ymd", "raceDate", "race_date", "race_dt", "rcDate", "rc_date"), standard_year)
        key_payload = {
            "source": "data_go",
            "standard_year": standard_year,
            "meet_name": _first(item, "meet_nm", "trackCode", "track_code", "meet", "meetName"),
            "week_count": _first(item, "week_tcnt"),
            "day_count": _first(item, "day_tcnt"),
            "race_number": _first(item, "race_no", "raceNo", "raceNumber", "rcNo"),
            "race_date": race_date,
            "entry_count": 0,
        }
        key = tuple(key_payload.get(part) for part in ("standard_year", "meet_name", "week_count", "day_count", "race_number", "race_date"))
        grouped.setdefault(key, key_payload)
        grouped[key]["entry_count"] = int(grouped[key]["entry_count"]) + 1
    return list(grouped.values())


def _extract_rank_results(item: dict[str, str]) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for rank in (1, 2, 3):
        value = _first(item, f"rank{rank}", f"rank_{rank}")
        if not value:
            continue
        entry_number, player_name = _split_rank_value(value)
        results.append(
            {
                "external_player_id": None,
                "player_name": player_name,
                "entry_number": entry_number,
                "result_rank": rank,
                "result_status": "finished",
            }
        )
    return results


def _split_rank_value(value: str) -> tuple[str | None, str | None]:
    normalized = _clean_rank_value(value)
    if not normalized or normalized in {"[]", "-", "취소"}:
        return None, None
    match = re.match(r"^\s*(\d{1,2})\s*(?:번\s*)?(.+?)\s*$", normalized)
    if match:
        return match.group(1), match.group(2).strip()
    return None, normalized


def _clean_rank_value(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Cf")
    normalized = normalized.replace("\u00a0", " ").strip()
    return normalized.strip("[](){}").strip()


def _normalize_race_date(value: str | None, standard_year: str | None = None) -> str | None:
    if value is None or not value.strip():
        return None
    text = value.strip()
    try:
        if re.fullmatch(r"\d{4}", text) and standard_year and re.fullmatch(r"\d{4}", standard_year):
            return f"{standard_year}-{text[:2]}-{text[2:]}"
        if re.fullmatch(r"\d{8}", text):
            return f"{text[:4]}-{text[4:6]}-{text[6:]}"
        if re.fullmatch(r"\d{4}[.-]\d{2}[.-]\d{2}", text):
            return text.replace(".", "-")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return text
    except ValueError:
        return None
    return None


def _numeric_compare_key(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.isdigit():
        return str(int(text))
    return text


def _result_coverage_type(result_items: list[dict[str, str]]) -> str:
    if not result_items:
        return "unverified"
    if all(any(_first(item, f"rank{rank}", f"rank_{rank}") for rank in (1, 2, 3)) for item in result_items):
        return "top3_only"
    return "unverified"


def _first(item: dict[str, str], *keys: str) -> str | None:
    lowered = {key.lower().replace("_", ""): value for key, value in item.items()}
    for key in keys:
        value = item.get(key) or lowered.get(key.lower().replace("_", ""))
        if value and value.strip():
            return value.strip()
    return None


def _find_text(root: ET.Element, local_name: str) -> str | None:
    for element in root.iter():
        if _local_name(element.tag).lower() == local_name.lower():
            text = "".join(element.itertext()).strip()
            if text:
                return text
    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].split(":")[-1].strip()
