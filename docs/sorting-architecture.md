# Sorting Architecture

This document defines canonical sorting behavior across generated artifacts and runtime pages.

## Canonical Source Of Truth

- Canonical per-series work order is `assets/series/index/<series_id>.json` `work_ids`.
- `header.sort_fields` records the declared sort strategy (for example `title,work_id`).

## Cached Derivative

- `_works/<work_id>.md` contains `series_sort`.
- `series_sort` is a cache derived by `scripts/generate_work_pages.py` from workbook rules.
- `series_sort` is still used by some build-time Liquid sorts (for example in `_layouts/work.html`).

## Runtime Usage By Page

- `series` page grid (`_layouts/series.html`):
  - Uses series JSON `work_ids` order.
- Work page series navigation (`_layouts/work.html`):
  - Runtime prev/next uses series JSON.
  - Build-time counter context still uses front-matter `series_sort`.
- Works index (`works/index.md`):
  - Uses per-row data attributes and JS sorting.
  - Supports `seriessort` key via work front matter `series_sort`.

## Regeneration Contract

Whenever series ordering might change (new work in series, title/year edits affecting sort, SeriesSort changes):

1. Regenerate `work-pages` for affected series (refresh `_works` `series_sort` cache).
2. Regenerate `series-json` for affected series (refresh canonical JSON order).

Recommended command:

```bash
./scripts/generate_work_pages.py --only work-pages,series-json --series-ids <series_id> --force --write
```

## Generator-Enforced Consistency (Drift Guard)

`scripts/generate_work_pages.py` enforces a drift guard during `series-json` runs:

- It compares existing `_works/*.md` `series_sort` to generator-computed canonical values.
- If drift exists, generation fails with a remediation command.
- This prevents writing updated series JSON while leaving stale work front matter.

Opt-out (not recommended):

```bash
./scripts/generate_work_pages.py ... --no-series-sort-drift-guard
```

## Why This Hybrid Exists

- JSON order is the canonical, cross-page runtime order.
- Front-matter `series_sort` remains useful as a fast build-time cache for Liquid templates.
- The drift guard + regeneration contract keeps both aligned.
