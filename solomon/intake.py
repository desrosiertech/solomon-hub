"""Turn a receipt or a recipe the Adult submitted into Records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import select

from solomon.food import default_storage
from solomon.models import (
    PlannedMealRow,
    ReceiptLineRow,
    ReceiptRow,
    RecipeIngredientRow,
    RecipeProposalRow,
    RecipeRow,
)
from solomon.provider import ReaderOff
from solomon.seed import MEMBER_ID
from solomon.service import FoodStore, _new_id


def save_blob(blob_dir: Path, data: bytes) -> Path:
    blob_dir.mkdir(parents=True, exist_ok=True)
    path = blob_dir / hashlib.sha256(data).hexdigest()
    if not path.exists():
        path.write_bytes(data)
    return path


def _line_payload(line: ReceiptLineRow) -> dict:
    return {
        "id": line.id,
        "label": line.label,
        "category": line.category,
        "storage": line.storage,
        "food": bool(line.food),
    }


def _receipt_payload(receipt: ReceiptRow, lines: list[ReceiptLineRow]) -> dict:
    return {"id": receipt.id, "lines": [_line_payload(line) for line in lines]}


def submit_receipt(store: FoodStore, image: bytes) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    with store.session() as session:
        existing = session.scalar(select(ReceiptRow).where(ReceiptRow.sha256 == digest))
        if existing is not None:
            lines = session.scalars(
                select(ReceiptLineRow).where(ReceiptLineRow.receipt_id == existing.id)
            ).all()
            return _receipt_payload(existing, list(lines))

    try:
        read = store.provider.read_receipt(image)
    except ReaderOff:
        raise
    path = save_blob(store.blob_dir, image)
    with store.session() as session:
        receipt = ReceiptRow(
            id=_new_id("rcpt"),
            sha256=digest,
            image_path=str(path),
            status="proposed",
            created_at=store.clock.now(),
        )
        session.add(receipt)
        lines: list[ReceiptLineRow] = []
        for raw in read:
            category = raw.get("category") or "unknown"
            line = ReceiptLineRow(
                id=_new_id("line"),
                receipt_id=receipt.id,
                label=raw["label"],
                category=category,
                storage=default_storage(category),
                food=1 if raw.get("food", True) else 0,
            )
            session.add(line)
            lines.append(line)
        session.commit()
        return _receipt_payload(receipt, lines)


def apply_receipt(store: FoodStore, receipt_id: str, corrections: list[dict]) -> dict:
    with store.session() as session:
        receipt = session.get(ReceiptRow, receipt_id)
        if receipt is None:
            raise KeyError(receipt_id)
        lines = list(
            session.scalars(select(ReceiptLineRow).where(ReceiptLineRow.receipt_id == receipt_id))
        )
        if receipt.status == "applied":
            return {"added": 0}

    chosen = {row["id"]: row.get("storage") for row in corrections}
    added = 0
    for line in lines:
        if not line.food or line.id not in chosen:
            continue
        storage = chosen[line.id] or line.storage
        item = store.add_item(
            {
                "label": line.label,
                "category": line.category,
                "storage": storage,
                "source": "receipt_confirmed",
            }
        )
        added += 1
        with store.session() as session:
            stored = session.get(ReceiptLineRow, line.id)
            if stored is not None:
                stored.item_id = item["id"]
                stored.storage = storage
                session.commit()
    with store.session() as session:
        receipt = session.get(ReceiptRow, receipt_id)
        if receipt is not None and added:
            receipt.status = "applied"
            store._audit(
                session,
                action="receipt.applied",
                actor_kind="member",
                actor_id=MEMBER_ID,
                subject_type="receipt",
                subject_id=receipt_id,
                detail=f"{added} lines",
            )
            session.commit()
    return {"added": added}


def propose_recipe(
    store: FoodStore,
    *,
    kind: str,
    image: bytes | None = None,
    url: str | None = None,
    fetch_page,
) -> dict:
    page = None
    image_path = None
    if kind == "url":
        if not url:
            raise ValueError("A recipe URL is required")
        probe = store.provider.status()
        if not probe.get("signed_in"):
            raise ReaderOff("The reader is off.")
        page = fetch_page(url) if fetch_page else ""
    elif kind in {"screenshot", "book_photo"}:
        if not image:
            raise ValueError("A recipe image is required")
    else:
        raise ValueError("source_kind must be url, screenshot, or book_photo")

    try:
        card = store.provider.read_recipe(kind=kind, image=image, url=url, page=page)
    except ReaderOff:
        raise
    if image:
        image_path = str(save_blob(store.blob_dir, image))
    ingredients = list(card.get("ingredients") or [])
    steps = list(card.get("steps") or [])
    with store.session() as session:
        proposal = RecipeProposalRow(
            id=_new_id("prop"),
            title=card["title"],
            source_kind=kind,
            source_url=url,
            ingredients_json=json.dumps(ingredients),
            steps_json=json.dumps(steps),
            image_path=image_path,
            status="proposed",
        )
        session.add(proposal)
        session.commit()
        return _proposal_payload(proposal)


def _proposal_payload(proposal: RecipeProposalRow) -> dict:
    return {
        "id": proposal.id,
        "title": proposal.title,
        "source_kind": proposal.source_kind,
        "source_url": proposal.source_url,
        "ingredients": json.loads(proposal.ingredients_json),
        "steps": json.loads(proposal.steps_json),
        "status": proposal.status,
    }


def accept_recipe(store: FoodStore, proposal_id: str) -> dict:
    with store.session() as session:
        proposal = session.get(RecipeProposalRow, proposal_id)
        if proposal is None:
            raise KeyError(proposal_id)
        if proposal.recipe_id:
            recipe = session.get(RecipeRow, proposal.recipe_id)
            return {"id": proposal.recipe_id, "title": recipe.title if recipe else proposal.title, "status": "banked"}
        recipe = RecipeRow(
            id=_new_id("recipe"),
            title=proposal.title,
            source_kind=proposal.source_kind,
            source_url=proposal.source_url,
            steps_json=proposal.steps_json,
            image_path=proposal.image_path,
        )
        session.add(recipe)
        for text in json.loads(proposal.ingredients_json):
            session.add(
                RecipeIngredientRow(
                    recipe_id=recipe.id,
                    canonical=text,
                    staple=0,
                )
            )
        proposal.status = "banked"
        proposal.recipe_id = recipe.id
        store._audit(
            session,
            action="recipe.banked",
            actor_kind="member",
            actor_id=MEMBER_ID,
            subject_type="recipe",
            subject_id=recipe.id,
            detail=proposal.title,
        )
        session.commit()
        return {"id": recipe.id, "title": recipe.title, "status": "banked"}


def list_recipes(store: FoodStore) -> dict:
    with store.session() as session:
        rows = session.scalars(select(RecipeRow)).all()
        recipes = []
        for row in rows:
            ingredients = session.scalars(
                select(RecipeIngredientRow).where(RecipeIngredientRow.recipe_id == row.id)
            ).all()
            recipes.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "source_kind": row.source_kind,
                    "source_url": row.source_url,
                    "ingredients": [item.canonical for item in ingredients],
                    "steps": json.loads(row.steps_json or "[]"),
                }
            )
        return {"recipes": recipes}


def plan_meal(store: FoodStore, on: str, recipe_id: str) -> dict:
    with store.session() as session:
        existing = session.scalar(select(PlannedMealRow).where(PlannedMealRow.on_date == on))
        if existing is not None:
            raise FileExistsError(on)
        recipe = session.get(RecipeRow, recipe_id)
        if recipe is None:
            raise KeyError(recipe_id)
        night = PlannedMealRow(
            id=_new_id("night"),
            on_date=on,
            recipe_id=recipe.id,
            title=recipe.title,
        )
        session.add(night)
        session.commit()
        return {"on": night.on_date, "recipe_id": night.recipe_id, "title": night.title}


def list_planned(store: FoodStore) -> dict:
    with store.session() as session:
        rows = session.scalars(select(PlannedMealRow).order_by(PlannedMealRow.on_date)).all()
        return {
            "nights": [
                {"on": row.on_date, "recipe_id": row.recipe_id, "title": row.title} for row in rows
            ]
        }
