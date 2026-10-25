"""Spooktober diary through the app API. No model and no streaming service.

Seams:
- GET /api/spooktober is the diary the page renders: counts, favorites, recent
  entries, year comparison, and an empty diary. It does not cover chat wording.
- SpooktoberStore.record_watch is how a watch gets into that diary. Tests seed
  rows there. The page has no add-movie form.
"""

import pytest

NOW = "2026-10-23T21:42:00+00:00"  # 5:42 PM in America/New_York


def test_empty_diary_has_nothing_to_show(client):
    client.put("/api/clock", json={"now": NOW})
    diary = client.get("/api/spooktober").json()
    assert diary == {
        "empty": True,
        "year": 2026,
        "annual_count": 0,
        "favorites": [],
        "recent": [],
        "comparison": [
            {"year": 2026, "count": 0},
            {"year": 2025, "count": 0},
        ],
    }
    assert client.get("/api/provider").json()["name"] == "Disabled"


def test_a_recorded_watch_shows_its_date_rating_and_note(client):
    client.put("/api/clock", json={"now": NOW})
    client.app.state.journal.record_watch(
        title="The Witch",
        member_id="member-adult",
        watched_on="2026-10-03",
        rating=3,
        notes="Still the one we quote.",
    )
    diary = client.get("/api/spooktober").json()
    assert diary["empty"] is False
    assert diary["year"] == 2026
    assert diary["annual_count"] == 1
    assert diary["favorites"] == []
    assert diary["recent"] == [
        {
            "title": "The Witch",
            "watched_on": "2026-10-03",
            "watched_label": "October 3",
            "people": [
                {
                    "member_id": "member-adult",
                    "display_name": "Adult",
                    "initial": "A",
                    "rating": 3,
                    "notes": "Still the one we quote.",
                    "watched_on": "2026-10-03",
                }
            ],
        }
    ]
    assert diary["comparison"] == [
        {"year": 2026, "count": 1},
        {"year": 2025, "count": 0},
    ]


def test_only_a_five_star_rating_is_a_favorite(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    journal.record_watch(
        title="The Witch",
        member_id="member-adult",
        watched_on="2026-10-03",
        rating=5,
        notes="Still the one we quote.",
    )
    journal.record_watch(
        title="Halloween",
        member_id="member-adult",
        watched_on="2026-10-17",
        rating=4,
        notes="The walk home was the good part.",
    )
    diary = client.get("/api/spooktober").json()
    assert diary["annual_count"] == 2
    assert diary["favorites"] == [{"title": "The Witch", "people": ["Adult"]}]


def test_two_people_keep_their_own_rating_date_and_note(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    journal.record_watch(
        title="The Witch",
        member_id="member-adult",
        watched_on="2026-10-03",
        rating=5,
        notes="Still the one we quote.",
    )
    journal.record_watch(
        title="The Witch",
        member_id="member-blair",
        display_name="Blair",
        watched_on="2026-10-04",
        rating=4,
        notes="Too quiet, then it isn't.",
    )
    diary = client.get("/api/spooktober").json()
    assert diary["annual_count"] == 1
    assert diary["recent"] == [
        {
            "title": "The Witch",
            "watched_on": "2026-10-04",
            "watched_label": "October 4",
            "people": [
                {
                    "member_id": "member-adult",
                    "display_name": "Adult",
                    "initial": "A",
                    "rating": 5,
                    "notes": "Still the one we quote.",
                    "watched_on": "2026-10-03",
                },
                {
                    "member_id": "member-blair",
                    "display_name": "Blair",
                    "initial": "B",
                    "rating": 4,
                    "notes": "Too quiet, then it isn't.",
                    "watched_on": "2026-10-04",
                },
            ],
        }
    ]
    assert diary["favorites"] == [{"title": "The Witch", "people": ["Adult"]}]


def test_recent_entries_list_the_newest_watch_first(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    journal.record_watch(
        title="The Witch",
        member_id="member-adult",
        watched_on="2026-10-03",
        rating=5,
    )
    journal.record_watch(
        title="Coraline",
        member_id="member-adult",
        watched_on="2026-10-24",
        rating=5,
    )
    journal.record_watch(
        title="Halloween",
        member_id="member-adult",
        watched_on="2026-10-17",
        rating=4,
    )
    diary = client.get("/api/spooktober").json()
    assert [movie["title"] for movie in diary["recent"]] == ["Coraline", "Halloween", "The Witch"]
    assert [movie["watched_label"] for movie in diary["recent"]] == [
        "October 24",
        "October 17",
        "October 3",
    ]
    assert diary["favorites"] == [
        {"title": "Coraline", "people": ["Adult"]},
        {"title": "The Witch", "people": ["Adult"]},
    ]


def test_last_spooktober_is_a_count_beside_this_year(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    journal.record_watch(
        title="Hocus Pocus",
        member_id="member-adult",
        watched_on="2025-10-18",
        rating=5,
        notes="We know every song.",
    )
    journal.record_watch(
        title="Halloween",
        member_id="member-adult",
        watched_on="2026-10-17",
        rating=4,
        notes="The walk home was the good part.",
    )
    diary = client.get("/api/spooktober").json()
    assert diary["empty"] is False
    assert diary["annual_count"] == 1
    assert [movie["title"] for movie in diary["recent"]] == ["Halloween"]
    assert diary["favorites"] == []
    assert diary["comparison"] == [
        {"year": 2026, "count": 1},
        {"year": 2025, "count": 1},
    ]


def test_recording_a_watch_again_replaces_that_persons_line(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    journal.record_watch(
        title="The Witch",
        member_id="member-adult",
        watched_on="2026-10-03",
        rating=3,
        notes="First pass.",
    )
    journal.record_watch(
        title="The Witch",
        member_id="member-adult",
        watched_on="2026-10-05",
        rating=5,
        notes="Still the one we quote.",
    )
    diary = client.get("/api/spooktober").json()
    assert diary["annual_count"] == 1
    assert diary["recent"][0]["people"] == [
        {
            "member_id": "member-adult",
            "display_name": "Adult",
            "initial": "A",
            "rating": 5,
            "notes": "Still the one we quote.",
            "watched_on": "2026-10-05",
        }
    ]
    assert diary["favorites"] == [{"title": "The Witch", "people": ["Adult"]}]


def test_a_rating_outside_one_to_five_is_refused(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    with pytest.raises(ValueError):
        journal.record_watch(
            title="Nope",
            member_id="member-adult",
            watched_on="2026-10-11",
            rating=6,
        )
    assert client.get("/api/spooktober").json()["empty"] is True
