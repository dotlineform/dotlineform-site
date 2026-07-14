---
doc_id: stride-overview-2
title: "1‑in‑n Sampling (Stride) — Processing Permutation Composites"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# 1‑in‑n Sampling (Stride)

> Timestamp: 2025-08-29 19:22:15 BST

When there are many permutations (e.g., 720 for 6 images), computing all can be slow. The new **1‑in‑n** option lets you render only every n‑th permutation (n between 1 and 10). With `n=10`, you’ll process ~10% of the total set.

## How it works

- After generating all permutations, the sketch keeps only indices where `i % n == 0`.
- Then the normal “First N” cap is applied on top, so you can combine both filters.
- Filenames include a `__stride_n` tag; the manifest logs the resulting files as usual.

## When to use it

- Quick surveys across the permutation space without creating thousands of images.
- Combine with *Preview Scale* and *First N* for very fast iterations.

Want a *random subset* option as an alternative to regular stride? Easy to add next.
