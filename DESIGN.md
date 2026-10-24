# Solomon visual system

Operate surface. Sleek, technical, and cool. Three themes share one structure. Light is the daytime screen, navy is the house-at-night screen, dark is the low-light screen. None of them is pure black or pure gray.

## Themes

Set `data-theme` on the document: `light`, `navy`, or `dark`. Remember the choice. If nothing is saved, follow the operating system between light and dark. Navy is always an explicit choice.

| Token | Light | Navy | Dark |
|---|---|---|---|
| canvas | `#e7edf6` | `#08101c` | `#0e131b` |
| card | `#f5f8fc` | `#101a2e` | `#171d28` |
| ink | `#101828` | `#e9f0fc` | `#eef3fb` |
| muted | `#3e4c63` | `#c9d6ee` | `#c3cedf` |
| line | `#c5d0e2` | `#2a3d5c` | `#2c3648` |
| accent | `#1e4fd7` | `#d5e4ff` | `#c9dbff` |
| on-accent | `#f5f8ff` | `#07111f` | `#10141c` |
| wash | `#d9e4f8` | `#1a2d4d` | `#243044` |

Accent is the one action color. Freshness never uses red. A stale note uses wash and ink, not a warning badge.

## Type

Sora, shipped with the app under the SIL Open Font License, weights 400, 500, and 600. Headings are 600 and slightly tight, never below -0.04em. Body stays within a comfortable measure. Timestamps and the model status may use tabular numerals. Do not set the interface in monospace.

## Surfaces

One card is the section. Rows inside it are separated by a hairline, not by a second card. Shadows are a soft downward tint, never a colored halo. The bottom navigation is a solid bar with a top hairline.

## Motion

Color and background move in 180ms with an ease-out. Nothing bounces. Content is visible before any motion.

## Controls

Primary actions are filled accent with on-accent text. Secondary actions are a hairline and ink text. Focus is a 2px accent outline, offset, and visible on keyboard. Selection, caret, and scrollbars use the same palette.
