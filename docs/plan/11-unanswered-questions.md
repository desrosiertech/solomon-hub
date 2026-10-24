# Unanswered questions

Architectural impact first. At most five are "ask now"; the rest wait. Never answer these with secrets.

## Ask now

1. **Where does the daily model live?** Dedicated box vs a cautious 1080 Ti experiment vs CPU-only until a GPU is bought. This decides the Phase 0 shopping list and whether Skynet is touched. (ADR-0001; bench first if unsure.)
2. **Who is on the tailnet, and who may admin Proxmox/UniFi/HA?** Needed to write real grants (adults vs kids vs you-only). No need to name children in the reply — "two adults admin, kids get Solomon only" is enough.
3. **Is a public media-request page required, or can requests stay on the tailnet?** If public, Cloudflare Tunnel + Access becomes a Phase 4 project; if not, it stays off forever.
4. **Intake mailbox vendor: hosted IMAP (Fastmail-class) vs a separate Google mailbox?** Not credentials — just which kind. This picks the OAuth vs app-password path (ADR-0003).
5. **Samsung TV model/year, and the name of the existing media-request site?** Decides whether a Tizen app is worth a prototype or the TV is "browser on a stick / HDMI device."

## Later (do not block the grocery slice)

- Exact Blink camera models still in use; confirm they still work through the unofficial HA integration.
- UniFi / Proxmox / *arr / Tautulli versions.
- Photo source: Google Takeout vs iCloud vs "not yet."
- Whether you want a wake word at all, or push-to-talk only.
- Local ¢/kWh, so the electricity column in the cost model is yours rather than EIA's US average.
- Whether Headscale is a requirement (default is Tailscale SaaS).
- Letterboxd/Goodreads: export files vs skip.
- Dogs' and cars' missing fields — collected in the onboarding wizard, not here.

## Assumed so we could proceed

Listed in `00-assumptions.md`: GitHub Issues + default triage labels; `AGENTS.md`; US household / NWS; Cloudflare off; Discord off; voice off until Phase 3; conservative food profile; one Household.
