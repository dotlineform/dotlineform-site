---
doc_id: site-request-js-config-structural-review-search-performance-instrumentation
title: Search Performance Instrumentation Slice
added_date: 2026-05-10
last_updated: "2026-05-10 17:35"
ui_status: done
parent_id: site-request-js-config-structural-review
sort_order: 60
hidden: false
---
# Search Performance Instrumentation Slice

Status:

- implemented

## Purpose

This child doc tracks the sixth implementation slice from the [JavaScript And Browser Config Structural Review Request](/docs/?scope=studio&doc=site-request-js-config-structural-review).

The goal is to measure public search runtime cost before deciding whether the search page needs workers, lazy loading, index slimming, or a different execution model.
This slice should make search performance visible without changing search results, ranking semantics, generated search index schemas, public URLs, or the current search page workflow.

## Problem

The public search runtime has a useful first split between:

- `assets/js/search/search-page.js`
- `assets/js/search/search-policy.js`
- generated search indexes under `assets/data/search/<scope>/index.json`
- search policy under `assets/data/search/policy.json`

The remaining performance question is not yet pinned by measurements.
Aggregate search can load multiple enabled scopes and scan normalized entries on each render.
The catalogue search index is currently the largest payload, but the practical browser impact depends on actual payload size, load time, normalization time, search time, render time, and user-device constraints.

Without instrumentation, worker extraction or index reshaping would be speculative.

## Non-Goals

- do not change result ranking, matching, highlighting, grouping, or display copy
- do not change generated search index schemas
- do not move search matching into a Web Worker in this slice
- do not add a search framework or build step
- do not persist analytics or send performance data off-device
- do not expose debug instrumentation in normal public browsing unless explicitly enabled

## Current Surface

Primary runtime files:

- `assets/js/search/search-page.js`
- `assets/js/search/search-policy.js`

Primary generated/config data:

- `assets/data/search/policy.json`
- `assets/data/search/catalogue/index.json`
- `assets/data/search/studio/index.json`
- `assets/data/search/library/index.json`
- `assets/data/search/analysis/index.json`

Primary public route:

- `/search/`

The exact enabled scopes, payload sizes, and current render pipeline should be confirmed before implementation.

## Target Boundary Questions

This slice should answer:

1. Which search runtime phases can be measured cleanly without changing behavior?
2. Should instrumentation be enabled by query flag, config flag, local-storage flag, or a combination?
3. What is the smallest useful report: scope payload bytes, load duration, entry count, normalization duration, query duration, render duration, and first-result duration?
4. Where should instrumentation output appear: console only, a hidden debug panel, or an existing status area when enabled?
5. Which thresholds would justify a later worker or lazy-loading slice?
6. What smoke checks prove instrumentation is off by default and does not change visible results when enabled?

## Candidate Module Boundary

Potential helper:

- `assets/js/search/search-performance.js`

Target ownership:

- opt-in instrumentation state
- timing helpers using `performance.now()`
- optional byte-size estimation for fetched payloads when available
- compact per-scope and per-query measurement records
- console or debug-panel reporting when instrumentation is enabled

Keep in `search-page.js`:

- route bootstrapping
- query input and URL state
- search result rendering
- existing scope loading orchestration unless a later slice changes it

Keep in `search-policy.js`:

- policy parsing and scope eligibility decisions
- defaults for public search behavior

## Implementation

Implemented as measurement only.

Changed files:

- `assets/js/search/search-performance.js`
- `assets/js/search/search-page.js`
- `search/index.md`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`

The new helper owns:

- opt-in instrumentation state
- timing helpers based on `performance.now()`
- static/docs-management search payload byte estimates when instrumentation is enabled
- per-scope load, parse, normalization, raw-entry, and normalized-entry records
- recent query evaluation, sort, render, total-duration, result-count, and visible-count records
- compact debug-panel formatting with no full payload dumps

`assets/js/search/search-page.js` still owns:

- route bootstrapping
- search policy and config loading
- scope loading orchestration
- query matching, scoring, sorting, and rendering
- docs-management fallback behavior for local docs-domain scope reads

Instrumentation is enabled only when explicitly requested:

- `?searchPerf=1` or `?debug=search-performance` shows the debug panel
- `?searchPerf=console` writes compact snapshots to the console
- local storage key `dlf.search.performance` can be set to `1`, `panel`, or `console` for local repeat testing

Normal public browsing leaves the panel hidden and does not switch the static JSON loader onto the byte-counting fetch path.
No analytics are sent and no search payload content is logged.

## Acceptance Checks

- search instrumentation is disabled by default
- enabling instrumentation does not change result count, order, route URL behavior, or visible search copy except for the explicit debug output
- aggregate search still loads enabled scopes according to existing policy
- a representative catalogue search reports payload/load/query/render timing
- instrumentation handles failed scope loads without hiding the existing failure behavior
- any debug panel or console output avoids local paths, credentials, or full search payload dumps

## Targeted Verification

For an implementation slice, use focused checks:

- `node --check` for changed search JavaScript files
- targeted browser smoke for `/search/` with instrumentation disabled
- targeted browser smoke for `/search/` with instrumentation enabled
- compare representative result counts/order with and without instrumentation
- verify no page errors or failed local JS/data requests
- rebuild Studio docs payloads and Studio docs search after updating this doc

Broader checks are only needed if the implementation changes generated search schemas, search ranking, search policy parsing, or public search route behavior.

## Follow-Up Thresholds

Use the collected timings to justify later slices rather than guessing:

- worker extraction becomes worth revisiting if query evaluation or sort time is consistently visible on representative devices
- lazy or staged aggregate loading becomes worth revisiting if aggregate scope load time dominates the first usable page state
- index slimming becomes worth revisiting if catalogue payload bytes or normalization time dominate the report
- docs-management/static fallback behavior should stay unchanged unless failed-attempt counts hide a real local-development issue

This slice does not set hard budgets yet because the first goal is local measurement coverage.

## Initial Local Smoke Observation

Against a static Jekyll build on `2026-05-10`, a representative `/search/?scope=catalogue&searchPerf=1` query for `body` reported:

- catalogue payload: `1679324` bytes
- raw/normalized entries: `2135/2135`
- static payload load: about `10ms`
- JSON parse: about `6ms`
- normalization: about `13ms`
- query total: about `8ms`

An aggregate `/search/?searchPerf=1` query for `search` loaded catalogue plus Library, Studio, and Analysis scopes and reported `2368` total normalized entries with a query total of about `7ms`.

These local measurements do not justify worker extraction by themselves.
Keep collecting measurements on lower-powered devices or after search payload growth before choosing workers, lazy aggregate loading, or index slimming.

## Benefits And Risks

Benefits:

- makes future search performance work measurement-led
- gives a lightweight way to compare catalogue, Studio, Library, and Analysis search cost
- keeps the current simple search architecture until data shows a real need to split it

Risks:

- instrumentation can become noisy if it writes too much to the UI or console
- byte-size and duration measurements are approximate in static/local builds
- adding debug output carelessly could expose full query payloads or implementation details that do not belong in normal public browsing
