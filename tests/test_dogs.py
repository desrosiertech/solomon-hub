"""Dogs page through the app API. Display only. No model and no invented dates."""


def test_missing_vaccine_date_is_asked_for_and_no_due_date_is_invented(client):
    page = client.get("/api/dogs").json()

    assert client.get("/api/provider").json()["name"] == "Disabled"
    assert [dog["id"] for dog in page["dogs"]] == ["dog_1", "dog_2"]
    assert [(dog["name"], dog["missing"], dog["ask"], dog["records"]) for dog in page["dogs"]] == [
        ("Dog 1", ["vaccine date"], "I don't have Dog 1's vaccine date yet.", []),
        ("Dog 2", ["vaccine date"], "I don't have Dog 2's vaccine date yet.", []),
    ]


def test_stored_vaccine_date_is_exported_and_next_due_only_when_stored(client):
    dogs = client.app.state.dogs
    dogs.record(
        dog_id="dog_1",
        kind="vaccine",
        date="2024-03-12",
        evidence_note="Rabies certificate",
        next_due="2027-03-12",
    )
    dogs.record(
        dog_id="dog_2",
        kind="vaccine",
        date="2025-06-01",
        evidence_note="Bordetella sticker",
    )

    page = client.get("/api/dogs").json()
    first, second = page["dogs"]

    assert first["missing"] == []
    assert first["ask"] is None
    stored = first["records"][0]
    assert stored["date"] == "2024-03-12"
    assert stored["kind"] == "vaccine"
    assert stored["evidence_note"] == "Rabies certificate"
    assert stored["next_due"] == "2027-03-12"

    assert second["missing"] == []
    assert second["ask"] is None
    open_ended = second["records"][0]
    assert open_ended["date"] == "2025-06-01"
    assert open_ended["kind"] == "vaccine"
    assert open_ended["evidence_note"] == "Bordetella sticker"
    assert "next_due" not in open_ended


def test_a_vaccine_without_a_date_still_asks_and_does_not_invent_one(client):
    client.app.state.dogs.record(
        dog_id="dog_1",
        kind="vaccine",
        evidence_note="Certificate with the date left blank",
    )

    dog = client.get("/api/dogs").json()["dogs"][0]
    record = dog["records"][0]

    assert dog["missing"] == ["vaccine date"]
    assert dog["ask"] == "I don't have Dog 1's vaccine date yet."
    assert record["kind"] == "vaccine"
    assert record["date"] is None
    assert record["evidence_note"] == "Certificate with the date left blank"
    assert "next_due" not in record


def test_a_visit_or_a_payment_does_not_become_a_vaccine_or_a_due_date(client):
    dogs = client.app.state.dogs
    dogs.record(
        dog_id="dog_1",
        kind="vet_visit",
        date="2026-10-01",
        evidence_note="Annual exam. Invoice paid. Mentions rabies.",
    )
    dogs.record(
        dog_id="dog_1",
        kind="payment",
        date="2026-10-01",
        evidence_note="Payment for rabies vaccine",
    )

    dog = client.get("/api/dogs").json()["dogs"][0]

    assert dog["missing"] == ["vaccine date"]
    assert dog["ask"] == "I don't have Dog 1's vaccine date yet."
    assert {(row["kind"], row["date"], row["evidence_note"]) for row in dog["records"]} == {
        ("vet_visit", "2026-10-01", "Annual exam. Invoice paid. Mentions rabies."),
        ("payment", "2026-10-01", "Payment for rabies vaccine"),
    }
    assert all("next_due" not in row for row in dog["records"])
    assert all(row["kind"] != "vaccine" for row in dog["records"])
