# Local inference by default, with an explicit cloud fallback

Solomon's default AI path is an on-LAN OpenAI-compatible endpoint (Ollama first). Household content is not sent to a model provider unless a Member approves that one request and sees what would leave. The product stays useful with the provider disabled.

**Status:** accepted (planning). Hardware pick is *proposed* until Phase 0 measures it.

## Considered options

- **A. Fully local open-weight inference.** Best privacy and offline behaviour. Tool quality and vision depend on the box. Concurrent chat plus OCR plus a briefing can thrash an 11 GB card.
- **B. Locally hosted Hermes calling a paid cloud API.** Same as the friend's hub. Prompts leave the house. A rented GPU is also off-premises. Better tool-use, worse privacy and a recurring bill.
- **C. Local by default, cloud only after per-request approval (chosen).** Keeps A as the daily path. Unlocks a stronger model for a hard receipt or a travel brief, with a visible disclosure. Needs a provider interface and a `cloud_request` audit row.

A private server calling an API is still cloud inference. Option B is rejected as the *default*.

## Why Ollama first

Ollama is an OpenAI-compatible local endpoint with documented tool calling, vision tags, Windows and Linux GPU support, and a simple keep-alive story. **[documented]** https://github.com/ollama/ollama/blob/main/docs/gpu.md lists GTX 1080 Ti (compute 6.1) as supported, with driver 570 or newer on Pascal. Alternatives (llama.cpp server, vLLM) are evaluated only if a Phase 0 number shows a real gain. vLLM is a poor fit for a 1080 Ti / one-household box.

Grok 4.7 is the *coding* model for this repo. It is not the household production model.

## Starting models (to confirm on hardware)

Not measured. Do not treat these as results.

| Role | Candidate to bench | Why |
|---|---|---|
| Daily tool-capable | A current 7–9B class Ollama model with tools (Qwen3 8B or whatever `ollama.com/library` lists as tool-capable when Phase 0 runs) | Fits 8–11 GB with room for KV if context stays modest |
| Stronger local | A 20–32B Q4 or a 12B vision-language model, only on ≥16–24 GB VRAM | Receipts, harder tool use |
| OCR without a VLM | Tesseract in-process, optional PaddleOCR | Deterministic fallback; no GPU required |
| Cloud fallback (off) | A cheap current Flash/Haiku/mini class, chosen at enable-time from live vendor pages | Never the default |

Exact names, licenses and file sizes live in `docs/plan/02-inference-and-hosting.md` and must be re-checked on the Phase 0 date.

## Hardware threshold

- Do **not** run the household model inside HAOS. Deepthink's 16 GB is already split with Home Assistant.
- Do **not** displace Plex on Skynet. A 1080 Ti can *host a short benchmark* and maybe a small nightly job if VRAM headroom during transcodes is proven.
- **Upgrade when** Phase 0 shows the daily model cannot hold the target context (8k) plus tools at a usable latency (p95 < 8 s for a tool turn) without touching Plex, or when local OCR+rules fail the receipt fixture set. The first upgrade class is a dedicated box with ≥16 GB VRAM (used 3090 / 4060 Ti 16 GB) or 32 GB+ unified memory. Apple Silicon and Ryzen AI Max+ are in the comparison; pick after the bench, not before.

## Interface

Solomon talks to a `ModelProvider` seam: `complete(messages, tools, policy) -> { text, tool_calls, usage }`. Adapters: `OllamaProvider`, `DisabledProvider`, later `CloudProvider` gated by `Cloud request approval`. The outbound data policy is a Household setting, default `local_only`.
