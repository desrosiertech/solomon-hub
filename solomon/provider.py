"""ModelProvider seam (ADR-0001). The grocery slice uses Disabled only."""

from __future__ import annotations

from typing import Any, Protocol


class ModelProvider(Protocol):
    name: str

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


class DisabledProvider:
    name = "Disabled"

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise RuntimeError("ModelProvider is Disabled")
