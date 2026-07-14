---
doc_id: seededrandom-overview
title: "Seeded Random Subset — How It Works"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Seeded Random Subset (Final‑Only build)

> Timestamp: 2025-08-29 19:54:17 BST

## What it is

Instead of keeping every *n*‑th permutation (stride), the sketch can select a **random subset** of permutations by percentage. It uses a **fixed seed**, so the same seed reproduces the same subset exactly.

## Controls

- **Sampling Mode**: *STRIDE* or *RANDOM*
- **Random keep %**: 1–100% of the total permutations (rounded to at least 1)
- **Random SEED**: integer (e.g., 12345) for reproducibility
- **First N (Final)**: optional cap after sampling

## How it works (RANDOM)

```
// Java-like pseudocode
build all permutations → workerTotal
want = round(workerTotal * keep_pct)
indices = [0, 1, 2, ..., workerTotal-1]
shuffle(indices, seed)      // deterministic shuffle
selected = take first 'want'
sort(selected)              // keep ascending order for filenames/progress
render selected[0..FirstN-1]
```

## Filenames

Output files include a tag indicating the sampling, e.g.:

```
__stride_10 or __randpct_10_seed_12345
```

## Why use seeded random?

- Less regular than stride; gives a more natural sample across the space.
- Still reproducible for audits/regeneration: same seed → same subset.
