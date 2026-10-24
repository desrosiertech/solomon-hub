"""Same food-engine behaviour through the app API the UI will call. No model."""

from datetime import UTC, datetime

ACQUIRED = "2026-10-20T12:00:00+00:00"


def _add_three(client):
    client.put("/api/clock", json={"now": ACQUIRED})
    spinach = client.post(
        "/api/inventory",
        json={
            "label": "Spinach",
            "category": "leafy_greens",
            "storage": "fridge",
            "quantity_kind": "one_package",
        },
    )
    chili = client.post(
        "/api/inventory",
        json={
            "label": "Leftover chili",
            "category": "cooked_leftovers",
            "leftover": True,
            "storage": "fridge",
            "quantity_kind": "count",
            "quantity_count": 2,
        },
    )
    eggs = client.post(
        "/api/inventory",
        json={
            "label": "Eggs",
            "category": "unknown",
            "storage": "pantry",
            "quantity_kind": "count",
            "quantity_count": 6,
        },
    )
    assert spinach.status_code == 201
    assert chili.status_code == 201
    assert eggs.status_code == 201
    return spinach.json(), chili.json(), eggs.json()


def test_provider_is_disabled():
    from solomon.provider import DisabledProvider, ModelProvider

    provider: ModelProvider = DisabledProvider()
    assert provider.name == "Disabled"


def test_member_adds_three_items_each_with_an_estimated_use_by_window(client):
    spinach, chili, eggs = _add_three(client)
    assert client.get("/api/provider").json()["name"] == "Disabled"

    items = {row["label"]: row for row in client.get("/api/inventory").json()["items"]}
    assert set(items) == {"Spinach", "Leftover chili", "Eggs"}
    assert items["Spinach"]["estimated_use_by"].startswith("2026-10-24T12:00:00")
    assert items["Spinach"]["window_explain"] == (
        "Fridge · leafy greens · bought Oct 20 · about 4 days"
    )
    assert items["Spinach"]["window_label"] == "Estimated use-by window"
    assert items["Leftover chili"]["window_explain"] == (
        "Fridge · cooked leftovers · bought Oct 20 · about 2.4 days"
    )
    assert items["Leftover chili"]["leftover"] is True
    assert items["Eggs"]["window_explain"].startswith("Pantry · unknown · bought Oct 20")
    assert spinach["id"] and chili["id"] and eggs["id"]


def test_home_and_meals_show_up_to_three_ideas_and_use_soon(client):
    _add_three(client)
    # Oct 23 12:00: spinach enters use_soon; leftover chili is past its 2.4-day window.
    client.put("/api/clock", json={"now": "2026-10-23T12:00:00+00:00"})

    home = client.get("/api/home").json()
    meals = client.get("/api/meals").json()
    assert len(home["ideas"]) <= 3
    assert len(meals["ideas"]) <= 3
    assert {idea["title"] for idea in home["ideas"]} == {
        "Greens with leftovers",
        "Leftover chili bowl",
        "Sautéed greens",
    }
    assert home["ideas"] == meals["ideas"]
    use_soon_titles = [row["title"] for row in home["use_soon"]]
    assert use_soon_titles == ["Leftover chili", "Spinach"]
    assert home["use_soon"] == meals["use_soon"]
    assert "may be past its expected freshness window" in home["use_soon"][0]["detail"]
    assert meals["ideas_card"]["state"] == "ready"


def test_stop_asking_suppresses_that_suggestion_after_reload(client):
    _add_three(client)
    client.put("/api/clock", json={"now": "2026-10-23T12:00:00+00:00"})
    home = client.get("/api/home").json()
    spinach = next(row for row in home["use_soon"] if row["title"] == "Spinach")

    stopped = client.post("/api/suggestions/stop-asking", json={"key": spinach["key"]})
    assert stopped.status_code == 204

    home_again = client.get("/api/home").json()
    meals_again = client.get("/api/meals").json()
    assert "Spinach" not in [row["title"] for row in home_again["use_soon"]]
    assert "Spinach" not in [row["title"] for row in meals_again["use_soon"]]
    assert "Leftover chili" in [row["title"] for row in home_again["use_soon"]]


def test_unresolved_item_becomes_stale_then_presumed_discarded_never_eaten(client):
    client.put(
        "/api/settings",
        json={"grace_period_minutes": 10, "presume_after_minutes": 10},
    )
    spinach, _, _ = _add_three(client)
    # Leafy window ends 2026-10-24 12:00. Stale at +10m; presumed discarded at +20m.
    client.put("/api/clock", json={"now": "2026-10-24T12:10:00+00:00"})
    client.post("/api/jobs/age")
    items = {row["id"]: row for row in client.get("/api/inventory").json()["items"]}
    assert items[spinach["id"]]["state"] == "stale"

    client.put("/api/clock", json={"now": "2026-10-24T12:20:00+00:00"})
    client.post("/api/jobs/age")
    items = {row["id"]: row for row in client.get("/api/inventory").json()["items"]}
    assert items[spinach["id"]]["state"] == "presumed_discarded"
    assert items[spinach["id"]]["closed_reason"] == "presumed_discarded"
    body = str(items[spinach["id"]]).lower()
    assert "eaten" not in body
    assert "consumed" not in body


def test_audit_records_add_suppress_and_presumed_discard(client):
    client.put(
        "/api/settings",
        json={"grace_period_minutes": 10, "presume_after_minutes": 10},
    )
    spinach, _, _ = _add_three(client)
    client.put("/api/clock", json={"now": "2026-10-23T12:00:00+00:00"})
    home = client.get("/api/home").json()
    spinach_line = next(row for row in home["use_soon"] if row["title"] == "Spinach")
    client.post("/api/suggestions/stop-asking", json={"key": spinach_line["key"]})
    client.put("/api/clock", json={"now": "2026-10-24T12:20:00+00:00"})
    client.post("/api/jobs/age")

    events = client.get("/api/audit").json()["events"]
    actions = [event["action"] for event in events]
    assert actions.count("inventory.added") == 3
    assert "suggestion.stop_asking" in actions
    assert "inventory.presumed_discarded" in actions
    presumed = next(
        e
        for e in events
        if e["action"] == "inventory.presumed_discarded"
        and e["subject_id"] == spinach["id"]
    )
    assert presumed["actor_kind"] == "job"
    assert presumed["actor_id"] == "job:aging"
    assert presumed["at"]
    added = next(e for e in events if e["action"] == "inventory.added")
    assert added["actor_kind"] == "member"
    assert added["at"]


def test_meals_ideas_card_empty_when_inventory_is_empty(client):
    meals = client.get("/api/meals").json()
    assert meals["ideas"] == []
    assert meals["ideas_card"]["state"] == "empty"


def test_meals_ideas_card_is_stale_after_two_hours_without_a_refresh(client):
    _add_three(client)
    client.put("/api/clock", json={"now": "2026-10-23T12:00:00+00:00"})
    assert client.get("/api/meals").json()["ideas_card"]["state"] == "ready"

    client.put("/api/clock", json={"now": "2026-10-23T14:00:00+00:00"})
    meals = client.get("/api/meals").json()
    assert meals["ideas_card"]["state"] == "stale"
    assert meals["ideas"]
    generated = datetime.fromisoformat(meals["ideas_card"]["generated_at"])
    assert generated.astimezone(UTC) == datetime(2026, 10, 23, 12, 0, tzinfo=UTC)
    assert datetime.fromisoformat(meals["ideas_card"]["now"]).astimezone(UTC) == datetime(
        2026, 10, 23, 14, 0, tzinfo=UTC
    )
