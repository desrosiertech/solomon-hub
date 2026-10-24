from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    from solomon.main import create_app

    app = create_app(db_path=tmp_path / "solomon.db")
    with TestClient(app) as test_client:
        yield test_client
