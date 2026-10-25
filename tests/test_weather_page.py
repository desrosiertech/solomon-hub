"""Weather page through the app API. No model and no outside service."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from solomon.board import WeatherReport

NOW = "2026-10-23T21:42:00+00:00"  # 5:42 PM in America/New_York


class ScriptedWeather:
    configured = True

    def __init__(self, report: WeatherReport | None) -> None:
        self.report = report

    def fetch(self) -> WeatherReport | None:
        return self.report


def _app(tmp_path: Path, weather: ScriptedWeather):
    from solomon.main import create_app

    return TestClient(create_app(db_path=tmp_path / "solomon.db", weather=weather))


def test_weather_page_is_empty_until_a_forecast_is_fetched(client):
    client.put("/api/clock", json={"now": NOW})
    page = client.get("/api/weather").json()
    assert page["place"] == "Home"
    assert page["date_label"] == "Friday, October 23"
    assert page["state"] == "empty"
    assert page["chip"] is None
    assert page["temp_f"] is None
    assert page["high_f"] is None
    assert page["low_f"] is None
    assert page["summary"] is None
    assert client.get("/api/provider").json()["name"] == "Disabled"


def test_weather_page_shows_the_home_forecast(tmp_path: Path):
    weather = ScriptedWeather(
        WeatherReport(temp_f=58, high_f=64, low_f=49, summary="Rain after 9 PM")
    )
    with _app(tmp_path, weather) as client:
        client.put("/api/clock", json={"now": NOW})
        assert client.post("/api/weather/refresh").status_code == 200
        page = client.get("/api/weather").json()
        assert page["place"] == "Home"
        assert page["date_label"] == "Friday, October 23"
        assert page["state"] == "ready"
        assert page["chip"] is None
        assert page["temp_f"] == 58
        assert page["high_f"] == 64
        assert page["low_f"] == 49
        assert page["summary"] == "Rain after 9 PM"
        assert client.get("/api/provider").json()["name"] == "Disabled"


def test_unreachable_weather_keeps_the_last_forecast_on_the_page(tmp_path: Path):
    weather = ScriptedWeather(
        WeatherReport(temp_f=58, high_f=64, low_f=49, summary="Rain after 9 PM")
    )
    with _app(tmp_path, weather) as client:
        client.put("/api/clock", json={"now": "2026-10-23T19:00:00+00:00"})
        assert client.post("/api/weather/refresh").status_code == 200
        weather.report = None
        client.put("/api/clock", json={"now": "2026-10-23T21:00:00+00:00"})
        assert client.post("/api/weather/refresh").status_code == 200
        page = client.get("/api/weather").json()
        assert page["place"] == "Home"
        assert page["state"] == "stale"
        assert page["temp_f"] == 58
        assert page["high_f"] == 64
        assert page["low_f"] == 49
        assert page["summary"] == "Rain after 9 PM"
        assert page["chip"] == "Updated 2 h ago · Weather unreachable"
        assert "none" not in (page["summary"] or "").lower()
        assert client.get("/api/home").json()["weather"]["chip"] == page["chip"]


def test_a_down_source_with_no_snapshot_is_not_an_empty_forecast(tmp_path: Path):
    with _app(tmp_path, ScriptedWeather(None)) as client:
        client.put("/api/clock", json={"now": NOW})
        assert client.post("/api/weather/refresh").status_code == 200
        page = client.get("/api/weather").json()
        assert page["place"] == "Home"
        assert page["state"] == "unknown"
        assert page["chip"] == "Weather unreachable"
        assert page["temp_f"] is None
        assert page["summary"] is None
        assert "none" not in (page["summary"] or "").lower()
        home = client.get("/api/home").json()["weather"]
        assert home["state"] == "unknown"
        assert home["chip"] == page["chip"]


def test_a_restart_keeps_the_last_forecast_on_the_page(tmp_path: Path):
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
        page = client.get("/api/weather").json()
        assert page["place"] == "Home"
        assert page["state"] == "stale"
        assert page["temp_f"] == 58
        assert page["summary"] == "Rain after 9 PM"
        assert page["chip"] == "Updated 2 h ago · Weather unreachable"
        assert client.get("/api/provider").json()["name"] == "Disabled"
