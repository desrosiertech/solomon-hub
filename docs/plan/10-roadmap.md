# Roadmap

Effort is relative (S/M/L), not calendar time. Each phase ends with acceptance tests you can run on the LAN.

## Phase 0 — inventory, security, model bench

**Deliverables:** this plan (done); Tailscale + default-deny firewall; encrypted backup restore drill; `bench/` run on real hardware; a written hardware pick.

**Depends on:** physical access to Deepthink / Skynet / UniFi.

**Acceptance:** `13-phase0-security-checklist.md` S0.1–S0.9; `bench/README.md` produces a filled results file (not guessed numbers).

**Effort:** M (mostly human + a short agent loop on the bench script).

## Phase 1 — read-only household dashboard

**Deliverables:** Solomon app skeleton (ADR-0002); Member + Display auth; Home, Calendar (manual + optional Google read), Weather, News (RSS), Settings; right rail; stale chips; Systems read-only for adults; tailnet access from a phone.

**Depends on:** Phase 0 firewall/tailnet.

**Acceptance:**

- Home answers "what is everyone doing today" from fixture or live calendar.
- Killing the weather Adapter leaves the last forecast with a stale chip, not an empty card.
- Phone on tailnet works; phone off tailnet does not (S0.3–S0.4 still pass).
- Guest Display hides Systems.

**Effort:** L.

## Phase 2 — meals, inventory, quiet suggestions, intake

**Deliverables:** food engine + UI (`06-food-engine.md`); Review queue; local OCR path; dedicated mailbox intake (ADR-0003); first ticket `001`.

**Depends on:** Phase 1 auth and Home layout.

**Acceptance:**

- Ticket 001 (AI off).
- Forward one receipt from an approved sender → Review queue → apply three lines → Inventory updates. **No cloud AI call** (`cloud_request` table empty).
- Duplicate of the same receipt (camera + email) does not double-add.
- A vet invoice does not create a vaccine Record.

**Effort:** L.

## Phase 3 — voice, security, media

**Deliverables:** optional HA Assist (ADR-0004); Blink snapshots + arming state via HA, no live-view promise; Spooktober journal; Plex/Tautulli read; request-app link.

**Depends on:** HA non-admin token; Blink still working in HA.

**Acceptance:**

- Voice-off path unchanged.
- PTT utterance turns an allow-listed light on; "disarm" only opens a confirmation.
- Security view is adult-only; Guest/TV hide it.
- Blink tile shows last snapshot + refresh time or "unavailable", never a fake live stream.

**Effort:** L.

## Phase 4 — travel, records, photos, TV

**Deliverables:** trips + destination weather; dogs/cars Records; photos *if* a legal source exists (likely Takeout or Picker, not library-wide Google Photos); 10-ft TV mode; optional public media-request hostname behind Cloudflare Access.

**Depends on:** Phase 1–2; photo source decision.

**Acceptance:**

- Missing vaccine dates stay empty; no invented due date.
- TV Display cannot open Records or Security.
- If Cloudflare is enabled: only the request app is public, Access is on, Solomon remains tailnet-only; S0.1 still clean.

**Effort:** L.

## First thin slice

Phase 2 starts with `docs/tickets/001-grocery-vertical-slice.md` (also a GitHub issue). No Google, Blink, or cloud AI.
