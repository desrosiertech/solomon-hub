# Trust-boundary table

What crosses each outbound (or third-party) hop. "Private content" means Household records, messages, images of the house, or names. Credentials never go in logs or prompts.

| Hop | When | Private content | Metadata | Images | Credentials | Notes |
|---|---|---|---|---|---|---|
| **LAN Display → Solomon** | Always | yes (whatever the Role can see) | yes | yes | Display cookie | Stays on LAN |
| **Phone → Solomon via Tailscale** | Remote access | yes | yes | yes | Member session | Encrypted WireGuard. Coordination via Tailscale SaaS |
| **Solomon host → Tailscale coordination / DERP** | Always if Tailscale is on | no (payloads are WireGuard; DERP relays ciphertext) | yes: device names, MagicDNS names, approx. traffic | no | Tailscale node key | **[documented]** https://tailscale.com/kb/1015/100.x-addresses . CT logs if `tailscale cert` is used |
| **Admin browser → HA / Proxmox / UniFi via tailnet** | Admin | HA/Proxmox state | yes | snapshots if the HA UI is opened | HA/Proxmox cookies | These UIs are tailnet-only (ADR-0005) |
| **Solomon → Home Assistant** | Devices, voice | entity states you chose to expose | yes | Blink snapshots if an adult view requests them | HA long-lived token of a **non-admin** user | Token is full-power for that user; there are no scoped LLATs. **[documented]** https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token |
| **HA → Blink cloud** | If Blink stays | arming state, motion events | yes | snapshots/clips via unofficial API | Blink username / 2FA | IoT class Cloud Polling. **No live view.** **[blocked by a third-party API]** https://www.home-assistant.io/integrations/blink/ |
| **Solomon → Google Calendar / Tasks** | If enabled | event titles, times, attendees you synced | yes | no | OAuth refresh token | Allow-list calendar IDs. Testing-mode tokens expire in 7 days. **[documented]** https://developers.google.com/identity/protocols/oauth2 |
| **Solomon → Google Photos** | Phase 4, only if chosen | **blocked for library-wide read** | — | — | — | Library API scopes removed 2025-03-31; Picker / app-created data only. **[blocked by a third-party API]** https://developers.google.com/photos/support/updates |
| **Solomon → weather (NWS or Open-Meteo)** | Weather views | no | lat/lon of home or a confirmed trip | no | none (NWS wants a User-Agent) | NWS is US-only |
| **Solomon → news feeds** | News view | no | feed URLs, IP | no | none | RSS only; no cloud "research" agent |
| **Solomon → Plex / Tautulli** | Media | watch history, library titles | yes | posters | Plex/Tautulli tokens | LAN or tailnet only |
| **Solomon → Sonarr/Radarr/Prowlarr** | Optional | request titles | yes | no | API keys | No piracy automation in Solomon |
| **Solomon → media-request app** | Optional | request titles | yes | no | API key | Distinguish inventory vs requests |
| **Solomon → intake mailbox IMAP** | Phase 2+ | email bodies, attachments | From, Message-ID | yes (receipts) | mailbox secret | Dedicated mailbox, inbound-only *use* |
| **Intake mailbox provider** | If hosted mail | they already have the mail | yes | yes | they host the box | Forwarded mail has already left the sender's provider |
| **Cloudflare edge ← `cloudflared`** | **Off by default.** Only a separate public app | **yes, for that hostname** — Cloudflare terminates TLS | yes: IP, SNI, URL | if you sent them | Access session, tunnel token | **Never** Solomon, cameras, records, chat. **[documented]** https://developers.cloudflare.com/fundamentals/concepts/how-cloudflare-works/ |
| **Cloudflare Access IdP / OTP** | Only if tunnel is on | email address used to sign in | yes | no | IdP | Free-plan seat limits apply |
| **Solomon → Ollama (LAN)** | Default AI | prompts, tool results | yes | if a VLM is used | none | Stays on LAN |
| **Solomon → cloud model API** | Per-request approval only | whatever the disclosure listed | yes | if approved | API key | A local host calling an API is still cloud inference |
| **Hermes → Solomon Tools** | When AI is on | only what the Tool returns | yes | no by default | Solomon service token, allow-listed | No host shell, no HA admin token |
| **Member → Discord** | Off by default | whatever they type | Discord metadata | if they attach | bot token | Warning: traverses Discord |
| **Letterboxd / Goodreads** | Phase 3 | ratings, titles | yes | no | API key if any | Letterboxd API is approval-gated; Goodreads keys are legacy. Prefer export/CSV |
| **UniFi / Proxmox APIs** | Systems view | client names, VMs | yes | no | local API tokens, least privilege | Tailnet only |
| **Encrypted backup off-box** | Nightly | everything, encrypted | backup size, time | n/a | backup key (held separately) | Restore drill in Phase 0 |

## What never crosses a cloud hop by default

Camera live views (there isn't an official one anyway), vet/medical Records, travel detail, Solomon chat, inventory photos, Display screenshots that include a Protected category, HA/Proxmox/UniFi admin, the Review queue.
