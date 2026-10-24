# Solomon

Private, LAN-first household dashboard. **Planning only** — see [`docs/plan/README.md`](docs/plan/README.md). Decisions live in [`docs/adr/`](docs/adr/). First build ticket: [`docs/tickets/001-grocery-vertical-slice.md`](docs/tickets/001-grocery-vertical-slice.md).

---

# Matt Pocock skills

Vendored copies of every published skill from [mattpocock/skills](https://github.com/mattpocock/skills), installed for Cursor.

Source: `main` at [`5beb35b`](https://github.com/mattpocock/skills/commit/5beb35b040e3de97e54fa9e386d7e42d15c295c2) (Oct 19, 2026, 11:51 AM EDT).

Skills live in `.agents/skills/`. Cursor loads that directory as project skills. Invoke one by typing `/` and the skill name, for example `/tdd`. `skills-lock.json` records the source path and content hash for each skill.

These files are MIT licensed. Copyright (c) 2026 Matt Pocock. See [LICENSE](LICENSE).

## Before first use

Run `/setup-matt-pocock-skills` once in a repo where you want the engineering skills to operate. It asks which issue tracker to use, which triage labels to apply, and where domain docs should go. That step is not done in this import.

## Skills

**Engineering** (20): ask-matt, code-review, codebase-design, diagnosing-bugs, domain-modeling, grill-with-docs, implement, implement-spec, improve-codebase-architecture, pr, prototype, research, retro, setup-matt-pocock-skills, tdd, to-spec, to-tickets, triage, wayfinder, wizard

**Productivity** (7): grill-me, grilling, handoff, teach, to-questionnaire, wait-what, writing-for-agents

**In progress** (7): chief-of-staff, claude-handoff, loop-me, setup-ts-deep-modules, writing-beats, writing-fragments, writing-shape

**Misc** (4): git-guardrails-claude-code, migrate-to-shoehorn, scaffold-exercises, setup-pre-commit

## Update

From this directory:

```bash
npx skills@latest add mattpocock/skills -a cursor --skill '*' -y --copy --full-depth
```

That recopies every skill from the latest `main` and refreshes `skills-lock.json`.
