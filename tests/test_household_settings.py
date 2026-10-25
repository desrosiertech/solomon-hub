"""Household preferences through the app API. No pixels, no tokens."""

from pathlib import Path

from fastapi.testclient import TestClient


def test_household_starts_with_a_placeholder_adult_and_pantry_defaults(client):
    body = client.get("/api/household").json()

    assert body == {
        "adults": [{"id": "member-adult", "display_name": "Adult"}],
        "storage_locations": ["Fridge", "Pantry", "Freezer", "Counter"],
        "freshness": "conservative",
        "suppression_days": 7,
        "presumed_discard": "archive",
        "serving_size": 2,
        "news_topics": [],
    }
    assert "token" not in body
    assert "password" not in body


SAVED = {
    "adults": [
        {"id": "member-adult", "display_name": "Alex"},
        {"display_name": "Jordan"},
    ],
    "storage_locations": ["Fridge", "Pantry", "Garage fridge"],
    "freshness": "permissive",
    "suppression_days": 14,
    "presumed_discard": "review",
    "serving_size": 3,
    "news_topics": ["local government", "school board"],
}


def _app(db_path: Path) -> TestClient:
    from solomon.main import create_app

    return TestClient(create_app(db_path=db_path))


def test_saved_household_preferences_are_still_there_after_restart(tmp_path: Path):
    db_path = tmp_path / "solomon.db"
    with _app(db_path) as first:
        saved = first.put("/api/household", json=SAVED)
        assert saved.status_code == 200
        body = saved.json()
        assert [adult["display_name"] for adult in body["adults"]] == ["Alex", "Jordan"]
        assert body["adults"][0]["id"] == "member-adult"
        assert body["adults"][1]["id"].startswith("member_")
        assert set(body["adults"][1]) == {"id", "display_name"}
        assert body["storage_locations"] == ["Fridge", "Pantry", "Garage fridge"]
        assert body["freshness"] == "permissive"
        assert body["suppression_days"] == 14
        assert body["presumed_discard"] == "review"
        assert body["serving_size"] == 3
        assert body["news_topics"] == ["local government", "school board"]
        remembered = body

    with _app(db_path) as second:
        assert second.get("/api/household").json() == remembered


def test_household_preferences_do_not_accept_a_token(client):
    refused = client.put(
        "/api/household",
        json={**SAVED, "token": "secret-token", "password": "secret-token"},
    )
    assert refused.status_code == 400
    assert "secret-token" not in refused.text

    adult = client.put(
        "/api/household",
        json={
            **SAVED,
            "adults": [{"id": "member-adult", "display_name": "Alex", "password": "secret-token"}],
        },
    )
    assert adult.status_code == 400
    assert "secret-token" not in adult.text

    body = client.get("/api/household").json()
    assert body["adults"] == [{"id": "member-adult", "display_name": "Adult"}]
    assert "secret-token" not in str(body)


def test_permissive_freshness_lengthens_the_estimated_use_by_window(client):
    client.put("/api/clock", json={"now": "2026-10-20T12:00:00+00:00"})
    saved = client.put(
        "/api/household",
        json={
            "adults": [{"id": "member-adult", "display_name": "Adult"}],
            "storage_locations": ["Fridge", "Pantry", "Freezer", "Counter"],
            "freshness": "permissive",
            "suppression_days": 7,
            "presumed_discard": "archive",
            "serving_size": 2,
            "news_topics": [],
        },
    )
    assert saved.status_code == 200

    spinach = client.post(
        "/api/inventory",
        json={
            "label": "Spinach",
            "category": "leafy_greens",
            "storage": "fridge",
            "quantity_kind": "one_package",
        },
    )
    assert spinach.status_code == 201
    assert spinach.json()["estimated_use_by"].startswith("2026-10-26T12:00:00")
    assert spinach.json()["window_explain"] == (
        "Fridge · leafy greens · bought Oct 20 · about 6 days"
    )


def test_review_holds_a_stale_item_instead_of_marking_it_presumed_discarded(client):
    assert (
        client.put(
            "/api/household",
            json={
                "adults": [{"id": "member-adult", "display_name": "Adult"}],
                "storage_locations": ["Fridge", "Pantry", "Freezer", "Counter"],
                "freshness": "conservative",
                "suppression_days": 7,
                "presumed_discard": "review",
                "serving_size": 2,
                "news_topics": [],
            },
        ).status_code
        == 200
    )
    assert (
        client.put(
            "/api/settings",
            json={"grace_period_minutes": 10, "presume_after_minutes": 10},
        ).status_code
        == 200
    )
    client.put("/api/clock", json={"now": "2026-10-20T12:00:00+00:00"})
    spinach = client.post(
        "/api/inventory",
        json={
            "label": "Spinach",
            "category": "leafy_greens",
            "storage": "fridge",
            "quantity_kind": "one_package",
        },
    )
    assert spinach.status_code == 201

    # Conservative leafy window ends 2026-10-24 12:00. Archive would presume at +20 minutes.
    client.put("/api/clock", json={"now": "2026-10-24T12:20:00+00:00"})
    client.post("/api/jobs/age")
    items = {row["id"]: row for row in client.get("/api/inventory").json()["items"]}
    assert items[spinach.json()["id"]]["state"] == "stale"
    assert items[spinach.json()["id"]]["closed_reason"] is None
    actions = [event["action"] for event in client.get("/api/audit").json()["events"]]
    assert "inventory.presumed_discarded" not in actions


def test_an_older_database_still_reads_the_placeholder_household(tmp_path: Path):
    import sqlite3

    db_path = tmp_path / "old.db"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE household (
            id VARCHAR PRIMARY KEY,
            profile VARCHAR,
            grace_period_minutes INTEGER,
            presume_after_minutes INTEGER,
            ideas_generated_at DATETIME,
            ideas_json TEXT
        );
        CREATE TABLE member (
            id VARCHAR PRIMARY KEY,
            display_name VARCHAR,
            role VARCHAR
        );
        INSERT INTO household (id, profile, grace_period_minutes, presume_after_minutes)
        VALUES ('household-1', 'conservative', 4320, 5760);
        INSERT INTO member (id, display_name, role)
        VALUES ('member-adult', 'Adult', 'adult');
        """
    )
    connection.commit()
    connection.close()

    with _app(db_path) as client:
        assert client.get("/api/household").json() == {
            "adults": [{"id": "member-adult", "display_name": "Adult"}],
            "storage_locations": ["Fridge", "Pantry", "Freezer", "Counter"],
            "freshness": "conservative",
            "suppression_days": 7,
            "presumed_discard": "archive",
            "serving_size": 2,
            "news_topics": [],
        }


def test_renamed_adults_are_the_names_on_the_calendar_day(client):
    client.put("/api/clock", json={"now": "2026-10-23T21:42:00+00:00"})
    saved = client.put("/api/household", json=SAVED)
    assert saved.status_code == 200
    names = {adult["display_name"] for adult in saved.json()["adults"]}

    day = client.get("/api/calendar/day").json()
    cards = {card["display_name"] for card in day["day_cards"]}
    assert names <= cards
    assert "Adult" not in cards
    assert "Everyone" in cards
