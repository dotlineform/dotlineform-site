---
doc_id: permutations-calc-and-save-explainer
title: How the Processing Sketch Calculates & Saves Permutations
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# How the Processing Sketch Calculates & Saves Permutations

> Project: Processing-based layered composites · Last updated: 2025-08-29 19:33:07 BST

## Overview

The sketch loads images from the selected *SOURCE* folder, builds all permutations of their indices, optionally downsamples (Preview), then composites each selected permutation and writes a PNG to the *OUTPUT* folder. Every saved image is also recorded in `manifest.csv` for traceability.

## 1) Building the permutation index list

After the images are loaded (and normalized to a common size if needed), the sketch creates an integer index array `baseIdx = [0, 1, 2, ..., n-1]` where `n` is the number of images. The recursive backtracking algorithm below generates every ordering (permutation) and appends a copy to `perms`:

```
// Classic backtracking with in-place swaps
void permute(int[] arr, int l) {{            // l = current position to fix
  if (l == arr.length - 1) {{                // base case: last position fixed
    perms.add(arr.clone());                  // store a copy of the current order
    return;
  }}
  for (int i = l; i < arr.length; i++) {{   // try each choice for position l
    swap(arr, l, i);                         // put choice i at position l
    permute(arr, l + 1);                     // recurse for the next position
    swap(arr, l, i);                         // backtrack (restore)
  }}
}}

void swap(int[] a, int i, int j) {{ int t = a[i]; a[i] = a[j]; a[j] = t; }}
```

If the files in the SOURCE folder are sorted alphanumerically before forming `baseIdx`, the permutation list has a deterministic, repeatable order (useful for “first N” and stride sampling).

Note:

The number of permutations grows as

n!

(factorial).

For example: 4 images → 24, 5 → 120, 6 → 720, 7 → 5040.

## 2) Selecting which permutations to render

Before rendering, the sketch applies two optional filters:

- **Stride (1‑in‑n):** keep only permutations where `index % n == 0` (e.g. n=10 ≈ 10% sampled).
- **First N:** cap the number rendered to the first N of the (optionally) strided list. Preview and Final have independent N values.

```
// After permute()
int total = perms.size();
ArrayList selected = new ArrayList();
for (int i = 0; i < total; i++) {{ if (i % STRIDE_N == 0) selected.add(i); }}

int limit = (FIRST_N < 0) ? selected.size() : min(FIRST_N, selected.size());
```

These controls make large jobs manageable without changing the underlying permutation order.

## 3) Rendering and saving each composite

For each chosen permutation (an array of layer indices), the sketch either: *Sequentially blends* the layers using a Photoshop‑like mode (Multiply, Screen, Overlay, etc.) and opacity, or computes an *Average* (weighted mean) across all layers. Then it optionally applies Auto Levels/Contrast with percentile clipping.

```
// Pseudocode for the main loop
for each selected permutation 'order':
  PImage out;
  String modesUsed = "N/A";

  if (BLEND_STRATEGY == "AVERAGE"):
    out = averageComposite(order);
  else:
    out, modesUsed = sequentialComposite(order, layerRules, opacity, modes…);

  if (AUTO_LEVELS):
    out = autoLevelsPercentile(out, perChannel, clipPercent);

  String name = buildFilename(order, BLEND_STRATEGY, AUTO_LEVELS, scale, stride);
  out.save(OUTPUT/name);
  appendManifestRow(name, order, BLEND_STRATEGY, modesUsed, autoLevelMode, sourceFilenames);
```

### Filename structure

Filenames encode the key settings for easy scanning:

```
perm_{{order}}__blend_{{strategy}}__auto_{{auto}}__scale_{{s}}[__stride_{{n}}].png
```

- `{{order}}` — e.g. `0-2-1-3` (indices into the sorted source file list).
- `{{strategy}}` — `SEQUENTIAL` or `AVERAGE`.
- `{{auto}}` — e.g. `AutoContrast_clip0.50pct` or `None`.
- `{{s}}` — preview scale, e.g. `0.25` or `1.00`.
- `__stride_{{n}}` — present only when using 1‑in‑n sampling.

### Manifest CSV

Each saved composite gets a row in `manifest.csv` located in OUTPUT. Columns:

| filename | Saved PNG filename (includes scale & stride tags) |
| --- | --- |
| order | Permutation indices, e.g., 0-2-1-3 |
| strategy | SEQUENTIAL or AVERAGE |
| modes | Per-layer modes when sequential (e.g., BASE-MULTIPLY-SCREEN-…); N/A for average |
| auto_levels | AutoLevels, AutoContrast, or None |
| source_files | CSV list of the source filenames in the exact order used |

## 4) Progress, Preview vs Final, and UHD

- **Preview vs Final:** The same pipeline runs at different scales (e.g. 25% vs 100% of UHD), so visual decisions match the final output.
- **Progress bar:** Compositing runs in a background thread; the draw loop shows a bar & counters.
- **UHD greyscale mode:** Enforce or auto-resize to 3840×2160 and optionally force-convert to greyscale before compositing.

## Why a backtracking permutation algorithm?

It generates permutations in-place without extra allocations, and emits them in a stable, deterministic order given the initial sorted input list. It’s simple, fast in Java, and works well with our stride and first‑N filters.

Want this page to include a complexity table (n vs n!) and estimated render times at UHD? I can add that.
