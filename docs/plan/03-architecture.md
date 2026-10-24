# Architecture

Solomon is a deep module: a small HTTP interface in front of domain services that hide food math, intake, sync and permissions. Hermes is a client of that interface, not a peer database.

```
 Displays (LAN)     Phones (tailnet)      TV device
        │                  │                  │
        └────────────┬─────┴──────────────────┘
                     ▼
              Solomon app/API          bind: LAN + tailnet only
         ┌───────────────────────────┐
         │ auth (Member / Display)   │
         │ domain services + jobs    │── SQLite WAL + blobs
         │ ModelProvider seam        │── Ollama (LAN) or Disabled
         └─────────────┬─────────────┘
                ▲      │ allow-listed
                │      ▼
           Hermes      Adapters ──► Google, weather, news, Plex,
           gateway                  intake IMAP, UniFi, Proxmox
                │
                ▼
           Home Assistant  ← Device authority, voice pipeline
                │
                ▼
              Blink, lights, satellites   (HA's credentials)
```

No WAN :80/:443. Optional Cloudflare Tunnel is a *separate* public app, never this diagram's left side (ADR-0005).

## Runtime pieces

| Piece | Runs where | Why |
|---|---|---|
| Solomon container | Dedicated VM/LXC on reserved LAN IP | ADR-0002 |
| Hermes container | Same host, no host network, no Docker socket | Isolated gateway |
| Ollama | Sibling VM on DeepThink | ADR-0006. Not inside HAOS |
| Home Assistant OS | Existing Proxmox VM on Deepthink | Untouched, except a non-admin token and Tailscale |
| `cloudflared` | Not installed | Overseerr stays on the tailnet. No public request page |

## Permissions matrix

Capabilities are granted to Roles. Displays never inherit a Member.

| Capability | Adult | Teen | Child | Guest | Display | Hermes service |
|---|---|---|---|---|---|---|
| View Home / Calendar / Weather / News | yes | yes | own + household | household public | household public | — |
| Plan meals, shop, inventory edits | yes | yes | limited | no | tap-sized only | propose only |
| Review queue (apply/reject) | yes | if granted | no | no | no | propose |
| Security cameras / arming | yes | no | no | no | no | no |
| Disarm / unlock | confirm in UI | no | no | no | no | `request_confirmation` only |
| Travel, vet, medical | yes | own | no | no | no | propose |
| Systems / Proxmox / UniFi | admin adult | no | no | no | no | no |
| Settings, Members, secrets | admin adult | no | no | no | Display settings only | no |
| Permanent delete | admin adult | no | no | no | no | **never** |
| Cloud request approval | yes | no | no | no | no | no |
| Tailnet admin | admin adult | no | no | no | no | no |

HA token: created as a **non-admin** HA user whose exposed entities are the allow-list. MCP Server, if used, has "Require administrator" **off** and "Expose all LLM APIs" **off**, Assist API only. **[documented]** https://www.home-assistant.io/integrations/mcp_server/  
Hermes has **no** host shell and **no** HA admin token.

## Jobs vs Hermes vs subagents

| Kind | Mechanism | Examples |
|---|---|---|
| Poll, age, sync, calculate | Solomon jobs (ordinary code) | calendar sync, weather, inventory aging, suggestion suppression, backup |
| Interpret a Member's words, write a brief | Hermes Skill on demand or a gated cron | "we're out of milk", optional Up Next curator |
| Bounded research / parallel extract | Delegated subagent, minutes of life, no standing rights | "summarize these three already-fetched feed items" |

A new Skill is reviewed, versioned and tested before it gains Tools. Hermes may not self-promote a Skill into production.

## Observability and fallback

- Each Adapter writes `integration_status`. Cards show "Updated 2 h ago" instead of emptying.
- Audit log for writes, permission changes, cloud approvals, Display enroll/revoke.
- Encrypted nightly SQLite backup + restore drill (Phase 0).
- Manual fallback: every Agent Tool is a tap in the UI.

## Outage behaviour

| Dependency down | What stays up |
|---|---|
| Ollama / Hermes | Dashboard, meals, inventory, shopping, calendar cache, devices via HA |
| Google | Last synced events, stale chip; manual events still writable |
| HA | Dashboard and records; device tiles stale; no voice |
| Tailscale | LAN Displays still work; phones away do not |
| Internet | Local data, HA, Ollama; weather/news/calendar go stale |
