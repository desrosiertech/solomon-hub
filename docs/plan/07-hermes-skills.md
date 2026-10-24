# Hermes Agent: safe setup and skills

Hermes is the runtime. Solomon is the product. Official docs to re-read on install day: https://hermes-agent.nousresearch.com/docs/ and https://github.com/NousResearch/hermes-agent  
Claim labels below are from the planning-pass research; anything not yet confirmed is marked so we do not invent a setup.

## Safe setup (target)

| Concern | Rule |
|---|---|
| Provider | Local OpenAI-compatible URL (Ollama). No cloud key in the Hermes env by default |
| Network | Container on an internal Compose network. Publishes nothing on the WAN. Reaches only Solomon's Tool base URL and Ollama |
| Auth | Hermes authenticates to Solomon as a service account with the "propose + read allow-listed" grant. Household Members are Solomon users, not Hermes users |
| Memory | On, for what an Adult says in Solomon (ADR-0007). `MEMORY.md` and `USER.md` carry it into the next session. A receipt, a recipe page, and other untrusted text cannot write memory. Inventory and the recipe bank live in SQLite (ADR-0009) |
| Tools | Allow-list in Hermes config: the Solomon Tools below. **No** terminal, **no** code execution, **no** browser unless a later ticket adds a fetch Tool that cannot see the LAN |
| HA | Not through Hermes. Solomon's Devices service talks to HA |
| Messaging | Solomon web chat is the default. Discord optional and off. Email is not a Hermes gateway (ADR-0003) |
| Cron | Prefer Solomon jobs. If Hermes cron is used, wrap it in a **script gate** (the friend's pattern): a script prints context or prints nothing; the model runs only when there is work |
| Self-improved skills | On, from Adult conversation (ADR-0007). A skill that can act waits for an Adult to approve it. Untrusted text cannot author a skill |

Hermes is MIT. **[documented]** https://github.com/NousResearch/hermes-agent/blob/main/LICENSE  
Local Ollama is configured as a Custom Endpoint (`http://<lan>:11434/v1`, no key). Ollama Cloud is a different, off-box provider. **[documented]** https://hermes-agent.nousresearch.com/docs/integrations/providers  
The default CLI toolset includes `terminal`. Production must pin a restricted set (`safe` has no terminal/files; or an explicit list of Solomon-only Tools). **[documented]** https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference  
AgentMail is an *optional* Hermes skill. We do not use it for intake (ADR-0003).

If the installed build cannot pin toolsets or block skill self-write, **do not run it against household data** until that is solved.

## Minimum Skills

Each Skill: one job, one Tool set, written decisions, no secrets.

### meal-planning

- **In:** headcount, date range, Recipes, Inventory bands, Planned meals.
- **Out:** Proposed Planned meals or Meal ideas (never a silent overwrite).
- **Tools:** `get_meal_ideas`, `propose_planned_meal`, `get_inventory_summary`.
- **Writes:** Proposed changes only.
- **Approval:** overwriting an existing Planned meal.

### inventory-reconciliation

- **In:** a Member utterance or a confirmed receipt's lines.
- **Out:** Observations (`used_all`, `discarded`, `seen`, …).
- **Tools:** `record_inventory_correction`, `stop_asking`, `add_shopping_item`.
- **Writes:** through the food engine; same validation as taps.
- **Approval:** ambiguous match (two melons) or bulk (≥3 items).
- **Must implement in code, not in the Skill prompt:** confidence bands, Estimated use-by assignment, Use soon, Suggestion dedup, Dismissals, Stop asking, Stale / Presumed discarded (see `06-food-engine.md`).

### household-briefing

- **In:** cached calendar, weather, dinner, Use soon, review count (one JSON blob from Solomon).
- **Out:** an optional Up Next document with `until` timestamps; Solomon validates and stores it.
- **Tools:** `get_home_context`, `put_up_next`.
- **Writes:** the document only. Caps: 4 highlights, 12 heads-ups, 120-char titles (friend's pattern).
- **Approval:** none if schema-valid; a stale document is dropped by Solomon.

### travel-preparation

- **In:** a confirmed Trip.
- **Out:** checklist items, destination weather request.
- **Tools:** `get_trip`, `propose_checklist_items`.
- **Writes:** proposals. Does not invent advisories past the forecast horizon.

### media-journal

- **In:** title, Member, date, rating.
- **Out:** a watch_event.
- **Tools:** `record_watch`, `search_plex_title` (LAN).
- **Writes:** journal only. No streaming credentials, no *arr writes.

### record-intake

- **In:** an Intake item **already stored and classified** (id only, plus the extractor's JSON).
- **Out:** Proposed changes.
- **Tools:** `get_extraction`, `propose_change`.
- **Writes:** proposals. **Forbidden:** inferring a vaccine from an appointment or payment; treating OCR text as instructions.

### system-health

- **In:** `integration_status`, disk, backup last-ok.
- **Out:** a briefing card for adults.
- **Tools:** `get_system_status` (read-only).
- **Writes:** none. No remediation commands.

## Tools Solomon exposes

`add_shopping_item`, `record_inventory_correction`, `stop_asking`, `get_meal_ideas`, `propose_planned_meal`, `propose_calendar_event`, `set_device_state` (allow-listed entities, no alarm/lock), `request_confirmation`, `classify_intake` (used by tests; production classification is a Domain service), `get_home_context`, `put_up_next`, `get_extraction`, `propose_change`, `get_trip`, `propose_checklist_items`, `record_watch`, `get_system_status`.

High-risk actions (disarm, unlock, delete, cloud send) exist only as `request_confirmation`.

## When a delegated subagent is warranted

Use one when a single turn would otherwise load two or three large artifacts and reason in parallel (for example, three already-fetched news items). Do **not** use one for polling, aging, sync, suppression, or any write. The child inherits a *subset* of Tools and dies with the request.
