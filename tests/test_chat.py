"""Chat is the household's intake. The reader is off unless a test supplies a stand-in."""


def test_chat_keeps_a_message_when_the_reader_is_off(client):
    sent = client.post("/api/chat", json={"text": "We used the melon."})
    assert sent.status_code == 201
    body = sent.json()
    assert body["text"] == "We used the melon."
    assert body["has_image"] is False
    assert body["image_url"] is None
    assert body["proposal"] == {
        "status": "reader_off",
        "kind": None,
        "summary": "Reader is off. Solomon kept this message.",
    }

    listed = client.get("/api/chat").json()
    assert listed["messages"] == [body]


def test_chat_keeps_a_photo_with_the_message(client):
    photo = b"\x89PNG\r\nreceipt-photo"
    sent = client.post(
        "/api/chat",
        data={"text": "Receipt from the store"},
        files={"image": ("receipt.png", photo, "image/png")},
    )
    assert sent.status_code == 201
    body = sent.json()
    assert body["text"] == "Receipt from the store"
    assert body["has_image"] is True
    assert body["proposal"]["status"] == "reader_off"
    assert body["proposal"]["summary"] == "Reader is off. Solomon kept this message."

    image = client.get(body["image_url"])
    assert image.status_code == 200
    assert image.content == photo
    assert image.headers["content-type"].startswith("image/png")


def test_chat_refuses_an_empty_message(client):
    refused = client.post("/api/chat", json={"text": "   "})
    assert refused.status_code == 400
    assert refused.json()["detail"] == "Say something or attach a photo."
    assert client.get("/api/chat").json() == {"messages": []}


def test_a_stand_in_reader_proposes_without_a_model(tmp_path):
    from fastapi.testclient import TestClient

    from solomon.main import create_app

    class StandIn:
        def __init__(self) -> None:
            self.seen: list[tuple[str, bytes | None]] = []

        def read_message(self, *, text: str, image: bytes | None) -> dict:
            self.seen.append((text, image))
            return {
                "status": "proposed",
                "kind": "inventory_correction",
                "summary": "We used the melon.",
            }

    reader = StandIn()
    app = create_app(db_path=tmp_path / "solomon.db", chat_reader=reader)
    with TestClient(app) as client:
        sent = client.post("/api/chat", json={"text": "We used the melon."})

    assert sent.status_code == 201
    assert sent.json()["proposal"] == {
        "status": "proposed",
        "kind": "inventory_correction",
        "summary": "We used the melon.",
    }
    assert reader.seen == [("We used the melon.", None)]
