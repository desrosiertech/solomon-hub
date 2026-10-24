# Screen map and wireframes

Status: proposed.

> **Reference screenshots are missing.** The brief names eleven 1920×1080 design references (`02-home-busy-weekday-fri-oct-23.png`, `03-upnext.png`, `06-calendar-day-fri-oct-23.png`, `10-meals.png`, `13-meals-rate-dinner.png`, `17-recipe-original-qr.png`, `18-weather.png`, `20-news.png`, `26-settings.png`, `27-settings-feedback.png`). None of them is in this repo, in the project store, or attached to the brief. The reference PDF (a friend's "Home Hub") has small thumbnails of similar screens, but its screenshots belong to another household and are not reproduced here. These wireframes come from the written descriptions. **Re-check the layout once the PNGs are added under `docs/design/reference/`.**

## Design language

- A warm off-white canvas (`#FAF7F2`-ish), white cards with 1px warm-grey borders and soft shadows, and 16–20px radii.
- Accent colors per Member: used for calendar blocks, card headers and avatars. Every color is paired with an initial or icon, so color is never the only cue.
- Large type on the wall view (body 22–24px, headings 32–40px, clock 72px or more). The TV view scales everything to about 1.5× for a 10-foot distance.
- A compact bottom navigation (icons with labels) and a persistent right rail (time, weather, tonight's dinner, next up).
- Food freshness uses neutral and warm tones (sage and sand). **No red, no alert icons, no badges with counts on food.**
- Input: horizontal swipe between primary views on touch; arrow and Enter focus navigation on TV, with a visible focus ring; keyboard and mouse on desktop. Swipe always has visible arrow buttons as an accessible alternative.

## Screen map

| View | Wall / tablet | Desktop editor | TV (10-ft) | Guest / child | Phase |
|---|---|---|---|---|---|
| Home / Weekly snapshot | primary | yes | primary (reduced) | reduced | 1 |
| Calendar (day/week/month) | primary | full editing | week only | own and Household events | 1 |
| Meals (plan, ideas, freshness, ratings) | primary | full editing | tonight and this week | view, rate | 2 |
| Shopping list | via Meals | yes | no | view, check off | 2 |
| Recipe (steps, QR to original) | deep | yes | yes (cook mode) | yes | 2 |
| Needs review (Review queue) | deep (count chip) | yes | no | no | 2 |
| Weather | primary | yes | primary | yes | 1 |
| News digest | primary | yes | primary | configurable | 1 |
| Security (Blink snapshots, arming) | deep, adults only | yes | no | **hidden** | 3 |
| Devices / Schedules | deep | yes | no | limited toggles | 3 |
| Media / Spooktober | primary in October | yes | primary | yes | 3 |
| Travel | deep | yes | no | **hidden** (Protected category) | 4 |
| Records: Dogs, Cars | deep | yes | no | **hidden** for medical/vet | 4 |
| Photos | deep | yes | slideshow | curated albums only | 4 |
| Network / Systems | deep, adults | yes | no | **hidden** | 1 (read-only) |
| Settings | deep | yes | minimal (Display settings) | no | 1 |

The **primary rotation** (swipe order) is Home → Calendar → Meals → Weather → News, plus Media in October. Everything else is reached from a "More" grid. Every data-driven card has **loading** (skeleton), **empty** (a friendly explanation and a "how to add" link), **stale** ("Updated 2 h ago · Google Calendar unreachable") and **error** states. "Unknown" is never rendered as "none". This rule comes from the reference build.

## Wireframe 1: Home, wall view (1920×1080)

```
┌──────────────────────────────────────────────────────────────────────────────┬───────────────────────┐
│ Friday, October 23                                     ◀  Home  ▶            │  5:42 PM              │
│                                                                              │  ☁ 58°  H 64 L 49     │
│ ┌─ Up next ──────────────────────────────────────────────────────────────┐   │  Rain after 9 PM      │
│ │ 6:00  ● D  Soccer pickup (Field 3)      in 18 min                      │   ├───────────────────────┤
│ │ 7:30  ● A  Book club                                                    │   │ Tonight               │
│ │ Sat   ● Everyone  Pumpkin patch 10 AM                                   │   │ Sheet-pan chicken     │
│ └─────────────────────────────────────────────────────────────────────────┘   │ ✓ have most items     │
│ ┌─ D ──────────────┐ ┌─ A ──────────────┐ ┌─ K1 ─────────────┐ ┌─ K2 ───────┐ ├───────────────────────┤
│ │ 3:00 Dentist     │ │ 9–5 Work         │ │ School  ·  Art   │ │ School     │ │ Next up               │
│ │ 6:00 Pickup      │ │ 7:30 Book club   │ │ 4:30 Piano       │ │ —          │ │ 6:00 Soccer pickup    │
│ └──────────────────┘ └──────────────────┘ └──────────────────┘ └────────────┘ │ 7:30 Book club        │
│ ┌─ Ideas from what we have ───────────────┐ ┌─ Use soon ────────────────────┐ ├───────────────────────┤
│ │ Spinach frittata    have 4/5 · eggs ?   │ │ Spinach · fridge · ~1 day      │ │ Needs review  2       │
│ │ Chicken fried rice  have all            │ │ Leftover chili · 2 portions    │ │ (quiet chip)          │
│ │ Melon & yogurt bowl have all            │ │   freeze or use                │ │                       │
│ │                       See all in Meals ›│ │ Melon · may be past window     │ │                       │
│ └─────────────────────────────────────────┘ │   [Used] [Toss] [Still good] ⋯ │ │                       │
│                                             └────────────────────────────────┘ │                       │
├──────────────────────────────────────────────────────────────────────────────┴───────────────────────┤
│   ⌂ Home    ▦ Calendar    🍽 Meals    ☁ Weather    📰 News    ⋯ More                                    │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- The Member cards use accent color plus initial. A child or guest Display shows Household events and the child's own only.
- The Use soon row offers inline one-tap Corrections (`Used`, `Toss`, `Still good`). The `⋯` menu holds `Not now` (Dismissal) and `Stop asking` (Suppression rule). After a tap the line collapses with "Got it · Undo" for 8 seconds.
- Food cards never use red or badges. "May be past window" is grey-sand text.
- Data: `GET /api/home` returns one bundle (calendar today plus 2 days, weather snapshot, tonight's Planned meal, top-3 Meal ideas, top-3 Use soon, review count). It is cached server-side and polled every 60–120 s.

## Wireframe 2: Meals (wall and desktop)

```
┌─ Meals ─────────────────────────────────────────────────────────────────────┬─ rail ─┐
│ This week                                      [＋ Plan a night] [Shopping ›] │        │
│ Mon Tacos ★★★★ · Tue Leftover chili · Wed — (plan) · Thu Salmon · Fri Pizza  │        │
├──────────────────────────────────────────────────────────────────────────────┤        │
│ Dinner ideas from what we have                                                │        │
│ ┌ Spinach frittata ───────────┐ ┌ Chicken fried rice ─────┐ ┌ Chili mac ────┐ │        │
│ │ Have: spinach, onion, cheese│ │ Have: rice, chicken,     │ │ Have: leftover│ │        │
│ │ Probably have: milk         │ │  frozen peas, soy sauce  │ │  chili        │ │        │
│ │ Check amount: eggs (some)   │ │                          │ │ Need: elbow   │ │        │
│ │ Need: —                     │ │ Need: —                  │ │  pasta        │ │        │
│ │ [Plan for Wed] [Not now ⋯]  │ │ [Plan for Wed] [⋯]       │ │ [Plan] [⋯]    │ │        │
│ └─────────────────────────────┘ └──────────────────────────┘ └───────────────┘ │        │
├──────────────────────────────────────────────────────────────────────────────┤        │
│ Freshness (estimates)                                    Why these dates? ⓘ  │        │
│  Use soon     Spinach (fridge, ~1 day) · Berries (~2 days)                    │        │
│  Leftovers    Chili, 2 portions, made Tue — freeze or use by ~Fri             │        │
│  Past window  Melon — may be past its expected freshness window               │        │
│               [Used] [Toss] [Still good] [Stop asking]                        │        │
│  Probably gone (3) ▸   collapsed; Stale and Presumed discarded items          │        │
└──────────────────────────────────────────────────────────────────────────────┴────────┘
```

- "Plan for Wed" never replaces an existing Planned meal. If Wednesday is taken, it asks "Replace Tacos or add a second dinner?"
- `ⓘ` opens the explanation: category default, acquired date, storage, profile, and an edit field.
- Rating (from `13-meals-rate-dinner`): after a Planned meal's date, a per-Member star row appears on that day's tile.

## Wireframe 3: Needs review (desktop and tablet)

```
┌─ Needs review (2) ───────────────────────────────────────────────────────────────────────┐
│ ▸ Receipt · Grocery store · Oct 23 · forwarded by A · via email   [original] [provenance]  │
│   Extracted locally (Tesseract 5 + rules) — no cloud call                                 │
│   ┌──────────────────────────────┬──────────────┬─────────┬──────────┬────────────────┐   │
│   │ Line on receipt              │ Item         │ Qty     │ Store in │ Confidence     │   │
│   ├──────────────────────────────┼──────────────┼─────────┼──────────┼────────────────┤   │
│   │ ORG BBY SPINACH 5OZ   3.99   │ Spinach ▾    │ 1 pkg   │ Fridge ▾ │ ● high         │   │
│   │ CANTALOUPE EA         2.49   │ Melon ▾      │ 1       │ Counter ▾│ ● high         │   │
│   │ KS PAPER TWL 12PK    19.99   │ (non-food) ▾ │ —       │ —        │ ignored        │   │
│   │ GRK YGT PLN 32OZ      5.49   │ ? Yogurt ▾   │ 1 tub   │ Fridge ▾ │ ◐ check        │   │
│   └──────────────────────────────┴──────────────┴─────────┴──────────┴────────────────┘   │
│   [Apply 3 items]  [Reject receipt]  [Archive]       Duplicate check: no match            │
│ ▸ Vet invoice · Oct 20 · forwarded by D                                                    │
│   Proposed: Visit recorded for Dog 1 on Oct 20. Vaccines NOT inferred from invoice.        │
│   [Approve visit] [Edit] [Reject]                                                          │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Wireframe 4: TV home (10-ft, remote focus)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  Friday 5:42 PM                                                  ☁ 58°  rain after 9 │
│                                                                                      │
│  [ Tonight: Sheet-pan chicken ]   [ Up next: 6:00 Soccer pickup ]   [ Weather ▸ ]    │
│     ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ (focus ring)                                           │
│                                                                                      │
│  Spooktober 2026 · 14 watched     [ Recent ▸ ] [ Favorites ▸ ] [ Log a movie ▸ ]     │
│                                                                                      │
│  Watch                             [ Plex ] [ Netflix ] [ … ]  (launch only)         │
└──────────────────────────────────────────────────────────────────────────────────────┘
   ◀ ▶ move · OK select · Back returns · no camera, records, travel or systems tiles
```

The TV Display is enrolled with the `display` or `guest` Role. It never shows Security, Records, Travel or Systems. "Watch" tiles are app-launch shortcuts only; a unified continue-watching row stays out of scope until it is proven per app (see `01-feasibility.md`).
