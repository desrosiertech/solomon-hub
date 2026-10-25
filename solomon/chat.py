"""Household chat. A message is kept here. The reader is a stand-in seam, never a cloud model."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from solomon.clock import AppClock
from solomon.models import ChatMessage

MAX_TEXT = 4_000
MAX_IMAGE = 8 * 1024 * 1024
ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})
READER_OFF = {
    "status": "reader_off",
    "kind": None,
    "summary": "Reader is off. Solomon kept this message.",
}


class ChatReader(Protocol):
    def read_message(self, *, text: str, image: bytes | None) -> dict: ...


class OffReader:
    """No model. The message stays visible as reader-off."""

    def read_message(self, *, text: str, image: bytes | None) -> dict:
        return dict(READER_OFF)


class ChatStore:
    def __init__(self, engine: Engine, clock: AppClock, blob_dir: Path, reader: ChatReader) -> None:
        self.clock = clock
        self.blob_dir = blob_dir
        self.reader = reader
        self._session = sessionmaker(bind=engine, expire_on_commit=False)

    def session(self) -> Session:
        return self._session()

    def post(self, *, text: str, image: bytes | None = None, image_type: str | None = None) -> dict:
        cleaned = text.strip()
        if image is not None and len(image) == 0:
            image = None
            image_type = None
        if not cleaned and image is None:
            raise ValueError("Say something or attach a photo.")
        if len(cleaned) > MAX_TEXT:
            raise ValueError("That message is too long.")
        if image is not None:
            if image_type not in ALLOWED_IMAGE_TYPES:
                raise ValueError("Attach a photo.")
            if len(image) > MAX_IMAGE:
                raise ValueError("That photo is too large.")

        proposal = self._proposal(cleaned, image)
        image_name = self._save_image(image) if image is not None else None
        row = ChatMessage(
            id=f"chat_{uuid4().hex}",
            text=cleaned,
            image_name=image_name,
            image_type=image_type if image_name else None,
            created_at=self.clock.now(),
            reader_status=str(proposal["status"]),
            proposal_kind=proposal["kind"],
            proposal_summary=str(proposal["summary"]),
        )
        with self.session() as session:
            session.add(row)
            session.commit()
            return self._payload(row)

    def list_messages(self) -> dict:
        with self.session() as session:
            rows = session.scalars(select(ChatMessage).order_by(ChatMessage.created_at, ChatMessage.id)).all()
            return {"messages": [self._payload(row) for row in rows]}

    def image_file(self, message_id: str) -> tuple[Path, str] | None:
        with self.session() as session:
            row = session.get(ChatMessage, message_id)
            if row is None or not row.image_name:
                return None
            path = (self.blob_dir / row.image_name).resolve()
            root = self.blob_dir.resolve()
            if not path.is_relative_to(root) or not path.is_file():
                return None
            return path, row.image_type or "application/octet-stream"

    def _proposal(self, text: str, image: bytes | None) -> dict:
        result = self.reader.read_message(text=text, image=image)
        status = result.get("status")
        if status not in {"reader_off", "proposed"}:
            return dict(READER_OFF)
        summary = result.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            return dict(READER_OFF)
        kind = result.get("kind")
        if kind is not None and not isinstance(kind, str):
            kind = None
        return {"status": status, "kind": kind, "summary": summary}

    def _save_image(self, image: bytes) -> str:
        self.blob_dir.mkdir(parents=True, exist_ok=True)
        name = hashlib.sha256(image).hexdigest()
        (self.blob_dir / name).write_bytes(image)
        return name

    def _payload(self, row: ChatMessage) -> dict:
        image_url = f"/api/chat/{row.id}/image" if row.image_name else None
        return {
            "id": row.id,
            "text": row.text,
            "has_image": row.image_name is not None,
            "image_url": image_url,
            "at": _iso(row.created_at),
            "proposal": {
                "status": row.reader_status,
                "kind": row.proposal_kind,
                "summary": row.proposal_summary,
            },
        }


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()
