---
doc_id: layerpermutations-autolevels-overview
title: "Processing: Permutation Composites + Auto Levels"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Processing: Permutation Composites + Auto Levels

> Export meta Timestamp: 2025-08-29 15:26:12 BST Original prompt: Blending images needs low opacity so all the images contribute. Can processing emulate a Photoshop auto-levels or auto-contrast function? → Yes → integrate into pipeline.

## What’s new

- **Auto Levels / Auto Contrast** post-process with percentile clipping to approximate Photoshop’s behaviour.
- **Blend strategies:** `SEQUENTIAL` (Photoshop-like stacking using modes + opacity) or `AVERAGE` (equal-weight mean).
- Customizable clip percentage (`AUTO_CLIP_PERCENT`) and per-channel vs unified scaling (`AUTO_LEVELS_PER_CHANNEL`).

## Key Settings

| Setting | Default | Meaning |
| --- | --- | --- |
| `BLEND_STRATEGY` | `"SEQUENTIAL"` | Stack with modes, or use `"AVERAGE"` for equal contributions. |
| `LAYER_OPACITY` | `1.0` | Opacity per added layer (SEQUENTIAL only). |
| `AUTO_LEVELS` | `true` | Enable auto normalization after compositing. |
| `AUTO_LEVELS_PER_CHANNEL` | `false` | *false* ≈ Auto Contrast (preserves colour balance); *true* ≈ Auto Levels (per-channel scaling). |
| `AUTO_CLIP_PERCENT` | `0.5` | Clip percent from shadows and highlights (e.g. 0.5% on each side). |

## Auto Levels Algorithm

1. Build histograms for either each channel (R,G,B) or a luma-like combined channel.
2. Find low/high thresholds by clipping a small percentile from each end.
3. Linearly rescale pixel values so low → 0 and high → 255 (clamped).

## Functions

### `sequentialComposite(order)` / `averageComposite(order)`

Two compositing strategies: Photoshop-like stacking with blend modes or equal-weight averaging for low-opacity look.

### `autoLevelsPercentile(img, perChannel, clipPercent)`

Performs Auto Levels/Auto Contrast with configurable clipping; calls `rescalePerChannel` or `rescaleUnified`.

### `applyMode(b, t, mode)`

Implements common blend modes (NORMAL, MULTIPLY, SCREEN, OVERLAY, LIGHTEN, DARKEN, DIFFERENCE, ADD, SUBTRACT, SOFTLIGHT).

## Tips

- When using `SEQUENTIAL`, try `LAYER_OPACITY = 1.0 / n` to balance contributions.
- For faithful colour, prefer `AUTO_LEVELS_PER_CHANNEL = false` (Auto Contrast).
- Use `MAX_PERMS` while testing to avoid generating thousands of files.

Prepared for Apple Notes / GitHub. Ask for a Markdown variant or a combinations-only generator if needed.
