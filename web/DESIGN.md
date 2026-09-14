# Design plan for the web UI

Subject: boreal forest seen from orbit, and the quiet, careful work of a forest inventory.

## Palette (named hex values, taken from the summer composites)

| Name            | Hex       | Use                                                    |
|-----------------|-----------|--------------------------------------------------------|
| paper           | `#F4F6F5` | page background, cool near-white                        |
| ink             | `#111111` | all text, true dark                                     |
| ink-soft        | `#4B5350` | secondary text, axis labels (7.4:1 on paper)            |
| rule            | `#D5DBD8` | hairlines, chart grid                                   |
| canopy          | `#1F3D34` | dark blue-green of closed forest; headings, chart marks |
| forest          | `#2F5D3A` | mid green of the composites; primary series            |
| moss            | `#7FA86F` | light green; secondary series, hover fill               |
| clearcut        | `#C9A66B` | pale ochre of clearcuts; the "true value" marker        |
| accent          | `#2A6F7A` | one interactive state colour: focus ring, active toggle, links (5.0:1 on paper) |

The biomass map uses viridis and NDVI uses YlGn, both fixed in `summary.json`; the UI
draws legends from those limits and never invents colours for data.

## Type

One family: Inter (self-hosted through `@fontsource-variable/inter`), fallback system-ui.

| Role    | Size / line | Weight |
|---------|-------------|--------|
| display | 40 / 1.1    | 600    |
| heading | 26 / 1.2    | 600    |
| body    | 17 / 1.5    | 400    |
| small   | 14 / 1.4    | 400, 500 for emphasis |

Numbers use the same face with `font-variant-numeric: tabular-nums`. No monospace,
no all-caps, no eyebrow labels, no numbered section markers.

## Layout concept

A single left-aligned column, 72 ch wide for prose, opening out to 1100 px for the
patch pair, charts and gallery. The page opens on one patch shown large: true colour
beside the LiDAR biomass map, with the finding stated in a sentence under it, and a
previous/next control that crossfades the images. Everything after that is quieter:
plain headings, hairlines instead of cards, whitespace instead of boxes. The model
toggle, the residual band and the colour legend are the only decorated controls,
because they carry information. The detail view opens in place as a dialog with a
short fade; nothing animates on scroll, and both motions are off under
`prefers-reduced-motion`.

```
+----------------------------------------------------------------------+
|  Forest biomass from orbit                                    (display)|
|  one sentence of framing                                              |
|                                                                        |
|  [ true colour 256px ]   [ biomass map 256px ]   legend 0 ---- 250     |
|  Patch 3f2a9c1e  ·  LiDAR measured 87 t/ha  ·  CNN guessed 74 t/ha     |
|  That gap is 14,700 t of CO2 on this 655 ha patch.    ( prev ) ( next )|
|------------------------------------------------------------------------|
|  How well can a satellite image guess the forest?            (heading) |
|  [Ridge] [Random forest] [CNN]        MAE  RMSE  R²   tCO2/patch       |
|  +-------------------+                Ridge  ..   ..   ..   ..         |
|  |  scatter          |                RF     ..   ..   ..   ..         |
|  |     .  .          |                CNN    ..   ..   ..   ..         |
|  +-------------------+                                                 |
|  residual by bin  [ 0–50 ][ 50–100 ][ 100–150 ][ 150+ ]                |
|  one sentence on optical saturation                                    |
|------------------------------------------------------------------------|
|  Patch explorer                     sort: true biomass | CNN error | NDVI|
|  [img][img][img][img][img][img]                                        |
|  [img][img][img][img][img][img]      -> detail dialog: RGB | NDVI | AGB |
|------------------------------------------------------------------------|
|  Carbon           biomass [ 87 ] t/ha  carbon fraction [0.47]          |
|                   root-to-shoot [0.00]  area [655.36] ha  = 87,300 tCO2|
|------------------------------------------------------------------------|
|  Method and limits   (prose, 72 ch)                                    |
+----------------------------------------------------------------------+
```

At phone width the patch pair stacks, the gallery drops to two columns, the metrics
table sits under the scatter, and the detail view becomes full-screen.

## Check against the brief

- Palette from the data, cool near-white background, true dark text, one accent: yes.
- One family with a real scale; no monospace, caps, eyebrows, numbered markers, arrows: yes.
- Structure carries information (legend, residual band, toggle); no cards or gradients: yes.
- Motion only on crossfade and detail open; reduced-motion respected: yes.
- Phone width, visible focus (accent ring), contrast checked, alt text on every image: yes.
- Every number on the page traceable to `summary.json` or `patches.json`: yes.
