from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Callable, Iterable
import xml.etree.ElementTree as ET

import httpx

from app.collectors.data_go import DEFAULT_BASE_URL


INTEGER_FIELDS = {
    "run_count": "runcnt",
    "run_day_count": "rundaytcnt",
    "rank1_count": "rank1tcnt",
    "rank2_count": "rank2tcnt",
    "rank3_count": "rank3tcnt",
    "rank4_count": "rank4tcnt",
    "rank5_count": "rank5tcnt",
    "rank6_count": "rank6tcnt",
    "rank7_count": "rank7tcnt",
    "rank8_count": "rank8tcnt",
    "rank9_count": "rank9tcnt",
    "eliminated_count": "elimtcnt",
}
RATE_FIELDS = {
    "win_rate": "winrate",
    "high_rate": "highrate",
    "high_3_rate": "high3rate",
}


class DataGoPlayerStatCollectorError(RuntimeError):
    pass


@dataclass(frozen=True)
class DataGoPlayerStatQuery:
    service_key: str
    standard_year: str
    period_number: str | None = None
    racer_name: str | None = None
    page_size: int = 10
    max_pages: int = 1


@dataclass(frozen=True)
class CollectedPlayerStatistic:
    source: str
    standard_year: str
    racer_name: str
    period_number: str | None
    grade: str
    run_count: int | None
    run_day_count: int | None
    rank1_count: int | None
    rank2_count: int | None
    rank3_count: int | None
    rank4_count: int | None
    rank5_count: int | None
    rank6_count: int | None
    rank7_count: int | None
    rank8_count: int | None
    rank9_count: int | None
    eliminated_count: int | None
    win_rate: Decimal | None
    high_rate: Decimal | None
    high_3_rate: Decimal | None
    collected_at: datetime

    @property
    def provisional_key(self) -> tuple[str, str, str, str | None]:
        return (self.source, self.standard_year, self.racer_name, self.period_number)


@dataclass(frozen=True)
class PlayerStatCollectionIssue:
    error_code: str
    page: int
    row: int
    message: str


@dataclass
class PlayerStatCollectionResult:
    rows: list[CollectedPlayerStatistic] = field(default_factory=list)
    issues: list[PlayerStatCollectionIssue] = field(default_factory=list)
    item_count: int = 0
    pages_fetched: int = 0
    duplicates_skipped: int = 0
    parse_error_count: int = 0
    http_success: bool = False


@dataclass(frozen=True)
class _StatPage:
    items: list[dict[str, str]]
    total_count: int | None


class DataGoPlayerStatCollector:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.base_url = base_url
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)
        self._owns_client = client is None
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "DataGoPlayerStatCollector":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def collect(self, query: DataGoPlayerStatQuery) -> PlayerStatCollectionResult:
        if not query.service_key.strip():
            raise DataGoPlayerStatCollectorError("DATA_GO_KR_SERVICE_KEY is required.")
        if not 1 <= query.page_size <= 10:
            raise DataGoPlayerStatCollectorError("page_size must be between 1 and 10.")
        if query.max_pages != 1:
            raise DataGoPlayerStatCollectorError("max_pages must be 1 for preview collection.")
        if not query.standard_year.strip():
            raise DataGoPlayerStatCollectorError("standard_year is required.")

        page = self._fetch_page(query)
        result = PlayerStatCollectionResult(
            item_count=len(page.items),
            pages_fetched=1,
            http_success=True,
        )
        seen: set[tuple[str, str, str, str | None]] = set()
        collected_at = self._clock().astimezone(timezone.utc)

        for row_number, fields in enumerate(page.items, start=1):
            try:
                normalized = self._normalize(fields, collected_at)
            except _RowError as exc:
                if exc.error_code in {"INVALID_INTEGER", "INVALID_RATE"}:
                    result.parse_error_count += 1
                result.issues.append(
                    PlayerStatCollectionIssue(exc.error_code, 1, row_number, exc.message)
                )
                continue
            if normalized.provisional_key in seen:
                result.duplicates_skipped += 1
                result.issues.append(
                    PlayerStatCollectionIssue(
                        "DUPLICATE_SOURCE_ROW",
                        1,
                        row_number,
                        "Duplicate provisional source row.",
                    )
                )
                continue
            seen.add(normalized.provisional_key)
            result.rows.append(normalized)
        return result

    def _fetch_page(self, query: DataGoPlayerStatQuery) -> _StatPage:
        params: dict[str, object] = {
            "serviceKey": query.service_key,
            "pageNo": 1,
            "numOfRows": query.page_size,
            "resultType": "XML",
            "stnd_yr": query.standard_year,
        }
        if query.period_number:
            params["period_no"] = query.period_number
        if query.racer_name:
            params["racer_nm"] = query.racer_name
        try:
            response = self._client.get(self.base_url, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise DataGoPlayerStatCollectorError("OpenAPI request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise DataGoPlayerStatCollectorError(
                f"OpenAPI returned HTTP status {exc.response.status_code}."
            ) from exc
        except httpx.RequestError as exc:
            raise DataGoPlayerStatCollectorError("Unable to connect to the OpenAPI service.") from exc
        return self._parse_xml(response.text)

    def _parse_xml(self, xml_text: str) -> _StatPage:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise DataGoPlayerStatCollectorError("Unable to parse XML response.") from exc
        result_code = _find_text(root, "resultcode")
        if not result_code:
            raise DataGoPlayerStatCollectorError("OpenAPI response is missing resultCode.")
        if result_code not in {"00", "0", "NORMAL_SERVICE"}:
            raise DataGoPlayerStatCollectorError(f"OpenAPI returned error code {result_code}.")
        total_text = _find_text(root, "totalcount")
        total_count = int(total_text) if total_text and total_text.isdigit() else None
        items = [_flatten(item) for item in root.iter() if _key(item.tag) == "item"]
        return _StatPage(items=items, total_count=total_count)

    def _normalize(self, fields: dict[str, str], collected_at: datetime) -> CollectedPlayerStatistic:
        standard_year = fields.get("stndyr", "").strip()
        if not standard_year:
            raise _RowError("MISSING_STANDARD_YEAR", "Standard year is missing.")
        racer_name = fields.get("racernm", "").strip()
        if not racer_name:
            raise _RowError("MISSING_PLAYER_NAME", "Player name is missing.")

        integers = {
            target: _parse_optional_integer(fields.get(source), source)
            for target, source in INTEGER_FIELDS.items()
        }
        rates = {
            target: _parse_optional_rate(fields.get(source), source)
            for target, source in RATE_FIELDS.items()
        }
        return CollectedPlayerStatistic(
            source="data_go",
            standard_year=standard_year,
            racer_name=racer_name,
            period_number=_optional(fields.get("periodno")),
            grade=_optional(fields.get("racergrdcd")) or "unknown",
            collected_at=collected_at,
            **integers,
            **rates,
        )


@dataclass(frozen=True)
class _RowError(Exception):
    error_code: str
    message: str


def _parse_optional_integer(value: str | None, field_name: str) -> int | None:
    value = _optional(value)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise _RowError("INVALID_INTEGER", f"Invalid integer field: {field_name}") from exc


def _parse_optional_rate(value: str | None, field_name: str) -> Decimal | None:
    value = _optional(value)
    if value is None:
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise _RowError("INVALID_RATE", f"Invalid rate field: {field_name}") from exc


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _flatten(element: ET.Element) -> dict[str, str]:
    return {_key(child.tag): "".join(child.itertext()).strip() for child in list(element)}


def _find_text(root: ET.Element, key: str) -> str | None:
    for element in root.iter():
        if _key(element.tag) == key:
            text = "".join(element.itertext()).strip()
            if text:
                return text
    return None


def _key(tag: str) -> str:
    local = tag.rsplit("}", 1)[-1].split(":")[-1].lower()
    return re.sub(r"[^a-z0-9]+", "", local)
