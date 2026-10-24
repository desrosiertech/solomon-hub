# Phase 0 security checklist

Do this on the real network before any household data is loaded. Cloudflare Tunnel stays **off**.

## Build the empty inbound edge

1. UniFi gateway: no port-forward / DNAT / UPnP / NAT-loopback exceptions. WAN inbound default deny. **[documented]** UniFi port-forwarding is an explicit extra: https://help.ui.com (search "Port Forwarding"; UI moves — confirm on the controller version you run).
2. Each host (Proxmox, HAOS, Solomon, Windows Plex): host firewall default-deny inbound from WAN-facing interfaces. Allow LAN sources you intend (Displays → Solomon; satellites → HA).
3. Confirm nothing listens on public 80/443. Solomon binds `127.0.0.1` + LAN + tailnet. HA listens on LAN + tailnet only.

## Tailscale

1. Create the tailnet. Turn on **device approval**. Invite only household adults first.
2. Install the client on Solomon, HA, Proxmox, UniFi (or the controller), and one admin phone. Tag servers. Disable key expiry on tagged nodes; leave it on for phones.
3. Apply the decided grants in ADR-0005. Two Adult admins. Do not create `group:kids`.
4. MagicDNS names only, boring host labels (`hub`, `ha`, `pve`).
5. `tailscale funnel` denied. `--shields-up` on phones and Displays.
6. Turn the HA and Proxmox UIs off the general LAN if you can; if not, rely on passwords *and* the tailnet ACL so a guest Wi-Fi client still cannot admin them.

## Tests (acceptance)

| # | Test | Pass |
|---|---|---|
| S0.1 | From a host *outside* the house (phone on cellular, or a VPS you control), `nmap -Pn -p 22,80,443,8000,8123,41641,51820 <WAN-IP>` | No open ports. Filtered/closed is pass. **[documented]** nmap SYN scan: https://nmap.org/book/man-port-scanning-techniques.html |
| S0.2 | Optional second opinion: GRC ShieldsUP! or equivalent against the WAN IP | No unexpected open TCP |
| S0.3 | Phone **on** the tailnet opens `https://hub.<tailnet>.ts.net` (or the LAN IP over Tailscale) | Solomon dashboard loads |
| S0.4 | Same phone, Tailscale **off**, cellular only, same URL and the WAN IP | Connection fails. No dashboard |
| S0.5 | Tailnet has exactly the two Adult admins. No `group:kids` grant | Both can open Solomon, HA, Proxmox, and UniFi. Any other device cannot |
| S0.6 | Guest Wi-Fi client | No Solomon admin, no HA, no Proxmox |
| S0.7 | `cloudflared` is not installed, or the service is disabled | `systemctl is-enabled cloudflared` is inactive |
| S0.8 | Backup: take an encrypted copy, restore onto a throwaway VM, Alembic revision matches | Restore drill signed off |
| S0.9 | Secrets: `git grep` for tokens; host secret files are mode 600 and not in the repo | Clean |

External scanners see the WAN IP, not the tailnet. Do not paste the real WAN IP into this repo.

## After Phase 0

Re-run S0.1–S0.4 whenever a UniFi rule, a Compose port, or a "temporary" tunnel is added. The empty inbound firewall is a standing invariant, not a one-time setup.
