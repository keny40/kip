from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import csv
import re
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

import httpx
from sqlalchemy.orm import Session

from app.services.imports.race_data import CSVImportService, ImportReport

DEFAULT_BASE_URL = "https://apis.data.go.kr/B551014/SRVC_CRA_RACER_INFO/TODZ_CRA_RACER_INFO"
PLAYER_CSV_FIELDS = ("player_number", "name", "grade", "region", "status")
DEFAULT_PLAYER_GRADE = "unknown"
DEFAULT_PLAYER_REGION = "unknown"
DEFAULT_PLAYER_STATUS = "unknown"
DEFAULT_DUPLICATE_KEY = "racer_no"


@dataclass(frozen=True)
class CollectedPlayer:
    player_number: int
    name: str
    grade: str
    region: str
    status: str = DEFAULT_PLAYER_STATUS
    source_fields: dict[str, str] = field(default_factory=dict)

    def to_csv_row(self) -> dict[str, str]:
        return {
            "player_number": str(self.player_number),
            "name": self.name,
            "grade": self.grade,
            "region": self.region,
            "status": self.status,
        }


@dataclass(frozen=True)
class CollectionIssue:
    page_no: int
    row_number: int
    error_code: str
    message: str
    source_fields: dict[str, str] = field(default_factory=dict)


@dataclass
class CollectionResult:
    rows: list[CollectedPlayer] = field(default_factory=list)
    issues: list[CollectionIssue] = field(default_factory=list)
    pages_fetched: int = 0
    total_count: int | None = None
    duplicates_skipped: int = 0
    item_count: int = 0
    observed_tags: list[str] = field(default_factory=list)
    duplicate_key: str = DEFAULT_DUPLICATE_KEY
    normalized_preview: list[CollectedPlayer] = field(default_factory=list)


@dataclass(frozen=True)
class DataGoQuery:
    service_key: str
    stnd_yr: int | None = None
    racer_nm: str | None = None
    period_no: int | None = None
    page_size: int = 100
    max_pages: int | None = None


class DataGoCollectorError(RuntimeError):
    pass


class DataGoKeirinPlayerCollector:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> DataGoKeirinPlayerCollector:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def collect_players(self, query: DataGoQuery, *, inspect: bool = False) -> CollectionResult:
        if not query.service_key.strip():
            raise DataGoCollectorError("service_key is required")

        result = CollectionResult()
        records: OrderedDict[int, CollectedPlayer] = OrderedDict()
        observed_tags: set[str] = set()

        page_no = 1
        while True:
            page = self._fetch_page(query, page_no)
            result.pages_fetched += 1
            if page.total_count is not None:
                result.total_count = page.total_count
            for tag in page.tags:
                observed_tags.add(tag)

            if not page.items:
                break

            result.item_count += len(page.items)
            for row_number, item in enumerate(page.items, start=2):
                if self._extract_player_number(item) is None:
                    result.issues.append(
                        CollectionIssue(
                            page_no=page_no,
                            row_number=row_number,
                            error_code="MISSING_PLAYER_NUMBER",
                            message="Required player number could not be resolved.",
                        )
                    )
                    continue

                if not self._first_non_empty(item, ("racernm", "name", "playername", "playernm")):
                    result.issues.append(
                        CollectionIssue(
                            page_no=page_no,
                            row_number=row_number,
                            error_code="MISSING_PLAYER_NAME",
                            message="Required player name could not be resolved.",
                        )
                    )
                    continue

                normalized = self._normalize_item(item)
                if normalized is None:
                    result.issues.append(
                        CollectionIssue(
                            page_no=page_no,
                            row_number=row_number,
                            error_code="NORMALIZATION_FAILED",
                            message="Required player fields could not be resolved.",
                        )
                    )
                    continue

                if normalized.player_number in records:
                    result.duplicates_skipped += 1
                    continue

                records[normalized.player_number] = normalized

            if query.max_pages is not None and page_no >= query.max_pages:
                break
            if page.total_count is not None and page_no * query.page_size >= page.total_count:
                break
            if len(page.items) < query.page_size:
                break
            page_no += 1

        result.rows = list(records.values())
        result.observed_tags = sorted(observed_tags)
        result.normalized_preview = result.rows[:10] if inspect else []
        return result

    def _fetch_page(self, query: DataGoQuery, page_no: int) -> "_DataGoPage":
        params: dict[str, object] = {
            "serviceKey": query.service_key,
            "pageNo": page_no,
            "numOfRows": query.page_size,
            "resultType": "XML",
        }
        if query.stnd_yr is not None:
            params["stnd_yr"] = query.stnd_yr
        if query.racer_nm:
            params["racer_nm"] = query.racer_nm
        if query.period_no is not None:
            params["period_no"] = query.period_no

        try:
            response = self._client.get(self.base_url, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise DataGoCollectorError("OpenAPI request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise DataGoCollectorError(
                f"OpenAPI returned HTTP status {exc.response.status_code}."
            ) from exc
        except httpx.RequestError as exc:
            raise DataGoCollectorError("Unable to connect to the OpenAPI service.") from exc
        return self._parse_page(response.text)

    def _parse_page(self, xml_text: str) -> "_DataGoPage":
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise DataGoCollectorError("Unable to parse XML response.") from exc

        result_code = self._find_text(root, ("resultcode",))
        if not result_code:
            raise DataGoCollectorError("OpenAPI response is missing resultCode.")
        if result_code and result_code not in {"00", "0", "NORMAL_SERVICE"}:
            raise DataGoCollectorError(f"OpenAPI returned error code {result_code}.")

        total_count_text = self._find_text(root, ("totalcount", "total_count"))
        total_count = int(total_count_text) if total_count_text and total_count_text.isdigit() else None

        items: list[dict[str, str]] = []
        tags: set[str] = set()
        for item_element in self._iter_item_elements(root):
            item_fields = self._flatten_element(item_element, tags)
            if item_fields:
                items.append(item_fields)

        return _DataGoPage(total_count=total_count, items=items, tags=sorted(tags))

    def _iter_item_elements(self, root: ET.Element) -> Iterable[ET.Element]:
        for element in root.iter():
            if self._local_name(element.tag) == "item":
                yield element

    def _flatten_element(self, element: ET.Element, tags: set[str] | None = None) -> dict[str, str]:
        flattened: dict[str, str] = {}
        for child in list(element):
            local_name = self._local_name(child.tag)
            if tags is not None:
                tags.add(local_name)
            key = self._canonical_key(child.tag)
            value = self._element_text(child)
            if key and value:
                flattened[key] = value
        return flattened

    def _normalize_item(self, fields: dict[str, str]) -> CollectedPlayer | None:
        player_number = self._extract_player_number(fields)
        name = self._first_non_empty(fields, ("racernm", "name", "playername", "playernm"))
        if player_number is None or not name:
            return None

        grade = self._first_non_empty(
            fields,
            ("racergrdcd", "grade", "racergrade", "playergrade", "gradecode"),
            default=DEFAULT_PLAYER_GRADE,
        )
        region = self._first_non_empty(
            fields,
            (
                "region",
                "area",
                "homearea",
                "homeareanm",
                "birthplace",
                "trainingsite",
                "trainingsitename",
                "team",
                "teamname",
                "affiliation",
                "residence",
                "origin",
            ),
            default=DEFAULT_PLAYER_REGION,
        )
        status = self._normalize_status(
            self._first_non_empty(
                fields,
                ("status", "racerstatus", "state", "useyn", "activeyn", "retireyn"),
                default=DEFAULT_PLAYER_STATUS,
            )
        )

        return CollectedPlayer(
            player_number=player_number,
            name=name,
            grade=grade,
            region=region,
            status=status,
            source_fields=fields,
        )

    def _extract_player_number(self, fields: dict[str, str]) -> int | None:
        # The 2026-07-13 live response omitted racer_no. period_no is a rider
        # generation filter/data field and must never be used as player_number.
        value = self._first_non_empty(
            fields,
            ("racerno", "playernumber", "racernumber", "playerno", "ridernumber"),
        )
        if value is None:
            return None

        digits = re.sub(r"\D+", "", value)
        if not digits:
            return None
        return int(digits)

    def _first_non_empty(
        self,
        fields: dict[str, str],
        keys: tuple[str, ...],
        *,
        default: str | None = None,
    ) -> str | None:
        for key in keys:
            value = fields.get(key)
            if value is not None and value.strip():
                return value.strip()
        return default

    def _normalize_status(self, value: str | None) -> str:
        if value is None or not value.strip():
            return DEFAULT_PLAYER_STATUS

        normalized = value.strip().lower()
        if normalized in {"y", "yes", "1", "active"}:
            return "active"
        if normalized in {"n", "no", "0", "inactive"}:
            return "inactive"
        if "retire" in normalized:
            return "retired"
        return DEFAULT_PLAYER_STATUS

    def _find_text(self, root: ET.Element, keys: tuple[str, ...]) -> str | None:
        for element in root.iter():
            canonical = self._canonical_key(element.tag)
            if canonical in keys:
                text = self._element_text(element)
                if text:
                    return text
        return None

    def _element_text(self, element: ET.Element) -> str:
        text = "".join(element.itertext()).strip()
        return text

    def _local_name(self, tag: str) -> str:
        return tag.rsplit("}", 1)[-1].split(":")[-1].strip()

    def _canonical_key(self, tag: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", self._local_name(tag).lower())


@dataclass(frozen=True)
class _DataGoPage:
    total_count: int | None
    items: list[dict[str, str]]
    tags: list[str] = field(default_factory=list)


def export_players_csv(csv_path: Path, rows: Iterable[CollectedPlayer]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(PLAYER_CSV_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())


def collect_players_to_csv(
    csv_path: Path,
    query: DataGoQuery,
    *,
    collector: DataGoKeirinPlayerCollector | None = None,
) -> CollectionResult:
    active_collector = collector or DataGoKeirinPlayerCollector()
    should_close = collector is None
    try:
        result = active_collector.collect_players(query)
        export_players_csv(csv_path, result.rows)
        return result
    finally:
        if should_close:
            active_collector.close()


def import_players_csv(db: Session, csv_path: Path, *, dry_run: bool = False) -> ImportReport:
    importer = CSVImportService()
    return importer.import_players(db, csv_path, dry_run=dry_run)
