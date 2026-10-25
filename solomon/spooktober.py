"""Spooktober movie diary. Watches are household records. No streaming service and no model."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from sqlalchemy import Integer, String, Text, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from solomon.clock import AppClock
from solomon.models import Base

HOUSEHOLD_TZ = ZoneInfo("America/New_York")
MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
PEOPLE = {
    "member-desrosier": "Desrosier",
    "member-peter": "Peter",
}
PERSON_ORDER = ("member-desrosier", "member-peter")
SAMPLE = (
    {
        "title": "The Witch",
        "member_id": "member-desrosier",
        "watched_on": "2024-10-12",
        "rating": 9,
        "spook": 10,
        "notes": "Still the one we quote.",
        "best_of": True,
    },
    {
        "title": "The Witch",
        "member_id": "member-peter",
        "watched_on": "2024-10-12",
        "rating": 8,
        "spook": 9,
        "notes": "The goat still gets me.",
    },
    {
        "title": "Halloween",
        "member_id": "member-desrosier",
        "watched_on": "2026-10-17",
        "rating": 7,
        "spook": 8,
        "notes": "The walk home was the good part.",
        "best_of": True,
    },
    {
        "title": "Halloween",
        "member_id": "member-peter",
        "watched_on": "2026-10-17",
        "rating": 9,
        "spook": 10,
        "notes": "We turned the lights off.",
    },
    {
        "title": "Coraline",
        "member_id": "member-desrosier",
        "watched_on": "2026-10-24",
        "rating": 10,
        "spook": 6,
        "notes": "The garden.",
        "best_of": False,
    },
    {
        "title": "Coraline",
        "member_id": "member-peter",
        "watched_on": "2026-10-24",
        "rating": 6,
        "spook": 4,
        "notes": "Pretty, not scary.",
    },
)


class MediaEntry(Base):
    __tablename__ = "media_entry"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, default="movie")
    title: Mapped[str] = mapped_column(String)
    title_key: Mapped[str] = mapped_column(String, unique=True)
    best_of: Mapped[int] = mapped_column(Integer, default=0)


class WatchEvent(Base):
    __tablename__ = "watch_event"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    entry_id: Mapped[str] = mapped_column(String)
    member_id: Mapped[str] = mapped_column(String)
    member_name: Mapped[str] = mapped_column(String)
    watched_on: Mapped[str] = mapped_column(String)
    rating: Mapped[int | None] = mapped_column(Integer)
    spook: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    collection: Mapped[str] = mapped_column(String)


class SpooktoberStore:
    def __init__(self, engine: Engine, clock: AppClock) -> None:
        Base.metadata.create_all(engine)
        _ensure_columns(engine)
        self.engine = engine
        self.clock = clock
        self._session = sessionmaker(bind=engine, expire_on_commit=False)

    def session(self) -> Session:
        return self._session()

    def seed_sample(self) -> None:
        for watch in SAMPLE:
            self.record_watch(**watch)

    def record_watch(
        self,
        *,
        title: str,
        member_id: str,
        watched_on: str,
        rating: int | None = None,
        spook: int | None = None,
        notes: str | None = None,
        best_of: bool | None = None,
    ) -> None:
        cleaned = title.strip()
        if not cleaned:
            raise ValueError("title is required")
        name = PEOPLE.get(member_id)
        if name is None:
            raise ValueError("unknown member")
        day = _parse_day(watched_on)
        rating = _score(rating, "rating")
        spook = _score(spook, "spook")
        note = notes.strip() if isinstance(notes, str) else None
        note = note or None
        with self.session() as session:
            key = cleaned.casefold()
            entry = session.scalar(select(MediaEntry).where(MediaEntry.title_key == key))
            if entry is None:
                entry = MediaEntry(
                    id=f"media_{uuid4().hex}",
                    kind="movie",
                    title=cleaned,
                    title_key=key,
                    best_of=0,
                )
                session.add(entry)
                session.flush()
            if best_of is not None:
                entry.best_of = 1 if best_of else 0
            collection = f"spooktober:{day.year}"
            existing = session.scalar(
                select(WatchEvent).where(
                    WatchEvent.entry_id == entry.id,
                    WatchEvent.member_id == member_id,
                    WatchEvent.collection == collection,
                )
            )
            if existing is None:
                session.add(
                    WatchEvent(
                        id=f"watch_{uuid4().hex}",
                        entry_id=entry.id,
                        member_id=member_id,
                        member_name=name,
                        watched_on=day.isoformat(),
                        rating=rating,
                        spook=spook,
                        notes=note,
                        collection=collection,
                    )
                )
            else:
                existing.member_name = name
                existing.watched_on = day.isoformat()
                existing.rating = rating
                existing.spook = spook
                existing.notes = note
            session.commit()

    def diary(self) -> dict:
        year = _year(self.clock.now())
        with self.session() as session:
            events = list(session.scalars(select(WatchEvent)))
            entries = {row.id: row for row in session.scalars(select(MediaEntry))}
        return _project(events, entries, year)


def build_router(store: SpooktoberStore) -> APIRouter:
    router = APIRouter()

    @router.get("/api/spooktober")
    def spooktober() -> dict:
        return store.diary()

    return router


def _project(events: list[WatchEvent], entries: dict[str, MediaEntry], year: int) -> dict:
    movies = _movies(events, entries)
    return {
        "empty": len(events) == 0,
        "year": year,
        "chart": _chart(events, year),
        "movies": movies,
        "best_of": [movie for movie in movies if movie["best_of"]],
    }


def _movies(events: list[WatchEvent], entries: dict[str, MediaEntry]) -> list[dict]:
    grouped: dict[str, list[WatchEvent]] = {}
    for event in events:
        grouped.setdefault(event.entry_id, []).append(event)
    order = {member_id: index for index, member_id in enumerate(PERSON_ORDER)}
    movies = []
    for entry_id, rows in grouped.items():
        entry = entries[entry_id]
        people = [
            {
                "member_id": row.member_id,
                "display_name": row.member_name,
                "initial": _initial(row.member_name),
                "rating": row.rating,
                "spook": row.spook,
                "notes": row.notes,
                "watched_on": row.watched_on,
            }
            for row in sorted(rows, key=lambda row: order.get(row.member_id, len(order)))
        ]
        watched_on = max(person["watched_on"] for person in people)
        movies.append(
            {
                "title": entry.title,
                "watched_on": watched_on,
                "watched_label": _watched_label(watched_on),
                "best_of": bool(entry.best_of),
                "people": people,
            }
        )
    movies.sort(key=lambda movie: movie["title"])
    movies.sort(key=lambda movie: movie["watched_on"], reverse=True)
    return movies


def _chart(events: list[WatchEvent], year: int) -> list[dict]:
    if not events:
        return []
    by_year: dict[int, set[str]] = {}
    for event in events:
        watched_year = int(event.collection.split(":", 1)[1])
        by_year.setdefault(watched_year, set()).add(event.entry_id)
    start = min(by_year)
    end = max(year, max(by_year))
    return [{"year": item, "count": len(by_year.get(item, set()))} for item in range(start, end + 1)]


def _ensure_columns(engine: Engine) -> None:
    with engine.begin() as connection:
        tables = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "media_entry" in tables:
            columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(media_entry)")}
            if "best_of" not in columns:
                connection.exec_driver_sql("ALTER TABLE media_entry ADD COLUMN best_of INTEGER DEFAULT 0")
        if "watch_event" in tables:
            columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(watch_event)")}
            if "spook" not in columns:
                connection.exec_driver_sql("ALTER TABLE watch_event ADD COLUMN spook INTEGER")


def _score(value: int | None, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > 10:
        raise ValueError(f"{label} must be from 1 to 10")
    return value


def _parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("watched_on must be a date") from exc


def _watched_label(iso_day: str) -> str:
    day = date.fromisoformat(iso_day)
    return f"{MONTHS[day.month - 1]} {day.day}"


def _initial(name: str) -> str:
    for char in name:
        if char.isalnum():
            return char.upper()
    return "?"


def _year(now: datetime) -> int:
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return now.astimezone(HOUSEHOLD_TZ).year
