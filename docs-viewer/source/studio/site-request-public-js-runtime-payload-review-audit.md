---
doc_id: site-request-public-js-runtime-payload-review-audit
title: Public JS Runtime and Payload Static Audit
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-js-runtime-payload-review
viewable: true
---
# Public JS Runtime and Payload Static Audit

Status:

- done

## Scope

This is the first static audit for [Public JavaScript Runtime and Payload Review Request](/docs/?scope=studio&doc=site-request-public-js-runtime-payload-review).

It reviews tracked `site/` route HTML, public JavaScript assets, and public JSON payload sizes.
It does not include a browser-observed waterfall, console run, or route interaction smoke.
Those heavier checks should happen after review of this structural pass.

## Route Script Inventory

All public HTML routes currently keep one inline script in `<head>` for pre-paint theme selection.
That inline script is the only inline JavaScript found in the representative public route files.

| Route | Public route scripts |
| --- | --- |
| `/series/` and `/series/?mode=moments` | `public-catalogue-runtime.js`, `series-index.js`, `site-nav.js`, `theme-toggle.js` |
| `/recent/` | `public-catalogue-runtime.js`, `recent-index.js`, `site-nav.js`, `theme-toggle.js` |
| `/works/` and `/works/?work=...` | `public-catalogue-runtime.js`, `work-page.js`, `work.js`, `works-index.js`, `site-nav.js`, `theme-toggle.js` |
| `/work-details/?detail=...` | `swipe-nav.js`, `public-catalogue-runtime.js`, `work-detail-page.js`, `work.js`, `site-nav.js`, `theme-toggle.js` |
| `/moments/?moment=...` | `public-catalogue-runtime.js`, `moment.js`, `site-nav.js`, `theme-toggle.js` |
| `/catalogue/search/` | module `catalogue-search.js`, static import `search/catalogue-search-runtime.js`, dynamic import `search/search-policy.js`, optional dynamic import `search/search-performance.js`, plus `site-nav.js`, `theme-toggle.js` |
| `/library/` and `/analysis/` | module `/docs-viewer/runtime/js/public/docs-viewer-public.js`, shared Docs Viewer public runtime graph, `site-nav.js`, `theme-toggle.js` |

Non-catalogue routes such as `/`, `/about/`, and `/404.html` load only `site-nav.js` and `theme-toggle.js` after the inline theme bootstrap.

## Script Sizes

Raw and gzip sizes from checked-in files:

| File | Raw bytes | Gzip bytes | Notes |
| --- | ---: | ---: | --- |
| `site/assets/js/series-index.js` | 29,049 | 5,979 | largest catalogue route script |
| `site/assets/js/catalogue-search.js` | 16,839 | 4,268 | module search page coordinator |
| `site/assets/js/works-index.js` | 15,487 | 3,846 | works list route behavior |
| `site/assets/js/work-page.js` | 11,875 | 3,088 | selected work route behavior |
| `site/assets/js/search/catalogue-search-runtime.js` | 11,532 | 3,011 | search projection/scoring/render support |
| `site/assets/js/public-catalogue-runtime.js` | 9,729 | 2,434 | shared URL/payload/media helpers |
| `site/assets/js/moment.js` | 9,837 | 2,618 | moment route behavior |
| `site/assets/js/work-detail-page.js` | 8,363 | 2,135 | work-detail route behavior |
| `site/assets/js/search/search-performance.js` | 7,647 | 2,300 | optional instrumentation |
| `site/assets/js/search/search-policy.js` | 6,721 | 1,899 | search policy loader/defaults |
| `site/assets/js/swipe-nav.js` | 6,269 | 1,639 | work-detail swipe navigation |
| `site/assets/js/work.js` | 5,635 | 1,767 | work navigation plus keyboard navigation |
| `site/assets/js/recent-index.js` | 6,326 | 1,876 | recent route behavior |
| `site/assets/js/site-nav.js` | 1,556 | 501 | currently no-op on current shells |
| `site/assets/js/theme-toggle.js` | 1,331 | 525 | global theme toggle |

Estimated route JS payloads before browser cache:

| Route | Raw bytes | Gzip bytes | Notes |
| --- | ---: | ---: | --- |
| `/series/` | 41,665 | 9,439 | includes both works and moments index behavior |
| `/works/` | 45,613 | 12,161 | loads selected-work scripts even for list mode |
| `/work-details/` | 32,883 | 9,001 | `work.js` mostly supplies keyboard navigation here |
| `/catalogue/search/` initial modules | 31,258 | 8,305 | excludes dynamic policy/performance modules and JSON index |

Docs Viewer public routes are different: `docs-viewer-public.js` is tiny, but it imports the shared Docs Viewer public runtime graph.
That graph is already covered by the Docs Viewer runtime boundary docs and should be reviewed as its own public-runtime payload pass if performance budgets become enforced.

## Payload Sizes

Largest public JSON payloads:

| Payload | Raw bytes | Gzip bytes | Notes |
| --- | ---: | ---: | --- |
| `site/assets/data/search/catalogue/index.json` | 1,500,946 | 75,736 | largest public payload by a wide margin |
| `site/assets/data/works_index.json` | 346,425 | 22,206 | broad works listing payload |
| `site/assets/data/series_index.json` | 85,668 | 9,995 | series and series-work membership data |
| `site/assets/data/search/library/index.json` | 9,489 | 1,542 | small docs search payload |
| `site/assets/data/moments_index.json` | 9,185 | 1,683 | small moment index |
| `site/assets/data/recent_index.json` | 3,819 | 753 | small recent index |
| Library by-id docs payloads | 161-9,937 | 148-3,297 | fetched per selected doc |
| Analysis docs payloads | 293-600 | 202-294 | very small current scope |

The catalogue search index is the obvious payload-size outlier.
It is compressed reasonably well, but it still creates a large parse/normalization workload because the browser receives one monolithic JSON index.

## Static Fetch Map

Static code inspection shows these route-level data loads:

| Route | Static fetch pattern |
| --- | --- |
| `/series/` | always fetches `series_index.json` and `moments_index.json`; fetches `works_index.json` only when a specific `series` query is selected |
| `/series/?mode=moments` | still fetches `series_index.json` as well as `moments_index.json` |
| `/recent/` | fetches `recent_index.json` and `series_index.json` |
| `/works/` | `works-index.js` fetches `works_index.json` and `series_index.json`; `work.js` also fetches `series_index.json` because the hidden selected-work nav exists in the shared shell |
| `/works/?work=...` | `work-page.js` fetches one work payload; `work.js` fetches `series_index.json`; `works-index.js` downloads but exits before fetching list payloads |
| `/work-details/?detail=...` | `work-detail-page.js` fetches the related work payload when it needs work context |
| `/moments/?moment=...` | fetches one moment payload; `/moments/` falls back to `moments_index.json` for a listing |
| `/catalogue/search/` | fetches `search/policy.json`, then the monolithic `search/catalogue/index.json`; performance instrumentation is optional |
| `/library/` and `/analysis/` | fetch public Docs Viewer route config, public Docs Viewer config/UI text, index tree, recently-added/search payloads, and selected by-id docs as needed |

## Findings

### 1. `site-nav.js` Is Globally Loaded But Currently No-Ops

Every tracked public route loads `site/assets/js/site-nav.js`, but current route shells do not render `[data-nav-more]`.
The script returns immediately on all scanned routes.

This is small, but it is a clear route-loading mismatch.
Either the nav-more control should return, or the script should stop loading globally.

### 2. `/works/` Mixes Index And Selected-Work Runtime

`site/works/index.html` is a dual-purpose shell for the works index and selected work detail state.
It always downloads:

- `work-page.js`
- `work.js`
- `works-index.js`

The scripts then decide which branch to run from query state.
For `/works/?work=...`, `works-index.js` exits early after download.
For `/works/`, `work-page.js` exits early, but `work.js` still fetches `series_index.json` because hidden selected-work navigation markup exists in the shell.
`works-index.js` also fetches `series_index.json`, so the index path has duplicated series-index fetch intent.

This is the strongest obvious route-boundary issue in the catalogue runtime.

### 3. `work.js` Has Mixed Responsibilities

`work.js` owns at least two different concerns:

- series/back-link navigation for selected work pages
- keyboard navigation for work and work-detail pages

That is why `/work-details/` loads the whole file even though the first work-navigation block is not useful there.
Splitting keyboard navigation from work-series metadata projection would make route loading easier to reason about.

### 4. Public Search Still Carries Studio Naming

The public catalogue search route uses `studioSearch*` IDs/classes in `site/catalogue/search/index.html`, `catalogue-search.js`, and `search/catalogue-search-runtime.js`.

This does not appear to be a runtime bug, but it is a file-organization smell.
It makes the route look like a Studio surface even though it is public-site runtime.

### 5. Route Scripts Duplicate Small Helpers Instead Of Using One Boundary Consistently

Several route scripts define local helper variants even though `public-catalogue-runtime.js` already exposes related helpers:

- `fetchJson` appears in `public-catalogue-runtime.js`, `series-index.js`, `recent-index.js`, and `works-index.js`.
- text normalization appears in `public-catalogue-runtime.js`, `recent-index.js`, `works-index.js`, and `swipe-nav.js`.
- dataset JSON parsing for image widths/sizes is repeated in `series-index.js`, `recent-index.js`, `work-page.js`, `work-detail-page.js`, and `moment.js`.
- route/query parsing appears both in `public-catalogue-runtime.js` and directly in route scripts.

Not all of this deserves abstraction.
The useful boundary question is whether `public-catalogue-runtime.js` should become the single owner of public route/path/payload helpers and small dataset parsers, or whether route scripts should stay self-contained.

### 6. `series-index.js` Is The Largest Route Script And Owns Several Behaviors

`series-index.js` owns list/grid view, works/moments mode, sorting, paging, localStorage state migration, thumbnail rendering, and route-state updates.
That explains its size, but it also makes it the main maintainability candidate after the `/works/` split.

The first refactor should not automatically split it.
The clearer next step is to decide which of those behaviors are route-specific and which belong in a shared public catalogue helper.

### 7. Catalogue Search Payload Is The Dominant Payload Issue

`site/assets/data/search/catalogue/index.json` is about 1.5 MB raw and 75 KB gzip.
No other current public JSON payload is close.

Before changing search runtime code, inspect the generated search index fields and determine whether all fields are needed for first meaningful interaction.
Potential follow-ups include field trimming, per-kind split indexes, prefix/lazy segments, or deferred normalization.

### 8. Stale Builder/Jekyll Language Remains In Public Runtime Code Comments

`site/assets/js/work.js` still says parameters are passed from Jekyll.
That is now wrong; values come from tracked `site/` route HTML data attributes.

This is minor, but it is exactly the kind of historical context drift this review should clean up.

## Recommended First Implementation Slices

1. Remove or retarget `site-nav.js` loading.
   If current static route shells have no nav-more control, stop loading it globally.

2. Split `/works/` route runtime by mode.
   Avoid downloading `works-index.js` on selected-work routes and avoid selected-work helpers/fetches on index routes.
   This can be done without changing URLs by using a small route bootstrap that chooses which script to load.

3. Split `work.js` into focused owners.
   Keep keyboard navigation separate from selected-work series/back-link projection.

4. Rename public catalogue search DOM/CSS/JS selectors away from `studioSearch*`.
   Treat this as a public route ownership cleanup, not a behavior change.

5. Consolidate only proven duplicate helpers.
   Start with `fetchJson`, dataset positive-size parsing, and URL/query helpers.
   Avoid turning `public-catalogue-runtime.js` into a broad utility dump.

6. Audit catalogue search index fields before changing search UI behavior.
   The payload size issue is larger than any single route script.

## Decisions Needed Before Refactor

- Should public catalogue route scripts remain classic scripts, or should new route bootstrap code use ES modules?
- Is a small route bootstrap acceptable for `/works/`, or should the route remain static-script-only with early exits?
- Should `public-catalogue-runtime.js` remain a global classic-script object, or should future shared helpers be ES modules?
- Is `site-nav.js` retired with nav-more, or is nav-more expected to return?
- Should catalogue search selector renaming be included in this request, or tracked as a separate CSS/HTML naming cleanup?
- Should catalogue search payload budget be advisory at first, or should the next pass define a hard threshold?

## Verification For Follow-Up Refactors

- Run browser smoke for `/series/`, `/series/?mode=moments`, `/recent/`, `/works/`, `/works/?work=00008&series=105`, `/work-details/?detail=00001-001`, `/moments/?moment=a-doll-story`, `/catalogue/search/`, `/library/`, and `/analysis/`.
- Check console errors on each representative route.
- Record before/after script requests and JSON fetches.
- Keep `bin/site-validate` passing.
- Confirm public search, selected work, selected detail, moments, Library, and Analysis behavior stays equivalent unless a follow-up decision explicitly changes it.
