# Approachable local stack, not inside Home Assistant

Solomon is a single Docker Compose app on a dedicated LAN host or VM: FastAPI (Python 3.12), SQLAlchemy 2, Alembic, SQLite WAL, a small job table, React 19 + TypeScript + Vite + Tailwind + TanStack Query. Home Assistant stays the Device authority. Hermes is a sibling container that can only call Solomon's Tools.

**Status:** accepted (planning).

## Why this stack

One household, one writer process, one operator. The friend's hub already proved this combination for the same shape of product (see `docs/plan/12-reference-home-hub-comparison.md`). Python matches HA, Hermes scripts, Tesseract and the food-engine tests. SQLite plus a nightly encrypted backup is enough until a second writer appears, which it should not.

Rejected for v1:

- Putting the app in HAOS as an add-on — couples upgrades, RAM and blast radius to the Device authority.
- Postgres on day one — another container and backup story for no concurrency need.
- Next.js / a separate Node server — two runtimes to deploy. Vite SPA served by FastAPI is one image.
- Kubernetes, a message bus, or a separate worker fleet.

## Seams (codebase-design)

| Module | Interface | Implementation hidden |
|---|---|---|
| Inventory | Observations in, current item + Suggestions out | Window math, aging, suppression |
| Meals | Plan / rate / list commands | Scaling, leftover creation |
| Intake | Artifact in, Proposed changes out | OCR engines, dedup, MIME policy |
| Calendar | Sync cursor + manual events | Google tokens, RRULE expansion |
| Devices | Allow-listed entity read/write | HA token, MCP, timeouts |
| ModelProvider | `complete(...)` | Ollama vs disabled vs cloud |
| Display auth | Enroll / revoke / cookie | Code hashing, rate limits |

Callers and tests use the same interface. A second Adapter (in-memory, or a fake HA) makes the seam real.

## Deploy shape

- Host: dedicated LXC/VM or small box on reserved LAN IPs, **not** the HAOS VM.
- Bind the app to the LAN and the tailnet only. No `:80`/`:443` on the WAN-facing firewall (ADR-0005).
- One image, Alembic on start, image pinned by digest, Display polls a build id and reloads when idle.
- Secrets: files or a local secret manager on the host, mode 600, never in the repo or in `SKILL.md`.
