---
doc_id: n9-sjt-1min-all-fps-explainer
title: "n=9 — 1‑Minute Video Strategies (SJT, 24/25/30/60 fps)"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# n=9 — 1‑Minute Video Strategies

> Timestamp: Sunday, 31 August 2025 at 06:04 PM Prompt: Create an Excel and HTML that assemble SJT‑order permutations for a 1‑minute video at 24/25/30/60 fps and explain the options.

Download the Excel (SJT subsets, 1 minute each):

n9_SJT_1min_all_fps.xlsx

## Best Strategy

**Use Steinhaus–Johnson–Trotter (SJT) order** and truncate to the exact number of frames for your chosen frame rate. SJT changes only two adjacent elements per step (adjacent swap), producing the *minimal possible change* between frames — smooth and visually coherent.

## Frame Counts for 1 Minute

| Frame Rate | Frames (1 min) | ms/frame | Visual feel |
| --- | --- | --- | --- |
| 24 fps | 1,440 | ≈ 41.7 | Classic cinematic cadence, light stutter/blur |
| 25 fps | 1,500 | 40.0 | PAL/EU broadcast, slightly smoother than 24 |
| 30 fps | 1,800 | ≈ 33.3 | Crisper “live” look (web/TV) |
| 60 fps | 3,600 | ≈ 16.7 | Ultra‑smooth, high clarity (sports/gaming) |

## How to Render

1. Generate each permutation frame (e.g., render your scene/visual using the ordering from the Excel sheet).
2. Export as an image sequence (e.g., PNGs) named with zero‑padded indices.
3. Assemble in your NLE or FFmpeg at the chosen frame rate (24/25/30/60 fps).
4. *Looping tip:* SJT isn’t cyclic; add a short crossfade (≈ 6–12 frames) from end to start for a seamless loop.

## Why Not Random/Stride?

- **Random:** maximizes variety but produces uneven, jumpy motion between frames.
- **Stride/Spaced indices:** spreads coverage but breaks the adjacent‑swap continuity → larger visual jumps.

SJT is a permutation Gray code with an adjacent swap at each step. For n=9, the full set has 362,880 permutations; for a 1‑minute video, you only need the first N items for your frame rate.
