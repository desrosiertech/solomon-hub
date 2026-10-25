"""Settings connections stay unwired. No token is accepted or stored."""


def test_connections_are_not_connected_and_keep_no_secret(client):
    body = client.get("/api/connections").json()
    assert body == {
        "calendar": {"connected": False, "state": "not_connected"},
        "api": {"connected": False, "state": "not_connected"},
    }

    refused = client.put("/api/connections", json={"token": "secret-token"})
    assert refused.status_code == 405
    assert "secret-token" not in refused.text

    again = client.get("/api/connections").json()
    assert again["calendar"]["connected"] is False
    assert again["api"]["connected"] is False
    assert "secret-token" not in str(again)
