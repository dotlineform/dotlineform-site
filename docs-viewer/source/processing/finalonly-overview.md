---
doc_id: finalonly-overview
title: "Final‑Only Build — Overview"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Final‑Only Build (Preview removed)

> Timestamp: 2025-08-29 19:45:27 BST

## What changed

- Preview path removed entirely: no preview button, no preview scale, no preview code.
- Single **EXPORT FINAL** button drives the whole pipeline at full resolution.
- Estimator shows time for *Final only*.

## What’s still included

- UHD mode / strictness / greyscale.
- Blend strategies (Sequential, Average), layer opacity, Photoshop‑like modes.
- Auto Levels / Auto Contrast (percentile clip).
- CSV layer rules and manifest logging.
- 1‑in‑n stride sampling and Final “First N” cap.
- Progress bar and runtime/memory estimator.

## Filenames & Manifest

Final images include a `__stride_n` tag when sampling is used. The `manifest.csv` retains the same columns as previous builds.
