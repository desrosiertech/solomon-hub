"""Home calendar and weather through the app API. No model and no outside service."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from solomon.board import ExternalEvent, WeatherReport

NOW = "2026-10-23T21:42:00+00:00"  # 5:42 PM in America/New_York


class ScriptedWeather:
    configured = True

    def __init__(self, report: WeatherReport | None) -> None:
        self.report = report

    def fetch(self) -> WeatherReport | None:
        return self.report


class ScriptedCalendar:
    configured = True

    def __init__(self, events: list[ExternalEvent] | None) -> None:
        self.events = events

    def fetch(self) -> list[ExternalEvent] | None:
        return self.events


def _app(tmp_path: Path, *, weather: ScriptedWeather | None = None, calendar: ScriptedCalendar | None = None):
    from solomon.main import create_app

    app = create_app(db_path=tmp_path / "solomon.db", weather=weather, calendar=calendar)
    return TestClient(app)


def test_home_shows_upcoming_events_and_todays_cards(client):
    client.put("/api/clock", json={"now": NOW})
    soccer = client.post(
        "/api/calendar/events",
        json={
            "title": "Soccer pickup",
            "start_local": "2026-10-23T18:00",
            "location": "Field 3",
            "member_id": "member-adult",
        },
    )
    patch = client.post(
        "/api/calendar/events",
        json={"title": "Pumpkin patch", "start_local": "2026-10-24T10:00"},
    )
    ended = client.post(
        "/api/calendar/events",
        json={
            "title": "Dentist",
            "start_local": "2026-10-23T09:00",
            "end_local": "2026-10-23T10:00",
            "member_id": "member-adult",
        },
    )
    assert soccer.status_code == 201
    assert patch.status_code == 201
    assert ended.status_code == 201

    home = client.get("/api/home").json()
    assert home["date_label"] == "Friday, October 23"
    assert [row["title"] for row in home["up_next"]] == ["Soccer pickup", "Pumpkin patch"]
    assert home["up_next"][0]["when_label"] == "6:00 PM"
    assert home["up_next"][0]["location"] == "Field 3"
    assert home["up_next"][0]["who"] == "Adult"
    assert home["up_next"][0]["initial"] == "A"
    assert home["up_next"][1]["when_label"] == "Sat 10:00 AM"
    assert home["up_next"][1]["who"] == "Everyone"

    adult = next(card for card in home["day_cards"] if card["display_name"] == "Adult")
    assert [row["title"] for row in adult["events"]] == ["Dentist", "Soccer pickup"]
    assert adult["events"][0]["when_label"] == "9:00 AM"
    assert adult["initial"] == "A"
    everyone = next(card for card in home["day_cards"] if card["display_name"] == "Everyone")
    assert everyone["events"] == []
    assert home["calendar"]["state"] == "ready"
    assert home["calendar"]["chip"] is None
    assert home["weather"]["state"] == "empty"
    assert home["weather"]["temp_f"] is None
    assert home["weather"]["summary"] is None
    assert home["weather"]["chip"] is None


def test_unreachable_weather_keeps_the_last_forecast(tmp_path: Path):
    weather = ScriptedWeather(
        WeatherReport(temp_f=58, high_f=64, low_f=49, summary="Rain after 9 PM")
    )
    with _app(tmp_path, weather=weather) as client:
        client.put("/api/clock", json={"now": "2026-10-23T19:00:00+00:00"})
        assert client.post("/api/weather/refresh").status_code == 200
        ready = client.get("/api/home").json()["weather"]
        assert ready["state"] == "ready"
        assert ready["temp_f"] == 58
        assert ready["high_f"] == 64
        assert ready["low_f"] == 49
        assert ready["summary"] == "Rain after 9 PM"
        assert ready["chip"] is None
        assert client.get("/api/provider").json()["name"] == "Disabled"

        weather.report = None
        client.put("/api/clock", json={"now": "2026-10-23T21:00:00+00:00"})
        assert client.post("/api/weather/refresh").status_code == 200
        stale = client.get("/api/home").json()["weather"]
        assert stale["state"] == "stale"
        assert stale["temp_f"] == 58
        assert stale["high_f"] == 64
        assert stale["low_f"] == 49
        assert stale["summary"] == "Rain after 9 PM"
        assert stale["chip"] == "Updated 2 h ago · Weather unreachable"


def test_unreachable_calendar_keeps_events_instead_of_an_empty_day(tmp_path: Path):
    calendar = ScriptedCalendar(
        [
            ExternalEvent(
                ext_id="book-club",
                title="Book club",
                start=datetime(2026, 10, 23, 23, 30, tzinfo=UTC),
                member_id="member-adult",
                location="Library",
            )
        ]
    )
    with _app(tmp_path, calendar=calendar) as client:
        client.put("/api/clock", json={"now": "2026-10-23T21:00:00+00:00"})
        assert client.post("/api/calendar/refresh").status_code == 200
        ready = client.get("/api/home").json()
        assert ready["calendar"]["state"] == "ready"
        assert [row["title"] for row in ready["up_next"]] == ["Book club"]
        assert ready["up_next"][0]["when_label"] == "7:30 PM"
        assert ready["up_next"][0]["who"] == "Adult"

        calendar.events = None
        client.put("/api/clock", json={"now": "2026-10-23T23:00:00+00:00"})
        assert client.post("/api/calendar/refresh").status_code == 200
        stale = client.get("/api/home").json()
        assert [row["title"] for row in stale["up_next"]] == ["Book club"]
        assert stale["calendar"]["state"] == "stale"
        assert stale["calendar"]["chip"] == "Updated 2 h ago · Calendar unreachable"
        adult = next(card for card in stale["day_cards"] if card["display_name"] == "Adult")
        assert [row["title"] for row in adult["events"]] == ["Book club"]


def test_a_reachable_calendar_with_no_events_is_an_empty_day(tmp_path: Path):
    with _app(tmp_path, calendar=ScriptedCalendar([])) as client:
        client.put("/api/clock", json={"now": NOW})
        assert client.post("/api/calendar/refresh").status_code == 200
        home = client.get("/api/home").json()
        assert home["calendar"]["state"] == "empty"
        assert home["calendar"]["chip"] is None
        assert home["up_next"] == []


def test_a_down_source_with_no_snapshot_is_not_an_empty_day(tmp_path: Path):
    with _app(
        tmp_path,
        weather=ScriptedWeather(None),
        calendar=ScriptedCalendar(None),
    ) as client:
        client.put("/api/clock", json={"now": NOW})
        assert client.post("/api/weather/refresh").status_code == 200
        assert client.post("/api/calendar/refresh").status_code == 200
        home = client.get("/api/home").json()
        assert home["weather"]["state"] == "unknown"
        assert home["weather"]["chip"] == "Weather unreachable"
        assert home["weather"]["temp_f"] is None
        assert home["weather"]["summary"] is None
        assert home["calendar"]["state"] == "unknown"
        assert home["calendar"]["chip"] == "Calendar unreachable"
        assert home["up_next"] == []
        assert "none" not in (home["weather"]["summary"] or "").lower()

        added = client.post(
            "/api/calendar/events",
            json={
                "title": "Soccer pickup",
                "start_local": "2026-10-23T18:00",
                "member_id": "member-adult",
            },
        )
        assert added.status_code == 201
        held = client.get("/api/home").json()
        assert [row["title"] for row in held["up_next"]] == ["Soccer pickup"]
        assert held["calendar"]["state"] == "stale"
        assert held["calendar"]["chip"] == "Calendar unreachable"


def test_a_restart_keeps_the_last_forecast_stale(tmp_path: Path):
    from solomon.clock import AppClock
    from solomon.main import create_app

    db = tmp_path / "solomon.db"
    weather = ScriptedWeather(
        WeatherReport(temp_f=58, high_f=64, low_f=49, summary="Rain after 9 PM")
    )
    clock = AppClock()
    opened = datetime(2026, 10, 23, 19, 0, tzinfo=UTC)
    clock.freeze(opened)
    with TestClient(create_app(db_path=db, clock=clock, weather=weather)) as client:
        assert client.post("/api/weather/refresh").status_code == 200
        weather.report = None
        clock.freeze(opened + timedelta(hours=2))
        assert client.post("/api/weather/refresh").status_code == 200

    restarted = AppClock()
    restarted.freeze(opened + timedelta(hours=2))
    with TestClient(create_app(db_path=db, clock=restarted)) as client:
        weather_card = client.get("/api/home").json()["weather"]
        assert weather_card["state"] == "stale"
        assert weather_card["temp_f"] == 58
        assert weather_card["summary"] == "Rain after 9 PM"
        assert weather_card["chip"] == "Updated 2 h ago · Weather unreachable"
        assert client.get("/api/provider").json()["name"] == "Disabled"
