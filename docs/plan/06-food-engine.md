# Food engine: deterministic rules

Status: proposed (planning pass, 2026-10-24). Vocabulary follows `GLOSSARY.md`.

The food engine is plain code inside the Inventory and Meals domain services. It assigns estimated use-by windows, derives confidence, generates Use soon lines and Meal ideas, suppresses them, ages items to Stale and Presumed discarded, and computes the Shopping list. **None of it calls a model.** A model (local by default) may only *propose* inputs, for example by interpreting an ambiguous receipt line ("ORG BBY SPN 5OZ") or by translating "we used the melon" into a structured Correction. Those proposals pass through the same validation as a Member's tap.

Every number below is a **default to tune during Phase 2**, not a food-safety statement. UI copy uses "estimated use-by window" and "may be past its expected freshness window".

## 1. Inventory state is derived from Observations

An Inventory item's current state is a fold over its append-only Observations. The item row caches the result for fast reads, and the cache can always be rebuilt.

| Observation kind | Typical source | Effect |
|---|---|---|
| `acquired` | receipt line, quick-add, barcode | creates the item or adds quantity; sets `acquired_at`; confidence starts at the source's base |
| `seen` | "we still have two", inventory walk | resets confidence to confident; can set the quantity |
| `opened` | tap, chat | sets `opened_at`; recomputes the window |
| `moved` | "put it in the freezer" | changes the storage location; recomputes the window |
| `used_some` / `used_all` | tap, chat, cooking a Planned meal | lowers the quantity; `used_all` closes the item as consumed (**only** from explicit Member input) |
| `discarded` | "throw out the old spinach" | closes the item as discarded |
| `presumed_discarded` | the aging job | closes the item as a presumption; reversible |
| `quantity_corrected` | "we have about half" | sets the coarse quantity |
| `window_override` | Member edits the date | pins the window; source becomes `user_override` |

Rules:

- A receipt proves acquisition only. It never proves storage or consumption, so storage comes from the category default and stays editable.
- Consumption is never inferred. The engine may *propose* "probably gone" (a Proposed change) or *presume* discard (§5). It never writes `used_all` on its own.
- Each Observation carries `source`, `actor` (a Member, Display, Hermes skill or job), `observed_at`, `confidence` and an optional `intake_item_id`.

## 2. Coarse quantities

`quantity` is one of: `count(n)`, `some`, `one_package`, `about_half`, `a_few`, `low`, `unknown`. Recipes can need exact amounts; the engine compares them coarsely:

- `count(n)` versus a recipe need of `m`: available when n ≥ m.
- `one_package`, `some` or `a_few` versus any need: **quantity uncertain**, unless a known package size covers the need.
- `low` or `unknown`: **quantity uncertain**.

## 3. Estimated use-by window

```
window_days = base_days[category][storage]
            × opened_factor[category]      (if opened_at is set; default 0.5, min 1 day)
            × profile_factor               (conservative 0.8 | balanced 1.0 | permissive 1.2)
anchor      = opened_at ?? acquired_at ?? first observed_at
estimated_use_by = anchor + window_days
```

Precedence (first match wins; the winner is stored as `window_source`):

1. `user_override`: a Member-entered date.
2. `package_date`: a printed date captured by OCR or typed in. It is shown as "package says …" and still estimated.
3. `product_guidance`: an imported guidance table, if one is enabled. Candidate source: USDA FoodKeeper data. *Unverified*: check its licence and format in Phase 2 before importing.
4. `category_default`: the table below.

The UI always shows the "why" ("Fridge · leafy greens · bought Oct 20 · about 5 days"), with an edit affordance.

**Starter defaults (days; placeholders to tune, deliberately conservative):**

| Category | Pantry | Fridge | Freezer | Counter |
|---|---|---|---|---|
| Leafy greens | n/a | 5 | 180 | 1 |
| Berries | n/a | 4 | 240 | 1 |
| Whole melon | n/a | 7 | n/a | 5 |
| Cut fruit | n/a | 3 | 240 | n/a |
| Dairy milk | n/a | 7 | 90 | n/a |
| Hard cheese | n/a | 28 | 180 | n/a |
| Raw poultry or ground meat | n/a | 2 | 120 | n/a |
| Cooked leftovers | n/a | 3 | 90 | n/a |
| Bread | 5 | 10 | 90 | 4 |
| Dry goods | 365 | n/a | n/a | 365 |
| Canned, unopened | 730 | n/a | n/a | n/a |
| Unknown category | 7 | 4 | 90 | 2 |

## 4. Confidence bands

Each item has a numeric `confidence` in [0, 1], computed deterministically and mapped to a band:

- **confident**: ≥ 0.75
- **probable**: 0.4–0.75
- **uncertain**: < 0.4

```
base = { seen: 0.95, quick_add: 0.9, barcode: 0.9, receipt_confirmed: 0.85,
         receipt_auto: 0.7, agent_proposed_applied: 0.7 }[last_strong_observation.source]
age_ratio = days_since(last_strong_observation) / window_days
confidence = base × decay(age_ratio)      # decay = 1.0 until 0.5, then linear to 0.3 at 1.0,
                                          # then to 0.1 by 1.0 + grace_ratio
```

An Ingredient availability check uses the band and the quantity:

- **available**: confident, with a sufficient quantity.
- **probably available**: probable, or confident with an uncertain quantity that is not `low` or `unknown`.
- **quantity uncertain**: present, but the quantity is `low` or `unknown`, or coarse against an exact need.
- **missing**: no open item, or an item that is uncertain *and* past its window.

## 5. Aging, staleness and presumed discard (scheduled job, hourly)

States: `active → use_soon → past_window → stale → presumed_discarded` (terminal states: `consumed`, `discarded`, `presumed_discarded`).

| Transition | Condition (defaults) |
|---|---|
| active → use_soon | `now ≥ estimated_use_by − use_soon_lead` (lead = max(1 day, 25% of the window)) |
| use_soon → past_window | `now ≥ estimated_use_by` |
| past_window → stale | `now ≥ estimated_use_by + grace_period` (default 3 days; per Household; per category optional) |
| stale → presumed_discarded | `now ≥ estimated_use_by + grace_period + presume_after` (default 4 days) |

- Stale items are **not surfaced** in Use soon or Meal ideas. They appear only in Inventory under a collapsed "Probably gone" group.
- The Household setting `presumed_discard_mode` is either `auto_archive` (default; writes a `presumed_discarded` Observation with actor `job:aging`) or `review` (creates one Proposed change per batch: "These 3 items are probably gone").
- Any later `seen` Observation revives the item and records the revival.
- The job is idempotent. Re-running it in the same hour writes nothing new, because transitions are keyed by `(item_id, to_state)`.

## 6. Suggestions: generation, dedup, impressions, suppression

A **Suggestion key** is stable and content-addressed:

| Kind | Key |
|---|---|
| Use soon | `use_soon:{item_id}:{window_epoch}` (`window_epoch` changes only when the window is recomputed) |
| Past window | `past_window:{item_id}` |
| Meal idea | `meal_idea:{recipe_id}:{sorted ingredient item ids}` |
| Freeze leftovers | `freeze:{item_id}` |

Generation runs on read (cheap) and on Observation writes. It produces candidates and then filters them:

1. Drop candidates whose item is `stale` or in a terminal state.
2. Drop candidates matching an active **Suppression rule**:
   - `dismissal`: `(key)` until `dismissed_at + dismiss_period` (default 7 days; Household setting).
   - `stop_asking`: `(subject_type, subject_id)`, for example an item, a recipe or a category, with no expiry. Only an explicit "reintroduce" removes it, and that action is itself logged.
3. Rate-limit by **Impressions**: the same key appears in at most `max_impressions_per_day` (default 3 renders that count, meaning a distinct screen per day). After `max_total_impressions` (default 6) with no interaction, Solomon behaves as if the item were dismissed.
4. Rank: past_window < use_soon by hours remaining; Meal ideas by the count of use-soon ingredients used, then by the fewest missing ingredients.
5. Cap per surface: Home "Use soon" 3, "Ideas from what we have" 3, Meals freshness section 8, Shopping "use first" 3.

An Impression is recorded once per `(key, surface, Display or Member, local day)`, so a wall display rendering every two minutes counts once.

**No notifications.** Suggestions exist only as passive content in Home, Meals and Shopping, and in chat context when a Member asks. There is no push, no notification-center entry and no unsolicited voice unless a Member explicitly enables a "food digest" channel (off by default).

## 7. Meal ideas

Inputs: Recipes (ingredients mapped to categories or canonical foods), active Inventory items, Leftovers, Planned meals and the headcount.

```
for recipe in recipes:
  per_ingredient = classify(ingredient, inventory)   # §4 availability
  if count(missing) > max_missing (default 1, excluding pantry staples): skip
  score = 3·uses_use_soon + 1·uses_leftover − 2·missing − 1·quantity_uncertain
show the top 3 that are not suppressed and not already planned this week
```

The display groups each ingredient as "Have", "Probably have", "Check amount" or "Need". Leftovers count as ingredients, and "Freeze or use the remaining portions" is a Suggestion on the Leftover item itself.

## 8. Shopping list

```
need = Σ planned_meal ingredients for the next 7 days, scaled to headcount
for each need:
  if available (confident, sufficient):    skip
  if probably available / qty uncertain:   add to "Check at home" (not "Buy")
  if missing:                              add to "Needed for planned meals"
  if the item will pass its window before the planned date: add to "Needed", noted "yours may not last until Thu"
restock = staples whose band ≤ probable or whose quantity is low → "Optional restock"
```

Consolidation merges by canonical food and unit family. Members can pin "always buy" or "never suggest" per staple; "never suggest" is a Stop asking rule.

## 9. Corrections in natural language

The chat or voice path maps an utterance to one structured command, and each command goes through the same domain service as the tap UI:

| Utterance | Command | Needs confirmation? |
|---|---|---|
| "We used the melon." | `used_all(item=melon)` | Only if more than one open melon matches |
| "Throw out the old spinach." | `discarded(item=spinach, oldest)` | Yes, if several match; otherwise applied and shown with Undo |
| "We still have two." | `seen + quantity_corrected(count 2)` | No |
| "Stop asking about this." | `stop_asking(subject=last surfaced suggestion)` | No; shows "Won't ask again · Undo" |
| "Mark this as discarded." | `discarded(item=context)` | No; Undo is available |

With the AI disabled, the same commands are one-tap buttons, so the fallback is complete.

## 10. What needs confirmation

- Anything a model proposed (receipt lines, natural-language corrections that resolve ambiguously).
- Bulk changes: three or more items, or any presumed-discard batch in `review` mode.
- Overwriting a Planned meal, which is always confirmed.
- Never needed: an explicit single-item tap by a Member, or a deterministic aging transition (always reversible).

## 11. Food onboarding asks only

Common storage locations; household serving size; preferred store(s); conservative or permissive estimates (the `profile_factor`); the suppression period for dismissed suggestions (`dismiss_period`); and auto-archive versus review for Presumed discarded items.
