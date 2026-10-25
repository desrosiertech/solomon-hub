from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from solomon.board import BoardStore, CalendarAdapter, WeatherAdapter
from solomon.cars import CarStore, mount as mount_cars
from solomon.chat import ChatStore, OffReader
from solomon.clock import AppClock
from solomon.dogs import DogStore
from solomon.household_settings import (
    HouseholdPreferenceError,
    parse_household,
    read_household,
    save_household,
)
from solomon.news import NewsAdapter, NewsStore
from solomon.intake import (
    accept_recipe,
    apply_receipt,
    list_planned,
    list_recipes,
    plan_meal,
    propose_recipe,
    submit_receipt,
)
from solomon.provider import DisabledProvider, ModelProvider, ReaderOff
from solomon.service import FoodStore, make_engine, seed_if_empty
from solomon.spooktober import SpooktoberStore, build_router as spooktober_router

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


class ApplyIn(BaseModel):
    lines: list[dict] = Field(default_factory=list)


class RecipeUrlIn(BaseModel):
    source_kind: str
    url: str | None = None


class PlanIn(BaseModel):
    on: str
    recipe_id: str


class CalendarEventIn(BaseModel):
    title: str
    start_local: str
    end_local: str | None = None
    location: str | None = None
    member_id: str | None = None


def create_app(
    db_path: Path | str | None = None,
    *,
    clock: AppClock | None = None,
    provider: ModelProvider | None = None,
    blob_dir: Path | str | None = None,
    fetch_page=None,
    weather: WeatherAdapter | None = None,
    calendar: CalendarAdapter | None = None,
    news: NewsAdapter | None = None,
    chat_reader=None,
) -> FastAPI:
    path = Path(db_path) if db_path is not None else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(path)
    with session_for(engine) as session:
        seed_if_empty(session)
    clock = clock or AppClock()
    store = FoodStore(engine, clock, provider or DisabledProvider())
    store.blob_dir = Path(blob_dir) if blob_dir is not None else path.parent / "blobs"
    board = BoardStore(engine, clock, weather, calendar)
    news_store = NewsStore(engine, clock, news)
    chat = ChatStore(engine, clock, store.blob_dir, chat_reader or OffReader())
    cars = CarStore(engine, clock)
    dogs = DogStore(engine)
    journal = SpooktoberStore(engine, clock)

    app = FastAPI(title="Solomon", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.store = store
    app.state.board = board
    app.state.news = news_store
    app.state.chat = chat
    app.state.cars = cars
    app.state.dogs = dogs
    app.state.journal = journal
    app.state.clock = clock
    app.state.provider = store.provider
    app.include_router(spooktober_router(journal))

    @app.get("/api/provider")
    def provider_status() -> dict:
        return store.provider.status()

    @app.get("/api/connections")
    def connections() -> dict:
        return {
            "calendar": {"connected": False, "state": "not_connected"},
            "api": {"connected": False, "state": "not_connected"},
        }

    @app.post("/api/chat", status_code=201)
    async def post_chat(request: Request) -> dict:
        text, image, image_type = await _chat_parts(request)
        try:
            return chat.post(text=text, image=image, image_type=image_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/chat")
    def list_chat() -> dict:
        return chat.list_messages()

    @app.get("/api/chat/{message_id}/image")
    def chat_image(message_id: str):
        found = chat.image_file(message_id)
        if found is None:
            raise HTTPException(status_code=404, detail="photo not found")
        path, media_type = found
        return FileResponse(path, media_type=media_type)

    @app.put("/api/clock")
    def set_clock(body: ClockIn) -> dict:
        clock.freeze(_parse_dt(body.now))
        return {"now": clock.now().isoformat()}

    @app.get("/api/clock")
    def get_clock() -> dict:
        return {"now": clock.now().isoformat()}

    @app.get("/api/household")
    def household() -> dict:
        with store.session() as session:
            return read_household(session)

    @app.put("/api/household")
    async def put_household(request: Request) -> dict:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=400, detail="Household preferences do not take a token or a password."
            )
        try:
            preferences = parse_household(payload)
        except HouseholdPreferenceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        with store.session() as session:
            try:
                saved = save_household(session, preferences)
            except HouseholdPreferenceError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            session.commit()
            return saved

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
        return {**store.home(), **board.home()}

    @app.get("/api/calendar/day")
    def calendar_day(on: str | None = None) -> dict:
        try:
            return board.day(on)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/calendar/events", status_code=201)
    def add_calendar_event(body: CalendarEventIn) -> dict:
        try:
            return board.add_event(body.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/calendar/refresh")
    def refresh_calendar() -> dict:
        return board.refresh_calendar()

    @app.get("/api/weather")
    def weather() -> dict:
        return board.forecast()

    @app.post("/api/weather/refresh")
    def refresh_weather() -> dict:
        return board.refresh_weather()

    @app.get("/api/dogs")
    def dogs_export() -> dict:
        return dogs.export()

    @app.get("/api/news")
    def news_digest() -> dict:
        return news_store.digest()

    @app.post("/api/news/refresh")
    def refresh_news() -> dict:
        return news_store.refresh()

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

    @app.post("/api/receipts", status_code=201)
    async def post_receipt(image: UploadFile = File(...)) -> dict:
        payload = await image.read()
        try:
            return submit_receipt(store, payload)
        except ReaderOff as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/receipts/{receipt_id}/apply")
    def post_apply(receipt_id: str, body: ApplyIn) -> dict:
        try:
            return apply_receipt(store, receipt_id, body.lines)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="receipt not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/recipes/proposals", status_code=201)
    async def post_proposal(request: Request) -> dict:
        content_type = request.headers.get("content-type", "")
        url = None
        picture = None
        if content_type.startswith("application/json"):
            body = RecipeUrlIn.model_validate(await request.json())
            kind = body.source_kind
            url = body.url
        else:
            form = await request.form()
            kind = str(form.get("source_kind") or "")
            upload = form.get("image")
            picture = await upload.read() if upload is not None and hasattr(upload, "read") else None
        try:
            return propose_recipe(
                store,
                kind=kind or "",
                image=picture,
                url=url,
                fetch_page=fetch_page,
            )
        except ReaderOff as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/recipes/proposals/{proposal_id}/accept", status_code=201)
    def post_accept(proposal_id: str) -> dict:
        try:
            return accept_recipe(store, proposal_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="proposal not found") from exc

    @app.get("/api/recipes")
    def recipes() -> dict:
        return list_recipes(store)

    @app.post("/api/planned-meals", status_code=201)
    def post_plan(body: PlanIn) -> dict:
        try:
            return plan_meal(store, body.on, body.recipe_id)
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail="That night is already planned.") from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="recipe not found") from exc

    @app.get("/api/planned-meals")
    def planned() -> dict:
        return list_planned(store)

    mount_cars(app, cars)

    web_dist = Path(__file__).resolve().parent.parent / "web" / "dist"
    if web_dist.is_dir():

        @app.get("/")
        def spa_index(request: Request):
            from fastapi.responses import FileResponse

            return FileResponse(web_dist / "index.html")

        app.mount("/assets", StaticFiles(directory=web_dist / "assets"), name="assets")

    return app


async def _chat_parts(request: Request) -> tuple[str, bytes | None, str | None]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Say something or attach a photo.")
        text = body.get("text", "")
        if not isinstance(text, str):
            raise HTTPException(status_code=400, detail="Say something or attach a photo.")
        return text, None, None
    form = await request.form()
    raw_text = form.get("text") or ""
    text = raw_text if isinstance(raw_text, str) else str(raw_text)
    upload = form.get("image")
    if upload is None or not hasattr(upload, "read"):
        return text, None, None
    payload = await upload.read()
    media = getattr(upload, "content_type", None) or ""
    return text, payload, media


def session_for(engine):
    from sqlalchemy.orm import Session

    return Session(engine)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


# Uvicorn: `uvicorn solomon.main:create_app --factory`
