---
doc_id: dualres-overview
title: "Dual‑Resolution Preview & Final Export — Processing Workflow"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Dual‑Resolution Preview & Final Export

> Timestamp: 2025-08-29 19:06:51 BST

## Why Dual‑Res?

UHD (3840×2160) images are large (~33 MB per layer in ARGB). When you composite multiple layers and iterate across many permutations, the time and memory add up quickly. The dual‑resolution workflow lets you iterate quickly at a much smaller size (e.g., 960×540 at 25%), then export the same settings at full resolution.

## How It Works

1. Pick your SOURCE and OUTPUT folders in the GUI.
2. Adjust options (UHD mode, strictness, greyscale, strategy, opacity, auto‑levels, clip %, preview scale).
3. Click **PREVIEW (scaled)** to generate downscaled composites (filenames contain `__scale_0.25` etc.).
4. When satisfied, click **EXPORT FINAL** to generate the full‑resolution set (`__scale_1.00`).

## What Gets Logged

A single `manifest.csv` is maintained in the OUTPUT folder. Each row records the composite’s filename (which includes the scale tag), permutation order, strategy, modes, auto‑levels setting, and the filenames of the source images used. This keeps preview and final runs traceable together.

## Performance Tips

- Use **Preview Scale 10–50%** while tuning. Expect 10–100× faster loops vs UHD.
- Cap runs during development with `MAX_PERMS` in the code (e.g., 25 or 100).
- If UHD Mode is on but inputs aren’t UHD, set *UHD STRICT* = off to auto‑resize; turn it on to validate final sources.
- Leave Auto Levels in *Auto Contrast* (per‑channel off) for greyscale inputs.

## Compatibility

The dual‑res path preserves blend strategy, layer rules (via CSV), and auto‑levels behaviour. Only the pixel resolution changes between preview and final runs.

Want a “first N permutations only” preview mode, or a progress bar? I can add those as well.
