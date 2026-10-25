"""Household cars. Dates are stored facts. A missing date stays missing."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from solomon.clock import AppClock
from solomon.models import Base

# Spoken labels for the dates Solomon asks about until one is stored.
ASKED_DATES = (
    ("oil_change", "oil-change", "an"),
    ("registration", "registration", "a"),
    ("inspection", "inspection", "an"),
)

KIND_LABELS = {
    "oil_change": "Oil change",
    "registration": "Registration",
    "inspection": "Inspection",
}

KIND_ALIASES = {
    "oil change": "oil_change",
    "oil-change": "oil_change",
    "oil_change": "oil_change",
    "registration": "registration",
    "inspection": "inspection",
    "state inspection": "inspection",
}


class Vehicle(Base):
    __tablename__ = "vehicle"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    nickname: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class VehicleMaintenance(Base):
    __tablename__ = "vehicle_maintenance"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    performed_on: Mapped[str | None] = mapped_column(String)
    evidence_note: Mapped[str | None] = mapped_column(Text)
    next_due: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class VehicleCorrection(Base):
    __tablename__ = "vehicle_correction"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    before_json: Mapped[str] = mapped_column(Text)
    after_json: Mapped[str] = mapped_column(Text)


class CarIn(BaseModel):
    nickname: str | None = None


class MaintenanceIn(BaseModel):
    kind: str
    performed_on: str | None = None
    evidence_note: str | None = None
    next_due: str | None = None


class CarPatch(BaseModel):
    nickname: str | None = None


class MaintenancePatch(BaseModel):
    kind: str | None = None
    performed_on: str | None = None
    evidence_note: str | None = None
    next_due: str | None = None


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _blank(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _calendar_date(value: str | None, *, field: str) -> str | None:
    text = _blank(value)
    if text is None:
        return None
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field} must be a stored calendar date (YYYY-MM-DD)") from exc
    return parsed.date().isoformat()


def _canonical_kind(value: str | None) -> str:
    text = _blank(value)
    if text is None:
        raise ValueError("kind is required")
    key = text.replace("-", " ").replace("_", " ").lower()
    key = " ".join(key.split())
    if key in KIND_ALIASES:
        return KIND_ALIASES[key]
    slug = key.replace(" ", "_")
    if not slug.replace("_", "").isalnum():
        raise ValueError("kind is required")
    return slug


def _kind_label(kind: str) -> str:
    if kind in KIND_LABELS:
        return KIND_LABELS[kind]
    return kind.replace("_", " ").capitalize()


def _missing_lines(nickname: str | None, events: list[VehicleMaintenance]) -> list[str]:
    lines: list[str] = []
    if _blank(nickname) is None:
        lines.append("I don't have a nickname for this car yet.")
    dated = {event.kind for event in events if event.performed_on}
    noted = {event.kind for event in events if event.performed_on and _blank(event.evidence_note)}
    for kind, label, article in ASKED_DATES:
        if kind not in dated:
            lines.append(f"I don't have {article} {label} date yet.")
        elif kind not in noted:
            lines.append(f"I don't have {article} {label} evidence note yet.")
    return lines


def _event_payload(event: VehicleMaintenance, *, for_page: bool) -> dict:
    payload = {
        "id": event.id,
        "kind": event.kind,
        "performed_on": event.performed_on,
        "evidence_note": event.evidence_note,
    }
    if for_page:
        payload["kind_label"] = _kind_label(event.kind)
    if event.next_due:
        payload["next_due"] = event.next_due
    return payload


def _car_payload(
    vehicle: Vehicle,
    events: list[VehicleMaintenance],
    *,
    for_page: bool,
    corrections: list[VehicleCorrection] | None = None,
) -> dict:
    payload: dict = {
        "id": vehicle.id,
        "nickname": _blank(vehicle.nickname),
        "maintenance": [_event_payload(event, for_page=for_page) for event in events],
    }
    if for_page:
        payload["missing"] = _missing_lines(vehicle.nickname, events)
    else:
        payload["corrections"] = [
            {
                "at": _aware(row.at).isoformat(),
                "before": json.loads(row.before_json),
                "after": json.loads(row.after_json),
            }
            for row in corrections or []
        ]
    return payload


class CarStore:
    def __init__(self, engine: Engine, clock: AppClock) -> None:
        self.clock = clock
        self._session = sessionmaker(bind=engine, expire_on_commit=False)

    def session(self) -> Session:
        return self._session()

    def create_car(self, nickname: str | None) -> dict:
        now = self.clock.now()
        with self.session() as session:
            row = Vehicle(id=_new_id("car"), nickname=_blank(nickname), created_at=now)
            session.add(row)
            session.commit()
            return _car_payload(row, [], for_page=True)

    def list_cars(self) -> dict:
        with self.session() as session:
            vehicles = session.scalars(select(Vehicle).order_by(Vehicle.created_at, Vehicle.id)).all()
            return {"cars": [self._page_car(session, vehicle) for vehicle in vehicles]}

    def export_cars(self) -> dict:
        with self.session() as session:
            vehicles = session.scalars(select(Vehicle).order_by(Vehicle.created_at, Vehicle.id)).all()
            cars = []
            for vehicle in vehicles:
                events = self._events(session, vehicle.id)
                corrections = session.scalars(
                    select(VehicleCorrection)
                    .where(VehicleCorrection.vehicle_id == vehicle.id)
                    .order_by(VehicleCorrection.at, VehicleCorrection.id)
                ).all()
                cars.append(_car_payload(vehicle, events, for_page=False, corrections=list(corrections)))
            return {"cars": cars}

    def add_maintenance(self, car_id: str, body: MaintenanceIn) -> dict:
        try:
            kind = _canonical_kind(body.kind)
            performed_on = _calendar_date(body.performed_on, field="performed_on")
            next_due = _calendar_date(body.next_due, field="next_due")
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        now = self.clock.now()
        with self.session() as session:
            vehicle = session.get(Vehicle, car_id)
            if vehicle is None:
                raise KeyError(car_id)
            event = VehicleMaintenance(
                id=_new_id("mnt"),
                vehicle_id=vehicle.id,
                kind=kind,
                performed_on=performed_on,
                evidence_note=_blank(body.evidence_note),
                next_due=next_due,
                created_at=now,
            )
            session.add(event)
            session.commit()
            return _event_payload(event, for_page=True)

    def correct_car(self, car_id: str, nickname: str | None) -> dict:
        now = self.clock.now()
        with self.session() as session:
            vehicle = session.get(Vehicle, car_id)
            if vehicle is None:
                raise KeyError(car_id)
            before = _blank(vehicle.nickname)
            after = _blank(nickname)
            if before != after:
                session.add(
                    VehicleCorrection(
                        id=_new_id("cor"),
                        vehicle_id=vehicle.id,
                        at=now,
                        before_json=json.dumps({"nickname": before}),
                        after_json=json.dumps({"nickname": after}),
                    )
                )
                vehicle.nickname = after
                session.commit()
            return self._page_car(session, vehicle)

    def correct_maintenance(self, car_id: str, event_id: str, patch: dict) -> dict:
        now = self.clock.now()
        with self.session() as session:
            vehicle = session.get(Vehicle, car_id)
            if vehicle is None:
                raise KeyError(car_id)
            event = session.get(VehicleMaintenance, event_id)
            if event is None or event.vehicle_id != car_id:
                raise KeyError(event_id)
            before: dict = {}
            after: dict = {}
            if "kind" in patch:
                kind = _canonical_kind(patch.get("kind"))
                if kind != event.kind:
                    before["kind"] = event.kind
                    after["kind"] = kind
                    event.kind = kind
            if "performed_on" in patch:
                performed_on = _calendar_date(patch.get("performed_on"), field="performed_on")
                if performed_on != event.performed_on:
                    before["performed_on"] = event.performed_on
                    after["performed_on"] = performed_on
                    event.performed_on = performed_on
            if "evidence_note" in patch:
                note = _blank(patch.get("evidence_note"))
                if note != event.evidence_note:
                    before["evidence_note"] = event.evidence_note
                    after["evidence_note"] = note
                    event.evidence_note = note
            if "next_due" in patch:
                next_due = _calendar_date(patch.get("next_due"), field="next_due")
                if next_due != event.next_due:
                    before["next_due"] = event.next_due
                    after["next_due"] = next_due
                    event.next_due = next_due
            if before:
                session.add(
                    VehicleCorrection(
                        id=_new_id("cor"),
                        vehicle_id=vehicle.id,
                        at=now,
                        before_json=json.dumps({"maintenance_id": event.id, **before}),
                        after_json=json.dumps({"maintenance_id": event.id, **after}),
                    )
                )
                session.commit()
            return _event_payload(event, for_page=True)

    def _events(self, session: Session, vehicle_id: str) -> list[VehicleMaintenance]:
        rows = session.scalars(
            select(VehicleMaintenance)
            .where(VehicleMaintenance.vehicle_id == vehicle_id)
            .order_by(VehicleMaintenance.performed_on, VehicleMaintenance.created_at, VehicleMaintenance.id)
        ).all()
        return list(rows)

    def _page_car(self, session: Session, vehicle: Vehicle) -> dict:
        return _car_payload(vehicle, self._events(session, vehicle.id), for_page=True)


def mount(app: FastAPI, store: CarStore) -> None:
    @app.get("/api/cars")
    def list_cars() -> dict:
        return store.list_cars()

    @app.get("/api/cars/export")
    def export_cars() -> JSONResponse:
        return JSONResponse(
            content=store.export_cars(),
            headers={"Content-Disposition": 'attachment; filename="cars.json"'},
        )

    @app.post("/api/cars", status_code=201)
    def create_car(body: CarIn) -> dict:
        return store.create_car(body.nickname)

    @app.patch("/api/cars/{car_id}")
    def correct_car(car_id: str, body: CarPatch) -> dict:
        if "nickname" not in body.model_fields_set:
            raise HTTPException(status_code=400, detail="nothing to correct")
        try:
            return store.correct_car(car_id, body.nickname)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="car not found") from exc

    @app.post("/api/cars/{car_id}/maintenance", status_code=201)
    def add_maintenance(car_id: str, body: MaintenanceIn) -> dict:
        try:
            return store.add_maintenance(car_id, body)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="car not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.patch("/api/cars/{car_id}/maintenance/{event_id}")
    def correct_maintenance(car_id: str, event_id: str, body: MaintenancePatch) -> dict:
        try:
            return store.correct_maintenance(car_id, event_id, body.model_dump(exclude_unset=True))
        except KeyError as exc:
            detail = "car not found" if exc.args and exc.args[0] == car_id else "maintenance not found"
            raise HTTPException(status_code=404, detail=detail) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
