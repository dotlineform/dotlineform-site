---
doc_id: sorting-architecture
title: "Sorting Architecture"
added_date: 2026-03-31
last_updated: 2026-03-31
parent_id: architecture
sort_order: 30
---

# Sorting Architecture

This document records the current canonical ordering rules across generated artifacts and runtime pages.

It is an architecture note because it defines where ordering is owned and how different runtime surfaces stay aligned. It is not a field-by-field schema reference.

## Canonical Source Of Truth

- Canonical per-series work order is `assets/data/series_index.json`:
  - `series.<series_id>.works` is the ordered `work_id` list.
  - `series.<series_id>.sort_fields` records the declared sort strategy (for example `title,work_id`).
- Runtime card metadata comes from:
  - `assets/data/works_index.json` (`works.<work_id>.*`)

## Cached Derivative

- `_works/<work_id>.md` contains `series_sort`.
- `series_sort` is a cache derived by the catalogue generator during scoped JSON rebuilds.
- `series_sort` is still used by some build-time Liquid/JS sorting paths (for example the works index `seriessort` sort key).

## Runtime Usage By Page

- `series` page grid (`_layouts/series.html`):
  - Uses `assets/data/series_index.json` for ordered works in series.
  - Uses `assets/data/works_index.json` for card text metadata; thumb URLs are derived from `work_id`.
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
3. Regenerate `works-index-json` when work card metadata changes (for example title/year/series fields).

Recommended command:

```bash
python3 ./scripts/catalogue_json_build.py --series-id <series_id> --write
```

This command is the live scoped rebuild path for JSON-led catalogue maintenance.

## Why This Hybrid Exists

- `assets/data/series_index.json` order is the canonical cross-page runtime order.
- Front-matter `series_sort` remains useful as a fast build-time cache for Liquid templates.
- The regeneration contract keeps both aligned.
