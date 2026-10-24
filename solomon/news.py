"""Household news digest. The feed adapter never sees other records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from solomon.clock import AppClock
from solomon.models import Headline, SourceStatus

HOUSEHOLD_TZ = ZoneInfo("America/New_York")
WEEKDAY_ABBR = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@dataclass(frozen=True)
class HeadlineItem:
    title: str
    url: str
    published_at: datetime
    source_name: str | None = None


class NewsAdapter(Protocol):
    configured: bool

    def fetch(self) -> list[HeadlineItem] | None: ...


class OfflineNews:
    """No network. The digest stays empty until a configured adapter is attached."""

    configured = False
    name = "offline"

    def fetch(self) -> list[HeadlineItem] | None:
        return None


class StandInFeed:
    """Canned headlines for this slice. No live third-party call."""

    configured = True
    name = "stand-in"

    def fetch(self) -> list[HeadlineItem] | None:
        published = datetime(2026, 10, 23, 15, 15, tzinfo=UTC)
        return [
            HeadlineItem(
                title="Town library extends Saturday hours",
                url="https://example.com/library-hours",
                published_at=published,
                source_name="Town desk",
            ),
            HeadlineItem(
                title="High school soccer hosts the playoff opener",
                url="https://example.com/soccer-playoff",
                published_at=published.replace(hour=14, minute=0),
                source_name="Sports desk",
            ),
            HeadlineItem(
                title="Weekend rain moves in after dark",
                url="https://example.com/weekend-rain",
                published_at=published.replace(hour=13, minute=40),
                source_name="Weather desk",
            ),
        ]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def published_label(published_at: datetime, now: datetime) -> str:
    local = _aware(published_at).astimezone(HOUSEHOLD_TZ)
    today = _aware(now).astimezone(HOUSEHOLD_TZ).date()
    hour = local.hour % 12 or 12
    clock = f"{hour}:{local.minute:02d} {'AM' if local.hour < 12 else 'PM'}"
    if local.date() == today:
        return clock
    return f"{WEEKDAY_ABBR[local.weekday()]} {clock}"


def updated_ago(updated_at: datetime, now: datetime) -> str:
    minutes = int((_aware(now) - _aware(updated_at)).total_seconds() // 60)
    minutes = max(0, minutes)
    if minutes < 60:
        return f"Updated {minutes} min ago"
    return f"Updated {minutes // 60} h ago"


def source_state(*, status: SourceStatus | None, has_rows: bool) -> str:
    if status is not None and not status.reachable:
        return "stale" if has_rows else "unknown"
    if has_rows:
        return "ready"
    return "empty"


def freshness_chip(state: str, status: SourceStatus | None, now: datetime) -> str | None:
    if state not in {"stale", "unknown"}:
        return None
    updated_at = _aware(status.last_ok_at) if status is not None and status.last_ok_at else None
    if updated_at is None:
        return "News unreachable"
    return f"{updated_ago(updated_at, now)} · News unreachable"


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


def _normalize_title(title: str) -> str:
    return " ".join(title.casefold().split())


def dedupe_headlines(items: list[HeadlineItem]) -> list[HeadlineItem]:
    ordered = sorted(items, key=lambda item: _aware(item.published_at), reverse=True)
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[HeadlineItem] = []
    for item in ordered:
        title = item.title.strip()
        url = item.url.strip()
        if not title or not url:
            continue
        url_key = _normalize_url(url)
        title_key = _normalize_title(title)
        if url_key in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(url_key)
        seen_titles.add(title_key)
        unique.append(
            HeadlineItem(
                title=title,
                url=url,
                published_at=_aware(item.published_at),
                source_name=item.source_name,
            )
        )
    return unique


class NewsStore:
    def __init__(
        self,
        engine: Engine,
        clock: AppClock,
        feed: NewsAdapter | None = None,
    ) -> None:
        self.engine = engine
        self.clock = clock
        self.feed = feed or StandInFeed()
        self._session = sessionmaker(bind=engine, expire_on_commit=False)

    def session(self) -> Session:
        return self._session()

    def refresh(self) -> dict:
        if not self.feed.configured:
            return self.digest()
        try:
            items = self.feed.fetch()
        except Exception:
            items = None
        now = self.clock.now()
        with self.session() as session:
            status = self._status(session)
            if items is None:
                status.reachable = 0
                status.last_error_at = now
            else:
                session.execute(delete(Headline))
                for item in dedupe_headlines(items):
                    session.add(
                        Headline(
                            id=_new_id("hdl"),
                            title=item.title,
                            url=item.url,
                            published_at=item.published_at,
                            source_name=item.source_name,
                        )
                    )
                status.reachable = 1
                status.last_ok_at = now
            session.commit()
        return self.digest()

    def digest(self) -> dict:
        now = self.clock.now()
        with self.session() as session:
            rows = list(session.scalars(select(Headline)))
            rows.sort(key=lambda row: _aware(row.published_at), reverse=True)
            status = session.get(SourceStatus, "news")
            state = source_state(status=status, has_rows=bool(rows))
            return {
                "state": state,
                "chip": freshness_chip(state, status, now),
                "updated_at": _iso(status.last_ok_at) if status and status.last_ok_at else None,
                "headlines": [
                    {
                        "id": row.id,
                        "title": row.title,
                        "url": row.url,
                        "published_at": _aware(row.published_at).isoformat(),
                        "published_label": published_label(row.published_at, now),
                        "source_name": row.source_name,
                    }
                    for row in rows
                ],
            }

    def _status(self, session: Session) -> SourceStatus:
        row = session.get(SourceStatus, "news")
        if row is None:
            row = SourceStatus(adapter="news", reachable=1)
            session.add(row)
        return row


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _aware(value).isoformat()
