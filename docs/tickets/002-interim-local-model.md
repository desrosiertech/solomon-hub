# 002: Interim local model on DeepThink

**What to build:** An Adult still uses the grocery screens with the model disabled, and can see whether the local model on DeepThink is reachable. That check sends no Household records off the machine. Home Assistant is unchanged. When the interim VM answers, the same status reads reachable, and the Phase 0 bench can ask that model one tool question on the LAN.

**Blocked by:** None (can start immediately). The grocery slice is already on main. Creating the VM on the household Proxmox is a human step described in ADR-0006. The app work does not wait on it. CI treats the model as unreachable.

**Status:** deferred (2026-10-24). The starting brain is Claude Opus through Nous Portal (ADR-0008). This ticket returns when a model must stay on the LAN. Next build is `docs/tickets/003-portal-receipts-and-recipes.md`.

**GitHub:** https://github.com/desrosiertech/solomon-hub/issues/4
(`ready-for-agent` label could not be created; this token cannot write repo labels. Applied `enhancement`.)

## Out of scope

Installing the 64 GB kit, the 8B bench, Gmail intake, Overseerr, live Tailscale grant edits, voice, a cloud model path, and any rebuild of the grocery slice.

## Acceptance criteria

- [ ] With the model disabled, the grocery flows from ticket 001 still pass.
- [ ] An Adult can see a local-model status of unreachable, or not set up, when nothing answers, and reachable when a LAN health check succeeds.
- [ ] The health check does not send inventory, mail, calendar, or other Household records.
- [ ] Outbound data policy stays local-only. This ticket adds no cloud model path.
- [ ] Tests use a fake endpoint. CI does not need Proxmox, a GPU, or a downloaded model.
- [ ] The check is aimed at the interim VM in ADR-0006: a sibling VM on DeepThink, not a Home Assistant add-on.

## Notes for the implementer

Read ADR-0001, ADR-0002, and ADR-0006. Use `/tdd`. Do not deploy to the household Proxmox from CI.
