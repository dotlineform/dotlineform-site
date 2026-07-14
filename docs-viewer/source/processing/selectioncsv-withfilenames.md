---
doc_id: selectioncsv-withfilenames
title: "Selection CSV — With Source Filenames"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Selection CSV — Now includes source filenames

> Timestamp: 2025-08-29 20:23:31 BST

The `selection_indices.csv` export now maps each permutation’s order indices to the **actual source filenames** (from your sorted SOURCE folder). This improves auditability and makes it trivial to reproduce a given composite elsewhere.

## CSV Columns

- `perm_index` — index into the full permutation list
- `order` — indices like 0-2-1-3
- `source_files` — filenames in the exact order for that permutation (semicolon‑separated)
- `sampling_mode`, `stride_n`, `random_keep_pct`, `random_seed`
- `first_n_applied` — cap after sampling
- `source_dir` — absolute path captured at export time
