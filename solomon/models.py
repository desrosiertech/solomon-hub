from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Household(Base):
    __tablename__ = "household"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile: Mapped[str] = mapped_column(String, default="conservative")
    grace_period_minutes: Mapped[int] = mapped_column(Integer, default=3 * 24 * 60)
    presume_after_minutes: Mapped[int] = mapped_column(Integer, default=4 * 24 * 60)
    ideas_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ideas_json: Mapped[str | None] = mapped_column(Text)


class Member(Base):
    __tablename__ = "member"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="adult")


class InventoryItem(Base):
    __tablename__ = "inventory_item"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    storage: Mapped[str] = mapped_column(String)
    quantity_kind: Mapped[str] = mapped_column(String)
    quantity_count: Mapped[int | None] = mapped_column(Integer)
    leftover: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[str] = mapped_column(String, default="active")
    confidence: Mapped[float] = mapped_column(Float)
    confidence_band: Mapped[str] = mapped_column(String)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_use_by: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_days: Mapped[float] = mapped_column(Float)
    window_source: Mapped[str] = mapped_column(String)
    window_explain: Mapped[str] = mapped_column(String)
    window_epoch: Mapped[str] = mapped_column(String)
    last_strong_observation_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_reason: Mapped[str | None] = mapped_column(String)


class InventoryObservation(Base):
    __tablename__ = "inventory_observation"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    item_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    actor: Mapped[str] = mapped_column(String)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RecipeRow(Base):
    __tablename__ = "recipe"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    source_kind: Mapped[str] = mapped_column(String, default="seed")
    source_url: Mapped[str | None] = mapped_column(String)
    steps_json: Mapped[str] = mapped_column(Text, default="[]")
    image_path: Mapped[str | None] = mapped_column(String)


class RecipeIngredientRow(Base):
    __tablename__ = "recipe_ingredient"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_id: Mapped[str] = mapped_column(String)
    canonical: Mapped[str] = mapped_column(String)
    staple: Mapped[int] = mapped_column(Integer, default=0)


class SuppressionRuleRow(Base):
    __tablename__ = "suppression_rule"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String)
    subject_type: Mapped[str] = mapped_column(String)
    subject_id: Mapped[str] = mapped_column(String)
    key: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StateTransition(Base):
    __tablename__ = "state_transition"
    __table_args__ = (
        UniqueConstraint("item_id", "to_state", "window_epoch", name="uq_item_state_epoch"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    item_id: Mapped[str] = mapped_column(String)
    from_state: Mapped[str] = mapped_column(String)
    to_state: Mapped[str] = mapped_column(String)
    window_epoch: Mapped[str] = mapped_column(String)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor: Mapped[str] = mapped_column(String)


class ReceiptRow(Base):
    __tablename__ = "receipt"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sha256: Mapped[str] = mapped_column(String, unique=True)
    image_path: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReceiptLineRow(Base):
    __tablename__ = "receipt_line"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    receipt_id: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    storage: Mapped[str] = mapped_column(String)
    food: Mapped[int] = mapped_column(Integer, default=1)
    item_id: Mapped[str | None] = mapped_column(String)


class RecipeProposalRow(Base):
    __tablename__ = "recipe_proposal"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    source_kind: Mapped[str] = mapped_column(String)
    source_url: Mapped[str | None] = mapped_column(String)
    ingredients_json: Mapped[str] = mapped_column(Text)
    steps_json: Mapped[str] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="proposed")
    recipe_id: Mapped[str | None] = mapped_column(String)


class PlannedMealRow(Base):
    __tablename__ = "planned_meal"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    on_date: Mapped[str] = mapped_column(String, unique=True)
    recipe_id: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)


class CalendarEvent(Base):
    __tablename__ = "calendar_event"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source: Mapped[str] = mapped_column(String)
    ext_id: Mapped[str | None] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location: Mapped[str | None] = mapped_column(String)
    member_id: Mapped[str | None] = mapped_column(String)


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshot"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    temp_f: Mapped[int] = mapped_column(Integer)
    high_f: Mapped[int] = mapped_column(Integer)
    low_f: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(String)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Headline(Base):
    __tablename__ = "headline"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_name: Mapped[str | None] = mapped_column(String)


class SourceStatus(Base):
    __tablename__ = "source_status"

    adapter: Mapped[str] = mapped_column(String, primary_key=True)
    reachable: Mapped[int] = mapped_column(Integer, default=1)
    last_ok_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_kind: Mapped[str] = mapped_column(String)
    actor_id: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    subject_type: Mapped[str] = mapped_column(String)
    subject_id: Mapped[str] = mapped_column(String)
    detail: Mapped[str | None] = mapped_column(Text)
