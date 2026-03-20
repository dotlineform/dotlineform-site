# Data Flow

This document describes the runtime JSON data flow for the main browsing path:

1. `series index`
2. `series page`
3. `work page`
4. `detail page`

It focuses on which JSON files are used by the frontend at each step and what data each file supplies.

## Overview

Current generated JSON files involved in this flow:

- `assets/data/series_index.json`
- `assets/data/works_index.json`
- `assets/works/index/<work_id>.json`

Current direction:

- keep `series_index.json`
- keep `works_index.json`
- keep per-work JSON in `assets/works/index/<work_id>.json`
- remove the obsolete global work-details index

## 1. Series Index

User-facing step:

- `/series/`
- lists all series

Current JSON used:

- [`assets/data/series_index.json`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/data/series_index.json)

Template:

- [`series/index.md`](/Users/dlf/Developer/dotlineform/dotlineform-site/series/index.md)

What this JSON provides:

- full list of series IDs
- series title
- year / year display
- ordered `works` membership for each series
- canonical `primary_work_id` for each series
- sort metadata and other series-level fields

Why it is used:

- the series index is fundamentally a global series listing, so a single global series JSON is the correct source

Replacement for the removed global work-details index:

- none here
- this step does not depend on any global detail index

## 2. Series Page

User-facing step:

- `/series/<series_id>/`
- shows a grid of all works in the series

Current JSON used:

- [`assets/data/series_index.json`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/data/series_index.json)
- [`assets/data/works_index.json`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/data/works_index.json)

Template:

- [`_layouts/series.html`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/series.html)

What `series_index.json` provides:

- the canonical ordered list of work IDs for the series
- series title
- series year / year display

What `works_index.json` provides:

- lightweight work metadata for each work card
- currently mainly title
- the card thumbs are derived by filename convention from `work_id`, not read from JSON

Why both are used:

- `series_index.json` answers membership and ordering
- `works_index.json` answers lightweight work-card metadata without fetching one JSON file per work

Replacement for the removed global work-details index:

- none here
- this step does not depend on any global detail index

## 3. Work Page

User-facing step:

- `/works/<work_id>/`
- shows the work
- shows one grid per detail section

Current JSON used:

- [`assets/works/index/<work_id>.json`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/works/index)
- [`assets/data/series_index.json`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/data/series_index.json)

Template:

- [`_layouts/work.html`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html)

What `assets/works/index/<work_id>.json` provides:

- canonical work metadata used by the page JS
- canonical `series_ids` membership for the work
- `sections[]`
- each section's `project_subfolder`
- each detail record in that work
- detail title
- detail UID
- detail dimensions
- detail-level metadata

What `series_index.json` provides on the work page:

- series context when the work is being viewed from a series
- previous / next work navigation
- series membership ordering
- the primary-series label/link derived from `work.series_ids[0]`

Why this is the right source:

- details belong to a work, so per-work JSON is the natural source for detail sections and detail grids
- this already scales better than using a global details JSON for work-page rendering

Replacement for the removed global work-details index:

- none needed for this step
- the work page already uses per-work JSON and does not depend on any global detail index

## 4. Detail Page

User-facing step:

- `/work_details/<detail_uid>/`
- shows a single detail image

Current JSON used:

- [`assets/works/index/<work_id>.json`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/works/index)

Template:

- [`_layouts/work_details.html`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work_details.html)

What the detail stub front matter provides:

- `work_id`
- `detail_id`
- `detail_uid`
- `title` as fallback text only

What per-work JSON provides:

- canonical detail record
- detail dimensions
- detail title
- section membership
- sibling detail ordering for prev/next navigation
- parent work title

How the page now works:

- it reads `page.work_id` from the stub
- it fetches [`assets/works/index/<work_id>.json`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/works/index)
- it finds the matching `detail_uid` in that work payload

From that work-local payload, the page derives:

- correct detail title
- section ID
- dimensions
- previous / next detail links
- back-link context

## Removed Global Detail Index

Removed artefacts:

- the global work-details index JSON
- `work_details/index.md`

Replacement:

- no replacement is needed
- per-work detail grids on `/works/<work_id>/` are the only detail index UI

## Current State

The implemented data flow is now:

1. `/series/`
   - uses `assets/data/series_index.json`

2. `/series/<series_id>/`
   - uses `assets/data/series_index.json`
   - uses `assets/data/works_index.json`

3. `/works/<work_id>/`
   - uses `assets/works/index/<work_id>.json`
   - uses `assets/data/series_index.json` for series context

4. `/work_details/<detail_uid>/`
   - uses stub front matter for `work_id`
   - uses `assets/works/index/<work_id>.json`

Result:

- detail browsing becomes fully work-local
- very large detail sets scale with the size of one work's JSON, not with one global details index
- a very large work+details set has no runtime impact on unrelated works
