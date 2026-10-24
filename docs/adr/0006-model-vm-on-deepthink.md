# Daily model on DeepThink, beside Home Assistant

The daily model runs on DeepThink, the ThinkCentre M910s (i7-6700, Proxmox), in its own VM. Home Assistant OS stays the Device authority and does not run Ollama. Skynet stays Plex. Solomon's Household default stays the disabled provider until a bench on this VM passes.

**Status:** accepted (2026-10-24). Supersedes the hardware-host paragraphs in ADR-0001. Configuration C in that ADR still stands.

## Why this host

The Household asked for the model on DeepThink, with a virtual machine in the interim. The chassis can take that job after a memory and disk upgrade. It cannot take a full-size GPU: Lenovo specifies a 180 W or 210 W supply and a 64 GB DDR4 UDIMM ceiling. **[documented]** https://psref.lenovo.com/syspool/Sys/PDF/ThinkCentre/ThinkCentre_M910_SFF/ThinkCentre_M910_SFF_Spec.pdf

Latency on this CPU is unmeasured. Expect multi-second replies for a 3B–8B model. **[experimental]** The pass bar in `bench/README.md` (p95 under 8 seconds at 8k context) still applies. Missing it means a different computer later, not a card in this Small chassis.

## Considered options

- **1080 Ti on Skynet.** Rejected as the home. Plex keeps that machine. A short bench there is no longer the plan.
- **Buy a dedicated GPU host first.** Rejected as the starting purchase. RAM and a disk let DeepThink hold an 8B beside Home Assistant. A faster GPU is a later machine.
- **Ollama inside Home Assistant OS.** Rejected. ADR-0002: do not couple the model to the Device authority's upgrades or RAM.

## What to buy

- 64 GB as 4×16 GB DDR4-2400 or 2666, 1.2 V, non-ECC, unbuffered, 288-pin. The i7-6700 runs it at 2133. 32 GB (2×16) is enough for Home Assistant plus one 8B, and is the smaller buy. Remove the existing sticks when filling all four slots.
- A 1 TB SSD for model files and the VM disk. NVMe if the M.2 slot is empty; otherwise a 2.5-inch SATA drive. Confirm which bay the current 240 GB drive uses before ordering.
- No GPU, and no CPU swap, in this order.

## Interim VM

Until that RAM is installed, one Ubuntu VM on the current 16 GB host:

- Sibling of the Home Assistant VM. Not an add-on.
- 2 vCPU, 6 GB pinned (no balloon), about 40 GB of disk if the SSD has room.
- One 3B tool-capable model. An 8B does not fit beside Home Assistant in 16 GB.
- Listen on the LAN and the tailnet only.
- Home Assistant keeps a fixed share of RAM (4 GB if it is currently allowed to take more).

After the RAM is in, raise the same VM to 16 GB and 3 vCPU and pull the 8B candidate. Run `bench/run_benchmark.py` there.
