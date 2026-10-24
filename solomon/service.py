from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from solomon.clock import AppClock
from solomon.food import (
    HouseholdSettings,
    InventorySnapshot,
    Recipe,
    RecipeIngredient,
    SuppressionRule,
    assign_estimated_window,
    confidence_band,
    derive_confidence,
    filter_suggestions,
    meal_ideas,
    next_item_state,
    use_soon_suggestions,
)
from solomon.models import (
    AuditEvent,
    Base,
    Household,
    InventoryItem,
    InventoryObservation,
    Member,
    RecipeIngredientRow,
    RecipeRow,
    StateTransition,
    SuppressionRuleRow,
)
from solomon.provider import DisabledProvider, ModelProvider
from solomon.seed import HOUSEHOLD_ID, MEMBER_ID, MEMBER_NAME, SEED_RECIPES

WINDOW_LABEL = "Estimated use-by window"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def make_engine(db_path: Path | str) -> Engine:
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL")
        connection.commit()
    Base.metadata.create_all(engine)
    return engine


def seed_if_empty(session: Session) -> None:
    if session.get(Household, HOUSEHOLD_ID):
        return
    session.add(
        Household(
            id=HOUSEHOLD_ID,
            profile="conservative",
            grace_period_minutes=3 * 24 * 60,
            presume_after_minutes=4 * 24 * 60,
        )
    )
    session.add(Member(id=MEMBER_ID, display_name=MEMBER_NAME, role="adult"))
    for recipe in SEED_RECIPES:
        session.add(RecipeRow(id=recipe.id, title=recipe.title))
        for ingredient in recipe.ingredients:
            session.add(
                RecipeIngredientRow(
                    recipe_id=recipe.id,
                    canonical=ingredient.canonical,
                    staple=1 if ingredient.staple else 0,
                )
            )
    session.commit()


def settings_from(household: Household) -> HouseholdSettings:
    return HouseholdSettings(
        profile=household.profile,
        grace_period=timedelta(minutes=household.grace_period_minutes),
        presume_after=timedelta(minutes=household.presume_after_minutes),
    )


def _aware(value):
    from datetime import UTC, datetime

    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class FoodStore:
    def __init__(
        self,
        engine: Engine,
        clock: AppClock,
        provider: ModelProvider | None = None,
    ) -> None:
        self.engine = engine
        self.clock = clock
        self.provider = provider or DisabledProvider()
        self._session = sessionmaker(bind=engine, expire_on_commit=False)

    def session(self) -> Session:
        return self._session()

    def household(self, session: Session) -> Household:
        row = session.get(Household, HOUSEHOLD_ID)
        if row is None:
            raise RuntimeError("household is not seeded")
        return row

    def update_settings(
        self, grace_period_minutes: int | None = None, presume_after_minutes: int | None = None
    ) -> dict:
        with self.session() as session:
            household = self.household(session)
            if grace_period_minutes is not None:
                household.grace_period_minutes = grace_period_minutes
            if presume_after_minutes is not None:
                household.presume_after_minutes = presume_after_minutes
            session.commit()
            return {
                "grace_period_minutes": household.grace_period_minutes,
                "presume_after_minutes": household.presume_after_minutes,
                "profile": household.profile,
            }

    def add_item(self, payload: dict) -> dict:
        now = self.clock.now()
        leftover = bool(payload.get("leftover"))
        category = payload.get("category") or (
            "cooked_leftovers" if leftover else "unknown"
        )
        storage = payload.get("storage") or "fridge"
        acquired_at = payload.get("acquired_at")
        if acquired_at:
            from datetime import datetime

            acquired = datetime.fromisoformat(acquired_at)
        else:
            acquired = now
        window = assign_estimated_window(
            category=category,
            storage=storage,
            acquired_at=acquired,
            profile="conservative",
        )
        settings = None
        with self.session() as session:
            household = self.household(session)
            settings = settings_from(household)
            confidence = derive_confidence(
                source="quick_add",
                days_since_strong=0.0,
                window_days=window.window_days,
                grace_period=settings.grace_period,
            )
            state = next_item_state(
                window.estimated_use_by, window.window_days, now, settings
            )
            item = InventoryItem(
                id=_new_id("inv"),
                label=payload["label"],
                category=category,
                storage=storage,
                quantity_kind=payload.get("quantity_kind") or "some",
                quantity_count=payload.get("quantity_count"),
                leftover=1 if leftover or category == "cooked_leftovers" else 0,
                state=state,
                confidence=confidence,
                confidence_band=confidence_band(confidence),
                acquired_at=acquired,
                opened_at=None,
                estimated_use_by=window.estimated_use_by,
                window_days=window.window_days,
                window_source=window.window_source,
                window_explain=window.explanation,
                window_epoch=window.estimated_use_by.date().isoformat(),
                last_strong_observation_at=acquired,
                closed_reason=None,
            )
            session.add(item)
            session.add(
                InventoryObservation(
                    id=_new_id("obs"),
                    item_id=item.id,
                    kind="acquired",
                    source="quick_add",
                    actor=f"member:{MEMBER_ID}",
                    observed_at=now,
                )
            )
            self._audit(
                session,
                action="inventory.added",
                actor_kind="member",
                actor_id=MEMBER_ID,
                subject_type="inventory_item",
                subject_id=item.id,
                detail=item.label,
            )
            self._refresh_ideas(session, household, settings)
            session.commit()
            return self._item_payload(item)

    def list_items(self) -> dict:
        self.age()
        with self.session() as session:
            rows = session.scalars(select(InventoryItem)).all()
            return {"items": [self._item_payload(row) for row in rows]}

    def home(self) -> dict:
        bundle = self._suggestion_bundle()
        return {"ideas": bundle["ideas"], "use_soon": bundle["use_soon"]}

    def meals(self) -> dict:
        return self._suggestion_bundle()

    def stop_asking(self, key: str) -> None:
        self.age()
        with self.session() as session:
            household = self.household(session)
            settings = settings_from(household)
            suggestions = self._current_use_soon(session, settings)
            match = next((row for row in suggestions if row.key == key), None)
            if match is None:
                raise KeyError(key)
            session.add(
                SuppressionRuleRow(
                    id=_new_id("sup"),
                    kind="stop_asking",
                    subject_type=match.subject_type,
                    subject_id=match.subject_id,
                    key=match.key,
                    created_at=self.clock.now(),
                )
            )
            self._audit(
                session,
                action="suggestion.stop_asking",
                actor_kind="member",
                actor_id=MEMBER_ID,
                subject_type=match.subject_type,
                subject_id=match.subject_id,
                detail=match.title,
            )
            self._refresh_ideas(session, household, settings)
            session.commit()

    def age(self) -> dict:
        now = self.clock.now()
        changed = 0
        with self.session() as session:
            household = self.household(session)
            settings = settings_from(household)
            items = list(session.scalars(select(InventoryItem)))
            for item in items:
                if item.state in {"consumed", "discarded", "presumed_discarded"}:
                    continue
                target = next_item_state(
                    _aware(item.estimated_use_by), item.window_days, now, settings
                )
                if target == item.state:
                    continue
                exists = session.scalar(
                    select(StateTransition).where(
                        StateTransition.item_id == item.id,
                        StateTransition.to_state == target,
                        StateTransition.window_epoch == item.window_epoch,
                    )
                )
                if exists:
                    item.state = target
                    if target == "presumed_discarded":
                        item.closed_reason = "presumed_discarded"
                    continue
                session.add(
                    StateTransition(
                        id=_new_id("trn"),
                        item_id=item.id,
                        from_state=item.state,
                        to_state=target,
                        window_epoch=item.window_epoch,
                        at=now,
                        actor="job:aging",
                    )
                )
                item.state = target
                if target == "presumed_discarded":
                    item.closed_reason = "presumed_discarded"
                    session.add(
                        InventoryObservation(
                            id=_new_id("obs"),
                            item_id=item.id,
                            kind="presumed_discarded",
                            source="job:aging",
                            actor="job:aging",
                            observed_at=now,
                        )
                    )
                    self._audit(
                        session,
                        action="inventory.presumed_discarded",
                        actor_kind="job",
                        actor_id="job:aging",
                        subject_type="inventory_item",
                        subject_id=item.id,
                        detail=item.label,
                    )
                changed += 1
            if changed:
                self._refresh_ideas(session, household, settings)
            session.commit()
        return {"changed": changed}

    def audit(self) -> dict:
        with self.session() as session:
            rows = session.scalars(select(AuditEvent).order_by(AuditEvent.at, AuditEvent.id)).all()
            return {
                "events": [
                    {
                        "id": row.id,
                        "at": _aware(row.at).isoformat(),
                        "actor_kind": row.actor_kind,
                        "actor_id": row.actor_id,
                        "action": row.action,
                        "subject_type": row.subject_type,
                        "subject_id": row.subject_id,
                        "detail": row.detail,
                    }
                    for row in rows
                ]
            }

    def _suggestion_bundle(self) -> dict:
        self.age()
        now = self.clock.now()
        with self.session() as session:
            household = self.household(session)
            settings = settings_from(household)
            use_soon = [
                {
                    "key": row.key,
                    "kind": row.kind,
                    "subject_id": row.subject_id,
                    "title": row.title,
                    "detail": row.detail,
                }
                for row in self._current_use_soon(session, settings)
            ]
            ideas, generated_at = self._ideas_payload(session, household, settings)
            state = "empty"
            if ideas:
                state = "ready"
                if generated_at is not None and now >= generated_at + settings.ideas_stale_after:
                    state = "stale"
            return {
                "ideas": ideas,
                "use_soon": use_soon,
                "ideas_card": {
                    "state": state,
                    "generated_at": generated_at.isoformat() if generated_at else None,
                },
            }

    def _current_use_soon(self, session: Session, settings: HouseholdSettings):
        snapshots = [self._snapshot(row) for row in session.scalars(select(InventoryItem))]
        rules = tuple(self._rules(session))
        return filter_suggestions(use_soon_suggestions(snapshots, settings=settings), rules)

    def _ideas_payload(
        self, session: Session, household: Household, settings: HouseholdSettings
    ) -> tuple[list[dict], object]:
        if household.ideas_json is None:
            self._refresh_ideas(session, household, settings)
            session.flush()
        ideas = json.loads(household.ideas_json or "[]")
        return ideas, _aware(household.ideas_generated_at) if household.ideas_generated_at else None

    def _refresh_ideas(
        self, session: Session, household: Household, settings: HouseholdSettings
    ) -> None:
        snapshots = [self._snapshot(row) for row in session.scalars(select(InventoryItem))]
        recipes = self._recipes(session)
        ideas = meal_ideas(snapshots, recipes, settings=settings)
        household.ideas_json = json.dumps(
            [
                {
                    "key": idea.key,
                    "title": idea.title,
                    "have": list(idea.have),
                    "probably_have": list(idea.probably_have),
                    "check_amount": list(idea.check_amount),
                    "missing": list(idea.missing),
                }
                for idea in ideas
            ]
        )
        household.ideas_generated_at = self.clock.now()

    def _recipes(self, session: Session) -> list[Recipe]:
        recipes: list[Recipe] = []
        for row in session.scalars(select(RecipeRow)):
            ingredients = tuple(
                RecipeIngredient(canonical=ing.canonical, staple=bool(ing.staple))
                for ing in session.scalars(
                    select(RecipeIngredientRow).where(RecipeIngredientRow.recipe_id == row.id)
                )
            )
            recipes.append(Recipe(id=row.id, title=row.title, ingredients=ingredients))
        return recipes

    def _rules(self, session: Session) -> list[SuppressionRule]:
        return [
            SuppressionRule(
                kind=row.kind,
                subject_type=row.subject_type,
                subject_id=row.subject_id,
                key=row.key,
            )
            for row in session.scalars(select(SuppressionRuleRow))
        ]

    def _snapshot(self, row: InventoryItem) -> InventorySnapshot:
        return InventorySnapshot(
            id=row.id,
            label=row.label,
            category=row.category,
            storage=row.storage,
            quantity_kind=row.quantity_kind,
            quantity_count=row.quantity_count,
            state=row.state,
            confidence=row.confidence,
            confidence_band=row.confidence_band,
            estimated_use_by=_aware(row.estimated_use_by),
            window_epoch=row.window_epoch,
            is_leftover=bool(row.leftover),
        )

    def _item_payload(self, item: InventoryItem) -> dict:
        return {
            "id": item.id,
            "label": item.label,
            "category": item.category,
            "storage": item.storage,
            "quantity_kind": item.quantity_kind,
            "quantity_count": item.quantity_count,
            "leftover": bool(item.leftover),
            "state": item.state,
            "confidence": item.confidence,
            "confidence_band": item.confidence_band,
            "acquired_at": _aware(item.acquired_at).isoformat(),
            "estimated_use_by": _aware(item.estimated_use_by).isoformat(),
            "window_source": item.window_source,
            "window_explain": item.window_explain,
            "window_label": WINDOW_LABEL,
            "closed_reason": item.closed_reason,
        }

    def _audit(
        self,
        session: Session,
        *,
        action: str,
        actor_kind: str,
        actor_id: str,
        subject_type: str,
        subject_id: str,
        detail: str | None,
    ) -> None:
        session.add(
            AuditEvent(
                id=_new_id("aud"),
                at=self.clock.now(),
                actor_kind=actor_kind,
                actor_id=actor_id,
                action=action,
                subject_type=subject_type,
                subject_id=subject_id,
                detail=detail,
            )
        )
