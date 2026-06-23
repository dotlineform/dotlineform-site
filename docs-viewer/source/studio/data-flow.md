---
doc_id: data-flow
title: Data Flow
added_date: 2026-03-31
last_updated: 2026-06-23
parent_id: studio
viewable: true
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
- `/moments/?doc=<moment_doc_id>`

The main live rebuild path for these artifacts is the scoped JSON build flow described in [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json).

## Overview

Current generated JSON files involved in this flow:

- `site/assets/data/series_index.json`
- `site/assets/data/moments_index.json`
- `site/assets/data/works_index.json`
- `site/assets/series/index/<series_id>.json`
- `site/assets/works/index/<work_id>.json`
- `site/assets/data/docs/scopes/moments/index-tree.json`
- `site/assets/data/docs/scopes/moments/by-id/<moment_doc_id>.json`

## 1. Catalogue Index

User-facing step:

- `/series/`
- lists series in `works` mode
- lists moments in `moments` mode

Current JSON used:

- `site/assets/data/series_index.json`
- `site/assets/data/moments_index.json`

Template:

- `series/index.md`

How the page uses them:

- `works` mode is built from `series_index.json`
- `moments` mode is built from `moments_index.json`
- selected-series state is restored from `?series=<series_id>` and uses `site/assets/data/works_index.json` for lightweight work-card metadata
- moment card URLs point to the Docs Viewer moments route as `/moments/?doc=<moment_doc_id>`

This route does not read per-series, per-work, or per-moment JSON records.

## 2. Selected Series State

User-facing step:

- `/series/?series=<series_id>`
- shows a grid of all works in the series if reached directly
- shows optional series prose below the grid

Current JSON used:

- `site/assets/data/series_index.json`
- `site/assets/data/works_index.json`
- `site/assets/series/index/<series_id>.json`

Template:

- `_layouts/series.html`

How the page uses them:

- `series_index.json` answers membership and ordering
- `works_index.json` answers lightweight work-card metadata without fetching one JSON file per work
- `site/assets/series/index/<series_id>.json` supplies prose content for the lower content block
- the page does not fetch per-work JSON for the series grid

## 3. Work Shell

User-facing step:

- `/works/`
- `/works/?work=<work_id>`
- shows the work
- shows one grid per detail section

Current JSON used:

- `site/assets/works/index/<work_id>.json`
- `site/assets/data/series_index.json`

Template:

- `works/index.md`

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

- `site/assets/works/index/<work_id>.json`

Template:

- `work-details/index.md`

How the page works:

- it derives `work_id` from the `detail_uid` query value or explicit `from_work` context
- it fetches `site/assets/works/index/<work_id>.json`
- it finds the matching `detail_uid` in that work payload

This route does not use a global detail index.

## 5. Moment Page

User-facing step:

- `/moments/`
- `/moments/?doc=<moment_doc_id>`
- shows the moments Docs Viewer shell or one selected moment document

Current JSON used:

- `site/assets/data/docs/scopes/moments/index-tree.json`
- `site/assets/data/docs/scopes/moments/by-id/<moment_doc_id>.json`
- `site/assets/data/search/moments/index.json`

Template and runtime:

- `site/moments/index.html`
- `site/docs-viewer/runtime/js/public/docs-viewer-public.js`

The selected moment view is now a public Docs Viewer scope route.
The route parser uses the shared Docs Viewer `doc` query parameter, and `/moments/` without a selected document renders the moments scope index.

## Search Boundary

Catalogue search is a separate surface:

- `/catalogue/search/`

It reads:

- `site/assets/data/search/catalogue/index.json`

Search behavior, ranking, and index structure are documented in the [Search](/docs/?scope=studio&doc=search) section rather than repeated here.

The catalogue artifact families themselves are documented in [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue).

## Current State

The implemented data flow is now:

1. `/series/`
   - uses `site/assets/data/series_index.json`
   - uses `site/assets/data/moments_index.json`
   - uses `site/assets/data/works_index.json` only for selected-series state

2. `/series/?series=<series_id>`
   - uses `site/assets/data/series_index.json`
   - uses `site/assets/data/works_index.json`

3. `/works/?work=<work_id>`
   - uses `site/assets/works/index/<work_id>.json`
   - uses `site/assets/data/series_index.json` for series context

4. `/work-details/?detail=<detail_uid>`
   - derives `work_id` from the `detail_uid` query value or explicit `from_work` context
   - uses `site/assets/works/index/<work_id>.json`

5. `/moments/`
   - uses `site/assets/data/docs/scopes/moments/index-tree.json`
   - renders the moments Docs Viewer index

6. `/moments/?doc=<moment_doc_id>`
   - uses `site/assets/data/docs/scopes/moments/by-id/<moment_doc_id>.json`

7. `/catalogue/search/`
   - uses `site/assets/data/search/catalogue/index.json`
   - derives public catalogue result URLs in the browser from `kind` and `id`
