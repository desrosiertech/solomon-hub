"""News digest through the app API. No model and no live feed."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from solomon.news import HeadlineItem, OfflineNews

NOW = "2026-10-23T21:42:00+00:00"  # 5:42 PM in America/New_York


class ScriptedFeed:
    configured = True

    def __init__(self, items: list[HeadlineItem] | None) -> None:
        self.items = items

    def fetch(self) -> list[HeadlineItem] | None:
        return self.items


def _app(tmp_path: Path, *, feed: ScriptedFeed | None = None):
    from solomon.main import create_app

    app = create_app(db_path=tmp_path / "solomon.db", news=feed)
    return TestClient(app)


def test_news_is_empty_until_headlines_arrive(client):
    client.put("/api/clock", json={"now": NOW})
    digest = client.get("/api/news").json()
    assert digest["state"] == "empty"
    assert digest["chip"] is None
    assert digest["headlines"] == []
    assert client.get("/api/provider").json()["name"] == "Disabled"


def test_stand_in_feed_fills_the_digest_without_a_live_call(client):
    client.put("/api/clock", json={"now": NOW})
    digest = client.post("/api/news/refresh").json()
    assert digest["state"] == "ready"
    assert digest["chip"] is None
    assert [row["title"] for row in digest["headlines"]] == [
        "Town library extends Saturday hours",
        "High school soccer hosts the playoff opener",
        "Weekend rain moves in after dark",
    ]
    assert digest["headlines"][0]["url"] == "https://example.com/library-hours"
    assert digest["headlines"][0]["published_label"] == "11:15 AM"
    assert digest["headlines"][1]["published_label"] == "10:00 AM"
    assert digest["headlines"][2]["published_label"] == "9:40 AM"


def test_refresh_lists_headlines_with_links_and_publication_time(tmp_path: Path):
    feed = ScriptedFeed(
        [
            HeadlineItem(
                title="Town library extends Saturday hours",
                url="https://example.com/library-hours",
                published_at=datetime(2026, 10, 23, 19, 15, tzinfo=UTC),
                source_name="Town desk",
            ),
            HeadlineItem(
                title="High school soccer hosts the playoff opener",
                url="https://example.com/soccer-playoff",
                published_at=datetime(2026, 10, 22, 14, 0, tzinfo=UTC),
                source_name="Sports desk",
            ),
        ]
    )
    with _app(tmp_path, feed=feed) as client:
        client.put("/api/clock", json={"now": NOW})
        digest = client.post("/api/news/refresh").json()
        assert digest["state"] == "ready"
        assert digest["chip"] is None
        assert [row["title"] for row in digest["headlines"]] == [
            "Town library extends Saturday hours",
            "High school soccer hosts the playoff opener",
        ]
        assert digest["headlines"][0]["url"] == "https://example.com/library-hours"
        assert digest["headlines"][0]["published_label"] == "3:15 PM"
        assert digest["headlines"][1]["url"] == "https://example.com/soccer-playoff"
        assert digest["headlines"][1]["published_label"] == "Thu 10:00 AM"
        listed = client.get("/api/news").json()
        assert [row["title"] for row in listed["headlines"]] == [
            "Town library extends Saturday hours",
            "High school soccer hosts the playoff opener",
        ]
        assert client.get("/api/provider").json()["name"] == "Disabled"


def test_refresh_deduplicates_the_same_story(tmp_path: Path):
    feed = ScriptedFeed(
        [
            HeadlineItem(
                title="Town library extends Saturday hours",
                url="https://example.com/library-hours",
                published_at=datetime(2026, 10, 23, 19, 15, tzinfo=UTC),
            ),
            HeadlineItem(
                title="Town library extends Saturday hours",
                url="https://example.com/library-hours/",
                published_at=datetime(2026, 10, 23, 18, 0, tzinfo=UTC),
            ),
            HeadlineItem(
                title="TOWN LIBRARY EXTENDS SATURDAY HOURS",
                url="https://example.com/library-hours-mirror",
                published_at=datetime(2026, 10, 23, 17, 0, tzinfo=UTC),
            ),
            HeadlineItem(
                title="Weekend rain moves in after dark",
                url="https://example.com/weekend-rain",
                published_at=datetime(2026, 10, 23, 16, 0, tzinfo=UTC),
            ),
        ]
    )
    with _app(tmp_path, feed=feed) as client:
        client.put("/api/clock", json={"now": NOW})
        digest = client.post("/api/news/refresh").json()
        assert [row["title"] for row in digest["headlines"]] == [
            "Town library extends Saturday hours",
            "Weekend rain moves in after dark",
        ]
        assert [row["url"] for row in digest["headlines"]] == [
            "https://example.com/library-hours",
            "https://example.com/weekend-rain",
        ]


def test_unreachable_news_keeps_the_last_headlines(tmp_path: Path):
    feed = ScriptedFeed(
        [
            HeadlineItem(
                title="Town library extends Saturday hours",
                url="https://example.com/library-hours",
                published_at=datetime(2026, 10, 23, 19, 15, tzinfo=UTC),
            )
        ]
    )
    with _app(tmp_path, feed=feed) as client:
        client.put("/api/clock", json={"now": "2026-10-23T19:00:00+00:00"})
        assert client.post("/api/news/refresh").status_code == 200
        ready = client.get("/api/news").json()
        assert ready["state"] == "ready"
        assert ready["headlines"][0]["title"] == "Town library extends Saturday hours"
        assert ready["chip"] is None

        feed.items = None
        client.put("/api/clock", json={"now": "2026-10-23T21:00:00+00:00"})
        assert client.post("/api/news/refresh").status_code == 200
        stale = client.get("/api/news").json()
        assert stale["state"] == "stale"
        assert [row["title"] for row in stale["headlines"]] == [
            "Town library extends Saturday hours"
        ]
        assert stale["headlines"][0]["url"] == "https://example.com/library-hours"
        assert stale["chip"] == "Updated 2 h ago · News unreachable"


def test_an_offline_feed_does_not_pretend_to_fetch(tmp_path: Path):
    with _app(tmp_path, feed=OfflineNews()) as client:
        client.put("/api/clock", json={"now": NOW})
        digest = client.post("/api/news/refresh").json()
        assert digest["state"] == "empty"
        assert digest["chip"] is None
        assert digest["headlines"] == []


def test_a_reachable_feed_with_no_headlines_is_empty(tmp_path: Path):
    with _app(tmp_path, feed=ScriptedFeed([])) as client:
        client.put("/api/clock", json={"now": NOW})
        assert client.post("/api/news/refresh").status_code == 200
        digest = client.get("/api/news").json()
        assert digest["state"] == "empty"
        assert digest["chip"] is None
        assert digest["headlines"] == []


def test_a_down_feed_with_no_snapshot_is_not_empty(tmp_path: Path):
    with _app(tmp_path, feed=ScriptedFeed(None)) as client:
        client.put("/api/clock", json={"now": NOW})
        assert client.post("/api/news/refresh").status_code == 200
        digest = client.get("/api/news").json()
        assert digest["state"] == "unknown"
        assert digest["chip"] == "News unreachable"
        assert digest["headlines"] == []
        assert "none" not in (digest.get("empty_label") or "").lower()


def test_a_restart_keeps_the_last_headlines_stale(tmp_path: Path):
    from solomon.clock import AppClock
    from solomon.main import create_app

    db = tmp_path / "solomon.db"
    feed = ScriptedFeed(
        [
            HeadlineItem(
                title="Town library extends Saturday hours",
                url="https://example.com/library-hours",
                published_at=datetime(2026, 10, 23, 19, 15, tzinfo=UTC),
            )
        ]
    )
    clock = AppClock()
    opened = datetime(2026, 10, 23, 19, 0, tzinfo=UTC)
    clock.freeze(opened)
    with TestClient(create_app(db_path=db, clock=clock, news=feed)) as client:
        assert client.post("/api/news/refresh").status_code == 200
        feed.items = None
        clock.freeze(opened + timedelta(hours=2))
        assert client.post("/api/news/refresh").status_code == 200

    restarted = AppClock()
    restarted.freeze(opened + timedelta(hours=2))
    with TestClient(create_app(db_path=db, clock=restarted)) as client:
        digest = client.get("/api/news").json()
        assert digest["state"] == "stale"
        assert [row["title"] for row in digest["headlines"]] == [
            "Town library extends Saturday hours"
        ]
        assert digest["chip"] == "Updated 2 h ago · News unreachable"
        assert client.get("/api/provider").json()["name"] == "Disabled"
