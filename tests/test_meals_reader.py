"""Meals tells a Member whether the receipt reader is on. Grocery stays local."""

from pathlib import Path

from fastapi.testclient import TestClient


class _StandIn:
    """A reader that never calls Claude. It only reports the login we hand it."""

    name = "Nous Portal"

    def __init__(self, *, signed_in: bool, reachable: bool) -> None:
        self.signed_in = signed_in
        self.reachable = reachable
        self.receipts: list[bytes] = []
        self.pages: list[str | None] = []

    def status(self) -> dict:
        return {
            "name": self.name,
            "signed_in": self.signed_in,
            "reachable": self.reachable,
        }

    def read_receipt(self, image: bytes) -> list[dict]:
        self.receipts.append(image)
        return []

    def read_recipe(self, *, kind: str, image: bytes | None, url: str | None, page: str | None) -> dict:
        self.pages.append(page)
        return {"title": "Chili", "ingredients": [], "steps": []}


def _meals(tmp_path: Path, reader: _StandIn) -> dict:
    from solomon.main import create_app

    app = create_app(db_path=tmp_path / "solomon.db", provider=reader)
    with TestClient(app) as client:
        client.post(
            "/api/inventory",
            json={"label": "Eggs", "category": "unknown", "storage": "pantry"},
        )
        return client.get("/api/meals").json()


def test_meals_says_the_reader_is_off_while_grocery_still_works(client):
    client.put("/api/clock", json={"now": "2026-10-20T12:00:00+00:00"})
    added = client.post(
        "/api/inventory",
        json={
            "label": "Spinach",
            "category": "leafy_greens",
            "storage": "fridge",
            "quantity_kind": "one_package",
        },
    )
    assert added.status_code == 201

    client.put("/api/clock", json={"now": "2026-10-23T12:00:00+00:00"})
    meals = client.get("/api/meals").json()
    assert meals["reader"] == {"on": False, "label": "Reader off"}
    assert [row["title"] for row in meals["use_soon"]] == ["Spinach"]

    stopped = client.post("/api/suggestions/stop-asking", json={"key": meals["use_soon"][0]["key"]})
    assert stopped.status_code == 204

    again = client.get("/api/meals").json()
    assert again["reader"] == {"on": False, "label": "Reader off"}
    assert again["use_soon"] == []
    kept = client.get("/api/inventory").json()["items"]
    assert kept[0]["label"] == "Spinach"
    assert kept[0]["window_label"] == "Estimated use-by window"


def test_meals_says_the_reader_is_on_when_a_usable_login_answers(tmp_path: Path):
    reader = _StandIn(signed_in=True, reachable=True)
    meals = _meals(tmp_path, reader)
    assert meals["reader"] == {"on": True, "label": "Reader on"}
    assert reader.receipts == []
    assert reader.pages == []


def test_meals_says_the_reader_is_off_when_the_login_does_not_answer(tmp_path: Path):
    reader = _StandIn(signed_in=True, reachable=False)
    meals = _meals(tmp_path, reader)
    assert meals["reader"] == {"on": False, "label": "Reader off"}
    assert reader.receipts == []
    assert reader.pages == []
