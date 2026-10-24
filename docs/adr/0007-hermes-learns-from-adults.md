# Hermes learns from what Adults tell Solomon

What an Adult says in Solomon trains Hermes. That is the reason Hermes is in the house. Training means Hermes memory and skills, which later sessions load. It does not mean fine-tuning Claude or any local weights. The pantry and the recipe bank are Solomon Records (ADR-0009), not this memory.

**Status:** accepted (2026-10-24). Replaces the "disable household-facts memory" and "self-improved skills off" rows in `docs/plan/07-hermes-skills.md`.

## How Hermes learns

Documented on the Hermes site, re-check on install day. **[documented]** https://hermes-agent.nousresearch.com/docs/user-guide/features/memory and https://hermes-agent.nousresearch.com/docs/user-guide/features/skills

- `MEMORY.md` (about 2,200 characters) and `USER.md` (about 1,375 characters) in the Hermes home. Both are injected at the start of the next session.
- Skills under `~/.hermes/skills/`. A skill is a procedure Hermes can load when the situation matches. A background review can draft one after a turn.
- Past sessions stay searchable. They are not copied into the model.

SQLite on the Solomon VM remains the record of inventory, meals, and the audit trail. One sentence can do both: update that record through a proposed change, and teach Hermes how this household does the thing.

## What may train it

- An Adult speaking in Solomon chat, or confirming a proposal Hermes just made.

## What may not

- Email, attachments, OCR text, web pages, and any other untrusted text. Those can become a Proposed change. They cannot write memory or a skill.
- A skill that can act (devices, mail, delete) waits for an Adult to approve it before it goes live. **[documented]** the `skills.write_approval` section of the skills page above. The starting model is Opus (ADR-0008), so this gate is no longer waiting on a 3B. It stays because an acting skill is a loaded procedure.
- Preference memory from an Adult's own chat is saved. The Adult can open the learning trail and delete or edit an entry.
- A receipt, a recipe photo, or a recipe page does not train Hermes. Those become Inventory and Recipe Records (ADR-0009).
