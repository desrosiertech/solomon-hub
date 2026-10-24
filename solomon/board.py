"""Household calendar and weather for the home screen. Adapters never see other records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Protocol
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from solomon.clock import AppClock
from solomon.models import AuditEvent, CalendarEvent, Member, SourceStatus, WeatherSnapshot
from solomon.seed import MEMBER_ID

HOUSEHOLD_TZ = ZoneInfo("America/New_York")
WEATHER_ID = "home"
WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
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
WEEKDAY_ABBR = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@dataclass(frozen=True)
class WeatherReport:
    temp_f: int
    high_f: int
    low_f: int
    summary: str


@dataclass(frozen=True)
class ExternalEvent:
    ext_id: str
    title: str
    start: datetime
    end: datetime | None = None
    member_id: str | None = None
    location: str | None = None


class WeatherAdapter(Protocol):
    configured: bool

    def fetch(self) -> WeatherReport | None: ...


class CalendarAdapter(Protocol):
    configured: bool

    def fetch(self) -> list[ExternalEvent] | None: ...


class OfflineWeather:
    """No network. The home screen stays empty until a configured adapter is attached."""

    configured = False
    name = "offline"

    def fetch(self) -> WeatherReport | None:
        return None


class OfflineCalendar:
    configured = False
    name = "offline"

    def fetch(self) -> list[ExternalEvent] | None:
        return None


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_local(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=HOUSEHOLD_TZ)
    return parsed.astimezone(UTC)


def date_label(now: datetime) -> str:
    return date_label_for(_aware(now).astimezone(HOUSEHOLD_TZ).date())


def date_label_for(day: date) -> str:
    return f"{WEEKDAYS[day.weekday()]}, {MONTHS[day.month - 1]} {day.day}"


def when_label(start: datetime, now: datetime) -> str:
    local = _aware(start).astimezone(HOUSEHOLD_TZ)
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


def day_source_state(*, status: SourceStatus | None, has_rows: bool) -> str:
    unreachable = status is not None and not status.reachable
    ever_ok = status is not None and status.last_ok_at is not None
    if unreachable:
        if has_rows or ever_ok:
            return "stale"
        return "unknown"
    if has_rows:
        return "ready"
    return "empty"


def freshness_chip(state: str, status: SourceStatus | None, now: datetime, source: str) -> str | None:
    if state not in {"stale", "unknown"}:
        return None
    updated_at = _aware(status.last_ok_at) if status is not None and status.last_ok_at else None
    if updated_at is None:
        return f"{source} unreachable"
    return f"{updated_ago(updated_at, now)} · {source} unreachable"


class BoardStore:
    def __init__(
        self,
        engine: Engine,
        clock: AppClock,
        weather: WeatherAdapter | None = None,
        calendar: CalendarAdapter | None = None,
    ) -> None:
        self.engine = engine
        self.clock = clock
        self.weather = weather or OfflineWeather()
        self.calendar = calendar or OfflineCalendar()
        self._session = sessionmaker(bind=engine, expire_on_commit=False)

    def session(self) -> Session:
        return self._session()

    def add_event(self, payload: dict) -> dict:
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("title is required")
        if not payload.get("start_local"):
            raise ValueError("start_local is required")
        start = parse_local(payload["start_local"])
        end = parse_local(payload["end_local"]) if payload.get("end_local") else None
        if end is not None and end <= start:
            raise ValueError("end_local must be after start_local")
        member_id = payload.get("member_id") or None
        now = self.clock.now()
        with self.session() as session:
            if member_id is not None and session.get(Member, member_id) is None:
                raise ValueError("member not found")
            row = CalendarEvent(
                id=_new_id("evt"),
                source="manual",
                ext_id=None,
                title=title,
                start=start,
                end=end,
                location=(payload.get("location") or None),
                member_id=member_id,
            )
            session.add(row)
            session.add(
                AuditEvent(
                    id=_new_id("aud"),
                    at=now,
                    actor_kind="member",
                    actor_id=member_id or MEMBER_ID,
                    action="calendar.added",
                    subject_type="calendar_event",
                    subject_id=row.id,
                    detail=title,
                )
            )
            session.commit()
            names = self._names(session)
            return self._event_payload(row, names, now)

    def refresh_weather(self) -> dict:
        if not self.weather.configured:
            return self._weather_payload()
        try:
            report = self.weather.fetch()
        except Exception:
            report = None
        now = self.clock.now()
        with self.session() as session:
            status = self._status(session, "weather")
            if report is None:
                status.reachable = 0
                status.last_error_at = now
            else:
                snapshot = session.get(WeatherSnapshot, WEATHER_ID)
                if snapshot is None:
                    snapshot = WeatherSnapshot(
                        id=WEATHER_ID,
                        temp_f=report.temp_f,
                        high_f=report.high_f,
                        low_f=report.low_f,
                        summary=report.summary,
                        observed_at=now,
                    )
                    session.add(snapshot)
                else:
                    snapshot.temp_f = report.temp_f
                    snapshot.high_f = report.high_f
                    snapshot.low_f = report.low_f
                    snapshot.summary = report.summary
                    snapshot.observed_at = now
                status.reachable = 1
                status.last_ok_at = now
            session.commit()
        return self._weather_payload()

    def refresh_calendar(self) -> dict:
        if not self.calendar.configured:
            return self.home()["calendar"]
        try:
            events = self.calendar.fetch()
        except Exception:
            events = None
        now = self.clock.now()
        with self.session() as session:
            status = self._status(session, "calendar")
            if events is None:
                status.reachable = 0
                status.last_error_at = now
            else:
                session.execute(delete(CalendarEvent).where(CalendarEvent.source == "external"))
                for event in events:
                    member_id = event.member_id
                    if member_id is not None and session.get(Member, member_id) is None:
                        member_id = None
                    session.add(
                        CalendarEvent(
                            id=_new_id("evt"),
                            source="external",
                            ext_id=event.ext_id,
                            title=event.title.strip(),
                            start=_aware(event.start),
                            end=_aware(event.end) if event.end else None,
                            location=event.location,
                            member_id=member_id,
                        )
                    )
                status.reachable = 1
                status.last_ok_at = now
            session.commit()
        return self.home()["calendar"]

    def day(self, on: str | None) -> dict:
        now = self.clock.now()
        viewed = self._viewed_day(on, now)
        bounds = _bounds_for_date(viewed)
        label_now = datetime.combine(viewed, time(12, 0), tzinfo=HOUSEHOLD_TZ)
        with self.session() as session:
            names = self._names(session)
            rows = list(session.scalars(select(CalendarEvent)))
            status = session.get(SourceStatus, "calendar")
            on_day = [row for row in rows if _overlaps_bounds(row, *bounds)]
            state = day_source_state(status=status, has_rows=bool(on_day))
            today = _aware(now).astimezone(HOUSEHOLD_TZ).date()
            return {
                "on": viewed.isoformat(),
                "date_label": date_label_for(viewed),
                "prev": (viewed - timedelta(days=1)).isoformat(),
                "next": (viewed + timedelta(days=1)).isoformat(),
                "is_today": viewed == today,
                "day_cards": self._day_cards(rows, names, now, bounds=bounds, label_now=label_now),
                "calendar": {
                    "state": state,
                    "chip": freshness_chip(state, status, now, "Calendar"),
                    "updated_at": _iso(status.last_ok_at) if status else None,
                },
            }

    def _viewed_day(self, on: str | None, now: datetime) -> date:
        if on is None or not str(on).strip():
            return _aware(now).astimezone(HOUSEHOLD_TZ).date()
        try:
            return date.fromisoformat(on)
        except ValueError as exc:
            raise ValueError("on must be a YYYY-MM-DD date") from exc

    def home(self) -> dict:
        now = self.clock.now()
        with self.session() as session:
            names = self._names(session)
            rows = list(session.scalars(select(CalendarEvent)))
            calendar_status = session.get(SourceStatus, "calendar")
            shown = [row for row in rows if _overlaps_today(row, now) or _is_upcoming(row, now)]
            state = source_state(status=calendar_status, has_rows=bool(shown))
            return {
                "now": now.isoformat(),
                "date_label": date_label(now),
                "up_next": [
                    self._event_payload(row, names, now)
                    for row in _upcoming(rows, now)
                ],
                "day_cards": self._day_cards(rows, names, now),
                "calendar": {
                    "state": state,
                    "chip": freshness_chip(state, calendar_status, now, "Calendar"),
                    "updated_at": _iso(calendar_status.last_ok_at) if calendar_status else None,
                },
                "weather": self._weather_payload(session, now),
            }

    def _weather_payload(self, session: Session | None = None, now: datetime | None = None) -> dict:
        now = now or self.clock.now()
        own_session = session is None
        if own_session:
            session = self.session()
        assert session is not None
        try:
            snapshot = session.get(WeatherSnapshot, WEATHER_ID)
            status = session.get(SourceStatus, "weather")
            state = source_state(status=status, has_rows=snapshot is not None)
            return {
                "state": state,
                "chip": freshness_chip(state, status, now, "Weather"),
                "temp_f": snapshot.temp_f if snapshot else None,
                "high_f": snapshot.high_f if snapshot else None,
                "low_f": snapshot.low_f if snapshot else None,
                "summary": snapshot.summary if snapshot else None,
                "updated_at": _iso(status.last_ok_at) if status and status.last_ok_at else None,
            }
        finally:
            if own_session:
                session.close()

    def _day_cards(
        self,
        rows: list[CalendarEvent],
        names: dict[str, str],
        now: datetime,
        bounds: tuple[datetime, datetime] | None = None,
        label_now: datetime | None = None,
    ) -> list[dict]:
        start, end = bounds or _local_day_bounds(now)
        label_now = label_now or now
        cards = []
        for member_id, display_name in (*names.items(), (None, "Everyone")):
            events = [
                self._event_payload(row, names, label_now)
                for row in sorted(
                    (row for row in rows if row.member_id == member_id and _overlaps_bounds(row, start, end)),
                    key=lambda row: _aware(row.start),
                )
            ]
            cards.append(
                {
                    "member_id": member_id,
                    "display_name": display_name,
                    "initial": _initial(display_name),
                    "events": events,
                }
            )
        return cards

    def _event_payload(self, row: CalendarEvent, names: dict[str, str], now: datetime) -> dict:
        who = names.get(row.member_id or "", "Everyone")
        return {
            "id": row.id,
            "title": row.title,
            "when_label": when_label(row.start, now),
            "location": row.location,
            "who": who,
            "initial": _initial(who),
            "member_id": row.member_id,
        }

    def _names(self, session: Session) -> dict[str, str]:
        return {
            row.id: row.display_name
            for row in session.scalars(select(Member).order_by(Member.display_name))
        }

    def _status(self, session: Session, adapter: str) -> SourceStatus:
        row = session.get(SourceStatus, adapter)
        if row is None:
            row = SourceStatus(adapter=adapter, reachable=1)
            session.add(row)
        return row


def _initial(name: str) -> str:
    for char in name:
        if char.isalnum():
            return char.upper()
    return "?"


def _local_day_bounds(now: datetime) -> tuple[datetime, datetime]:
    local = _aware(now).astimezone(HOUSEHOLD_TZ)
    start = datetime.combine(local.date(), time.min, tzinfo=HOUSEHOLD_TZ)
    return start.astimezone(UTC), (start + timedelta(days=1)).astimezone(UTC)


def _window_end(now: datetime) -> datetime:
    local = _aware(now).astimezone(HOUSEHOLD_TZ)
    start = datetime.combine(local.date(), time.min, tzinfo=HOUSEHOLD_TZ)
    return (start + timedelta(days=3)).astimezone(UTC)


def _event_end(row: CalendarEvent) -> datetime:
    if row.end is not None:
        return _aware(row.end)
    return _aware(row.start)


def _bounds_for_date(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=HOUSEHOLD_TZ)
    return start.astimezone(UTC), (start + timedelta(days=1)).astimezone(UTC)


def _overlaps_bounds(row: CalendarEvent, day_start: datetime, day_end: datetime) -> bool:
    start = _aware(row.start)
    end = _event_end(row)
    return start < day_end and end > day_start


def _overlaps_today(row: CalendarEvent, now: datetime) -> bool:
    return _overlaps_bounds(row, *_local_day_bounds(now))


def _is_upcoming(row: CalendarEvent, now: datetime) -> bool:
    current = _aware(now)
    start = _aware(row.start)
    end = _event_end(row)
    if row.end is not None:
        still_going = end > current
    else:
        still_going = start >= current
    return still_going and start < _window_end(now)


def _upcoming(rows: list[CalendarEvent], now: datetime) -> list[CalendarEvent]:
    chosen = [row for row in rows if _is_upcoming(row, now)]
    chosen.sort(key=lambda row: _aware(row.start))
    return chosen[:5]


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _aware(value).isoformat()
