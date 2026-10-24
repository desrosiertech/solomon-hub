# Solomon

Solomon is a household's private dashboard and assistant: it owns the household's records and how they are presented, while devices, the agent runtime and third-party services sit behind boundaries it controls.

## Household and people

**Household**:
The group of people, pets, vehicles and places Solomon serves. One deployment serves exactly one Household.

**Member**:
A person in the Household with their own login, accent color and permissions.
_Avoid_: User (when you mean a person), account

**Role**:
A named bundle of permissions assigned to a Member or Display (Adult, Teen, Child, Guest, Display).
_Avoid_: Group, user type

**Guest view**:
The reduced presentation shown to Guests and on shared screens, with protected categories hidden.

**Protected category**:
A class of record that is hidden unless a Role grants it explicitly: camera feeds, medical and vet records, travel details, infrastructure detail.

**Display**:
An enrolled, revocable screen identity (wall tablet, kitchen screen, TV device) that is not a Member and never holds a Member's login.
_Avoid_: Kiosk user, device account

## Boundaries

**Hermes**:
The agent runtime and gateway that interprets requests and calls Solomon's Tools. It is a client of Solomon, never its database.
_Avoid_: Solomon (for the agent), the bot

**Tool**:
A narrow, permissioned operation Solomon exposes to Hermes (for example "propose inventory correction").
_Avoid_: Endpoint (in agent contexts), function

**Skill**:
A reviewed, versioned procedure Hermes follows for a recurring kind of request, using only its declared Tools.
_Avoid_: Agent, plugin

**Delegated subagent**:
A short-lived Hermes worker spawned for one bounded research or parallel-reasoning task, with no standing permissions.

**Domain service**:
Deterministic Solomon code that owns one area's rules and writes (Inventory, Meals, Calendar, Records, Intake).

**Adapter**:
Deterministic code that syncs one external system (Google Calendar, Home Assistant, Plex, the intake mailbox) into or out of Solomon.
_Avoid_: Integration (ambiguous with Home Assistant integrations), connector

**Device authority**:
Home Assistant's role as the sole controller of devices and safety-critical actions; Solomon requests, Home Assistant decides and executes.

**Outbound data policy**:
The Household setting that decides what may leave the LAN or tailnet; the default is local-only.

**Cloud request approval**:
An explicit, per-request consent, shown with a disclosure of exactly what would be sent, before any cloud model sees Household content.

**Trust boundary**:
A point where data leaves Solomon's control, recorded with what crosses it (private content, metadata, images, credentials, or none).

**Tailnet**:
The Household's private Tailscale network; the only path for remote and administrative access.

## Records and provenance

**Record**:
Any authoritative, structured fact Solomon holds (an inventory item, a vet visit, a trip), with source, timestamp, owner and confidence.

**Proposed change**:
A not-yet-authoritative edit to Records, produced by intake, OCR, the agent or a sync, that waits in the Review queue unless a policy auto-applies it.
_Avoid_: Draft, suggestion (reserved for food ideas)

**Review queue**:
The single place where Proposed changes are approved, corrected, rejected or archived; shown as a quiet "Needs review" count.
_Avoid_: Inbox (reserved for the intake mailbox), notifications

**Intake item**:
One captured artifact (forwarded email, receipt photo, scanned document, barcode scan) with its provenance and original copy, from which Proposed changes are extracted.

**Provenance**:
Where a Record or Intake item came from: source, capture method, Member, timestamps, hashes and message identifiers.

**Correction**:
A Member's edit to a Record, kept with the prior value so history is never lost.

**Audit event**:
An append-only entry recording who or what changed a Record, a permission or a setting, and why.

## Food

**Inventory item**:
A food the Household probably has, with a storage location, coarse quantity, confidence and estimated use-by window.
_Avoid_: Product, stock line

**Observation**:
A single piece of evidence about an Inventory item (bought on a receipt, scanned, "we still have two", "we used it"), from which current state is derived.

**Coarse quantity**:
An intentionally approximate amount: "some", "one package", "about half", "a few", "unknown", or a count when known.

**Confidence band**:
How sure Solomon is that an Inventory item is present and usable: confident, probable or uncertain.

**Storage location**:
Where food is kept (pantry, fridge, freezer, counter, or a Household-defined place), which changes its Estimated use-by window.

**Estimated use-by window**:
Solomon's conservative estimate of when an item may pass its expected freshness, with an explainable source. It is never a food-safety claim.
_Avoid_: Expiry, expiration date, best-before (unless printed on the package)

**Use soon**:
The quiet list of Inventory items nearing or past their Estimated use-by window, shown passively in existing screens.
_Avoid_: Alert, warning, expiring

**Meal idea**:
A dinner Solomon could suggest from what the Household probably has, with each ingredient's availability.
_Avoid_: Recommendation, suggestion (as a bare word)

**Ingredient availability**:
For a Meal idea's ingredient: available, probably available, quantity uncertain, or missing.

**Suggestion**:
Any passive food prompt Solomon may surface (a Use soon line, a Meal idea, a "freeze the leftovers" note), identified by a stable key so it can be deduplicated.

**Impression**:
One showing of a Suggestion to the Household, used to limit how often it reappears.

**Dismissal**:
A Member's "not now" on a Suggestion, which hides it for the Household's configured suppression period.

**Stop asking**:
A Member's request that a Suggestion or item never resurface until someone explicitly reintroduces it.
_Avoid_: Mute, snooze

**Grace period**:
How long an unresolved Use soon item keeps appearing before Solomon lowers its confidence and stops surfacing it.

**Stale**:
An Inventory item whose confidence has decayed past the Grace period; it is no longer surfaced but is not yet presumed gone.

**Presumed discarded**:
A Stale item Solomon believes is gone without confirmation; it is recorded as a presumption, never as consumption.
_Avoid_: Consumed, deleted

**Planned meal**:
A dinner a Member has put on the plan for a date; Solomon never overwrites one silently.

**Leftover**:
Portions of a cooked Planned meal tracked as an Inventory item with its own Estimated use-by window.

**Shopping list**:
The weekly list split into "needed for planned meals" and "optional restock", excluding items confidently available.
