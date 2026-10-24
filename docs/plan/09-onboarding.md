# Onboarding

Credentials are typed into the running app and stored on the host. They are never pasted into a chat, a ticket, or the repo.

## Wizard steps

1. **Household** — display name, time zone, accent colors per Member, Roles (Adult / Teen / Child).
2. **Auth** — first Adult passkey. Invite others by a one-time link on LAN/tailnet only.
3. **Displays** — enroll wall/TV with a 10-minute code (friend's pattern). Revoke lives in Settings.
4. **Tailnet** — checklist: install Tailscale on phones; confirm MagicDNS; do not enable Funnel. Link to ADR-0005. Optional: paste the tailnet policy for a sanity diff (no keys).
5. **Cloudflare Tunnel** — default **Skip**. If enabled later, a separate wizard: hostname, Access policy, disclosure "Cloudflare can see this site's traffic."
6. **Food** — only: storage locations; serving size; preferred store(s); conservative vs permissive estimates; Dismissal suppression days; auto-archive vs review for Presumed discarded.
7. **Dogs / cars** — names, and a missing-record list: "I don't have vaccine dates yet." No fabricated due dates.
8. **Calendars** — Google OAuth in-app. Allow-list calendar IDs. Disclose: event titles leave to Google and come back; tokens stay on disk.
9. **Home Assistant** — URL + a non-admin long-lived token. Entity picker (expose to Solomon).
10. **Weather / news** — home lat/lon (or a city pick), feed URLs, topics.
11. **Intake mailbox** — IMAP host and a dedicated address. Approved-sender list. Retention days.
12. **Media** — Plex/Tautulli URLs, request-app URL. Letterboxd/Goodreads skipped unless an export is uploaded.
13. **Voice** — default Off. If On: satellite type, hardware mute confirmed, wake-word disclosure checkbox.
14. **Model** — Ollama URL, model name, policy `local_only`. Cloud provider fields hidden until an Adult opts in.
15. **Backup** — destination and a reminder that the key is stored separately.

Each integration page has **Disconnect**, **Export my data**, and a "last sync / stale" line.

## Missing-record prompts (quiet)

Shown once per subject on Home for Adults, not as notifications:

- "I don't have Dog 1's rabies date yet."
- "I don't have the sedan's last oil change."
- "No reserved LAN check has been run this month" (links the Phase 0 checklist).

## Permissions recap (shown as a table in Settings)

The matrix from `03-architecture.md`, editable per Member. Child and Guest views hide Protected categories. A Display cannot be promoted to Adult.
