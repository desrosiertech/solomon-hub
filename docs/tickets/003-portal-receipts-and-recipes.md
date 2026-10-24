# 003: Receipts and the recipe bank, read by Claude Opus

**What to build:** An Adult submits a receipt photo, or a recipe as a screenshot, a photo of a book page, or a URL. A fake model in tests, and Claude Opus through Nous Portal when a person has signed in, reads it. Receipt lines wait for one tap, then become Inventory. A recipe card the Adult accepts is banked and can be chosen for a later week. The grocery screens from ticket 001 still pass with the model disabled.

**Blocked by:** None for the fake-model path. A live Nous login is a human step on the Solomon VM (`hermes setup --portal`), not a CI step. Ticket 002 (the interim Ollama VM) is deferred, not a prerequisite.

**Status:** ready-for-agent

**GitHub:** https://github.com/desrosiertech/solomon-hub/issues/7

## Out of scope

The 64 GB kit, the local 8B bench, Gmail intake, Overseerr, voice, the Tool Gateway (web search, generated pictures, cloud browser, cloud terminal), and any rebuild of the freshness rules.

## Acceptance criteria

- [ ] With the model disabled, the grocery flows from ticket 001 still pass, and a receipt or recipe submission explains that the reader is off.
- [ ] An Adult can see whether Nous Portal is signed in. A health check does not send Inventory, recipes, or mail.
- [ ] A receipt image returns proposed lines. One tap adds them as Inventory observations. Non-food lines are not added. The same image twice does not double-add.
- [ ] Storage location follows the kind of food (fridge, freezer, pantry, counter) and can be corrected before the tap.
- [ ] A screenshot, a book photo, and a URL each return a recipe card. Accepting it banks the recipe. The URL's page text is not stored as a skill.
- [ ] A banked recipe can be attached to a planned night. An existing planned night is not overwritten silently.
- [ ] Tests use a fake reader. CI does not call Nous, and it does not need a downloaded model.
- [ ] The original image stays in Solomon's files. Hermes memory is unchanged by the receipt or the page.

## Notes for the implementer

Read ADR-0008 and ADR-0009. Use `/tdd`. The food engine still computes freshness and the shopping list. The model only proposes.
