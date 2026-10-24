# 001: Grocery vertical slice (AI off)

**What to build:** A Member can type in a few grocery items, see conservative estimated use-by windows, get quiet dinner ideas and a non-alarming "use soon" list from those items, dismiss one with "stop asking about this," watch that item stay gone, and see a stale item become presumed discarded after the grace period — all with a visible audit trail, and with the AI provider disabled.

**Blocked by:** None (can start immediately), once this plan is reviewed.

**Status:** ready-for-agent

**GitHub:** https://github.com/desrosiertech/solomon-hub/issues/1  
(`ready-for-agent` label could not be created; this token cannot write repo labels. Applied `enhancement`.)

## Out of scope

Google, Blink, cloud AI, Hermes, voice, email intake, Tailscale beyond binding to localhost/LAN, real OCR.

## Acceptance criteria

- [ ] With `ModelProvider = Disabled`, a Member adds at least three Inventory items (including one leafy green and one leftover).
- [ ] Each item shows an Estimated use-by window and a one-line explanation (category, storage, acquired date). Copy uses "estimated use-by window" / "may be past its expected freshness window."
- [ ] Home and Meals show "Ideas from what we have" (up to 3) and "Use soon" without red alert styling and without a notification.
- [ ] "Stop asking about this" on one Use soon line suppresses that Suggestion across Home and Meals after reload.
- [ ] After the configured grace period (overridable in test to minutes), an unresolved item is marked Stale and then Presumed discarded; the UI never says it was eaten.
- [ ] Audit / revision history shows add, suppress, and presumed-discard with actor and timestamp.
- [ ] Tests cover the food engine transitions in `docs/plan/06-food-engine.md` without a running model.
- [ ] Empty, loading and stale-card states exist for the Meals ideas card.

## Notes for the implementer

Read `GLOSSARY.md`, ADR-0001, ADR-0002, `docs/plan/06-food-engine.md`, and wireframes 1–2 in `docs/plan/08-screens-and-wireframes.md`. Use `/tdd`. Do not add extra integrations.
