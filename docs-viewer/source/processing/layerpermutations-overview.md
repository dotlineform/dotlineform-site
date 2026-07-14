---
doc_id: layerpermutations-overview
title: "Processing: Layered Composites for All Permutations"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Processing: Static Layered Composites for All Image Permutations

> Export meta Timestamp: 2025-08-29 15:06:53 BST Original prompt: Provide a processing file and a html description of the approach and overview of the code functions

## Overview

This approach generates static composites by layering *n* source images in every possible order (permutations). Each output corresponds to a unique stacking order (top-over-bottom), optionally cycling through a list of blend modes per layer index. The system resizes inputs to a common target size, composites them using Photoshop-like blend formulae implemented per-pixel, and writes a PNG for each permutation with a filename that encodes the order and modes.

## Workflow

1. Place source images (`PNG`/`JPG`) into `data/input` in the Processing sketch.
2. Run the sketch. It will:
  - Load and optionally resize images to the size of the first image.
  - Compute all permutations of image indices (size `n!`).
  - For each permutation, composite images from base to top using selected blend modes.
  - Save results to `output/` (relative to the sketch folder).

## User Settings

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `INPUT_DIR` | String | `"input"` | Subfolder inside `data/` to load images from. |
| `OUTPUT_DIR` | String | `"output"` | Folder next to the sketch where composites are saved. |
| `TARGET_W, TARGET_H` | int | `-1` | Target size; if `RESIZE_TO_FIRST` true, uses first image size. |
| `LAYER_OPACITY` | float | `1.0` | Opacity applied to each top layer before alpha-over. |
| `RESIZE_TO_FIRST` | boolean | `true` | Resize all inputs to match the first image. |
| `CYCLE_MODES` | boolean | `true` | Cycle through `MODES` by layer index; if false, uses `MODES[0]` for all. |
| `MAX_PERMS` | int | `-1` | Limit number of permutations processed (useful for testing). |
| `MODES` | String[] | `('MULTIPLY', 'SCREEN', 'OVERLAY', 'LIGHTEN', 'DARKEN')` | Blend modes available: NORMAL, MULTIPLY, SCREEN, OVERLAY, LIGHTEN, DARKEN, DIFFERENCE, ADD, SUBTRACT, SOFTLIGHT. |

## Key Functions

### `setup()`

Loads images, normalizes sizes, generates permutations, and drives the composite-and-save loop.

### `permute(int[] arr, int l)`

Classic in-place recursive permutation generator; appends each completed permutation to `perms`.

### `blendTwo(PImage base, PImage top, String mode, float opacity)`

Performs per-pixel blending of `top` into `base` using the chosen `mode`, then alpha-composites the blended RGB against the base with standard Porter–Duff `over`. Returns a new `PImage`.

### `applyMode(float b, float t, String mode)`

Channel-wise (0–255) implementation of common blend modes: NORMAL, MULTIPLY, SCREEN, OVERLAY, LIGHTEN, DARKEN, DIFFERENCE, ADD, SUBTRACT, SOFTLIGHT (approximation). Extendable for other modes.

### Helpers

- `endsWithAny` filters filenames by extension.
- `joinInt` formats permutation indices into filenames.
- `swap` supports the permutation routine.

## Output Filenames

Each file is saved as `perm_<idx-idx-...>__modes_<mode[-mode...]>.png`, where indices refer to the order of images loaded from `data/input`.

## Performance Notes

- Time and storage scale with `n!`. Consider **combinations** instead of permutations if order is unimportant.
- For very large sets or real-time needs, port `blendTwo` to a `PShader` (GLSL) to use the GPU.
- Use `MAX_PERMS` while testing to avoid generating thousands of files unintentionally.

## Next Extensions

- CSV-driven per-layer *mode* and *opacity* schedules.
- K-combinations generator (choose *k* out of *n*, order-insensitive).
- Deterministic file ordering (alphanumeric sort) and explicit index ↔ filename manifest (CSV).

Prepared for Apple Notes / GitHub. If you need a Markdown variant, I can generate it too.
