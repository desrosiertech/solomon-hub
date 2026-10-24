# Feasibility verdicts

Checked 2026-10-24 against current primary docs. Labels: **documented** / **experimental** / **blocked by a third-party API**.

| Capability | Verdict | Why |
|---|---|---|
| Calendar (Google + manual) | **Supported now** (read); write needs care | Scopes exist (`calendar.readonly`, `calendar.events`, …). **[documented]** https://developers.google.com/workspace/calendar/api/auth . External *Testing* OAuth refresh tokens expire in **7 days**. **[documented]** https://developers.google.com/identity/protocols/oauth2 . Publish the Cloud project (accept the unverified-app screen) or expect weekly re-auth. Allow-list calendar IDs. Manual events work with no Google. |
| Google Tasks | **Supported now** if selected | `tasks` / `tasks.readonly`. **[documented]** https://developers.google.com/workspace/tasks/auth . Same OAuth-testing trap. |
| Food engine + grocery slice | **Supported now** | Pure code. Ticket 001. |
| Receipt OCR (local) | **Needs prototype** | Tesseract + rules in-process. Accuracy on grocery photos is unmeasured. **[experimental]** |
| Local VLM for messy lines | **Needs prototype** | Depends on VRAM (ADR-0001). |
| Cloud vision | **Blocked by policy (ours)** | Allowed only with Cloud request approval. |
| News digest | **Supported now** | RSS/Atom, timestamps, dedup, links. No generative "research" agent. |
| Weather | **Supported now** (US) | NWS API, free, User-Agent required, ~7-day forecast. **[documented]** https://www.weather.gov/documentation/services-web-api . Open-Meteo is a fallback (non-commercial terms — re-read https://open-meteo.com/en/terms). Do not invent past the horizon. |
| Blink snapshots + arming | **Supported now** via HA; **fragile** | HA integration is **Cloud Polling**, **no live view**. **[documented]** https://www.home-assistant.io/integrations/blink/ . Protocol is unofficial (`blinkpy`, reverse-engineered). **[blocked by a third-party API]** Vendor EU portability API shares no video. **[documented]** https://support.blinkforhome.com/en_US/transfer-your-blink-data-to-third-parties |
| Blink live video | **Third-party constrained** | Official HA path does not offer it. Community workarounds and camera migration are a Phase 3 feasibility test, not a promise. |
| Devices / schedules | **Supported now** | HA entities/services. Solomon uses a non-admin LLAT. LLATs last 10 years and have **no scopes** — power = that user's power. **[documented]** https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token |
| Voice (optional) | **Supported now** (HA Assist); quality **experimental** on i7-6700 | Local pipeline documented. Voice PE has a physical mic mute. Prefer PTT. See ADR-0004. |
| Private web chat | **Supported now** | Solomon page, local model or disabled. |
| Discord | **Supported, optional, warned** | Traverses Discord. Off by default. |
| Dedicated email intake | **Needs prototype** | Vendor decided: dedicated Gmail, IMAP app password, not the Gmail API (ADR-0003). Hermes still does not get the inbox. |
| Media journal (Spooktober) | **Supported now** | Local table. No API required. |
| Plex / Tautulli | **Supported now** | LAN APIs + API keys. HA also has a Plex integration. |
| Request app | **Decided: Overseerr, tailnet only** | API key on the LAN or tailnet. Cloudflare stays off. Phase 4 before Solomon calls it. |
| Sonarr/Radarr | **Supported now** as read/status | API-key auth. Solomon will not automate downloads. |
| Letterboxd | **Third-party constrained** | API is request-only and **not granted for private/personal projects**. Use export + profile RSS. **[blocked by a third-party API]** https://letterboxd.com/api-beta/access/ |
| Goodreads | **Third-party constrained** | New API keys have been shut down for years; CSV export is the path. |
| LG C5 (2025) Display | **Browser or HDMI device** | 65-inch webOS set. A native webOS app is not the plan. 10-foot layout is later. Unified continue-watching stays unverified. |
| Systems (Proxmox, Plex health, UniFi, the Verizon router) | **Supported now** (read) | Proxmox API tokens with privilege separation. **[documented]** https://pve.proxmox.com/wiki/Proxmox_VE_API . UniFi OS is a DeepThink VM that controls two access points. The Verizon router is the WAN edge. Admin UIs stay **tailnet-only**. |
| Cars / dogs records | **Supported now** | Structured tables + confirmation. OCR proposes only. |
| Photos | **Third-party constrained** | Google Photos Library API no longer reads the user's whole library (scopes removed 2025-03-31 / page note 2025-04-01). Picker API = user-selected items; Library API = **app-created** data. **[blocked by a third-party API]** https://developers.google.com/photos/support/updates and https://developers.google.com/photos/support/api-overview . Path: Google Takeout / a local export, or Picker for one-off choices. Never auto-delete. |
| Tailscale remote access | **Supported now** | Outbound-only client, grants, tags, MagicDNS. ADR-0005. |
| Cloudflare Tunnel | **Supported, off** | Outbound `cloudflared` + Access. TLS terminates at Cloudflare. |
| Local inference | **Needs Phase 0 bench** | Ollama + 1080 Ti is documented-supported; quality unknown. |
| Hermes as gateway | **Supported now**, with hardening | MIT. **[documented]** https://github.com/NousResearch/hermes-agent/blob/main/LICENSE . Local Ollama via Custom Endpoint. **[documented]** providers docs. Toolsets can omit `terminal` / `browser` (e.g. `safe`, `hermes-webhook`). **[documented]** https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference . Default CLI toolset includes terminal — **do not use that default** in production. |

## Hermes notes (safe setup)

- Config lives in `~/.hermes/` (`config.yaml`, `.env`). Skills are markdown playbooks loaded on demand. **[documented]** https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- Memory plugins (Honcho, etc.) exist; Solomon does not use them as a database.
- Cron/jobs exist; wrap with script gates (friend's pattern; not a Hermes-unique feature).
- Email: AgentMail skill + Himalaya/IMAP skill exist. **Rejected as the intake path** (ADR-0003).
- Voice/gadget plugins exist. **Rejected as the default** in favor of HA Assist (ADR-0004).
- HA: no first-party Hermes-HA toolset found; Solomon owns the HA Adapter. HA's own MCP Server can expose Assist entities — optional, LAN only. **[documented]** https://www.home-assistant.io/integrations/mcp_server/

## Screenshot status

The eleven named 1920×1080 references are **missing** from the repo and the project store. Plan from descriptions (`08-screens-and-wireframes.md`).
