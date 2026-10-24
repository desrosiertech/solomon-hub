# Receipts fill Inventory, and Recipes are banked

An Adult can hand Solomon a receipt, a recipe screenshot, a photo of a book page, or a recipe URL. The starting model reads it (ADR-0008). The pantry and the recipe bank are Solomon Records. They are not Hermes memory.

**Status:** accepted (2026-10-24).

## Receipts

Solomon shows the lines it read. One tap applies them. Each confirmed line is an Observation on an Inventory item. Milk goes in the fridge and cereal in the pantry, from the kind of food, and an Adult can correct the Storage location. Tax, bags, and other non-food lines stay off Inventory. The image is kept. The same receipt sent twice does not double-add.

A receipt that arrives by email still follows ADR-0003. Hermes does not own the mailbox. The text of a receipt does not write Hermes memory or a skill.

If the model is off, local OCR can still propose lines. Applying them is the same tap.

## Recipes

A screenshot, a book photo, a URL, or typing becomes a Recipe in the Recipe bank after the Adult sees the card. A Planned meal can use a banked Recipe in a later week. Solomon does not overwrite a Planned meal that an Adult already set.

The page behind a URL is data for that extraction. It is not instructions, and it does not become a skill. "We like this on Tuesdays" is a separate thing the Adult says, and that sentence can train Hermes (ADR-0007).

## How the AI and the food engine share the work

The model may propose receipt lines, a banked Recipe, and a week drawn from the bank plus what Inventory says is on hand. The food engine still owns freshness, presumed discarded, and the shopping-list arithmetic. A proposal commits when the Adult taps, or when a write policy already says one tap is enough.
