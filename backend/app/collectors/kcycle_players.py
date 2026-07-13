from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Callable, Iterable
from urllib.parse import urljoin, urlparse

import httpx


DEFAULT_LIST_URL = "https://www.kcycle.or.kr/racer/info"
DEFAULT_SOURCE = "kcycle"
DEFAULT_REGION = "unknown"
DEFAULT_STATUS = "active"
PREVIEW_FIELDS = (
    "external_id",
    "name",
    "period_number",
    "grade",
    "region",
    "status",
    "detail_url",
    "source",
    "collected_at",
)


class KcyclePlayerCollectorError(RuntimeError):
    pass


@dataclass(frozen=True)
class KcyclePlayer:
    external_id: str
    name: str
    period_number: int | None
    grade: str
    region: str
    status: str
    detail_url: str
    source: str
    collected_at: str

    def to_csv_row(self) -> dict[str, str]:
        return {
            "external_id": self.external_id,
            "name": self.name,
            "period_number": "" if self.period_number is None else str(self.period_number),
            "grade": self.grade,
            "region": self.region,
            "status": self.status,
            "detail_url": self.detail_url,
            "source": self.source,
            "collected_at": self.collected_at,
        }


@dataclass(frozen=True)
class KcycleCollectionIssue:
    error_code: str
    page: int
    row: int
    message: str


@dataclass
class KcycleCollectionResult:
    rows: list[KcyclePlayer] = field(default_factory=list)
    issues: list[KcycleCollectionIssue] = field(default_factory=list)
    cards_seen: int = 0
    total_cards: int = 0
    duplicates_skipped: int = 0
    pages_fetched: int = 0
    http_success: bool = False
    page_end_reason: str = ""


@dataclass(frozen=True)
class KcyclePlayerQuery:
    page_size: int = 10
    max_pages: int = 1


@dataclass(frozen=True)
class _RawPlayerCard:
    external_id: str | None
    name: str | None
    grade: str | None
    period_text: str | None


class _KcyclePlayerCardParser(HTMLParser):
    _VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[_RawPlayerCard] = []
        self._card_depth = 0
        self._external_id: str | None = None
        self._name_parts: list[str] = []
        self._category_parts: list[list[str]] = []
        self._capture_name = False
        self._capture_category = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "a" and "prsn" in classes and self._card_depth == 0:
            self._card_depth = 1
            self._external_id = _extract_external_id(attributes.get("onclick"))
            self._name_parts = []
            self._category_parts = []
            return

        if self._card_depth == 0:
            return
        if tag in self._VOID_TAGS:
            return
        self._card_depth += 1
        if tag == "b" and "name" in classes:
            self._capture_name = True
        elif tag == "span" and "cate" in classes:
            self._category_parts.append([])
            self._capture_category = True

    def handle_data(self, data: str) -> None:
        if self._capture_name:
            self._name_parts.append(data)
        if self._capture_category and self._category_parts:
            self._category_parts[-1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._card_depth == 0:
            return
        if tag == "b" and self._capture_name:
            self._capture_name = False
        elif tag == "span" and self._capture_category:
            self._capture_category = False

        self._card_depth -= 1
        if self._card_depth == 0 and tag == "a":
            categories = [_clean_text("".join(parts)) for parts in self._category_parts]
            grade = next((value for value in categories if value and not value.endswith("기")), None)
            period_text = next((value for value in categories if value.endswith("기")), None)
            self.cards.append(
                _RawPlayerCard(
                    external_id=self._external_id,
                    name=_clean_text("".join(self._name_parts)) or None,
                    grade=grade,
                    period_text=period_text,
                )
            )


class KcyclePlayerCollector:
    def __init__(
        self,
        *,
        list_url: str = DEFAULT_LIST_URL,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.list_url = list_url
        self._client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "KIP collector validation/1.0"},
        )
        self._owns_client = client is None
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "KcyclePlayerCollector":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def collect(self, query: KcyclePlayerQuery) -> KcycleCollectionResult:
        if not 1 <= query.page_size <= 10:
            raise KcyclePlayerCollectorError("page_size must be between 1 and 10 for preview collection.")
        if query.max_pages != 1:
            raise KcyclePlayerCollectorError("KCYCLE exposes a single unpaged list; max_pages must be 1.")

        html_text = self._fetch_list()
        cards = self._parse_cards(html_text)
        result = KcycleCollectionResult(
            total_cards=len(cards),
            pages_fetched=1,
            http_success=True,
            page_end_reason="single_unpaged_response",
        )
        collected_at = self._clock().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        seen_ids: set[str] = set()

        for row_number, card in enumerate(cards[: query.page_size], start=1):
            result.cards_seen += 1
            if not card.external_id:
                result.issues.append(
                    KcycleCollectionIssue(
                        error_code="MISSING_EXTERNAL_ID",
                        page=1,
                        row=row_number,
                        message="KCYCLE racerNo is missing.",
                    )
                )
                continue
            if not card.name:
                result.issues.append(
                    KcycleCollectionIssue(
                        error_code="MISSING_PLAYER_NAME",
                        page=1,
                        row=row_number,
                        message="Player name is missing.",
                    )
                )
                continue
            if card.external_id in seen_ids:
                result.duplicates_skipped += 1
                continue

            detail_url = urljoin(self.list_url, f"/racer/info/{card.external_id}")
            if urlparse(detail_url).path.rsplit("/", 1)[-1] != card.external_id:
                result.issues.append(
                    KcycleCollectionIssue(
                        error_code="INVALID_DETAIL_URL",
                        page=1,
                        row=row_number,
                        message="Detail URL does not contain racerNo.",
                    )
                )
                continue

            seen_ids.add(card.external_id)
            result.rows.append(
                KcyclePlayer(
                    external_id=card.external_id,
                    name=card.name,
                    period_number=_parse_period_number(card.period_text),
                    grade=card.grade or "unknown",
                    region=DEFAULT_REGION,
                    status=DEFAULT_STATUS,
                    detail_url=detail_url,
                    source=DEFAULT_SOURCE,
                    collected_at=collected_at,
                )
            )

        return result

    def _fetch_list(self) -> str:
        try:
            response = self._client.get(self.list_url)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise KcyclePlayerCollectorError("KCYCLE request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise KcyclePlayerCollectorError(
                f"KCYCLE returned HTTP status {exc.response.status_code}."
            ) from exc
        except httpx.RequestError as exc:
            raise KcyclePlayerCollectorError("Unable to connect to KCYCLE.") from exc

        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type:
            raise KcyclePlayerCollectorError("KCYCLE returned an unexpected response type.")
        return response.text

    def _parse_cards(self, html_text: str) -> list[_RawPlayerCard]:
        parser = _KcyclePlayerCardParser()
        try:
            parser.feed(html_text)
            parser.close()
        except Exception as exc:
            raise KcyclePlayerCollectorError("Unable to parse the KCYCLE player list.") from exc
        if not parser.cards:
            raise KcyclePlayerCollectorError("KCYCLE player list area was not found.")
        return parser.cards


def export_kcycle_players_csv(csv_path: Path, rows: Iterable[KcyclePlayer]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(PREVIEW_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())


def _extract_external_id(onclick: str | None) -> str | None:
    if not onclick:
        return None
    match = re.search(r"fnMoveTo\(\s*['\"]?/racer/info['\"]?\s*,\s*['\"](\d+)['\"]\s*\)", onclick)
    return match.group(1) if match else None


def _parse_period_number(value: str | None) -> int | None:
    if not value:
        return None
    match = re.fullmatch(r"0*(\d+)기", value.strip())
    return int(match.group(1)) if match else None


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
