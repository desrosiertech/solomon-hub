# Data model outline

Status: proposed. The database is the source of truth; Hermes memory is not. Every table listed carries `id` (a ULID), `household_id`, `created_at` and `updated_at`, plus soft-delete fields (`deleted_at`, `deleted_by`) where a Record can be deleted. Permanent deletion is a separate, audited, adult-only action that purges the row and its blobs.

## Cross-cutting columns ("record envelope")

Every authoritative Record table includes:

| Column | Meaning |
|---|---|
| `owner_member_id` | whose Record it is (nullable for Household-wide) |
| `visibility` | `household`, `adults`, `owner_only`, or a protected category |
| `source` | `manual`, `receipt`, `barcode`, `email_intake`, `photo`, `google_calendar`, `ha`, `agent`, `import`, `job:*` |
| `source_ref` | external identifier (Google event id, email Message-ID, intake item id) |
| `confidence` | 0–1 where meaningful |
| `observed_at` | when the fact was true or observed, which can differ from `created_at` |

Corrections are stored in `record_revision(table, record_id, revision, before_json, after_json, actor, reason, at)`. The current row is the latest revision.

## Identity and access

- `member(id, display_name, accent_color, role, birth_year?, is_child, login_disabled)`
- `credential(member_id, kind = passkey|password, …)`: local authentication. Passkeys are preferred; the tailnet identity can be an extra factor (ADR-0006).
- `display_device(id, name, kind = wall|tv|kitchen, role = display|guest, token_hash, last_seen_at, revoked_at)`: this pattern is adopted from the reference build.
- `role_grant(role, capability)` and `member_grant(member_id, capability, scope)`: see the permissions matrix in `03-architecture.md`.
- `audit_event(id, at, actor_kind, actor_id, action, subject_type, subject_id, detail_json, ip?, tailnet_node?)`: append-only, never edited.

## Provenance and review

- `intake_item(id, channel = email|camera|upload|scanner|barcode, received_at, from_address?, forwarding_member_id?, message_id?, subject?, sha256, blob_path, mime, size, status = new|quarantined|extracted|reviewed|archived|rejected, retention_until)`
- `intake_attachment(intake_item_id, filename, sha256, mime, size, scan_result, blob_path)`
- `extraction(id, intake_item_id, engine = tesseract|paddleocr|vlm:<model>|rules|cloud:<provider>, engine_version, ran_at, raw_text_path, output_json, cloud_request_id?)`
- `proposed_change(id, origin = intake|agent|sync|job, origin_ref, target_type, target_id?, op = create|update|close, payload_json, confidence, explanation, status = pending|approved|corrected|rejected|auto_applied|superseded, decided_by?, decided_at?)`
- `dedup_key(kind, key, first_seen_intake_id)`: keyed on the message-id, the attachment hash and a normalized receipt fingerprint `(store, date, total)`, so one receipt arriving by email and by camera is caught.
- `cloud_request(id, at, member_id, provider, model, purpose, disclosed_fields_json, approved_by, bytes_sent, response_ref)`: present only if cloud use is ever enabled.

## Food (see `06-food-engine.md`)

- `storage_location(id, name, kind = pantry|fridge|freezer|counter|other, sort)`
- `food_category(id, name, base_days_json, opened_factor)` and `expiration_default(category_id, storage_kind, days, profile)`
- `canonical_food(id, name, category_id, aliases[], typical_package)`
- `inventory_item(id, canonical_food_id?, label, storage_location_id, quantity_kind, quantity_count?, state, confidence, confidence_band, acquired_at?, opened_at?, estimated_use_by, window_source, window_explain, last_strong_observation_at, closed_reason?)`: state and confidence are cached projections.
- `inventory_observation(id, item_id, kind, payload_json, source, actor, observed_at, intake_item_id?, receipt_line_id?)`: append-only.
- `receipt(id, intake_item_id, store, purchased_at, total, currency, fingerprint)`
- `receipt_line(id, receipt_id, raw_text, parsed_label?, canonical_food_id?, qty?, unit?, price?, parse_confidence, status = proposed|confirmed|ignored|non_food)`
- `expiration_estimate(item_id, computed_at, window_days, source, inputs_json)`: kept as history, so the explanation is reproducible.
- `suggestion(key, kind, subject_type, subject_id, first_generated_at, last_generated_at, payload_json)`
- `suggestion_impression(key, surface, viewer_kind, viewer_id, local_day, at)`: unique on `(key, surface, viewer_id, local_day)`.
- `suggestion_dismissal(key, member_id, at, until)`
- `suppression_rule(id, kind = stop_asking|never_suggest, subject_type, subject_id, created_by, created_at, reintroduced_by?, reintroduced_at?)`
- `state_transition(item_id, from_state, to_state, at, actor = job:aging|member:*, reason)`: unique on `(item_id, to_state, window_epoch)`. A presumed-disposal event is a row here plus an Observation.

## Meals

- `recipe(id, title, source_url?, source_kind = url|photo|manual, servings, steps_json, image_path?, original_qr_text)`
- `recipe_ingredient(recipe_id, canonical_food_id?, text, qty?, unit?, optional)`
- `planned_meal(id, date, slot = dinner, recipe_id?, free_text?, headcount, planned_by, status = planned|cooked|skipped)`: edits are revisions; there are no silent overwrites.
- `meal_rating(planned_meal_id, member_id, stars, note)`
- `shopping_list(id, week_of)` and `shopping_list_line(list_id, canonical_food_id?, text, section = planned|check_at_home|restock, reason, checked_by?, checked_at?)`

## Calendar, travel, records, media (later phases)

- `calendar_source(id, provider = google|manual|ics, account_label, calendar_ext_id, member_id, visibility, sync_token?, last_synced_at, status)` and `calendar_event(id, source_id, ext_id, etag, start, end, tz, rrule?, title, location?, member_ids[], visibility)`. The sync is idempotent, keyed on `(source_id, ext_id)` plus the etag.
- `trip(id, member_ids[], destination, lat?, lon?, start, end, status = idea|confirmed)` and `trip_checklist_item(…)`
- `dog(id, name, …)`, `vehicle(id, nickname, vin_hash?, …)`, `care_event(subject_type, subject_id, kind = vaccine|vet_visit|service|registration, performed_at?, due_at?, due_rule?, evidence_intake_item_id?, status = recorded|proposed)`. `due_at` is never fabricated: it is null until a due rule or a document supplies it.
- `media_entry(id, kind = movie|show|book, title, ext_ids_json)`, `watch_event(entry_id, member_id, watched_on, rating?, notes, collection = spooktober:2026?)`
- `integration_status(adapter, last_ok_at, last_error_at, last_error_code, stale_after)`: this backs the "stale, last updated …" chips.

## Jobs and sync

- `job(id, kind, run_after, idempotency_key, attempts, status, last_error)`: a SQLite-backed queue (ADR-0002).
- Every Adapter writes through a domain service using an `idempotency_key` built from `(adapter, ext_id, ext_version)`.
