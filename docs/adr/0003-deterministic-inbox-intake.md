# Dedicated mailbox, deterministic intake, Hermes stays off the inbox

Solomon has its own inbound mailbox (not anyone's personal Gmail). A Domain service polls it, stores originals, extracts locally, and opens Proposed changes. Hermes may *read an already-classified Proposed change* through a Tool. It never has IMAP credentials, never sends or deletes mail, and never sees raw email as "instructions".

**Status:** accepted. Vendor decided 2026-10-24: a dedicated Gmail address that belongs to Solomon, read over IMAP with an app password. Not either Adult's personal mailbox. Not the Gmail API. A consumer OAuth client in testing mode drops its refresh token after 7 days, which an unattended poller cannot live with. The app password can do more than read; the intake service never sends, replies, or deletes. Hermes still never sees the mailbox.

## Considered options

- **Separate Google mailbox + Gmail API.** Reliable. `gmail.readonly` is a restricted scope for public apps. **[blocked by a third-party API]** A personal "testing" OAuth client expires refresh tokens in 7 days unless the project is published. **[documented]** https://developers.google.com/identity/protocols/oauth2
- **Hosted mailbox with IMAP** (Fastmail, a consumer mailbox using an app password, or similar). Least-privilege is "inbound-only" in Solomon: we store IMAP credentials that *could* do more, and we simply never send. Maintenance is low.
- **Self-hosted (Mailcow or similar).** Full privacy. Costs: port 25, PTR, rDNS, residential-IP blocks, spam. Not worth it for one intake address.
- **AgentMail / Hermes email gateway.** The friend's hub uses this so the agent owns the inbox. Rejected: untrusted mail must not be a prompt, and the brief forbids the agent from personal inboxes *and* from send/reply/forward/delete unless separately enabled.

## Write policy (Household-tunable)

| Type | Default |
|---|---|
| Grocery receipt (local OCR) | Proposed change; one-tap apply |
| Order / shipping | Proposed change |
| Recipe | Proposed change |
| Trip | Proposed change |
| Vet or medical | Proposed change; **never** infer a vaccine from an appointment or payment |
| Vehicle | Proposed change until three confirmed matches (from the reference hub) |
| Unknown sender or type | Stay in the Review queue |

Approved senders only, plus an explicit "allow this sender" action. Spoofing: compare the authenticated From (SPF/DKIM alignment when the provider exposes it) to the allow-list; otherwise treat as unknown. Forwards inherit the *forwarding Member*, not the original From, as the trusted actor.

## Security rules

- Tokens live in the host secret store. No credentials, raw bodies or attachments in logs or in any model prompt.
- Attachments: documented MIME allow-list and size cap; AV/type sniff; no link-following; no executing attachments.
- Email body, attachments, links and OCR text are **untrusted data**. The extractor never treats them as instructions (see the injection fixture in `bench/household-tasks.json`).
- Originals stay on disk with `retention_until`. Search, export, permanent deletion and disconnect are first-class.

Hermes current email capability is recorded in `docs/plan/07-hermes-skills.md`. Even if Hermes grows a first-class mail plugin, Solomon still owns intake.
