# Solomon plan (2026-10-24)

Vocabulary: `GLOSSARY.md`. Decisions: `docs/adr/`. Grocery slice: `docs/tickets/001-grocery-vertical-slice.md` (on main). Next ticket: `docs/tickets/003-portal-receipts-and-recipes.md`. The local-model ticket (`002`) waits.

## How to read this

1. `00-assumptions.md` — setup-skill choices and hardware guesses you can change.
2. `01-feasibility.md` — verdict per capability, with citations and claim labels.
3. `02-inference-and-hosting.md` — A/B/C, cost model, Phase 0 benchmark.
4. `03-architecture.md` — modules, permissions, jobs vs Hermes.
5. `04-trust-boundaries.md` — outbound connections, including Tailscale and Cloudflare.
6. `05-data-model.md` — tables and the record envelope.
7. `06-food-engine.md` — deterministic food rules (no LLM).
8. `07-hermes-skills.md` — skills, tools, when a subagent is warranted.
9. `08-screens-and-wireframes.md` — screen map (reference PNGs are missing).
10. `09-onboarding.md` — wizard, secrets, missing-record prompts.
11. `10-roadmap.md` — Phase 0–4, acceptance tests, first vertical slice.
12. `11-unanswered-questions.md` — at most five shown first.
13. `12-reference-home-hub-comparison.md` — what we borrowed from a friend's hub.
14. `13-phase0-security-checklist.md` — firewall, tailnet, tunnel-off tests.

## ADRs

| ADR | Decision |
|---|---|
| [0001](../adr/0001-local-inference-by-default.md) | Local Ollama by default; explicit per-request cloud fallback |
| [0002](../adr/0002-approachable-local-stack.md) | FastAPI + React + SQLite, on-prem, not inside HAOS |
| [0003](../adr/0003-deterministic-inbox-intake.md) | Dedicated mailbox + deterministic intake; Hermes never owns mail |
| [0004](../adr/0004-voice-optional-ha-first.md) | Voice optional; HA Assist is the pipeline; no ambient recording |
| [0005](../adr/0005-tailscale-and-optional-cloudflare-tunnel.md) | Tailscale for remote/admin; Cloudflare Tunnel off; two Adult admins; Overseerr on the tailnet |
| [0006](../adr/0006-model-vm-on-deepthink.md) | Daily model VM on DeepThink, beside Home Assistant |
| [0007](../adr/0007-hermes-learns-from-adults.md) | What Adults tell Solomon trains Hermes memory and skills |
| [0008](../adr/0008-opus-via-nous-portal.md) | Starting brain: Claude Opus through Nous Portal |
| [0009](../adr/0009-receipts-and-recipe-bank.md) | Receipts fill Inventory; recipes are banked |

## Claim labels

Every contentious fact in this plan is one of:

- **documented** — stated in a current official doc or the project's own source.
- **experimental** — marked beta by the project, or a sizing/latency claim we have not measured.
- **blocked by a third-party API** — limited by a vendor's API, policy or approval process.
