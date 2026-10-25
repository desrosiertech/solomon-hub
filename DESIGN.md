# Solomon visual system

Household surface. Warm and readable in daylight, still cool at night. Three themes share one structure. Light is a warm off-white canvas with crisp cards. Navy is the house-at-night screen. Dark is the low-light screen. None of them is pure black or pure gray. The theme control lives on Settings and is remembered in the app. A compact bottom nav and, on a wide screen, a right rail for the time, weather, dinner, and next up. Member colors mark people on the calendar. They are separate from the one blue accent.

## Themes

Set `data-theme` on the document: `light`, `navy`, or `dark`. Remember the choice. If nothing is saved, follow the operating system between light and dark. Navy is always an explicit choice.

| Token | Light | Navy | Dark |
|---|---|---|---|
| canvas | `#f3efe6` | `#08101c` | `#0e131b` |
| card | `#fffcf7` | `#101a2e` | `#171d28` |
| ink | `#241f1a` | `#e9f0fc` | `#eef3fb` |
| muted | `#6e655c` | `#c9d6ee` | `#c3cedf` |
| line | `#e4d8c8` | `#2a3d5c` | `#2c3648` |
| accent | `#1e4fd7` | `#d5e4ff` | `#c9dbff` |
| on-accent | `#f7f4ee` | `#07111f` | `#10141c` |
| wash | `#efe4d4` | `#1a2d4d` | `#243044` |

Accent is the one action color. Freshness never uses red. A stale note uses wash and ink, not a warning badge.

## Type

Sora, shipped with the app under the SIL Open Font License, weights 400, 500, and 600. Headings are 600 and slightly tight, never below -0.04em. Body stays within a comfortable measure. Timestamps and the model status may use tabular numerals. Do not set the interface in monospace.

## Surfaces

One card is the section. Rows inside it are separated by a hairline, not by a second card. Shadows are a soft downward tint, never a colored halo. The bottom navigation is a solid bar with a top hairline.

## Motion

Color and background move in 180ms with an ease-out. Nothing bounces. Content is visible before any motion.

## Controls

Primary actions are filled accent with on-accent text. Secondary actions are a hairline and ink text. Focus is a 2px accent outline, offset, and visible on keyboard. Selection, caret, and scrollbars use the same palette.
