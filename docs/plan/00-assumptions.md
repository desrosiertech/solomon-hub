# Assumptions

These are planning defaults, not locked facts. Change them in an ADR or a comment on the first ticket.

## Skills setup (this pass)

`/setup-matt-pocock-skills` was run non-interactively with the skill's recommended defaults, because this is a planning agent and there is no live interview.

| Choice | Default used | Why |
|---|---|---|
| Issue tracker | GitHub Issues for `desrosiertech/solomon-hub` | Remote is GitHub; `gh` works |
| Triage labels | `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix` | `triage` is installed |
| Domain docs | Single-context: root `GLOSSARY.md` + `docs/adr/` | No monorepo signals |
| Steering file | Created `AGENTS.md` | Neither `AGENTS.md` nor `CLAUDE.md` existed; the skill would normally ask, and the assignment said create `AGENTS.md` in that case |

`PRs as a request surface` is **off** (template default). Creating the five triage labels returned **HTTP 403** (this token cannot write labels). Existing default labels were left as-is; the first ticket used `enhancement`. An admin can add the five strings later.

### Installed Matt Pocock skills

All published skills from `mattpocock/skills@5beb35b` are vendored under `.agents/skills/` (see `skills-lock.json`). The `/ask-matt` router is present.

**Planning flow chosen:** this is a greenfield idea that already has a written brief, so it is *not* `/wayfinder` (the destination is visible). It is `/grill-with-docs` + `/domain-modeling` + `/codebase-design` + `/research` + `/to-tickets` for the first slice. `/prototype` is deferred: the brief forbids scaffolding the app. Missing from this pass: a live `/grilling` interview with Desrosier (the brief and follow-ups stand in). Nothing was installed silently.

## Hardware and network (unverified until Phase 0)

- Home Assistant OS is a Proxmox VM on ThinkCentre M910s "Deepthink" (i7-6700, 16 GB RAM, 240 GB SSD). The model lives in a sibling VM on that same host (ADR-0006), never inside HAOS. HA does not get all of the RAM.
- "Skynet" is a Windows Plex server with a GTX 1080 Ti (11 GB). Plex stays. It is not the model host.
- UniFi gear + controller, Blink cameras in HA, *arr + Tautulli + qBittorrent, Google Calendar exist. Versions and exact models are unknown.
- Servers already have reserved/static LAN addresses outside the DHCP pool.
- Household is in the US (NWS weather is usable). Electricity price uses the latest EIA US residential average until a local rate is supplied.
- Two dogs, two cars; names and records arrive later via onboarding, never in chat.
- The Display is a 65-inch LG C5 (2025, webOS). The media-request app is Overseerr, on the tailnet. Cloudflare Tunnel stays off.

## Product defaults

- One Household, a handful of Members, one or two Displays.
- Outbound data policy: **local-only**.
- Cloudflare Tunnel: **off**. Overseerr stays on the tailnet for the two Adults.
- Intake mailbox: a dedicated Gmail, IMAP with an app password (ADR-0003).
- Tailnet: two Adult admins. No kids group.
- Discord: **off**.
- Voice: **off** until Phase 3; the product works without it.
- Food profile: conservative estimates; `presumed_discard_mode = auto_archive`; dismiss period 7 days; grace 3 days.
- No public hostname for Solomon itself.

## Cost-model knobs (visible so the math can be redone)

| Knob | Placeholder | Change when |
|---|---|---|
| Residential electricity | EIA US average, see `02-inference-and-hosting.md` | You supply the local ¢/kWh |
| Inference host | DeepThink sibling VM (ADR-0006). 64 GB DDR4 + 1 TB SSD before an 8B | A bench miss means a different computer, not a card in this chassis |
| Monthly cloud-API usage (if ever enabled) | Light / normal / heavy token bands in that same doc | Real logs exist |
