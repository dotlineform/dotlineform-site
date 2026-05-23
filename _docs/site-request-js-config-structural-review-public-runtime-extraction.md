---
doc_id: site-request-js-config-structural-review-public-runtime-extraction
title: Public Runtime Extraction Slice
added_date: 2026-05-10
last_updated: "2026-05-10 17:25"
ui_status: done
parent_id: site-request-js-config-structural-review
sort_order: 5000
viewable: true
---
# Public Runtime Extraction Slice

Status:

- implemented

## Purpose

This child doc tracks the fifth implementation slice from the [JavaScript And Browser Config Structural Review Request](/docs/?scope=studio&doc=site-request-js-config-structural-review).

The goal is to reduce public-route inline JavaScript only where a stable helper boundary exists.
This slice should make work, work-detail, and series route behavior easier to test and cache without changing public URLs, Liquid-rendered route shells, generated catalogue payload schemas, or media URL contracts.

## Problem

Public catalogue routes still split runtime behavior across Liquid templates, route-local inline scripts, and `assets/js/work.js`.

Current mixed responsibilities include:

- public work page payload fetching and metadata refresh
- detail-section rendering and pagination on work pages
- work-detail context hydration from parent work payloads
- series grid rendering and pagination
- public work/series/detail URL shaping
- thumbnail and primary media URL shaping
- hash scrolling and route query preservation
- swipe and keyboard navigation binding

Some of this code must stay close to Liquid because it depends on generated page metadata and page-specific DOM structure.
Other pieces are pure enough to become public runtime helpers.

## Non-Goals

- do not rewrite public routes into a client-side app
- do not change generated JSON schemas for works, work details, series, moments, or indexes
- do not change public route URLs or query parameters
- do not change Liquid-rendered primary media URLs, `srcset` strings, or route shell markup unless an extraction requires a tiny data-attribute handoff
- do not merge public runtime behavior with Studio route helpers unless there is an existing shared browser contract
- do not move code only because it is inline; extract only behavior with a clear reuse, cacheability, or testability benefit

## Current Surface

Primary templates and modules:

- `_layouts/work.html`
- `_layouts/work_details.html`
- `_layouts/series.html`
- `assets/js/work.js`
- `assets/js/swipe-nav.js`

Primary generated data consumed by these routes:

- `assets/data/series_index.json`
- `assets/data/works_index.json`
- per-work JSON payloads under public generated data paths
- per-series JSON payloads under public generated data paths

The exact generated paths and record shapes should be confirmed before implementation.

## Implementation Notes

Added `assets/js/public-catalogue-runtime.js` as the public catalogue helper boundary for behavior that was already shared or duplicated across public work, work-detail, series, and work-navigation scripts.

The helper now owns:

- `fetchJson` with the current `cache: "default"` fetch behavior
- cached per-work payload loading through `getWorkRecord` and the legacy `window.__dlfGetWorkRecord` alias
- base URL trimming and public generated-data URL construction
- work, work-detail, series index, works index, and per-series payload URL shaping
- text trimming, positive-size normalization, numeric parsing, and slug normalization
- thumbnail URL and `srcset` construction for public catalogue grids

The route templates still own:

- work metadata DOM updates and public prose rendering
- work details section rendering, paging, hash scrolling, and section-local swipe binding
- work-detail context hydration, back-link shaping, and detail Prev/Next navigation
- series grid rendering, pagination state, prose rendering, and page URL replacement

`assets/js/work.js` stays focused on public work/work-detail navigation behavior.
It now imports shared fetch, URL, and ID normalization behavior from the helper, while retaining series link visibility, series back-link labels, Prev/Next links, and keyboard navigation locally.

## Target Boundary Questions

This slice should answer:

1. Which inline functions are pure URL, text, media, or payload helpers that can move safely?
2. Which functions are route renderers and should remain inline until a clearer public-route module boundary exists?
3. Should `assets/js/work.js` become the work/work-detail runtime owner, or should a new public catalogue helper module be added?
4. Can work-page detail rendering and work-detail context hydration share a small payload client/cache?
5. Which series-grid helpers are generic public catalogue utilities versus series-route-specific render logic?
6. What browser smoke checks prove public work, work-detail, and series routes still navigate and render correctly?

## Candidate Module Boundaries

Potential first helper:

- `assets/js/public-catalogue-runtime.js`

Target ownership:

- `fetchJson` with the current cache mode
- base-url-safe asset and route URL shaping
- id normalization and list normalization
- shared catalogue query-string helpers
- thumbnail URL and `srcset` helpers where the template already passes all required config through data attributes

Potential route owner:

- `assets/js/work.js`

Target ownership:

- public work and work-detail navigation behavior that already runs on both routes
- series navigation context
- keyboard navigation
- swipe-zone bootstrap where it is shared by work and work-detail pages

Keep inline or route-local for now:

- work-page detail group DOM rendering until a cleaner renderer contract is defined
- series grid rendering until the route data shape and pagination contract are pinned
- page-specific DOM node lookup and Liquid-provided data-attribute extraction
- any behavior that depends on one route's exact markup structure

## Recommended First Slice

Start with an inventory and helper extraction, not a renderer move.

Scope:

- inventory inline functions in `_layouts/work.html`, `_layouts/work_details.html`, and `_layouts/series.html`
- identify duplicated or near-duplicated helpers such as URL joining, JSON fetching, id normalization, query preservation, and media URL construction
- add a small public catalogue runtime helper only if at least two routes can use it immediately
- update route inline scripts to call the helper while keeping DOM rendering and page state local
- keep `assets/js/work.js` focused on public work/work-detail navigation rather than generic route rendering

Avoid in the first implementation:

- moving the entire details renderer
- moving the entire series grid renderer
- changing public link structure or query parameters
- changing generated payload builders

## Acceptance Checks

- public work pages still render primary media, details, pager controls, series back link, and Prev/Next navigation
- public work-detail pages still hydrate title, media dimensions, parent-work context, and detail Prev/Next navigation
- public series pages still render grid items, pagination, prose, and work links with preserved `series` and `series_page` query context
- `assets/js/work.js` keeps keyboard navigation behavior intact
- generated payload schemas and public route URLs are unchanged
- helper extraction has immediate callers from work, work-detail, series, and `assets/js/work.js`

## Targeted Verification

For an implementation slice, use focused checks:

- `node --check` for changed public JavaScript files
- Jekyll build to a separate destination if `bin/dev-studio` or `jekyll serve` is running
- Playwright smoke against representative static routes:
  - one work page with details and series navigation
  - one work-detail page reached with parent work context
  - one series page with enough works to exercise pagination when fixture data allows
- verify no page errors or failed local JS/data requests
- verify current query parameters survive navigation where expected

Broader checks are only needed if the implementation changes generated data paths, route templates, or public navigation contracts.

Verification run for this slice:

- `node --check assets/js/public-catalogue-runtime.js`
- `node --check assets/js/work.js`
- `./scripts/build_docs.rb --scope studio --write`
- `./scripts/build_search.rb --scope studio --write`
- Jekyll build to a separate destination because local Studio/Jekyll services may already be running
- static Playwright smoke for a representative work page, work-detail page, and series page

## Benefits And Risks

Benefits:

- reduces repeated public-route browser helpers without creating a public app framework
- makes URL/media/query behavior easier to review and smoke-test
- keeps route-specific rendering close to the templates until a stronger renderer boundary appears

Risks:

- extracting renderer code too early could make Liquid/data-attribute contracts harder to follow
- changing query preservation would affect public back links and series navigation
- media URL helper mistakes would be visible on public artwork pages, so the first slice should keep image URL contracts pinned by browser checks
