---
doc_id: estimator-overview
title: "On‑Canvas Estimator — How It Works"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# On‑Canvas Time & Memory Estimator

> Timestamp: 2025-08-29 19:37:35 BST

This build adds a live estimator panel (right side) so you can sanity‑check runtimes and RAM before hitting PREVIEW or FINAL.

## What it uses

- **n**: number of images detected in the SOURCE folder (PNG/JPG/JPEG).
- **Resolution**: UHD if UHD mode is on, otherwise it probes the first image.
- **Preview Scale**: scales pixel count by `scale²`.
- **Stride** (1‑in‑n) and **First N**: to estimate how many composites will be produced.
- **MPix/s** slider: your CPU’s effective throughput (default 150).
- **Auto‑Levels**: adds a 20% overhead to the estimate.

## Formulas

```
pixels_per_image = width × height × scale²
seconds_per_composite ≈ (n × pixels_per_image) / (MPix/s × 1e6) × (1.2 if Auto‑Levels else 1.0)
total_seconds ≈ seconds_per_composite × composites_to_render  (after stride & First‑N)
```

These are ballpark numbers; actual timings depend on JVM, disk, and modes used.
