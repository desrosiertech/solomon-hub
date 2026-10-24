# Solomon

A private, LAN-first household dashboard and assistant. The first runnable slice is the grocery / food engine with `ModelProvider = Disabled`. Do not expand past the current ticket into Google, Blink, cloud AI, Hermes, voice, email intake, or deploy.

## Before changing anything

- **Plan**: `docs/plan/README.md` indexes the architecture, roadmap, security, and feasibility docs. Read the one covering the area you touch.
- **Decisions**: `docs/adr/` holds accepted decisions. Contradicting one means reopening it explicitly, not overriding it.
- **Tickets**: `docs/tickets/` mirrors build tickets that are also on GitHub Issues.

## Hard constraints

- Household data stays on the LAN or tailnet. Outbound data policy defaults to local-only; any cloud model call needs explicit per-request approval.
- Core features work with the AI provider disabled. The database, not agent memory, is the source of truth.
- Secrets never go in the repo, prompts, logs, or docs. Use placeholders such as `<HA_URL>`.
- Food freshness wording is an estimate ("estimated use-by window"), never a food-safety claim, and never an alert.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `desrosiertech/solomon-hub`, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `GLOSSARY.md` plus `docs/adr/`. See `docs/agents/domain.md`.
