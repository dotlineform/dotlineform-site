---
doc_id: data-flow
title: Data Flow
added_date: 2026-03-31
last_updated: 2026-06-01
parent_id: catalogue
---
# Data Flow

This document describes the current runtime data flow for the public catalogue.

It focuses on which generated artifacts each route reads at runtime. It does not try to document every field in those payloads.

For the catalogue artifact contracts themselves, use [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue).

Current public browsing routes covered here:

- `/series/`
- `/series/?series=<series_id>`
- `/series/?mode=moments`
- `/works/`
- `/works/?work=<work_id>`
- `/work-details/?detail=<detail_uid>`
- `/moments/`
- `/moments/<moment_id>/`

The main live rebuild path for these artifacts is the scoped JSON build flow described in [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json).

## Overview

Current generated JSON files involved in this flow:

- `assets/data/series_index.json`
- `assets/data/moments_index.json`
- `assets/data/works_index.json`
- `assets/series/index/<series_id>.json`
- `assets/works/index/<work_id>.json`
- `assets/moments/index/<moment_id>.json`

## 1. Catalogue Index

User-facing step:

- `/series/`
- lists series in `works` mode
- lists moments in `moments` mode

Current JSON used:

- `assets/data/series_index.json`
- `assets/data/moments_index.json`

Template:

- `series/index.md`

How the page uses them:

- `works` mode is built from `series_index.json`
- `moments` mode is built from `moments_index.json`
- selected-series state is restored from `?series=<series_id>` and uses `assets/data/works_index.json` for lightweight work-card metadata
- moment card URLs still come from `site.moments` URLs embedded into the page at build time

This route does not read per-series, per-work, or per-moment JSON records.

## 2. Legacy Series Collection Page

User-facing step:

- `/series/<series_id>/`
- legacy Jekyll collection output
- current first-party navigation uses `/series/?series=<series_id>`
- shows a grid of all works in the series if reached directly
- shows optional series prose below the grid

Current JSON used:

- `assets/data/series_index.json`
- `assets/data/works_index.json`
- `assets/series/index/<series_id>.json`

Template:

- `_layouts/series.html`

How the page uses them:

- `series_index.json` answers membership and ordering
- `works_index.json` answers lightweight work-card metadata without fetching one JSON file per work
- `assets/series/index/<series_id>.json` supplies prose content for the lower content block
- the page does not fetch per-work JSON for the series grid

## 3. Work Shell

User-facing step:

- `/works/`
- `/works/?work=<work_id>`
- shows the work
- shows one grid per detail section

Current JSON used:

- `assets/works/index/<work_id>.json`
- `assets/data/series_index.json`

Template:

- `works/index.md`
- `_layouts/work.html` remains as legacy Jekyll collection output while collections are still generated

What `series_index.json` provides on the work page:

- series context when the work is opened with `?series=<series_id>`
- previous and next work navigation inside that series
- series title used for the inline series link and back-link labeling
- no-context back-link fallback to the work's primary series when no explicit return source is present

The work page is work-local by design. Detail sections, detail links, prose, downloads, and published links all come from the per-work record.

## 4. Detail Shell

User-facing step:

- `/work-details/?detail=<detail_uid>`
- shows a single detail image

Current JSON used:

- `assets/works/index/<work_id>.json`

Template:

- `work-details/index.md`
- `_layouts/work_details.html` remains as legacy Jekyll collection output while collections are still generated

How the page works:

- it derives `work_id` from the `detail_uid` query value or explicit `from_work` context
- it fetches `assets/works/index/<work_id>.json`
- it finds the matching `detail_uid` in that work payload

This route does not use a global detail index.

## 5. Moment Page

User-facing step:

- `/moments/<moment_id>/`
- shows one moment plus its prose body

Current JSON used:

- `assets/moments/index/<moment_id>.json`

Template and runtime:

- `_layouts/moment.html`
- `assets/js/moment.js`

The moment page is moment-local. It does not read `moments_index.json` at runtime.

## Search Boundary

Catalogue search is a separate surface:

- `/catalogue/search/`

It reads:

- `assets/data/search/catalogue/index.json`

Search behavior, ranking, and index structure are documented in the [Search](/docs/?scope=studio&doc=search) section rather than repeated here.

The catalogue artifact families themselves are documented in [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue).

## Current State

The implemented data flow is now:

1. `/series/`
   - uses `assets/data/series_index.json`
   - uses `assets/data/moments_index.json`
   - uses `assets/data/works_index.json` only for selected-series state

2. `/series/?series=<series_id>`
   - uses `assets/data/series_index.json`
   - uses `assets/data/works_index.json`

3. `/works/?work=<work_id>`
   - uses `assets/works/index/<work_id>.json`
   - uses `assets/data/series_index.json` for series context

4. `/work-details/?detail=<detail_uid>`
   - derives `work_id` from the `detail_uid` query value or explicit `from_work` context
   - uses `assets/works/index/<work_id>.json`

5. `/moments/`
   - recovers to `/series/?mode=moments` with a visible fallback link

6. `/moments/<moment_id>/`
   - uses `assets/moments/index/<moment_id>.json`

7. `/catalogue/search/`
   - uses `assets/data/search/catalogue/index.json`
   - derives public catalogue result URLs in the browser from `kind` and `id`
