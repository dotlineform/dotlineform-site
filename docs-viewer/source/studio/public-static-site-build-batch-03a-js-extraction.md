---
doc_id: public-static-site-build-batch-03a-js-extraction
title: Public Static Site Build Batch 3a Public Route JavaScript Extraction
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: done
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 3a Public Route JavaScript Extraction

This is the delivery specification for the inserted Batch 3a in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: move large public route inline scripts into owned public JavaScript files before Batch 3 renders those routes with Python.

## Steer for these tasks

- Batch 3 route rendering pauses until this batch is complete.
- Keep behavior equivalent on the current Jekyll-rendered routes.
- Move runtime behavior into JS files under `assets/js/`; keep Python renderers responsible for HTML shells, data attributes, config injection, and script tags.
- Perform obvious cleanup during extraction when it reduces duplication or removes route-script coupling without changing the public route model.
- Do not redesign route state, URL contracts, visual layout, generated payload schemas, or catalogue runtime ownership.
- Keep `assets/js/public-catalogue-runtime.js`, `assets/js/work.js`, `assets/js/moment.js`, and `assets/js/catalogue-search.js` as existing shared/runtime owners unless a focused extraction task records a specific change.

## Extraction Targets

| current source | extracted owner | note |
| --- | --- | --- |
| `series/index.md` inline catalogue index script | `assets/js/series-index.js` | Preserves works/moments list/grid/sort/pager behavior. |
| `recent/index.md` inline recent script | `assets/js/recent-index.js` | Preserves recent payload rendering and back link behavior. |
| `works/index.md` selected-work inline script | `assets/js/work-page.js` | Preserves selected work loading, media, metadata, downloads/links, prose, detail thumbnails, series nav events, and back-link behavior. |
| `works/index.md` works-list inline script | `assets/js/works-index.js` | Preserves works list sorting, series filtering, counts, and return-state query updates. |
| `work-details/index.md` detail inline script | `assets/js/work-detail-page.js` | Preserves selected detail loading, image srcset, back link, swipe navigation, and detail nav. |

No extraction is required for `moments/index.md` or `catalogue/search/index.md` in this batch because they already delegate to `assets/js/moment.js` and `assets/js/catalogue-search.js`.

## Deliverables

- New public JS files for the extraction targets.
- Route templates updated to load those JS files instead of embedding the moved script bodies.
- Shared helper functions extracted only when two or more route modules use the same logic and the helper has a clear public owner.
- Browser smoke coverage for routes touched by extraction.
- A Batch 3 handoff that names the script tags the Python renderers must emit.

## Implementation and policy guidance

- Preserve current data attributes and DOM ids so the later Python renderer can generate the same shell contract.
- Keep moved scripts in classic script files unless the source route already uses `type="module"`.
- Keep route initialization side-effect based, matching current page behavior.
- Do not bundle or transpile JavaScript.
- Do not move generated payload ownership in this batch.

## Proposed verification set

- JavaScript syntax checks for new and changed public JS files.
- Existing Jekyll build to prove the current route templates still render.
- Browser smoke checks against the Jekyll preview or an isolated Jekyll build for:
  - `/series/`
  - `/series/?mode=moments`
  - `/recent/`
  - `/works/`
  - `/works/?work=00008&series=105`
  - `/work-details/?detail=00001-001`
- Check that route HTML no longer contains the extracted large inline script bodies.
- Check that script tags reference the new `assets/js/*.js` files with the existing asset-version query convention.

## Tasks

### Batch 3a: Public Route JavaScript Extraction

| ID | status | action |
| --- | --- | --- |
| 3a.1 | done | Extract `series/index.md` inline behavior to `assets/js/series-index.js` and update the route template script tag. |
| 3a.2 | done | Extract `recent/index.md` inline behavior to `assets/js/recent-index.js` and update the route template script tag. |
| 3a.3 | done | Extract `works/index.md` selected-work behavior to `assets/js/work-page.js` and update the route template script tag. |
| 3a.4 | done | Extract `works/index.md` works-list behavior to `assets/js/works-index.js` and update the route template script tag. |
| 3a.5 | done | Extract `work-details/index.md` inline behavior to `assets/js/work-detail-page.js` and update the route template script tag. |
| 3a.6 | done | Add focused syntax and smoke verification for the extracted route modules. |
| 3a.7 | done | Update Batch 3 with the final script tags and route shell contracts for Python rendering. |

## completed verification

- `node --check assets/js/series-index.js`
- `node --check assets/js/recent-index.js`
- `node --check assets/js/work-page.js`
- `node --check assets/js/works-index.js`
- `node --check assets/js/work-detail-page.js`
- `git diff --check -- series/index.md recent/index.md works/index.md work-details/index.md assets/js/series-index.js assets/js/recent-index.js assets/js/work-page.js assets/js/works-index.js assets/js/work-detail-page.js`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Built HTML check confirmed extracted script tags in:
  - `/tmp/dlf-jekyll-build/series/index.html`
  - `/tmp/dlf-jekyll-build/recent/index.html`
  - `/tmp/dlf-jekyll-build/works/index.html`
  - `/tmp/dlf-jekyll-build/work-details/index.html`
- Browser smoke against `http://127.0.0.1:8162` passed with no console errors:
  - `/series/`: `#seriesIndexRoot` visible, 80 initial items.
  - `/series/?mode=moments`: `#seriesIndexRoot` visible, 56 moment items.
  - `/recent/`: `#recentIndexRoot` visible, 12 items.
  - `/works/`: `#worksIndexRoot` visible, 1940 works in 141 series.
  - `/works/?work=00008&series=105`: selected work visible, title `nerve`, download link `nerve.pdf` visible.
  - `/work-details/?detail=00001-001&from_work=00001`: detail visible, title `a poem divided into 4 parts - end 1`, cat `00001-001`.

## follow-on tasks

- Batch 3 must emit script tags for the extracted JS files rather than embedding the moved runtime code in Python strings.
- Batch 4 must include the extracted JS files in the public asset copy allowlist.

## batch close

- Batch 3a is complete. Batch 3 resumes with route renderers that emit the extracted JS script tags listed in this document.
