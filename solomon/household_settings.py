"""Household preferences: display names, pantry, servings, news topics.

No logins, tokens, or other secrets. The database row is the memory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from solomon.models import Household, Member
from solomon.seed import HOUSEHOLD_ID

DEFAULT_STORAGE = ["Fridge", "Pantry", "Freezer", "Counter"]
DEFAULT_SUPPRESSION_DAYS = 7
DEFAULT_PRESUMED_DISCARD = "archive"
DEFAULT_SERVING_SIZE = 2
DEFAULT_FRESHNESS = "conservative"

TOP_KEYS = frozenset(
    {
        "adults",
        "storage_locations",
        "freshness",
        "suppression_days",
        "presumed_discard",
        "serving_size",
        "news_topics",
    }
)
ADULT_KEYS = frozenset({"id", "display_name"})
FRESHNESS = frozenset({"conservative", "permissive"})
PRESUMED_DISCARD = frozenset({"archive", "review"})


class HouseholdPreferenceError(ValueError):
    pass


@dataclass(frozen=True)
class AdultName:
    id: str | None
    display_name: str


@dataclass(frozen=True)
class HouseholdPreferences:
    adults: tuple[AdultName, ...]
    storage_locations: tuple[str, ...]
    freshness: str
    suppression_days: int
    presumed_discard: str
    serving_size: int
    news_topics: tuple[str, ...]


def ensure_household_columns(engine: Engine) -> None:
    with engine.begin() as connection:
        tables = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "household" in tables:
            columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(household)")
            }
            additions = {
                "suppression_days": "INTEGER DEFAULT 7",
                "presumed_discard": "VARCHAR DEFAULT 'archive'",
                "serving_size": "INTEGER DEFAULT 2",
                "storage_locations_json": "TEXT DEFAULT '[\"Fridge\", \"Pantry\", \"Freezer\", \"Counter\"]'",
                "news_topics_json": "TEXT DEFAULT '[]'",
            }
            for name, ddl in additions.items():
                if name not in columns:
                    connection.exec_driver_sql(f"ALTER TABLE household ADD COLUMN {name} {ddl}")
        if "member" in tables:
            columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(member)")}
            if "sort_order" not in columns:
                connection.exec_driver_sql(
                    "ALTER TABLE member ADD COLUMN sort_order INTEGER DEFAULT 0"
                )


def read_household(session: Session) -> dict:
    household = _household(session)
    adults = session.scalars(
        select(Member).where(Member.role == "adult").order_by(Member.sort_order, Member.id)
    ).all()
    return {
        "adults": [
            {"id": row.id, "display_name": row.display_name} for row in adults
        ],
        "storage_locations": _strings(household.storage_locations_json, DEFAULT_STORAGE),
        "freshness": household.profile,
        "suppression_days": household.suppression_days,
        "presumed_discard": household.presumed_discard,
        "serving_size": household.serving_size,
        "news_topics": _strings(household.news_topics_json, []),
    }


def parse_household(payload: dict) -> HouseholdPreferences:
    extra = set(payload) - TOP_KEYS
    missing = TOP_KEYS - set(payload)
    if extra:
        raise HouseholdPreferenceError(
            "Household preferences do not take a token or a password."
        )
    if missing:
        raise HouseholdPreferenceError("Household preferences need every field in the block.")
    return HouseholdPreferences(
        adults=_adults(payload["adults"]),
        storage_locations=_phrases(payload["storage_locations"], "Storage location"),
        freshness=_choice(payload["freshness"], FRESHNESS, "Freshness is conservative or permissive."),
        suppression_days=_whole_days(payload["suppression_days"]),
        presumed_discard=_choice(
            payload["presumed_discard"],
            PRESUMED_DISCARD,
            "Presumed discard is archive or review.",
        ),
        serving_size=_serving_size(payload["serving_size"]),
        news_topics=_phrases(payload["news_topics"], "News topic", allow_empty=True),
    )


def save_household(session: Session, preferences: HouseholdPreferences) -> dict:
    household = _household(session)
    household.profile = preferences.freshness
    household.suppression_days = preferences.suppression_days
    household.presumed_discard = preferences.presumed_discard
    household.serving_size = preferences.serving_size
    household.storage_locations_json = json.dumps(list(preferences.storage_locations))
    household.news_topics_json = json.dumps(list(preferences.news_topics))
    _save_adults(session, preferences.adults)
    session.flush()
    return read_household(session)


def _household(session: Session) -> Household:
    row = session.get(Household, HOUSEHOLD_ID)
    if row is None:
        raise RuntimeError("household is not seeded")
    return row


def _strings(raw: str | None, fallback: list[str]) -> list[str]:
    if not raw:
        return list(fallback)
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        return list(fallback)
    return [item for item in parsed if isinstance(item, str)]


def _adults(value: object) -> tuple[AdultName, ...]:
    if not isinstance(value, list) or not value:
        raise HouseholdPreferenceError("Keep at least one adult display name.")
    if len(value) > 12:
        raise HouseholdPreferenceError("Twelve adult display names is the limit.")
    names: list[AdultName] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict) or set(item) - ADULT_KEYS:
            raise HouseholdPreferenceError(
                "Household preferences do not take a token or a password."
            )
        raw_id = item.get("id")
        if raw_id is not None and not isinstance(raw_id, str):
            raise HouseholdPreferenceError("Unknown adult.")
        if isinstance(raw_id, str):
            if raw_id in seen:
                raise HouseholdPreferenceError("Each adult is listed once.")
            seen.add(raw_id)
        display_name = _phrase(item.get("display_name"), "Adult display name")
        names.append(AdultName(id=raw_id, display_name=display_name))
    return tuple(names)


def _phrases(value: object, label: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise HouseholdPreferenceError(f"{label}s are a list of phrases.")
    if not value and not allow_empty:
        raise HouseholdPreferenceError(f"Name at least one {label.lower()}.")
    if len(value) > 24:
        raise HouseholdPreferenceError(f"Twenty-four {label.lower()}s is the limit.")
    phrases: list[str] = []
    seen: set[str] = set()
    for item in value:
        phrase = _phrase(item, label)
        key = phrase.casefold()
        if key in seen:
            raise HouseholdPreferenceError(f"Each {label.lower()} is listed once.")
        seen.add(key)
        phrases.append(phrase)
    return tuple(phrases)


def _phrase(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise HouseholdPreferenceError(f"Each {label.lower()} is a short phrase.")
    phrase = " ".join(value.split())
    if not phrase:
        raise HouseholdPreferenceError(f"Each {label.lower()} is a short phrase.")
    if len(phrase) > 80:
        raise HouseholdPreferenceError(f"Each {label.lower()} is a short phrase.")
    return phrase


def _choice(value: object, allowed: frozenset[str], message: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise HouseholdPreferenceError(message)
    return value


def _whole_days(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 365:
        raise HouseholdPreferenceError("Suppression length is a number of days from 1 to 365.")
    return value


def _serving_size(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 24:
        raise HouseholdPreferenceError("Household serving size is a whole number from 1 to 24.")
    return value


def _save_adults(session: Session, adults: tuple[AdultName, ...]) -> None:
    existing = {
        row.id: row
        for row in session.scalars(select(Member).where(Member.role == "adult"))
    }
    kept: set[str] = set()
    for index, adult in enumerate(adults):
        if adult.id is None:
            row = Member(
                id=f"member_{uuid4().hex}",
                display_name=adult.display_name,
                role="adult",
                sort_order=index,
            )
            session.add(row)
            continue
        row = existing.get(adult.id)
        if row is None:
            raise HouseholdPreferenceError("Unknown adult.")
        row.display_name = adult.display_name
        row.sort_order = index
        kept.add(adult.id)
    for member_id, row in existing.items():
        if member_id not in kept:
            session.delete(row)
