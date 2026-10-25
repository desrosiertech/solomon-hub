"""Spooktober diary through the app API. No model and no streaming service.

Seams:
- GET /api/spooktober is the diary the page renders: a year chart, every movie,
  and the chosen best-of list. An empty diary stays empty.
- SpooktoberStore.record_watch is how a watch gets into that diary. Tests seed
  rows there. The page has no add-movie form, and chat does not parse one.
"""

import pytest

NOW = "2026-10-23T21:42:00+00:00"  # 5:42 PM in America/New_York
DESROSIER = "member-desrosier"
PETER = "member-peter"


def test_empty_diary_has_nothing_to_show(client):
    client.put("/api/clock", json={"now": NOW})
    diary = client.get("/api/spooktober").json()
    assert diary == {
        "empty": True,
        "year": 2026,
        "chart": [],
        "movies": [],
        "best_of": [],
    }
    assert client.get("/api/provider").json()["name"] == "Disabled"


def test_peter_and_desrosier_each_score_the_movie_and_the_scare(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    journal.record_watch(
        title="The Witch",
        member_id=DESROSIER,
        watched_on="2026-10-03",
        rating=9,
        spook=10,
        notes="Still the one we quote.",
    )
    journal.record_watch(
        title="The Witch",
        member_id=PETER,
        watched_on="2026-10-04",
        rating=8,
        spook=9,
        notes="The goat still gets me.",
    )
    movie = client.get("/api/spooktober").json()["movies"][0]
    assert movie["watched_on"] == "2026-10-04"
    assert movie["watched_label"] == "October 4"
    assert movie["best_of"] is False
    assert movie["people"] == [
        {
            "member_id": DESROSIER,
            "display_name": "Desrosier",
            "initial": "D",
            "rating": 9,
            "spook": 10,
            "notes": "Still the one we quote.",
            "watched_on": "2026-10-03",
        },
        {
            "member_id": PETER,
            "display_name": "Peter",
            "initial": "P",
            "rating": 8,
            "spook": 9,
            "notes": "The goat still gets me.",
            "watched_on": "2026-10-04",
        },
    ]


def test_best_of_is_chosen_not_the_highest_scores(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    journal.record_watch(
        title="Coraline",
        member_id=DESROSIER,
        watched_on="2026-10-24",
        rating=10,
        spook=10,
        best_of=False,
    )
    journal.record_watch(
        title="The Witch",
        member_id=DESROSIER,
        watched_on="2026-10-03",
        rating=6,
        spook=6,
        best_of=True,
    )
    journal.record_watch(
        title="The Witch",
        member_id=PETER,
        watched_on="2026-10-03",
        rating=6,
        spook=7,
    )
    diary = client.get("/api/spooktober").json()
    assert [movie["title"] for movie in diary["movies"]] == ["Coraline", "The Witch"]
    assert [movie["title"] for movie in diary["best_of"]] == ["The Witch"]
    assert diary["best_of"][0]["people"][0]["rating"] == 6
    assert diary["best_of"][0]["people"][0]["spook"] == 6


def test_year_chart_keeps_an_empty_year_and_lists_every_movie(client):
    client.put("/api/clock", json={"now": NOW})
    client.app.state.journal.seed_sample()
    diary = client.get("/api/spooktober").json()
    assert diary["empty"] is False
    assert diary["chart"] == [
        {"year": 2024, "count": 1},
        {"year": 2025, "count": 0},
        {"year": 2026, "count": 2},
    ]
    assert [movie["title"] for movie in diary["movies"]] == ["Coraline", "Halloween", "The Witch"]
    assert [movie["title"] for movie in diary["best_of"]] == ["Halloween", "The Witch"]
    coraline = diary["movies"][0]
    assert coraline["best_of"] is False
    assert [(person["display_name"], person["rating"], person["spook"]) for person in coraline["people"]] == [
        ("Desrosier", 10, 6),
        ("Peter", 6, 4),
    ]
    witch = next(movie for movie in diary["best_of"] if movie["title"] == "The Witch")
    assert [(person["display_name"], person["rating"], person["spook"]) for person in witch["people"]] == [
        ("Desrosier", 9, 10),
        ("Peter", 8, 9),
    ]


def test_recording_again_replaces_that_persons_scores(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    journal.record_watch(
        title="The Witch",
        member_id=DESROSIER,
        watched_on="2026-10-03",
        rating=4,
        spook=4,
        notes="First pass.",
    )
    journal.record_watch(
        title="The Witch",
        member_id=DESROSIER,
        watched_on="2026-10-05",
        rating=9,
        spook=8,
        notes="Still the one we quote.",
        best_of=True,
    )
    diary = client.get("/api/spooktober").json()
    assert diary["movies"][0]["people"] == [
        {
            "member_id": DESROSIER,
            "display_name": "Desrosier",
            "initial": "D",
            "rating": 9,
            "spook": 8,
            "notes": "Still the one we quote.",
            "watched_on": "2026-10-05",
        }
    ]
    assert [movie["title"] for movie in diary["best_of"]] == ["The Witch"]


def test_a_score_outside_one_to_ten_is_refused(client):
    client.put("/api/clock", json={"now": NOW})
    journal = client.app.state.journal
    with pytest.raises(ValueError):
        journal.record_watch(
            title="Nope",
            member_id=DESROSIER,
            watched_on="2026-10-11",
            rating=11,
            spook=5,
        )
    with pytest.raises(ValueError):
        journal.record_watch(
            title="Nope",
            member_id=DESROSIER,
            watched_on="2026-10-11",
            rating=5,
            spook=0,
        )
    assert client.get("/api/spooktober").json()["empty"] is True


def test_only_peter_and_desrosier_are_on_the_diary(client):
    client.put("/api/clock", json={"now": NOW})
    with pytest.raises(ValueError):
        client.app.state.journal.record_watch(
            title="Nope",
            member_id="member-adult",
            watched_on="2026-10-11",
            rating=8,
            spook=8,
        )
    assert client.get("/api/spooktober").json()["empty"] is True
