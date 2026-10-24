# Unanswered questions

Architectural impact first. At most five are "ask now"; the rest wait. Never answer these with secrets.

## Answered (2026-10-24)

1. **Where does the daily model live?** The starting brain is Claude Opus through Nous Portal. Hermes runs on the Solomon VM and the prompts leave the house (ADR-0008). A later local model still belongs on DeepThink, in a sibling VM, after 64 GB and a 1 TB SSD (ADR-0006). That VM is not the start. Receipts and recipes the Adult submits are read by Opus and stored as Inventory and Recipe Records (ADR-0009).
2. **Who is on the tailnet?** Two Adults, both admins, for Solomon, Home Assistant, Proxmox, and the UniFi OS VM. No kids group. The WAN router is a Verizon router. UniFi OS on DeepThink controls two access points and is not the gateway.
3. **Public media-request page?** No. Overseerr stays on the tailnet. Cloudflare Tunnel stays off.
4. **Intake mailbox?** A dedicated Gmail, read over IMAP with an app password. Not the Gmail API. Not a personal mailbox. ADR-0003.
5. **TV and request site?** 65-inch LG C5 (2025, webOS). Request site is Overseerr. 10-foot UI is a browser or an HDMI device, not a native TV app.

## Later (do not block the grocery slice)

- Exact Blink camera models still in use; confirm they still work through the unofficial HA integration.
- Exact Verizon router model, so the firewall clicks match that admin page.
- Proxmox / UniFi OS / *arr / Tautulli versions. RAM currently assigned to the UniFi OS VM.
- Photo source: Google Takeout vs iCloud vs "not yet."
- Whether you want a wake word at all, or push-to-talk only.
- Local ¢/kWh, so the electricity column in the cost model is yours rather than EIA's US average.
- Whether Headscale is a requirement (default is Tailscale SaaS).
- Letterboxd/Goodreads: export files vs skip.
- Dogs' and cars' missing fields — collected in the onboarding wizard, not here.

## Assumed so we could proceed

Listed in `00-assumptions.md`: GitHub Issues + default triage labels; `AGENTS.md`; US household / NWS; Cloudflare off; Discord off; voice off until Phase 3; conservative food profile; one Household.
