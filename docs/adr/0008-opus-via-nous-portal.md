# Claude Opus through Nous Portal is the starting brain

Hermes starts on Claude Opus, reached through Nous Portal, the same kind of arrangement as the friend's hub. Hermes itself stays on the Solomon VM. Each thinking turn leaves the house. The DeepThink Ollama VM in ADR-0006 is the later brain, the one that stays on the LAN. Grocery still runs with the provider disabled.

**Status:** accepted (2026-10-24). Supersedes "option B is rejected as the default" in ADR-0001, and supersedes the interim 3B as the model we start with in ADR-0006.

## Why

The Household asked to start here. A 3B on the current DeepThink cannot read a receipt photo or a book page. Opus can, and it can call Solomon's tools. Nous Portal is one subscription and one login (`hermes setup --portal`), not an Anthropic API key. **[documented]** https://hermes-agent.nousresearch.com/docs/integrations/nous-portal

The call goes to `https://inference-api.nousresearch.com/v1`. Nous picks the upstream for that model, and the upstream can change. Some models go through OpenRouter. The friend's diagram labels this box "Claude Opus via Nous Portal."

## What is sent

An Adult's turn. A receipt image they submitted. A recipe screenshot, a photo of a book page, or the text of a recipe URL they asked Solomon to bank. Hermes memory and skills ride along in later turns, because that is how Hermes loads them.

The Tool Gateway stays off: no web search, no generated recipe pictures, no cloud browser, no cloud terminal. A recipe image is the photo they sent or the picture on the source page.

## What stays home

SQLite, the original images, and the Hermes files. The Verizon router still has no inbound ports. Solomon does not move to a public VPS.
