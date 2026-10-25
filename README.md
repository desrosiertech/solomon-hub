# Solomon

Private, LAN-first household dashboard. This repo has the grocery vertical slice (AI off), a Calendar day page, a Weather page, a News digest, Chat as the only intake, Settings for the theme and connections, plus the planning docs.

- Plan: [`docs/plan/README.md`](docs/plan/README.md)
- Decisions: [`docs/adr/`](docs/adr/)
- Ticket: [`docs/tickets/001-grocery-vertical-slice.md`](docs/tickets/001-grocery-vertical-slice.md) / [issue #1](https://github.com/desrosiertech/solomon-hub/issues/1)

## Grocery slice

The dashboard shows inventory, conservative estimated use-by windows, quiet dinner ideas, and a Use soon list. An unresolved item still becomes Stale, then Presumed discarded. Chat is where a person sends an event, a correction, a recipe, or a receipt. With the reader off, Chat keeps the message and does not call a model. There is no login. `ModelProvider` is `Disabled`. No Google, Blink, cloud AI, Hermes, voice, email, or OCR.

```text
solomon/food.py     # domain functions (window, aging, ideas, suppression)
solomon/board.py    # calendar day, weather page, stale-not-blank
solomon/news.py     # news digest
solomon/chat.py     # chat intake; reader-off keeps the message
solomon/service.py  # SQLite + audit + cached meal ideas
solomon/main.py     # FastAPI the UI calls
web/                # React dashboard, News, Weather, Chat, and Settings
```

### Run

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
cd web && npm install && npm run build && cd ..
python3 -m uvicorn solomon.main:create_app --factory --host 127.0.0.1 --port 8000
```

Or leave the Vite proxy running (`cd web && npm run dev`) against the API on port 8000. SQLite lives at `data/solomon.db` (not committed). Do not put secrets in the repo.

---

# Matt Pocock skills

Vendored copies of every published skill from [mattpocock/skills](https://github.com/mattpocock/skills), installed for Cursor.

Source: `main` at [`5beb35b`](https://github.com/mattpocock/skills/commit/5beb35b040e3de97e54fa9e386d7e42d15c295c2) (Oct 19, 2026, 11:51 AM EDT).

Skills live in `.agents/skills/`. Cursor loads that directory as project skills. Invoke one by typing `/` and the skill name, for example `/tdd`. `skills-lock.json` records the source path and content hash for each skill.

These files are MIT licensed. Copyright (c) 2026 Matt Pocock. See [LICENSE](LICENSE).
