"""Household dogs and their vet records.

A vaccine date is stored only when a record says so. A visit or a payment
stays that kind. Next due is stored only when a record already has it.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Text, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from solomon.models import Base

DOG_SLOTS = (
    ("dog_1", "Dog 1"),
    ("dog_2", "Dog 2"),
)
KINDS = {"vaccine", "vet_visit", "payment", "service", "registration"}


class Dog(Base):
    __tablename__ = "dog"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)


class DogVetRecord(Base):
    __tablename__ = "dog_vet_record"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    dog_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    performed_on: Mapped[str | None] = mapped_column(String)
    evidence_note: Mapped[str | None] = mapped_column(Text)
    next_due: Mapped[str | None] = mapped_column(String)


class DogStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._session = sessionmaker(bind=engine, expire_on_commit=False)
        Base.metadata.create_all(engine)

    def export(self) -> dict:
        with self._session() as session:
            _ensure_dogs(session)
            session.commit()
            dogs = list(session.scalars(select(Dog).order_by(Dog.id)))
            records = list(session.scalars(select(DogVetRecord)))
        by_dog: dict[str, list[DogVetRecord]] = {dog.id: [] for dog in dogs}
        for record in records:
            by_dog.setdefault(record.dog_id, []).append(record)
        return {
            "dogs": [
                _dog_export(dog, by_dog.get(dog.id, []))
                for dog in dogs
            ]
        }

    def record(
        self,
        *,
        dog_id: str,
        kind: str,
        date: str | None = None,
        evidence_note: str | None = None,
        next_due: str | None = None,
    ) -> dict:
        if dog_id not in {slot for slot, _name in DOG_SLOTS}:
            raise ValueError("unknown dog")
        if kind not in KINDS:
            raise ValueError("unknown care kind")
        performed_on = _date_or_none(date)
        stored_due = _date_or_none(next_due)
        note = evidence_note.strip() if evidence_note and evidence_note.strip() else None
        with self._session() as session:
            _ensure_dogs(session)
            row = DogVetRecord(
                id=f"vet_{uuid4().hex}",
                dog_id=dog_id,
                kind=kind,
                performed_on=performed_on,
                evidence_note=note,
                next_due=stored_due,
            )
            session.add(row)
            session.commit()
            dog = session.get(Dog, dog_id)
            stored = list(session.scalars(select(DogVetRecord).where(DogVetRecord.dog_id == dog_id)))
        assert dog is not None
        return _dog_export(dog, stored)


def _ensure_dogs(session: Session) -> None:
    for dog_id, name in DOG_SLOTS:
        if session.get(Dog, dog_id) is None:
            session.add(Dog(id=dog_id, name=name))


def _dog_export(dog: Dog, records: list[DogVetRecord]) -> dict:
    ordered = sorted(records, key=lambda row: (row.performed_on is None, row.performed_on or "", row.id))
    has_vaccine_date = any(row.kind == "vaccine" and row.performed_on for row in records)
    missing = [] if has_vaccine_date else ["vaccine date"]
    exported_records = [_record_export(row) for row in ordered]
    return {
        "id": dog.id,
        "name": dog.name,
        "missing": missing,
        "ask": None if has_vaccine_date else f"I don't have {dog.name}'s vaccine date yet.",
        "records": exported_records,
    }


def _record_export(row: DogVetRecord) -> dict:
    exported = {
        "id": row.id,
        "date": row.performed_on,
        "kind": row.kind,
        "evidence_note": row.evidence_note,
    }
    if row.next_due:
        exported["next_due"] = row.next_due
    return exported


def _date_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    datetime.strptime(text, "%Y-%m-%d")
    return text
