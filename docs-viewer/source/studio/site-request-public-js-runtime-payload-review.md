---
doc_id: site-request-public-js-runtime-payload-review
title: Public JavaScript Runtime and Payload Review Request
added_date: 2026-06-12
last_updated: 2026-06-13
ui_status: planned
parent_id: change-requests
---
# Public JavaScript Runtime and Payload Review Request

Status:

- planned

## Summary

Review and refactor the public site's JavaScript runtime and generated payload loading.

The goal is to make public route JavaScript easier to maintain and better aligned with public-site performance goals without changing the public route model or user-facing behavior by accident.

## Context

The public site is now served directly from the tracked `site/` directory.
There is no public-site Python builder, generated deploy folder, or deploy-time copy step.
Public HTML, CSS, JavaScript, and browser-visible generated payloads under `site/` are canonical deploy input.

During the earlier static-site migration, large inline scripts were moved from public route HTML into public JS files:

- `site/assets/js/series-index.js`
- `site/assets/js/recent-index.js`
- `site/assets/js/work-page.js`
- `site/assets/js/works-index.js`
- `site/assets/js/work-detail-page.js`

That extraction deliberately preserved behavior and avoided a larger runtime redesign.
It was the right migration step because it moved long route runtime code out of page markup and into named public-site assets.

After the `site/` canonical-root migration, the public site needs a separate review of:

- what belongs inline, in classic scripts, or in ES modules;
- which route scripts need to load on each page;
- whether shared helpers should move out of route files;
- whether generated payloads are sized and fetched appropriately for the public routes.

The review should treat checked-in `site/` files as the source being improved.
It should not assume a builder layer that can rewrite route shells, inject includes, bundle scripts, copy assets, or generate deploy artifacts.

## Goals

- Inventory public route JavaScript by route, owner, size, dependencies, and load timing.
- Decide which public runtime code belongs inline, which belongs in route-level files, and which belongs in shared modules.
- Review the structure and ownership of:
  - `site/assets/js/public-catalogue-runtime.js`
  - `site/assets/js/series-index.js`
  - `site/assets/js/recent-index.js`
  - `site/assets/js/work-page.js`
  - `site/assets/js/works-index.js`
  - `site/assets/js/work-detail-page.js`
  - `site/assets/js/work.js`
  - `site/assets/js/moment.js`
  - `site/assets/js/catalogue-search.js`
  - `site/assets/js/search/*.js`
  - global scripts such as `site-nav.js` and `theme-toggle.js`
- Reduce duplicated helper logic where there is a clear shared owner.
- Avoid loading route-specific behavior on routes that do not need it.
- Measure generated public payload sizes and route fetch behavior.
- Identify payload-splitting, lazy-load, cache, or prefetch opportunities.
- Keep route URLs, route state semantics, visual behavior, and generated data schemas stable unless a specific follow-up decision approves a change.

## Non-Goals

- Changing the public route model.
- Redesigning public page layouts.
- Replacing generated catalogue, docs, or search payload ownership.
- Introducing a JavaScript bundler or transpiler without a separate explicit decision.
- Moving production away from static hosting.

## Audit Requirements

The first implementation batch must record:

- a route-by-route script inventory;
- current script sizes before compression and, where practical, after compression;
- current generated JSON payload sizes for catalogue index, works index, series index, moments index, recent index, per-record payloads, docs payloads, and search indexes;
- current fetch waterfall for representative public routes;
- duplicated helper functions and candidate shared-module owners;
- current inline scripts that remain in tracked `site/` route HTML;
- route-specific scripts loaded on routes where they are unused.

Representative routes:

- `/series/`
- `/series/?mode=moments`
- `/recent/`
- `/works/`
- `/works/?work=00008&series=105`
- `/work-details/?detail=00001-001`
- `/moments/?moment=a-doll-story`
- `/catalogue/search/`
- `/library/`
- `/analysis/`

## Decision Requirements

Before refactoring, decide and record:

- whether public route scripts stay classic scripts or move to ES modules;
- whether route files should share a dedicated public route helper module beyond `public-catalogue-runtime.js`;
- whether any behavior remains inline and why;
- whether payload splitting is needed for the first pass;
- whether route-level lazy loading is needed for the first pass;
- whether performance budgets are advisory or enforced in CI.

## Candidate Implementation Slices

1. Public JS and payload audit.
2. Public route script boundary cleanup.
3. Shared helper extraction.
4. Route-specific loading cleanup.
5. Payload size and fetch review.
6. Performance budget and CI/reporting decision.

## Child Docs

- [Public JS Runtime and Payload Static Audit](/docs/?scope=studio&doc=site-request-public-js-runtime-payload-review-audit)

## Verification Expectations

- Browser smoke checks for all representative public routes.
- Console-error checks for all representative public routes.
- Payload/file-size report before and after refactors.
- `bin/site-validate` still passes after script changes.
- Search, selected work, selected detail, moments, Library, and Analysis routes remain behavior-equivalent unless a recorded decision approves a change.
