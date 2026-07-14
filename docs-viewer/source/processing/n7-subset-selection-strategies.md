---
doc_id: n7-subset-selection-strategies
title: "Subset Selection Strategies for Permutations (n = 7)"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Subset Selection Strategies for Permutations (n = 7)

> Timestamp: Sunday, 31 August 2025 at 05:41 PM Prompt: Generate an Excel demonstrating subset selection methods for n = 7 and an HTML explanation of the strategies.

Download the Excel (n = 7 strategies):

n7_subset_selection_strategies.xlsx

For n = 7, the full set has 7! = 5,040 permutations. The workbook shows four practical ways to choose manageable subsets that still capture variety or structure:

| Sheet | Order | Method | Parameters | Count | When to Use |
| --- | --- | --- | --- | --- | --- |
| `SJT_first_500` | SJT (adjacent swaps) | Truncated prefix | M = 500 | 500 | When you want smooth, minimal-change transitions between successive permutations. |
| `Lexi_stride_10` | Lexicographic | Stride | k = 10 | 504 | When you want simple, evenly spaced coverage across the full list. |
| `Lexi_random_500` | Lexicographic | Random sample | M = 500, seed = 42 | 500 | When you want variety with reproducibility (seeded randomness). |
| `Lexi_spaced_500` | Lexicographic | Evenly spaced indices | M = 500 | 500 | When you want uniform spread across range without the periodicity of stride. |

## Strategy Notes

- **SJT truncated:** Uses the Steinhaus–Johnson–Trotter (SJT) order so that each successive permutation differs by a single adjacent swap, producing smooth changes. Truncating to the first `M` permutations yields a coherent minimal‑change sequence.
- **Stride (k):** Take every `k`-th item in lexicographic order. This gives even coverage but can introduce periodicity.
- **Random sample:** Uniformly sample permutations with a fixed seed for reproducibility. Captures variety; not smooth frame-to-frame.
- **Evenly spaced indices:** Select `M` indices approximately uniformly across `[0, 7!-1]`, which often avoids stride periodicity while giving good coverage.

## Extensions

Other interesting subsets include *derangements* (no fixed points) and selections by distance metrics (e.g., balance of Hamming distance or inversion count), or factorial-number-system ranking/unranking for direct indexed access.

All selections here are *reproducible* given the stated parameters (stride and seed). SJT ensures adjacent-swap continuity; lexicographic-based selections focus on coverage and variety.
