---
doc_id: data-models-catalogue
title: Catalogue Scope
last_updated: 2026-04-01
parent_id: data-models
sort_order: 20
---

# Catalogue Scope

This document covers the current data model for the public catalogue: works, series, moments, detail pages, and catalogue search.

## Scope Boundary

Current checked-in catalogue model families:

- route stubs:
  - `_works/*.md`
  - `_series/*.md`
  - `_work_details/*.md`
  - `_moments/*.md`
- shared indexes:
  - `assets/data/series_index.json`
  - `assets/data/works_index.json`
  - `assets/data/moments_index.json`
- per-record payloads:
  - `assets/series/index/<series_id>.json`
  - `assets/works/index/<work_id>.json`
  - `assets/moments/index/<moment_id>.json`
- scope search:
  - `assets/data/search/catalogue/index.json`

Primary writers:

- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages) for route stubs, shared indexes, and per-record catalogue payloads
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline) for `assets/data/search/catalogue/index.json`

Primary validator:

- [Audit Site Consistency](/docs/?scope=studio&doc=scripts-audit-site-consistency)

## Why The Model Is Split This Way

The catalogue model is intentionally split between minimal route stubs and generated JSON.

Why:

- Jekyll still needs stable route pages for `/works/`, `/series/`, `/work_details/`, and `/moments/`
- list pages need lightweight indexes, not full per-item prose and detail payloads
- work and moment pages need richer page-local data such as `content_html`, dimensions, and detail sections
- detail pages are cheaper to resolve through the owning work record than through a separate global detail index

In practice this means the route stub gives the page an ID and fallback metadata, while the JSON record gives the page its canonical runtime content.

## Route Stubs

### `_works/*.md`

Purpose:

- provide the public work route
- carry route identity and a small fallback set of metadata

Design:

- intentionally minimal
- the canonical detail/prose payload lives in `assets/works/index/<work_id>.json`

### `_series/*.md`

Purpose:

- provide the public series route
- carry route identity and title fallback

Design:

- intentionally minimal
- series prose and canonical series metadata live in `assets/series/index/<series_id>.json`

### `_work_details/*.md`

Purpose:

- provide one public route per detail image
- identify the owning work and detail UID

Design:

- detail pages do not own a standalone detail JSON artifact
- the page resolves through the parent work record in `assets/works/index/<work_id>.json`

This keeps sibling ordering, section grouping, and detail metadata consistent with the owning work payload.

### `_moments/*.md`

Purpose:

- provide the public moment route
- carry route identity and title fallback

Design:

- canonical moment metadata and prose live in `assets/moments/index/<moment_id>.json`
- the Markdown stub exists mainly for route generation and fallback text

## Shared Catalogue Indexes

### `assets/data/series_index.json`

Purpose:

- canonical lookup map for series-level list and membership data

Current content families:

- series identity and publishing state
- list-card display metadata
- ordered work membership
- `primary_work_id`
- sort metadata used elsewhere in the catalogue and Studio

Current consumers:

- `/series/` in works mode
- `/series/<series_id>/`
- `/works/<work_id>/` when series context is needed for prev/next navigation
- Studio pages that need canonical series membership context

Why it exists separately:

- series list and membership data is needed in multiple places
- pages should not fetch every per-series record just to build a grid or navigation context

### `assets/data/works_index.json`

Purpose:

- lightweight lookup map for works used by grids, titles, and cross-scope references

Current content families:

- work identity
- title and year display
- series membership

Current consumers:

- `/series/<series_id>/` for work cards
- Studio pages that need fast work lookup without loading every work record

Why it stays lightweight:

- the work page’s full detail/prose payload is much larger
- series grids need fast bulk access to many works at once

### `assets/data/moments_index.json`

Purpose:

- lightweight lookup map for moments in the merged catalogue

Current content families:

- moment identity
- title and date display
- thumbnail indirection via `thumb_id`

Current consumers:

- `/series/` in moments mode

Why it is separate from the per-moment record:

- the merged catalogue only needs card metadata
- loading prose and image metadata for every moment card would be unnecessary

## Per-Record Catalogue Payloads

### `assets/series/index/<series_id>.json`

Purpose:

- page-local payload for one series page

Current content families:

- canonical series metadata
- rendered prose as `content_html`

Current site mapping:

- `/series/<series_id>/`

Why it exists:

- the page needs prose and a second copy of the series record, but the shared index should stay lightweight

### `assets/works/index/<work_id>.json`

Purpose:

- page-local payload for one work and its detail structure

Current content families:

- canonical work metadata
- rendered prose as optional `content_html`
- `sections[]`
- ordered detail records grouped by section

Current site mapping:

- `/works/<work_id>/`
- `/work_details/<detail_uid>/`

Why it is the most important catalogue record:

- the work page needs richer metadata than the index provides
- the detail page derives its canonical title, ordering, and back-link context from the parent work record
- avoiding a separate global detail index reduces duplication and keeps detail ordering local to the work that owns it
- work prose is optional, so the record still exists even when no source Markdown is mapped for that work

### `assets/moments/index/<moment_id>.json`

Purpose:

- page-local payload for one moment

Current content families:

- canonical moment metadata
- rendered prose as `content_html`
- image list and dimensions

Current site mapping:

- `/moments/<moment_id>/`

Why it exists:

- the moment page needs prose and image metadata, but the merged catalogue list does not

## Catalogue Search Model

### `assets/data/search/catalogue/index.json`

Purpose:

- search-owned flat index for `works`, `series`, and `moments`

Current content families:

- one `entries[]` array across all three catalogue kinds
- per-entry display metadata and route href
- normalized search terms and combined `search_text`
- selected structured fields such as series relationships, work medium type from per-work JSON, and Studio-derived tag data where available
- work-only search enrichment terms such as `medium_caption` folded into derived search fields from per-work JSON

Current site mapping:

- `/search/?scope=catalogue`

Why it is separate from the main indexes:

- search needs a flattened, text-oriented shape
- list/runtime pages need lookup-oriented shapes
- keeping those concerns separate avoids bloating the runtime indexes used by ordinary pages

## Dependencies And Enforcement

Important dependencies:

- `_work_details/*.md` depends on the parent work record for canonical detail data
- `works_index.json` depends on valid `series_ids` membership
- `series_index.json` depends on ordered work membership and stable `sort_fields`
- catalogue search depends on series/work/moment data plus Studio tag data from:
  - `assets/studio/data/tag_assignments.json`
  - `assets/studio/data/tag_registry.json`

Current enforcement visible in code:

- the generator writes and hashes the shared catalogue indexes and per-record catalogue payloads
- the search builder writes the catalogue search artifact from those generated JSON families plus Studio tag data
- the generator keeps `_moments`, `_series`, and `_works` stubs minimal and current
- the audit script checks:
  - `detail_uid` and `work_id` consistency
  - `series_index` membership integrity
  - `works_index` `series_ids`
  - JSON header and root-shape expectations
  - `tag_assignments` references back into series/work membership

## Performance Notes

The catalogue model is optimized for the current static-site runtime:

- `/series/` reads only shared indexes
- `/series/<series_id>/` reads one per-series record, not one record per work
- `/works/<work_id>/` reads one work-local payload that already contains all detail sections
- `/work_details/<detail_uid>/` reuses the work-local payload instead of requiring a second fetch family
- `/search/` reads one search-optimized catalogue artifact rather than scanning several unrelated indexes in the browser

This is the main reason the catalogue model looks more normalized than a single-page-site JSON dump.

## Practical Update Rule

If a change affects:

- list/grid cards or cross-page lookup
  update the relevant shared index model here
- page-local prose, detail sections, or page hydration
  update the relevant per-record model here
- search-visible structured fields
  update this doc and the relevant search docs together
