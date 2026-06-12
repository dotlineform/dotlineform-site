---
doc_id: site-request-public-js-runtime-payload-review
title: Public JavaScript Runtime and Payload Review Request
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: change-requests
---
# Public JavaScript Runtime and Payload Review Request

Status:

- planned
- This is a post-migration follow-up to [Public Static Site Build Request](/docs/?scope=studio&doc=site-request-public-static-site-build).
- Do not start this request until the static public-site builder migration has completed production cutover or the migration closeout explicitly schedules it.

## Summary

Review and refactor the public site's JavaScript runtime and generated payload loading after the static builder migration is complete.

The goal is to make public route JavaScript easier to maintain and better aligned with public-site performance goals without changing the public route model or user-facing behavior by accident.

## Context

During the static public-site builder migration, [Public Route JavaScript Extraction](/docs/?scope=studio&doc=public-static-site-build-batch-03a-js-extraction) moved large inline scripts from Jekyll route templates into public JS files:

- `assets/js/series-index.js`
- `assets/js/recent-index.js`
- `assets/js/work-page.js`
- `assets/js/works-index.js`
- `assets/js/work-detail-page.js`

That extraction deliberately preserved behavior and avoided a larger runtime redesign. It was the right migration step because it kept long route runtime code out of Python renderers.

After the migration, the public site needs a separate review of:

- what belongs inline, in classic scripts, or in ES modules;
- which route scripts need to load on each page;
- whether shared helpers should move out of route files;
- whether generated payloads are sized and fetched appropriately for the public routes.

## Goals

- Inventory public route JavaScript by route, owner, size, dependencies, and load timing.
- Decide which public runtime code belongs inline, which belongs in route-level files, and which belongs in shared modules.
- Review the structure and ownership of:
  - `assets/js/public-catalogue-runtime.js`
  - `assets/js/series-index.js`
  - `assets/js/recent-index.js`
  - `assets/js/work-page.js`
  - `assets/js/works-index.js`
  - `assets/js/work-detail-page.js`
  - `assets/js/work.js`
  - `assets/js/moment.js`
  - `assets/js/catalogue-search.js`
  - `assets/js/search/*.js`
  - global scripts such as `site-nav.js` and `theme-toggle.js`
- Reduce duplicated helper logic where there is a clear shared owner.
- Avoid loading route-specific behavior on routes that do not need it.
- Measure generated public payload sizes and route fetch behavior.
- Identify payload-splitting, lazy-load, cache, or prefetch opportunities.
- Keep route URLs, route state semantics, visual behavior, and generated data schemas stable unless a specific follow-up decision approves a change.

## Non-Goals

- Reopening the static public-site build migration.
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
- current inline scripts that remain after the static builder migration;
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

## Verification Expectations

- Browser smoke checks for all representative public routes.
- Console-error checks for all representative public routes.
- Payload/file-size report before and after refactors.
- Generated artifact audit still passes after script changes.
- Search, selected work, selected detail, moments, Library, and Analysis routes remain behavior-equivalent unless a recorded decision approves a change.

## Relationship To Static Builder Migration

This request is intentionally deferred until after the static builder migration.

The migration should continue to prioritize:

- replacing Jekyll/Liquid rendering;
- preserving route behavior;
- keeping artifact assembly allowlist-driven;
- cutting over GitHub Pages to the static Actions artifact.

This request picks up the deeper public-runtime and payload performance work after that cutover path is stable.
