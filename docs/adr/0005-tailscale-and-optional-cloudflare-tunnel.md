# Tailscale for remote access; Cloudflare Tunnel off by default

Remote phone and admin access uses the Household tailnet. Cloudflare Tunnel is an optional, off-by-default path for a *public* page (for example a media-request site), never for Solomon's household data. The WAN-facing firewall is empty: default-deny inbound, no port forwards. Both Tailscale and `cloudflared` only need outbound connectivity.

**Status:** accepted. Household policy decided 2026-10-24, and it narrows the sketch below.

- The tailnet has two Adults. Both are admins. Both may open Solomon, Home Assistant, and Proxmox.
- The WAN router is a Verizon router. Firewall rules go there. There is no UniFi gateway.
- UniFi OS is a VM on DeepThink. It controls two access points. Both Adults may admin that VM. It does not route the house.
- Do not create `group:kids`. No guest device gets a tailnet login.
- Overseerr is the media-request app. It stays on the tailnet. Cloudflare Tunnel stays off. Nobody outside the two Adults submits requests.
- The Display is a 65-inch LG C5 (2025, webOS). A later 10-foot layout is a browser or an HDMI device. There is no Tizen app.

## Why

The attack surface of a household server is the tailnet. This Household does not turn on a Cloudflare hostname. A VPS with Traefik on :443 (the friend's hub) is rejected for Solomon itself. Overseerr stays on the tailnet with everything else.

## Tailscale (default on)

**Control plane vs data plane.** Peers coordinate through Tailscale's SaaS and then speak WireGuard to each other, falling back to Tailscale DERP relays when NAT blocks a direct path. **[documented]** https://tailscale.com/kb/1015/100.x-addresses and https://tailscale.com/blog/how-tailscale-works  
Metadata (who is online, device names, some traffic stats) is visible to Tailscale. Packet payloads are not, except when they transit DERP. Treat the coordination server as a Trust boundary (see `docs/plan/04-trust-boundaries.md`).

**Headscale** (https://github.com/juanfont/headscale) is the self-hosted coordination-server alternative. Use it only if the Household refuses Tailscale's SaaS; feature gaps (HTTPS certs, some app features, Funnel, support) must be re-read on the install date. Default: Tailscale SaaS.

### Identity and policy

Use **grants** as the current policy syntax, with classic ACLs only if a needed feature is still ACL-only. **[documented]** https://tailscale.com/docs/features/grants and https://tailscale.com/kb/1337/acl-syntax

Sketch from planning (names are placeholders). For this Household, skip the `group:kids` grant and treat both Adults as admins. The `group:adults` split that withholds Proxmox and UniFi does not apply.

```jsonc
{
  "tagOwners": {
    "tag:server": ["autogroup:admin"],
    "tag:ha": ["autogroup:admin"],
    "tag:infra": ["autogroup:admin"],
    "tag:display": ["autogroup:admin"]
  },
  "grants": [
    // Adults: Solomon + HA user UI. Not Proxmox, not UniFi, not SSH.
    {
      "src": ["group:adults"],
      "dst": ["tag:server"],
      "ip": ["tcp:443", "tcp:8000"]
    },
    {
      "src": ["group:adults"],
      "dst": ["tag:ha"],
      "ip": ["tcp:8123"]
    },
    // Admins: infra UIs and SSH.
    {
      "src": ["autogroup:admin"],
      "dst": ["tag:infra", "tag:ha", "tag:server"],
      "ip": ["*"]
    },
    // Phones of children: Solomon only, if they have a login.
    {
      "src": ["group:kids"],
      "dst": ["tag:server"],
      "ip": ["tcp:443", "tcp:8000"]
    }
  ],
  "ssh": [
    {
      "action": "check",
      "src": ["autogroup:admin"],
      "dst": ["tag:server", "tag:infra"],
      "users": ["autogroup:nonroot", "root"]
    }
  ]
}
```

- **Tags** on servers (`tag:server`, `tag:ha`, `tag:infra`, `tag:display`). Tagged devices are not owned by a departing person. **[documented]** https://tailscale.com/kb/1068/acl-tags
- **Groups** per person-role (`group:adults`, `group:kids`). A Guest does not get a tailnet device.
- **MagicDNS** on, so phones open `solomon.<tailnet>.ts.net`. **[documented]** https://tailscale.com/kb/1081/magicdns
- **HTTPS certs / `tailscale serve`:** useful, but `tailscale cert` publishes the machine name in Certificate Transparency logs. **[documented]** https://tailscale.com/kb/1153/enabling-https — do not put a secret hostname in the cert CN if that bothers you; use a boring name (`hub`, `ha`).
- **Key expiry:** default 180 days for user devices. **[documented]** https://tailscale.com/kb/1028/key-expiry  
  Tagged devices can have expiry disabled so a reboot does not lock the family out of Solomon. Review tagged-device keys on a calendar anyway.
- **Device approval** on for new nodes. MFA via the identity provider Tailscale is hooked to (Google / Apple / GitHub — pick at onboarding; no secrets in chat).
- **Funnel off.** Disable public Funnel exposure with a node attribute deny, so a curious `tailscale funnel` cannot publish Solomon. **[documented]** https://tailscale.com/kb/1223/tailscale-funnel
- **`--shields-up`** on Displays and phones that should not *accept* inbound tailnet connections. **[documented]** https://tailscale.com/docs/reference/tailscale-up (or `tailscale set --shields-up`)
- **Tailscale SSH** for admin hosts only, with `check` (not `accept`) so a session still needs an extra approval.

### Subnet routers vs installing the client

Prefer **the client on each host** that has an admin UI: Solomon, HAOS (HAOS Tailscale add-on), Proxmox, the UniFi controller (or the gateway if UniFi OS supports it).

| Pattern | Use when |
|---|---|
| Client on the host | Default. HA, Proxmox, Solomon, UniFi UI stay tailnet-only. |
| Subnet router | Last resort for a device that cannot run Tailscale (a printer, a camera NVR). One tagged router, routes approved, ACLs still deny cameras to kids. **[documented]** https://tailscale.com/kb/1019/subnets |
| Exit node | Not needed for Solomon. Optional for "send my phone's traffic out through home" while travelling. **[documented]** https://tailscale.com/kb/1103/exit-nodes |

**HA and the Proxmox admin UI are tailnet-only.** They bind to LAN + tailnet. They are not published through Cloudflare. Community Tailscale add-on for HA: https://github.com/tailscale/tailscale-homeassistant (or the current HA community add-on page — re-check at install).

Tailscale itself does **not** require an inbound WAN port. Direct paths use NAT traversal; otherwise traffic relays via DERP over outbound HTTPS. Optional UDP 41641 improves direct connections but is not required. **[documented]** https://tailscale.com/kb/1082/firewall-ports

Personal/free plan device and user limits: re-read https://tailscale.com/pricing on the day you invite everyone. A family of a few Members plus four tagged servers is usually inside the Personal tier; verify rather than assume.

## Cloudflare Tunnel (optional, default off)

`cloudflared` opens **outbound-only** connections to Cloudflare. The origin should not listen on public 80/443. **[documented]** https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/configure-tunnels/tunnel-with-firewall/ and https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/

When (and only when) something truly public is required — a media-*request* page, not the library, not Plex playback:

1. Run a **separate** Compose service with its own hostname.
2. Put **Cloudflare Access** (Zero Trust) in front. Free-plan Access seat limits: re-read https://www.cloudflare.com/plans/zero-trust-services/ (commonly cited as 50 users; confirm). Identity: one-time PIN or an IdP. **[documented]** https://developers.cloudflare.com/cloudflare-one/applications/configure-apps/self-hosted-public-app/ and https://developers.cloudflare.com/cloudflare-one/identity/one-time-pin/
3. Lock the origin so it only accepts Cloudflare (tunnel, not a public bind). **[documented]** https://developers.cloudflare.com/fundamentals/security/protect-your-origin-server/
4. Free-plan WAF managed rules sit in front. **[documented]** https://developers.cloudflare.com/waf/managed-rules/

**Disclosure:** Cloudflare **terminates TLS at the edge** and can see that hostname's request and response bodies. **[documented]** https://developers.cloudflare.com/ssl/concepts/ and https://developers.cloudflare.com/fundamentals/concepts/how-cloudflare-works/  
Never route camera feeds, medical/vet records, travel, chat, or the Solomon app itself through the tunnel by default. Cloudflare's application-service terms restrict using the CDN as a general video-hosting platform; **[documented]** https://www.cloudflare.com/service-specific-terms/application-services/ — another reason Plex and Blink do not go this way.

Tunnel tokens live in the host secret store, not in git.

## Firewall and test

On the Verizon router **and** on each host:

- Inbound WAN: default deny, no port-forward rules, no UPnP.
- Inbound LAN: only what that host needs (Solomon from LAN Displays; HA from Solomon and satellites).
- Outbound: allow Tailscale, (optional) cloudflared, then the explicit Adapter list (Google, weather, …).

Test procedure: `docs/plan/13-phase0-security-checklist.md`. Pass means an external scan of the WAN IP shows no 80/443/8123/8000/22, a phone on the tailnet reaches Solomon, and a phone *off* the tailnet does not.
