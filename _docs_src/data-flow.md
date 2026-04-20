---
doc_id: data-flow
title: "Data Flow"
last_updated: 2026-03-31
parent_id: architecture
sort_order: 10
---

# Data Flow

This document describes the current runtime data flow for the public catalogue.

It focuses on which generated artifacts each route reads at runtime. It does not try to document every field in those payloads.

For the catalogue artifact contracts themselves, use [Data Models: Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue).

Current public browsing routes covered here:

- `/series/`
- `/series/<series_id>/`
- `/works/<work_id>/`
- `/work_details/<detail_uid>/`
- `/moments/<moment_id>/`

The main live rebuild path for these artifacts is the scoped JSON build flow described in [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json) and [New Catalogue Pipeline](/docs/?scope=studio&doc=new-pipeline).

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
- moment card URLs still come from `site.moments` URLs embedded into the page at build time

This route does not read per-series, per-work, or per-moment JSON records.

## 2. Series Page

User-facing step:

- `/series/<series_id>/`
- shows a grid of all works in the series
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

## 3. Work Page

User-facing step:

- `/works/<work_id>/`
- shows the work
- shows one grid per detail section

Current JSON used:

- `assets/works/index/<work_id>.json`
- `assets/data/series_index.json`

Template:

- `_layouts/work.html`

What `series_index.json` provides on the work page:

- series context when the work is opened with `?series=<series_id>`
- previous and next work navigation inside that series
- series title used for the inline series link and back-link labeling

The work page is work-local by design. Detail sections, detail links, prose, downloads, and published links all come from the per-work record.

## 4. Detail Page

User-facing step:

- `/work_details/<detail_uid>/`
- shows a single detail image

Current JSON used:

- `assets/works/index/<work_id>.json`

Template:

- `_layouts/work_details.html`

How the page works:

- it reads `page.work_id` from the stub
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

- `/search/?scope=catalogue`

It reads:

- `assets/data/search/catalogue/index.json`

Search behavior, ranking, and index structure are documented in the [Search](/docs/?scope=studio&doc=search) section rather than repeated here.

The catalogue artifact families themselves are documented in [Data Models: Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue).

## Current State

The implemented data flow is now:

1. `/series/`
   - uses `assets/data/series_index.json`
   - uses `assets/data/moments_index.json`

2. `/series/<series_id>/`
   - uses `assets/data/series_index.json`
   - uses `assets/data/works_index.json`
   - uses `assets/series/index/<series_id>.json`

3. `/works/<work_id>/`
   - uses `assets/works/index/<work_id>.json`
   - uses `assets/data/series_index.json` for series context

4. `/work_details/<detail_uid>/`
   - uses stub front matter for `work_id`
   - uses `assets/works/index/<work_id>.json`

5. `/moments/<moment_id>/`
   - uses `assets/moments/index/<moment_id>.json`

6. `/search/?scope=catalogue`
   - uses `assets/data/search/catalogue/index.json`
