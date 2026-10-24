# What Solomon takes from the reference "Home Hub"

Desrosier shared a friend's technical overview of a similar household hub (12 pages; kept outside the repo). It is a **starting reference only**. Where it conflicts with the Solomon brief, the brief wins. No names, addresses, hostnames, credentials or photos from it are reproduced here.

The reference's shape: one Linux VPS running Docker, with Traefik on public :443; a FastAPI + React app on SQLite; Hermes Agent ("Gerald") with cron jobs and skills, using Claude via a hosted portal; Gemini Flash for extraction; a Raspberry Pi kiosk; an ESP32 push-to-talk gadget; a scan-to-SFTP document scanner; AgentMail; and Discord.

## Adopted (proven, fits the brief)

| Idea | Why it fits |
|---|---|
| **Two-layer polling**: Displays poll only Solomon; Adapters poll the outside world and cache snapshots | Keeps screens useful during outages; the brief requires "stale, not blank" |
| **"Unknown isn't none"**: stale or unavailable states, never an empty day | The brief requires real empty/error/loading states |
| **Revocable Display identity** enrolled with a one-time code (hash-stored, rate-limited, HttpOnly SameSite=Strict cookie) | Matches "children/guest views" and "no adult login on shared screens" |
| **Read-mostly Displays**: shared-screen writes limited to small taps | Least privilege on always-on screens |
| **Agent writes through the same validated API**, with strict schemas, caps and `invalid_field:<path>` errors | Matches "narrow tools" and "DB is the authority" |
| **Agent documents expire** (`until`), and the server drops expired items | Keeps the dashboard correct when the agent is offline |
| **Script gates on cron**: a cheap script runs first, and the LLM wakes only when there is work | Matches "ordinary code for polling"; cuts load on a modest local GPU |
| **Pending extraction before inventory**, with OCR + rules fallback when there's no AI | Exactly the brief's Proposed change and Review queue |
| **Written write-policy per document type** (for example, vehicle records proposed until N confirmations) | Becomes Solomon's per-type auto-apply policy (`09-hermes-design.md`) |
| **Calendar allow-list, deny by default**, and "Busy → Work" title mapping | Least data from Google |
| **Create/edit-only calendar writes**, never delete, `If-None-Match: *` | Matches "no autonomous deletion" |
| **Stack**: FastAPI, SQLAlchemy 2, Alembic, SQLite WAL, React + TS + Vite + Tailwind + TanStack Query, one container | Approachable and proven for one household (ADR-0002) |
| **Cold, verified nightly SQLite backup** with a schema-revision check | Extended with encryption and restore drills |
| **Preview mode from fixtures** for every screen | Lets design and E2E proceed without live data |
| **Immutable deploys pinned by image digest**; the Display reloads on a new build | Low-drama upgrades and rollbacks |
| **Feedback → GitHub issue with screenshots** | Kept, but screenshots are redacted of Protected categories, and the feature is off on guest Displays |
| **Push-to-talk voice device** with short spoken replies, treating transcripts as possibly wrong | Matches "no ambient recording, PTT preferred" |
| **Skill-writing tips** (one job and one script per skill, exit codes in the skill, decisions written down, secrets never in `SKILL.md`) | Adopted into the skill review checklist |

## Changed (good idea, different trade-off for Solomon)

| Reference | Solomon | Reason |
|---|---|---|
| Public VPS behind Traefik on :443 with Let's Encrypt | **On-prem host on the LAN; remote access only over Tailscale; no inbound ports** (ADR-0005) | Brief: LAN-only, no public port forwarding, household data stays in the network |
| Claude via a hosted portal as the agent model | **Same shape, adopted as the start** (ADR-0008): Hermes on the Solomon VM, Claude Opus through Nous Portal. The app stays on the LAN. A local model remains the later brain (ADR-0006) | The Household asked to start here so receipts and recipes can be read |
| Gemini Flash (via a cloud service) for receipt and menu extraction | **The same Opus path reads receipts and recipes** (ADR-0009). No second cloud extractor. Local OCR when Opus is off | One model path |
| Honcho memory (Postgres + pgvector) | **Hermes built-in memory limited to conversational preferences; household facts live only in Solomon's DB** | Brief: don't depend on agent memory as a database |
| AgentMail inbox for the agent | **Dedicated hosted mailbox polled by a deterministic intake service, never Hermes directly** (ADR-0003) | Untrusted email must not reach the agent as instructions; provider choice is a privacy trade-off |
| Scanner → SFTP → agent classifies at 85% or higher, then auto-writes | **Scanner/email/camera → Intake item → local extraction → Proposed change; auto-apply only for low-risk types the Household opts into** | Brief: documents create proposals; never infer a vaccine from an invoice |
| Raspberry Pi kiosk only | **Responsive web app: wall/tablet, desktop editor, 10-ft TV mode, phone over the tailnet** | Brief needs TV and remote views |
| ESP32 gadget talks to the Hermes gadget plugin over a public WebSocket | **Voice via the HA Assist pipeline (local STT/TTS) on the LAN**; Hermes only for non-device questions; voice optional (ADR-0004) | HA is the device and voice authority; no public endpoint |
| Kiosk feedback emails an adult | Feedback goes into a GitHub issue only if enabled; screenshots are redacted | Minimizes outbound data |
| CI on a self-hosted runner on the production VPS | CI on GitHub-hosted runners (code only, no household data); deploys pulled by the host | Keeps CI tokens off the household host |

## Rejected

| Idea | Reason |
|---|---|
| Discord as the family chat and voice channel by default | Brief: Discord is optional with a warning, never the private default; data traverses Discord |
| AI-generated recipe pictures via a cloud image model | Sends content out and adds cost and noise; use the source page image or none |
| Agent web research writing the News screen | News is a deterministic RSS/feeds digest. The local model may summarize titles; a cloud research run would leak topics and invent nothing reliable |
| Google Maps/Routes/Contacts drive-time integration | Not in the brief; extra outbound PII. Possible later idea |
| Staple price scraping and warehouse-club checks | Not in the brief; scraping is brittle and may breach terms |
| Gerald writing GitHub issues or PRs from the household server | Agent has no repo credentials in production |
| A single public hostname that routes the agent gadget endpoint | No public ingress by default |
