"""Deterministic food engine. Never calls a model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

PROFILE_FACTOR = {
    "conservative": 0.8,
    "balanced": 1.0,
    "permissive": 1.2,
}

# Days by category then storage. None means the combination is not used.
BASE_DAYS: dict[str, dict[str, int | None]] = {
    "leafy_greens": {"pantry": None, "fridge": 5, "freezer": 180, "counter": 1},
    "berries": {"pantry": None, "fridge": 4, "freezer": 240, "counter": 1},
    "whole_melon": {"pantry": None, "fridge": 7, "freezer": None, "counter": 5},
    "cut_fruit": {"pantry": None, "fridge": 3, "freezer": 240, "counter": None},
    "dairy_milk": {"pantry": None, "fridge": 7, "freezer": 90, "counter": None},
    "hard_cheese": {"pantry": None, "fridge": 28, "freezer": 180, "counter": None},
    "raw_poultry_or_ground_meat": {
        "pantry": None,
        "fridge": 2,
        "freezer": 120,
        "counter": None,
    },
    "cooked_leftovers": {"pantry": None, "fridge": 3, "freezer": 90, "counter": None},
    "bread": {"pantry": 5, "fridge": 10, "freezer": 90, "counter": 4},
    "dry_goods": {"pantry": 365, "fridge": None, "freezer": None, "counter": 365},
    "canned_unopened": {"pantry": 730, "fridge": None, "freezer": None, "counter": None},
    "unknown": {"pantry": 7, "fridge": 4, "freezer": 90, "counter": 2},
}

OPENED_FACTOR = 0.5
MIN_OPENED_DAYS = 1.0

WindowSource = Literal[
    "user_override", "package_date", "product_guidance", "category_default"
]


ItemState = Literal[
    "active",
    "use_soon",
    "past_window",
    "stale",
    "presumed_discarded",
    "consumed",
    "discarded",
]

TERMINAL_STATES = frozenset({"consumed", "discarded", "presumed_discarded"})
UNSURFACED_STATES = TERMINAL_STATES | frozenset({"stale"})


@dataclass(frozen=True)
class HouseholdSettings:
    profile: str = "conservative"
    grace_period: timedelta = timedelta(days=3)
    presume_after: timedelta = timedelta(days=4)
    dismiss_period: timedelta = timedelta(days=7)
    use_soon_lead_fraction: float = 0.25
    use_soon_lead_min: timedelta = timedelta(days=1)
    presumed_discard_mode: str = "auto_archive"
    max_ideas: int = 3
    max_use_soon: int = 3
    max_missing: int = 1
    ideas_stale_after: timedelta = timedelta(hours=2)


@dataclass(frozen=True)
class EstimatedWindow:
    estimated_use_by: datetime
    window_days: float
    window_source: WindowSource
    explanation: str
    anchor: datetime


def default_storage(category: str) -> str:
    table = BASE_DAYS.get(category, BASE_DAYS["unknown"])
    for place in ("fridge", "pantry", "counter", "freezer"):
        if table.get(place):
            return place
    return "pantry"


def _label(slug: str) -> str:
    return slug.replace("_", " ")


def _format_days(days: float) -> str:
    if days == int(days):
        return f"about {int(days)} days"
    return f"about {days:g} days"


def assign_estimated_window(
    *,
    category: str,
    storage: str,
    acquired_at: datetime,
    opened_at: datetime | None = None,
    profile: str = "conservative",
    override_use_by: datetime | None = None,
) -> EstimatedWindow:
    if override_use_by is not None:
        raise NotImplementedError("user_override is not part of this slice's tests yet")

    table = BASE_DAYS.get(category) or BASE_DAYS["unknown"]
    if storage not in table or table[storage] is None:
        raise ValueError(
            f"storage {storage!r} is not valid for category {category!r}"
        )

    base = float(table[storage])
    factor = PROFILE_FACTOR[profile]
    window_days = round(base * factor, 4)
    if opened_at is not None:
        window_days = max(MIN_OPENED_DAYS, round(window_days * OPENED_FACTOR, 4))

    anchor = opened_at or acquired_at
    estimated_use_by = anchor + timedelta(days=window_days)
    bought = acquired_at.strftime("%b ") + str(acquired_at.day)
    explanation = (
        f"{storage.capitalize()} · {_label(category)} · bought {bought} · "
        f"{_format_days(window_days)}"
    )
    return EstimatedWindow(
        estimated_use_by=estimated_use_by,
        window_days=window_days,
        window_source="category_default",
        explanation=explanation,
        anchor=anchor,
    )


def use_soon_lead(window_days: float, settings: HouseholdSettings) -> timedelta:
    fraction = timedelta(days=window_days * settings.use_soon_lead_fraction)
    return max(settings.use_soon_lead_min, fraction)


def next_item_state(
    estimated_use_by: datetime,
    window_days: float,
    now: datetime,
    settings: HouseholdSettings,
) -> ItemState:
    if now >= estimated_use_by + settings.grace_period + settings.presume_after:
        return "presumed_discarded"
    if now >= estimated_use_by + settings.grace_period:
        return "stale"
    if now >= estimated_use_by:
        return "past_window"
    if now >= estimated_use_by - use_soon_lead(window_days, settings):
        return "use_soon"
    return "active"


ConfidenceBand = Literal["confident", "probable", "uncertain"]
Availability = Literal["available", "probably_available", "quantity_uncertain", "missing"]

SOURCE_BASE = {
    "seen": 0.95,
    "quick_add": 0.9,
    "barcode": 0.9,
    "receipt_confirmed": 0.85,
    "receipt_auto": 0.7,
    "agent_proposed_applied": 0.7,
}


@dataclass(frozen=True)
class InventorySnapshot:
    id: str
    label: str
    category: str
    storage: str
    quantity_kind: str
    state: str
    confidence: float
    confidence_band: str
    estimated_use_by: datetime
    window_epoch: str
    is_leftover: bool
    quantity_count: int | None = None


@dataclass(frozen=True)
class RecipeIngredient:
    canonical: str
    staple: bool = False


@dataclass(frozen=True)
class Recipe:
    id: str
    title: str
    ingredients: tuple[RecipeIngredient, ...]


@dataclass(frozen=True)
class SuppressionRule:
    kind: str
    subject_type: str
    subject_id: str
    key: str | None = None
    until: datetime | None = None


@dataclass(frozen=True)
class Suggestion:
    key: str
    kind: str
    subject_type: str
    subject_id: str
    title: str
    detail: str


@dataclass(frozen=True)
class MealIdea:
    key: str
    recipe_id: str
    title: str
    have: tuple[str, ...]
    probably_have: tuple[str, ...]
    check_amount: tuple[str, ...]
    missing: tuple[str, ...]
    score: int


def confidence_band(confidence: float) -> ConfidenceBand:
    if confidence >= 0.75:
        return "confident"
    if confidence >= 0.4:
        return "probable"
    return "uncertain"


def decay_for_age_ratio(age_ratio: float, grace_ratio: float) -> float:
    if age_ratio <= 0.5:
        return 1.0
    if age_ratio <= 1.0:
        t = (age_ratio - 0.5) / 0.5
        return 1.0 + t * (0.3 - 1.0)
    span = grace_ratio if grace_ratio > 0 else 1.0
    t = min(1.0, (age_ratio - 1.0) / span)
    return 0.3 + t * (0.1 - 0.3)


def derive_confidence(
    *,
    source: str,
    days_since_strong: float,
    window_days: float,
    grace_period: timedelta,
) -> float:
    base = SOURCE_BASE.get(source, SOURCE_BASE["quick_add"])
    age_ratio = days_since_strong / window_days if window_days else 1.0
    grace_ratio = (grace_period / timedelta(days=window_days)) if window_days else 1.0
    return round(base * decay_for_age_ratio(age_ratio, grace_ratio), 4)


def _surfaced(item: InventorySnapshot) -> bool:
    return item.state not in UNSURFACED_STATES


def use_soon_suggestions(
    items: list[InventorySnapshot],
    *,
    settings: HouseholdSettings,
) -> list[Suggestion]:
    candidates: list[tuple[int, float, Suggestion]] = []
    for item in items:
        if item.state == "past_window":
            suggestion = Suggestion(
                key=f"past_window:{item.id}",
                kind="past_window",
                subject_type="item",
                subject_id=item.id,
                title=item.label,
                detail="may be past its expected freshness window",
            )
            candidates.append((0, 0.0, suggestion))
        elif item.state == "use_soon":
            suggestion = Suggestion(
                key=f"use_soon:{item.id}:{item.window_epoch}",
                kind="use_soon",
                subject_type="item",
                subject_id=item.id,
                title=item.label,
                detail=f"{item.storage.capitalize()} · estimated use-by window",
            )
            remaining = item.estimated_use_by.timestamp()
            candidates.append((1, remaining, suggestion))
    candidates.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in candidates[: settings.max_use_soon]]


def filter_suggestions(
    suggestions: list[Suggestion],
    rules: tuple[SuppressionRule, ...] | list[SuppressionRule],
    *,
    now: datetime | None = None,
) -> list[Suggestion]:
    active = list(rules)
    kept: list[Suggestion] = []
    for suggestion in suggestions:
        suppressed = False
        for rule in active:
            if rule.kind == "stop_asking" and (
                (
                    rule.subject_type == suggestion.subject_type
                    and rule.subject_id == suggestion.subject_id
                )
                or (rule.key is not None and rule.key == suggestion.key)
            ):
                suppressed = True
                break
            if (
                rule.kind == "dismissal"
                and rule.key == suggestion.key
                and (rule.until is None or now is None or now < rule.until)
            ):
                suppressed = True
                break
        if not suppressed:
            kept.append(suggestion)
    return kept


def _match_item(canonical: str, items: list[InventorySnapshot]) -> InventorySnapshot | None:
    for item in items:
        if _surfaced(item) and item.category == canonical:
            return item
    return None


def classify_ingredient(
    ingredient: RecipeIngredient,
    items: list[InventorySnapshot],
) -> Availability:
    item = _match_item(ingredient.canonical, items)
    if item is None:
        return "missing"
    if item.confidence_band == "uncertain" and item.state == "past_window":
        return "missing"
    if item.quantity_kind in {"low", "unknown"}:
        return "quantity_uncertain"
    if item.confidence_band == "confident":
        return "available"
    if item.confidence_band == "probable":
        return "probably_available"
    return "quantity_uncertain"


def meal_ideas(
    items: list[InventorySnapshot],
    recipes: tuple[Recipe, ...] | list[Recipe],
    *,
    settings: HouseholdSettings,
) -> list[MealIdea]:
    ideas: list[MealIdea] = []
    for recipe in recipes:
        have: list[str] = []
        probably: list[str] = []
        check: list[str] = []
        missing: list[str] = []
        used_ids: list[str] = []
        uses_use_soon = 0
        uses_leftover = 0
        uncertain = 0
        missing_count = 0
        for ingredient in recipe.ingredients:
            availability = classify_ingredient(ingredient, items)
            item = _match_item(ingredient.canonical, items)
            name = item.label if item else _label(ingredient.canonical)
            if availability == "available":
                have.append(name)
            elif availability == "probably_available":
                probably.append(name)
            elif availability == "quantity_uncertain":
                check.append(name)
                uncertain += 1
            elif not ingredient.staple:
                missing.append(name)
                missing_count += 1
            if item is not None:
                used_ids.append(item.id)
                if item.state in {"use_soon", "past_window"}:
                    uses_use_soon += 1
                if item.is_leftover:
                    uses_leftover += 1
        if not have and not probably and not check:
            continue
        if missing_count > settings.max_missing:
            continue
        score = 3 * uses_use_soon + uses_leftover - 2 * missing_count - uncertain
        key_ids = ",".join(sorted(used_ids))
        ideas.append(
            MealIdea(
                key=f"meal_idea:{recipe.id}:{key_ids}",
                recipe_id=recipe.id,
                title=recipe.title,
                have=tuple(have),
                probably_have=tuple(probably),
                check_amount=tuple(check),
                missing=tuple(missing),
                score=score,
            )
        )
    ideas.sort(key=lambda idea: (-idea.score, idea.title))
    return ideas[: settings.max_ideas]
