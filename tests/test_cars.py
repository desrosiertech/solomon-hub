"""Cars are household records. Tests create them; the page only reads.

Seams:
- GET /api/cars is the display payload (nickname, maintenance, missing-field lines).
- POST creates a car or a maintenance event for tests and later chat. It never fills in a due date.
- PATCH is a Correction. The prior value stays on the export.
- GET /api/cars/export is the records as JSON.
"""

def test_a_named_car_lists_missing_service_dates_and_invents_no_due_date(client):
    created = client.post("/api/cars", json={"nickname": "Blue"})
    assert created.status_code == 201
    car_id = created.json()["id"]

    page = client.get("/api/cars")
    assert page.status_code == 200
    assert page.json() == {
        "cars": [
            {
                "id": car_id,
                "nickname": "Blue",
                "maintenance": [],
                "missing": [
                    "I don't have an oil-change date yet.",
                    "I don't have a registration date yet.",
                    "I don't have an inspection date yet.",
            ],
        }
    ]
    }


def test_a_car_without_a_nickname_says_so(client):
    created = client.post("/api/cars", json={})
    assert created.status_code == 201
    missing = client.get("/api/cars").json()["cars"][0]["missing"]
    assert missing[0] == "I don't have a nickname for this car yet."


def test_maintenance_keeps_a_stored_date_and_does_not_invent_a_due_date(client):
    car_id = client.post("/api/cars", json={"nickname": "Blue"}).json()["id"]
    recorded = client.post(
        f"/api/cars/{car_id}/maintenance",
        json={
            "kind": "oil_change",
            "performed_on": "2026-03-12",
            "evidence_note": "Dealer invoice in the glovebox",
        },
    )
    assert recorded.status_code == 201
    event = recorded.json()
    assert event["kind"] == "oil_change"
    assert event["kind_label"] == "Oil change"
    assert event["performed_on"] == "2026-03-12"
    assert event["evidence_note"] == "Dealer invoice in the glovebox"
    assert "next_due" not in event

    page = client.get("/api/cars").json()["cars"][0]
    assert "I don't have an oil-change date yet." not in page["missing"]
    assert "I don't have an oil-change evidence note yet." not in page["missing"]
    assert page["missing"] == [
        "I don't have a registration date yet.",
        "I don't have an inspection date yet.",
    ]
    assert "next_due" not in page["maintenance"][0]


def test_next_due_appears_only_when_a_real_date_was_stored(client):
    car_id = client.post("/api/cars", json={"nickname": "Blue"}).json()["id"]
    recorded = client.post(
        f"/api/cars/{car_id}/maintenance",
        json={
            "kind": "registration",
            "performed_on": "2025-11-01",
            "evidence_note": "Registration card",
            "next_due": "2026-11-01",
        },
    )
    assert recorded.status_code == 201
    assert recorded.json()["next_due"] == "2026-11-01"
    assert client.get("/api/cars").json()["cars"][0]["maintenance"][0]["next_due"] == "2026-11-01"


def test_a_date_that_was_not_stored_is_refused(client):
    car_id = client.post("/api/cars", json={"nickname": "Blue"}).json()["id"]
    refused = client.post(
        f"/api/cars/{car_id}/maintenance",
        json={"kind": "oil_change", "performed_on": "soon", "next_due": "in six months"},
    )
    assert refused.status_code == 400
    page = client.get("/api/cars").json()["cars"][0]
    assert page["maintenance"] == []
    assert "I don't have an oil-change date yet." in page["missing"]


def test_a_correction_replaces_the_nickname_and_keeps_the_prior_value(client):
    client.put("/api/clock", json={"now": "2026-10-25T15:00:00+00:00"})
    car_id = client.post("/api/cars", json={"nickname": "Blue"}).json()["id"]
    corrected = client.patch(f"/api/cars/{car_id}", json={"nickname": "The wagon"})
    assert corrected.status_code == 200
    assert corrected.json()["nickname"] == "The wagon"

    exported = client.get("/api/cars/export")
    assert exported.status_code == 200
    assert exported.headers["content-disposition"] == 'attachment; filename="cars.json"'
    record = exported.json()["cars"][0]
    assert record["nickname"] == "The wagon"
    assert record["corrections"] == [
        {
            "at": "2026-10-25T15:00:00+00:00",
            "before": {"nickname": "Blue"},
            "after": {"nickname": "The wagon"},
        }
    ]


def test_a_correction_can_store_a_real_next_due_and_leaves_others_alone(client):
    car_id = client.post("/api/cars", json={"nickname": "Blue"}).json()["id"]
    event_id = client.post(
        f"/api/cars/{car_id}/maintenance",
        json={
            "kind": "oil change",
            "performed_on": "2026-01-15",
            "evidence_note": "Shop invoice",
        },
    ).json()["id"]

    corrected = client.patch(
        f"/api/cars/{car_id}/maintenance/{event_id}",
        json={"performed_on": "2026-02-02", "next_due": "2026-08-02"},
    )
    assert corrected.status_code == 200
    assert corrected.json()["performed_on"] == "2026-02-02"
    assert corrected.json()["evidence_note"] == "Shop invoice"
    assert corrected.json()["next_due"] == "2026-08-02"
    assert corrected.json()["kind"] == "oil_change"

    exported = client.get("/api/cars/export").json()["cars"][0]
    assert exported["maintenance"][0]["performed_on"] == "2026-02-02"
    assert exported["maintenance"][0]["next_due"] == "2026-08-02"
    assert exported["corrections"][0]["before"]["performed_on"] == "2026-01-15"
    assert exported["corrections"][0]["before"]["next_due"] is None
    assert exported["corrections"][0]["after"]["next_due"] == "2026-08-02"


def test_two_cars_export_as_separate_records(client):
    blue = client.post("/api/cars", json={"nickname": "Blue"}).json()["id"]
    red = client.post("/api/cars", json={"nickname": "Red"}).json()["id"]
    client.post(
        f"/api/cars/{red}/maintenance",
        json={"kind": "inspection", "performed_on": "2026-04-04", "evidence_note": "Sticker on the windshield"},
    )

    page = client.get("/api/cars").json()["cars"]
    assert [car["nickname"] for car in page] == ["Blue", "Red"]
    assert "I don't have an inspection date yet." in page[0]["missing"]
    assert "I don't have an inspection date yet." not in page[1]["missing"]
    assert page[1]["maintenance"][0]["evidence_note"] == "Sticker on the windshield"
    assert "next_due" not in page[1]["maintenance"][0]

    exported = client.get("/api/cars/export").json()["cars"]
    assert [car["id"] for car in exported] == [blue, red]
    assert "missing" not in exported[0]
    assert exported[1]["maintenance"][0]["kind"] == "inspection"


def test_an_oil_change_without_a_note_asks_for_the_note(client):
    car_id = client.post("/api/cars", json={"nickname": "Blue"}).json()["id"]
    client.post(
        f"/api/cars/{car_id}/maintenance",
        json={"kind": "oil_change", "performed_on": "2026-03-12"},
    )
    missing = client.get("/api/cars").json()["cars"][0]["missing"]
    assert missing == [
        "I don't have an oil-change evidence note yet.",
        "I don't have a registration date yet.",
        "I don't have an inspection date yet.",
    ]


def test_a_correction_that_omits_the_nickname_does_not_erase_it(client):
    car_id = client.post("/api/cars", json={"nickname": "Blue"}).json()["id"]
    omitted = client.patch(f"/api/cars/{car_id}", json={})
    assert omitted.status_code == 400
    assert client.get("/api/cars").json()["cars"][0]["nickname"] == "Blue"


def test_a_correction_for_an_unknown_car_is_refused(client):
    missing = client.patch("/api/cars/car_missing", json={"nickname": "Blue"})
    assert missing.status_code == 404
