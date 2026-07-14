---
doc_id: layerpermutations-csv-overview
title: CSV-driven Layer Rules for Processing Permutation Composites
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# CSV-driven Per-layer Rules

> Export meta Timestamp: 2025-08-29 15:31:22 BST Context: Add CSV: specify per-layer blend mode, opacity (SEQUENTIAL) and weight (AVERAGE).

## Where to put the CSV

Save as `data/layer_rules.csv` in the Processing sketch folder.

## CSV Columns (header required)

| Column | Type | Meaning |
| --- | --- | --- |
| `layer` | int (1..n) | Position of the layer in the stack; 1 = base/bottom, n = top. |
| `mode` | string | Blend mode (SEQUENTIAL only). Leave blank to use cycling/default. |
| `opacity` | 0..1 | Opacity for this layer (SEQUENTIAL only). Blank → uses `LAYER_OPACITY`. |
| `weight` | ≥ 0 | Weight for AVERAGE strategy. All weights are normalized; blank → 1.0. |

## Example

```
layer,mode,opacity,weight
1,,1.0,1.0
2,SOFTLIGHT,0.35,1.0
3,SCREEN,0.35,1.0
4,MULTIPLY,0.35,1.0
5,OVERLAY,0.35,1.0
6,DARKEN,0.35,1.0
```

## Behaviour & Fallbacks

- If a row is missing for some `layer`, the code falls back to cycling through `MODES` and using `LAYER_OPACITY` (SEQUENTIAL), or weight = 1.0 (AVERAGE).
- Extra rows beyond `n` are ignored.
- Weights are normalized to sum to 1 for the AVERAGE strategy.

## Tip

For “all images contribute”, try **AVERAGE** with weights tuned in the CSV, and keep **AUTO_LEVELS** enabled to restore contrast.

Need a combinations-only generator or a manifest CSV mapping indices → filenames? I can add those too.
