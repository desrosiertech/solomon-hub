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
from solomon.models import Base, Member

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


class MediaEntry(Base):
    __tablename__ = "media_entry"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, default="movie")
    title: Mapped[str] = mapped_column(String)
    title_key: Mapped[str] = mapped_column(String, unique=True)


class WatchEvent(Base):
    __tablename__ = "watch_event"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    entry_id: Mapped[str] = mapped_column(String)
    member_id: Mapped[str] = mapped_column(String)
    member_name: Mapped[str] = mapped_column(String)
    watched_on: Mapped[str] = mapped_column(String)
    rating: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    collection: Mapped[str] = mapped_column(String)


class SpooktoberStore:
    def __init__(self, engine: Engine, clock: AppClock) -> None:
        Base.metadata.create_all(engine)
        self.engine = engine
        self.clock = clock
        self._session = sessionmaker(bind=engine, expire_on_commit=False)

    def session(self) -> Session:
        return self._session()

    def record_watch(
        self,
        *,
        title: str,
        member_id: str,
        watched_on: str,
        rating: int | None = None,
        notes: str | None = None,
        display_name: str | None = None,
    ) -> None:
        cleaned = title.strip()
        if not cleaned:
            raise ValueError("title is required")
        day = _parse_day(watched_on)
        if rating is not None and (
            isinstance(rating, bool) or not isinstance(rating, int) or rating < 1 or rating > 5
        ):
            raise ValueError("rating must be from 1 to 5")
        note = notes.strip() if isinstance(notes, str) else None
        note = note or None
        with self.session() as session:
            name = _member_name(session, member_id, display_name)
            key = cleaned.casefold()
            entry = session.scalar(select(MediaEntry).where(MediaEntry.title_key == key))
            if entry is None:
                entry = MediaEntry(id=f"media_{uuid4().hex}", kind="movie", title=cleaned, title_key=key)
                session.add(entry)
                session.flush()
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
                        notes=note,
                        collection=collection,
                    )
                )
            else:
                existing.member_name = name
                existing.watched_on = day.isoformat()
                existing.rating = rating
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
    this_year = [event for event in events if event.collection == f"spooktober:{year}"]
    last_year = [event for event in events if event.collection == f"spooktober:{year - 1}"]
    recent = _movies(this_year, entries)
    return {
        "empty": len(events) == 0,
        "year": year,
        "annual_count": _count(this_year),
        "favorites": _favorites(recent),
        "recent": recent,
        "comparison": [
            {"year": year, "count": _count(this_year)},
            {"year": year - 1, "count": _count(last_year)},
        ],
    }


def _movies(events: list[WatchEvent], entries: dict[str, MediaEntry]) -> list[dict]:
    grouped: dict[str, list[WatchEvent]] = {}
    for event in events:
        grouped.setdefault(event.entry_id, []).append(event)
    movies = []
    for entry_id, rows in grouped.items():
        entry = entries[entry_id]
        people = [
            {
                "member_id": row.member_id,
                "display_name": row.member_name,
                "initial": _initial(row.member_name),
                "rating": row.rating,
                "notes": row.notes,
                "watched_on": row.watched_on,
            }
            for row in sorted(rows, key=lambda row: row.member_name)
        ]
        watched_on = max(person["watched_on"] for person in people)
        movies.append(
            {
                "title": entry.title,
                "watched_on": watched_on,
                "watched_label": _watched_label(watched_on),
                "people": people,
            }
        )
    movies.sort(key=lambda movie: movie["title"])
    movies.sort(key=lambda movie: movie["watched_on"], reverse=True)
    return movies


def _favorites(movies: list[dict]) -> list[dict]:
    favorites = []
    for movie in movies:
        people = [person["display_name"] for person in movie["people"] if person["rating"] == 5]
        if people:
            favorites.append({"title": movie["title"], "people": people})
    favorites.sort(key=lambda favorite: favorite["title"])
    return favorites


def _count(events: list[WatchEvent]) -> int:
    return len({event.entry_id for event in events})


def _member_name(session: Session, member_id: str, display_name: str | None) -> str:
    if display_name is not None and display_name.strip():
        return display_name.strip()
    member = session.get(Member, member_id)
    if member is None:
        raise ValueError("unknown member")
    return member.display_name


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
