from __future__ import annotations

from datetime import UTC, datetime


class AppClock:
    """System time, or a frozen instant for tests and the slice's grace-period demo."""

    def __init__(self) -> None:
        self._frozen: datetime | None = None

    def now(self) -> datetime:
        if self._frozen is not None:
            return self._frozen
        return datetime.now(UTC)

    def freeze(self, when: datetime) -> None:
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        self._frozen = when.astimezone(UTC)
