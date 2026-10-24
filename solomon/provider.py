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


class ReaderOff(RuntimeError):
    """The household model is not available to read a receipt or a recipe."""


class DisabledProvider:
    name = "Disabled"

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise RuntimeError("ModelProvider is Disabled")

    def status(self) -> dict[str, Any]:
        return {"name": self.name, "signed_in": False, "reachable": False}

    def read_receipt(self, image: bytes) -> list[dict[str, Any]]:
        raise ReaderOff("The reader is off.")

    def read_recipe(
        self,
        *,
        kind: str,
        image: bytes | None = None,
        url: str | None = None,
        page: str | None = None,
    ) -> dict[str, Any]:
        raise ReaderOff("The reader is off.")
