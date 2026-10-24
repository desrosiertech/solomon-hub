from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from solomon.clock import AppClock
from solomon.provider import DisabledProvider
from solomon.service import FoodStore, make_engine, seed_if_empty

DEFAULT_DB = Path("data/solomon.db")


class InventoryIn(BaseModel):
    label: str
    category: str | None = None
    storage: str | None = None
    quantity_kind: str | None = None
    quantity_count: int | None = None
    leftover: bool = False
    acquired_at: str | None = None


class ClockIn(BaseModel):
    now: str


class SettingsIn(BaseModel):
    grace_period_minutes: int | None = Field(default=None, ge=1)
    presume_after_minutes: int | None = Field(default=None, ge=1)


class StopAskingIn(BaseModel):
    key: str


def create_app(
    db_path: Path | str | None = None,
    *,
    clock: AppClock | None = None,
) -> FastAPI:
    path = Path(db_path) if db_path is not None else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(path)
    with session_for(engine) as session:
        seed_if_empty(session)
    clock = clock or AppClock()
    store = FoodStore(engine, clock, DisabledProvider())

    app = FastAPI(title="Solomon", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.store = store
    app.state.clock = clock
    app.state.provider = store.provider

    @app.get("/api/provider")
    def provider() -> dict:
        return {"name": store.provider.name}

    @app.put("/api/clock")
    def set_clock(body: ClockIn) -> dict:
        clock.freeze(_parse_dt(body.now))
        return {"now": clock.now().isoformat()}

    @app.get("/api/clock")
    def get_clock() -> dict:
        return {"now": clock.now().isoformat()}

    @app.put("/api/settings")
    def settings(body: SettingsIn) -> dict:
        return store.update_settings(
            grace_period_minutes=body.grace_period_minutes,
            presume_after_minutes=body.presume_after_minutes,
        )

    @app.post("/api/inventory", status_code=201)
    def add_inventory(body: InventoryIn) -> dict:
        try:
            return store.add_item(body.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/inventory")
    def list_inventory() -> dict:
        return store.list_items()

    @app.get("/api/home")
    def home() -> dict:
        return store.home()

    @app.get("/api/meals")
    def meals() -> dict:
        return store.meals()

    @app.post("/api/suggestions/stop-asking", status_code=204)
    def stop_asking(body: StopAskingIn) -> None:
        try:
            store.stop_asking(body.key)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="suggestion not found") from exc

    @app.post("/api/jobs/age")
    def age() -> dict:
        return store.age()

    @app.get("/api/audit")
    def audit() -> dict:
        return store.audit()

    web_dist = Path(__file__).resolve().parent.parent / "web" / "dist"
    if web_dist.is_dir():

        @app.get("/")
        def spa_index(request: Request):
            from fastapi.responses import FileResponse

            return FileResponse(web_dist / "index.html")

        app.mount("/assets", StaticFiles(directory=web_dist / "assets"), name="assets")

    return app


def session_for(engine):
    from sqlalchemy.orm import Session

    return Session(engine)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


# Uvicorn: `uvicorn solomon.main:create_app --factory`
