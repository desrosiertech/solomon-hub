"""The VM install keeps SQLite outside the checkout and listens only where told."""

from pathlib import Path

from solomon.main import DEFAULT_DB, create_app, database_path
from solomon.__main__ import listen_address

ROOT = Path(__file__).resolve().parent.parent


def test_database_path_defaults_inside_the_working_directory(monkeypatch):
    monkeypatch.delenv("SOLOMON_DB", raising=False)
    assert database_path() == DEFAULT_DB


def test_database_path_follows_solomon_db(monkeypatch, tmp_path):
    monkeypatch.setenv("SOLOMON_DB", str(tmp_path / "solomon.db"))
    assert database_path() == tmp_path / "solomon.db"


def test_explicit_database_path_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("SOLOMON_DB", str(tmp_path / "env.db"))
    assert database_path(tmp_path / "explicit.db") == tmp_path / "explicit.db"


def test_create_app_writes_sqlite_at_solomon_db(monkeypatch, tmp_path):
    db = tmp_path / "var" / "solomon.db"
    monkeypatch.setenv("SOLOMON_DB", str(db))
    app = create_app()
    assert db.is_file()
    assert app.state.store.blob_dir == db.parent / "blobs"


def test_listen_address_defaults_to_localhost(monkeypatch):
    monkeypatch.delenv("SOLOMON_HOST", raising=False)
    monkeypatch.delenv("SOLOMON_PORT", raising=False)
    assert listen_address() == ("127.0.0.1", 8000)


def test_listen_address_follows_the_service_environment(monkeypatch):
    monkeypatch.setenv("SOLOMON_HOST", "0.0.0.0")
    monkeypatch.setenv("SOLOMON_PORT", "8000")
    assert listen_address() == ("0.0.0.0", 8000)


def test_installer_matches_the_vm_contract():
    script = (ROOT / "deploy" / "install.sh").read_text(encoding="utf-8")
    unit = (ROOT / "deploy" / "solomon.service").read_text(encoding="utf-8")
    assert "--skip-browser --skip-computer-use" in script
    assert "hermes auth add nous --type oauth" in script
    assert "chmod 600" in script
    assert "/var/lib/solomon" in script
    assert "rm -rf /var/lib/solomon" not in script
    assert "hermes setup" not in script
    assert "auth-key" not in script
    assert "cloudflared" not in script
    assert "docker" not in script.lower()
    assert "User=solomon" in unit
    assert "SOLOMON_DB=/var/lib/solomon/solomon.db" in unit
    assert "SOLOMON_HOST=0.0.0.0" in unit
    assert "python -m solomon" in unit
    assert "auth.json" not in unit
