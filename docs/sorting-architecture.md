# Sorting Architecture

This document defines canonical sorting behavior across generated artifacts and runtime pages.

## Canonical Source Of Truth

- Canonical per-series work order is `assets/data/series_index.json`:
  - `series.<series_id>.works` is the ordered `work_id` list.
  - `series.<series_id>.sort_fields` records the declared sort strategy (for example `title,work_id`).
- Runtime card metadata comes from:
  - `assets/data/works_index.json` (`works.<work_id>.*`)

## Cached Derivative

- `_works/<work_id>.md` contains `series_sort`.
- `series_sort` is a cache derived by `scripts/generate_work_pages.py` from workbook rules.
- `series_sort` is still used by some build-time Liquid/JS sorting paths (for example the works index `seriessort` sort key).

## Runtime Usage By Page

- `series` page grid (`_layouts/series.html`):
  - Uses `assets/data/series_index.json` for ordered works in series.
  - Uses `assets/data/works_index.json` for card title/thumb metadata.
- Work page series navigation (`_layouts/work.html`):
  - Runtime prev/next and counter use `assets/data/series_index.json`.
  - Runtime series-link visibility (`| series`) uses `assets/data/series_index.json`.
- Works index (`works/index.md`):
  - Uses per-row data attributes and JS sorting.
  - Supports `seriessort` key via work front matter `series_sort`.

## Regeneration Contract

Whenever series ordering might change (new work in series, title/year edits affecting sort, SeriesSort changes):

1. Regenerate `work-pages` for affected series (refresh `_works` `series_sort` cache).
2. Regenerate `series-index-json` (refresh canonical runtime JSON order).
3. Regenerate `works-index-json` when work card metadata changes (title/year/media/thumb fields).

Recommended command:

```bash
./scripts/generate_work_pages.py --only work-pages,series-index-json,works-index-json --series-ids <series_id> --force --write
```

## Why This Hybrid Exists

- `assets/data/series_index.json` order is the canonical cross-page runtime order.
- Front-matter `series_sort` remains useful as a fast build-time cache for Liquid templates.
- The regeneration contract keeps both aligned.
