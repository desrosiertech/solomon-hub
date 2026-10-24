"""Calendar day page through the app API. No model and no outside service."""

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from solomon.board import ExternalEvent

NOW = "2026-10-23T21:42:00+00:00"  # 5:42 PM in America/New_York


class ScriptedCalendar:
    configured = True

    def __init__(self, events: list[ExternalEvent] | None) -> None:
        self.events = events

    def fetch(self) -> list[ExternalEvent] | None:
        return self.events


def _app(tmp_path: Path, calendar: ScriptedCalendar):
    from solomon.main import create_app

    return TestClient(create_app(db_path=tmp_path / "solomon.db", calendar=calendar))


def test_calendar_day_shows_that_day_for_each_member(client):
    client.put("/api/clock", json={"now": NOW})
    assert (
        client.post(
            "/api/calendar/events",
            json={
                "title": "Dentist",
                "start_local": "2026-10-23T09:00",
                "end_local": "2026-10-23T10:00",
                "member_id": "member-adult",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/calendar/events",
            json={
                "title": "Soccer pickup",
                "start_local": "2026-10-23T18:00",
                "location": "Field 3",
                "member_id": "member-adult",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/calendar/events",
            json={"title": "Pumpkin patch", "start_local": "2026-10-24T10:00"},
        ).status_code
        == 201
    )

    friday = client.get("/api/calendar/day", params={"on": "2026-10-23"}).json()
    assert friday["on"] == "2026-10-23"
    assert friday["date_label"] == "Friday, October 23"
    assert friday["prev"] == "2026-10-22"
    assert friday["next"] == "2026-10-24"
    assert friday["is_today"] is True
    assert friday["calendar"]["state"] == "ready"
    assert friday["calendar"]["chip"] is None
    adult = next(card for card in friday["day_cards"] if card["display_name"] == "Adult")
    assert [row["title"] for row in adult["events"]] == ["Dentist", "Soccer pickup"]
    assert [row["when_label"] for row in adult["events"]] == ["9:00 AM", "6:00 PM"]
    assert adult["events"][1]["location"] == "Field 3"
    everyone = next(card for card in friday["day_cards"] if card["display_name"] == "Everyone")
    assert everyone["events"] == []

    saturday = client.get("/api/calendar/day", params={"on": "2026-10-24"}).json()
    assert saturday["date_label"] == "Saturday, October 24"
    assert saturday["is_today"] is False
    assert saturday["calendar"]["state"] == "ready"
    adult_saturday = next(card for card in saturday["day_cards"] if card["display_name"] == "Adult")
    assert adult_saturday["events"] == []
    everyone_saturday = next(
        card for card in saturday["day_cards"] if card["display_name"] == "Everyone"
    )
    assert [row["title"] for row in everyone_saturday["events"]] == ["Pumpkin patch"]
    assert everyone_saturday["events"][0]["when_label"] == "10:00 AM"


def test_a_clear_day_is_empty(client):
    client.put("/api/clock", json={"now": NOW})
    day = client.get("/api/calendar/day").json()
    assert day["on"] == "2026-10-23"
    assert day["date_label"] == "Friday, October 23"
    assert day["calendar"]["state"] == "empty"
    assert day["calendar"]["chip"] is None
    assert day["day_cards"]
    assert all(card["events"] == [] for card in day["day_cards"])


def test_unreachable_calendar_keeps_fridays_events_and_marks_saturday_stale(tmp_path: Path):
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
    with _app(tmp_path, calendar) as client:
        client.put("/api/clock", json={"now": "2026-10-23T21:00:00+00:00"})
        assert client.post("/api/calendar/refresh").status_code == 200
        calendar.events = None
        client.put("/api/clock", json={"now": "2026-10-23T23:00:00+00:00"})
        assert client.post("/api/calendar/refresh").status_code == 200

        friday = client.get("/api/calendar/day", params={"on": "2026-10-23"}).json()
        assert friday["calendar"]["state"] == "stale"
        assert friday["calendar"]["chip"] == "Updated 2 h ago · Calendar unreachable"
        adult = next(card for card in friday["day_cards"] if card["display_name"] == "Adult")
        assert [row["title"] for row in adult["events"]] == ["Book club"]
        assert adult["events"][0]["when_label"] == "7:30 PM"

        saturday = client.get("/api/calendar/day", params={"on": "2026-10-24"}).json()
        assert saturday["calendar"]["state"] == "stale"
        assert saturday["calendar"]["chip"] == "Updated 2 h ago · Calendar unreachable"
        assert all(card["events"] == [] for card in saturday["day_cards"])


def test_a_down_calendar_with_no_snapshot_is_not_an_empty_day(tmp_path: Path):
    with _app(tmp_path, ScriptedCalendar(None)) as client:
        client.put("/api/clock", json={"now": NOW})
        assert client.post("/api/calendar/refresh").status_code == 200
        day = client.get("/api/calendar/day", params={"on": "2026-10-23"}).json()
        assert day["calendar"]["state"] == "unknown"
        assert day["calendar"]["chip"] == "Calendar unreachable"
        assert all(card["events"] == [] for card in day["day_cards"])
        assert client.get("/api/provider").json()["name"] == "Disabled"


def test_a_bad_day_is_rejected(client):
    response = client.get("/api/calendar/day", params={"on": "friday"})
    assert response.status_code == 400
