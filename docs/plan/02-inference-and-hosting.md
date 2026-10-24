# Inference and hosting

**No latency or VRAM-fit number in this file is a measurement.** Phase 0 runs `bench/` on the real box. Labels: **documented** / **experimental** / **blocked by a third-party API**.

Recommendation: **configuration C** (ADR-0001). Dedicated Solomon+Ollama host (or VM) on the LAN. Deepthink stays HAOS. Skynet stays Plex. Tailscale for remote access (ADR-0005). Cloudflare Tunnel off.

## Three configurations

| | A. Fully local | B. Local Hermes, cloud API | C. Local default + approved cloud (chosen) |
|---|---|---|---|
| Privacy | Prompts stay on LAN | Prompts leave on every turn | Prompts stay unless an Adult approves that request |
| Reliability | Needs the box up; no vendor outage | Needs internet + vendor | Local path works offline; cloud is extra |
| Tool-use quality | Depends on the 7–32B class you can host | Frontier (Haiku/Flash/mini) | Daily = A; hard jobs can use B once |
| Vision / OCR | Local Tesseract + optional VLM | Cheap cloud vision | Same as A unless approved |
| Concurrency | 1–2 chats if VRAM allows | Vendor-side | Same as A |
| Latency | Untested. Budget seconds, not ms | Typically <3 s for small APIs | Same as A for the default path |
| Idle / peak power | GPU TDP if a card is pinned; CPU-only is tens of watts | App host only (~20–40 W class) | Same as A |
| Setup | Ollama + weights | API key + disclosure UI | Both, cloud locked |
| Upfront | $0 extra on 1080 Ti / CPU; $400–1500 used GPU if you upgrade | $0 hardware | Same as A |
| Monthly | Electricity only | API bill (see bands) | Electricity + $0 until someone approves a cloud call |

A private server calling an API **is still B**. A rented GPU is off-premises.

## Hardware (do not overload what you have)

| Box | Role | Fit |
|---|---|---|
| Deepthink i7-6700 / 16 GB / HAOS VM | Device authority only | Do not put Ollama here. HA already wants RAM. Whisper `base-int8` *inside HA* for voice is a Phase 3 maybe. **[experimental]** |
| Skynet + GTX 1080 Ti 11 GB | Plex first | Ollama lists the 1080 Ti (CC 6.1) as supported with driver **570+**. **[documented]** https://github.com/ollama/ollama/blob/main/docs/gpu.md . A short bench is OK. Pinning a daily model here is **experimental** until a transcode + model run is measured. TDP 250 W (NVIDIA spec). |
| Dedicated host (proposed if bench fails) | Solomon + Ollama | Used RTX 3090 24 GB (~350 W) or 4060 Ti 16 GB (~160 W), or 32 GB+ unified memory (Mac mini M4 / Ryzen AI Max+). Pick after numbers, not before. |

Ollama is MIT. **[documented]** https://github.com/ollama/ollama  
Local Ollama is an OpenAI-compatible `/v1` endpoint; Hermes reaches it as a Custom Endpoint (`http://<lan>:11434/v1`, no key). **[documented]** https://hermes-agent.nousresearch.com/docs/integrations/providers (and the repo `website/docs/integrations/providers.md`). Ollama Cloud is a *different* provider and sends prompts off-box.

Useful knobs (names **documented** in Ollama FAQ/docs; values to set after the bench): `OLLAMA_CONTEXT_LENGTH`, `OLLAMA_NUM_PARALLEL`, `OLLAMA_MAX_LOADED_MODELS`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_KV_CACHE_TYPE`. Hermes warns that Ollama's default context is much smaller than the model's max. **[documented]** same providers page.

## Models to put on the bench (re-check tags on the day)

Do not invent a winner. On Phase 0 day, pull whatever `https://ollama.com/library` lists as **tools**-capable in the 7–9B class and one stronger tag that still fits the card.

| Role | Starting guess | License (re-check card) |
|---|---|---|
| Daily tools | Qwen3 8B class (Hermes docs still mention Qwen2.5/Qwen3 pulls) | Typically Apache-2.0 for Qwen — confirm the exact tag |
| Stronger local | 20–32B Q4 or a 12B VLM | Varies (Llama community / Gemma terms / Apache) |
| OCR without VLM | Tesseract (Apache-2.0) in the Solomon image | Always available, AI off |

Vision/OCR for receipts is **local first**. A cloud VLM is a Cloud request approval.

## Electricity

EIA Electric Power Monthly Table 5.6.A, **August 2026**: US residential average **18.16 ¢/kWh** (17.57 ¢/kWh August 2025). **[documented]** https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_6_a  
Use your utility rate when you have it. New England in the same table is 28.31 ¢ — replace the US average if that is you.

Sample monthly kWh (TDP × hours × 0.4 load factor — **experimental**, not a bench):

| Scenario | Hardware assumption | kWh / month | @ 18.16 ¢ |
|---|---|---|---|
| CPU-only Ollama, light | 40 W extra × 8 h/day | ~10 | ~$1.80 |
| 1080 Ti pinned, normal | 250 W × 0.4 × 4 h/day | ~12 | ~$2.20 |
| 3090 dedicated, heavy | 350 W × 0.5 × 8 h/day | ~42 | ~$7.60 |
| App host only, AI off | 15 W always | ~11 | ~$2.00 |

Plex already pays the 1080 Ti's idle; only *incremental* watts count if you share Skynet.

## Cloud API prices (optional path; 2026-10-24)

Per **1M tokens**, input / output, from vendor pages. Re-fetch before enabling.

| Provider | Cheap / fast SKU | Input | Output | Source |
|---|---|---|---|---|
| OpenAI | `gpt-5-mini` | $0.25 | $2.00 | **[documented]** https://platform.openai.com/docs/pricing |
| OpenAI | `gpt-5.4-mini` | $0.75 | $4.50 | same |
| Anthropic | Haiku 5.5 (≤100K) | $0.50 | $2.50 | **[documented]** https://www.anthropic.com/pricing |
| Anthropic | Sonnet 5.5 | $2.00 | $10.00 | same |
| Google | `gemini-3.8-flash` paid | $0.75 | $3.75 (promo through 2026-12-31) | **[documented]** https://ai.google.dev/gemini-api/docs/pricing |

OpenAI API: business data is not used for training by default. **[documented]** https://openai.com/api/pricing (Business/Enterprise copy) and https://platform.openai.com/docs/guides/your-data — re-read the current retention paragraph (commonly 30 days unless Zero Data Retention) before enabling.

### Token-band cost (visible assumptions)

Assumptions: 4k input + 400 output tokens per "turn"; 30 / 150 / 600 turns per month; using OpenAI `gpt-5-mini`.

| Band | Turns | Tokens in / out | Cost @ mini |
|---|---|---|---|
| Light | 30 | 0.12M / 0.012M | ~$0.05 |
| Normal | 150 | 0.60M / 0.06M | ~$0.27 |
| Heavy | 600 | 2.4M / 0.24M | ~$1.08 |

A Sonnet-class month at "heavy" is still tens of dollars, not hundreds — **privacy, not price, is why C's default is local**.

Ollama itself is free. Ollama Cloud (if someone turns it on) is a paid off-box API; treat it as B.

## Sizing

See `bench/README.md` for the KV formula. Speech (Whisper + Piper) lives on HA in Phase 3 and is budgeted separately. Vision/OCR is bursty: do not keep a VLM loaded (`OLLAMA_KEEP_ALIVE` short) on an 11 GB card.

## Decision points

1. Run `bench/run_benchmark.py` on Skynet (Plex idle and transcoding) and, if needed, on a spare box.
2. If the daily model meets the pass bar without starving Plex → stay on the 1080 Ti for Phase 1–2, dedicated later.
3. If it fails → buy/repurpose a dedicated ≥16 GB card; do not steal Deepthink from HA.
4. Cloud stays locked until an Adult opts in and we have the disclosure UI.
