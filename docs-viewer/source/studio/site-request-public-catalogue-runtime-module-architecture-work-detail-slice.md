---
doc_id: site-request-public-catalogue-runtime-module-architecture-work-detail-slice
title: Public Catalogue Runtime Work Detail Route Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Work Detail Route Slice

Status:

- completed

## Purpose

Track the `/work-details/` route migration slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Selected Work Route Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-selected-work-slice).

This slice should migrate selected work-detail behavior out of legacy `site/assets/js/work-detail-page.js` and into an ES module route, proving the selected-work to work-detail URL/context contract end to end before extracting shared navigation or primary-media foundations.

## Steer

- Treat the current `site/assets/js/work-detail-page.js` behavior as the authoritative behavior reference.
- Migrate work-detail behavior at a clean route boundary.
- Do not redesign the work-detail page.
- Preserve the selected-work return contract created by the selected-work route migration.
- Preserve `detail`, `from_work`, `section`, `details_section`, `details_page`, `series`, and `series_page` query behavior.
- Derive the selected-work back-link title from the fetched work payload instead of carrying `from_work_title` in detail URLs.
- Use `section` as the canonical section key in generated `/work-details/` URLs; keep `details_section` for accepted legacy/detail return state and for `/works/` return URLs.
- Preserve primary detail media rendering, title/category rows, back-link behavior, detail previous/next navigation, and unavailable-state behavior.
- Keep `work.js` keyboard navigation behavior in place unless a focused navigation extraction becomes unavoidable.
- Keep `swipe-nav.js` ownership in place; route code may bind the existing helper to detail media when the helper is present.
- Keep primary detail media route-owned unless a focused primary-media component fits without route-specific flags.
- Remove legacy `site/assets/js/work-detail-page.js` only after no public route loads it.
- Keep the completed slice functional and deployable.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- perform manual browser testing for touched routes and component states;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 4: Work Detail Route Migration

Purpose: migrate `/work-details/?detail=...` work-detail behavior to the target ES module route structure while preserving the selected-work return and detail navigation contracts.

Scope:

- inspect current work-detail behavior in:
  - `site/assets/js/work-detail-page.js`;
  - `site/assets/js/work.js` only for keyboard navigation and shared nav-link assumptions;
  - `site/assets/js/swipe-nav.js` only for the existing detail media swipe contract;
  - `site/work-details/index.html`;
  - selected-work detail-link generation in `site/assets/js/catalogue/routes/work-page.js`;
  - relevant route CSS in `site/assets/css/main.css` and component CSS in `site/assets/css/catalogue.css` if any component is reused;
- create `site/assets/js/catalogue/routes/work-detail-page.js`;
- port work-detail route bootstrapping, route-context parsing, payload lookup, record selection, primary media rendering, title/category rows, back-link rendering, and detail previous/next navigation into the new ES module route;
- preserve work-detail URL/query behavior, including `detail`, `from_work`, `section`, `details_section`, `details_page`, `series`, and `series_page`;
- remove `from_work_title` from generated detail URLs and resolve the back-link label from the source work payload;
- avoid generating duplicate `section` and `details_section` keys when both refer to the same detail section;
- preserve fallback behavior when no detail is selected, no source work can be loaded, or the selected detail cannot be found;
- switch the `/work-details/` route shell script from legacy `work-detail-page.js` to the new module;
- keep `work.js` loaded for current keyboard navigation unless a route-local event or markup contract must change;
- keep `swipe-nav.js` loaded and bind the existing helper to detail media previous/next links when available;
- remove legacy `site/assets/js/work-detail-page.js` after the route no longer loads it and validation config is updated.

Out of scope:

- generated catalogue data schema changes;
- redesigning the work-detail page layout;
- migrating selected-work route behavior already completed in Slice 3;
- migrating `work.js` keyboard navigation unless explicitly needed;
- migrating `swipe-nav.js` unless explicitly needed;
- creating a broad primary-media abstraction before the route proves the contract;
- public search runtime or payload changes;
- automated smoke-test maintenance.

## Candidate Module Ownership

The exact filenames should follow the implementation, but ownership should stay narrow:

- `routes/work-detail-page.js` owns work-detail route bootstrapping, DOM anchors, query-state wiring, source work payload lookup, detail record selection, primary media rendering, title/category/back-link rendering, detail navigation, and unavailable-state rendering.
- `shared/catalogue-urls.js` may gain route-independent selected-detail helpers only when they are not already present and do not duplicate runtime-global behavior.
- `shared/text.js` and existing narrow shared modules may own parsing primitives when they are route-independent.
- A new primary-media component should be introduced only if selected-work and work-detail media can share it without route-specific flags or regressions.
- `work.js` continues to own current keyboard navigation until a navigation-foundation slice moves it.
- `swipe-nav.js` continues to own current swipe behavior until a navigation-foundation slice moves it; the route may perform only the local DOM binding.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 4.1 | completed | Inspected legacy work-detail behavior, loaded scripts, route shell markup, selected-work detail links, and relevant CSS. | Work-detail behavior is recorded below; navigation extraction was not started. |
| 4.2 | completed | Defined the work-detail route module contract and the selected-work return-context contract. | Primary-media reuse would need more design, so primary media stayed route-owned. |
| 4.3 | completed | Implemented `catalogue/routes/work-detail-page.js` by porting/adapting legacy work-detail behavior. | Keep primary detail media route-owned until a later primary-media foundation is explicitly designed. |
| 4.4 | completed | Preserved detail previous/next navigation and keyboard-navigation markup contracts. | `work.js` remains the keyboard owner; the route binds the existing swipe helper to detail media when available. |
| 4.5 | completed | Switched `/work-details/?detail=...` to the new module while keeping unavailable `/work-details/` behavior stable. | The shell is fully switched to the ES module route. |
| 4.6 | completed | Removed obsolete `site/assets/js/work-detail-page.js` after no route loaded it and updated validation config. | No old filename compatibility alias was kept. |
| 4.7 | completed | Recorded completed verification and a slice assessment with parent-design acceptance evidence. | Use the follow-on triggers below for navigation and primary-media cleanup. |

## Completed Verification

- JavaScript syntax checks passed:
  - `node --check site/assets/js/catalogue/routes/work-detail-page.js`
  - `node --check site/assets/js/swipe-nav.js`
- `bin/site-validate` passed: `57 required files; 9 required directories; 44 Docs Viewer runtime modules`.
- Manual browser validation against `http://127.0.0.1:8175` covered:
  - `/work-details/?detail=00001-001&from_work=00001&section=00001-1&series=009` renders the selected detail title, category id, primary image state, back link, and `1/17` detail navigation with no console errors;
  - `/work-details/` leaves `#detailPageRoot` hidden, shows `#detailPageEmpty`, and reports no console errors;
  - `/works/?work=00001&series=009` still generates a detail link with work, section, series, and detail context;
  - navigating through that generated detail link resolves the selected-work back-link label from the work payload and preserves detail navigation state.
- `swipe-nav.js` was served with the new stable global/no-op fallback for browsers without `PointerEvent`; the in-app browser runtime reported no `PointerEvent` support, so real swipe gesture behavior was not exercised there.
- Automated browser smoke tests were not run, per the slice validation policy.

## Slice 4 Assessment

- Legacy behavior inspected:
  - `site/assets/js/work-detail-page.js` rendered work-detail route state, primary media URLs and `srcset`, title/category rows, selected-work back-link context, source work payload lookup, detail record selection, and previous/next detail navigation.
  - `site/assets/js/work.js` still owns current keyboard navigation by looking for `detailNavPrev` and `detailNavNext`.
  - `site/assets/js/swipe-nav.js` exposed a reusable swipe helper but the work-detail route did not bind the `data-swipe-nav-zone="detail-media"` element before this slice.
  - `site/work-details/index.html` loaded `swipe-nav.js`, `public-catalogue-runtime.js`, legacy `work-detail-page.js`, and `work.js`.
  - `site/assets/js/catalogue/routes/work-page.js` generates selected-work detail links with return context consumed by this route.
- Behavior preserved:
  - `/work-details/?detail=...` still derives a source work from `from_work` or the detail uid prefix and fetches `/assets/works/index/<work_id>.json`.
  - Detail title, category id, document title, primary image `href`/`src`/`srcset`/`alt`, aspect ratio, back link, previous/next detail links, counter text, and unavailable state remain behavior-equivalent.
  - Query-state behavior for `detail`, `from_work`, `section`, `details_section`, `details_page`, `series`, and `series_page` remains stable.
  - `from_work_title` is intentionally not part of generated detail URLs; back-link labels are resolved from the source work payload.
  - Generated detail URLs use `section` as the detail section key and omit duplicate `details_section` when it would carry the same value.
  - `work.js` keyboard navigation continues to use the existing `detailNavPrev` and `detailNavNext` anchors.
  - `swipe-nav.js` remains the swipe behavior owner; the route now performs the missing local binding to the detail media zone.
- Normalized into module contracts:
  - `routes/work-detail-page.js` now owns work-detail bootstrapping, route context, source work payload lookup, detail record selection, primary media, title/category/back-link rendering, detail previous/next navigation, swipe-helper binding, and unavailable-state rendering.
  - Existing `shared/catalogue-urls.js` and `shared/text.js` helpers were reused; no new broad utility module was introduced.
  - `swipe-nav.js` now exposes a stable `window.__dlfSwipeNav` object even when pointer events are unsupported, with no-op bind methods and `supported: false`.
- Intentionally not changed:
  - Primary detail media remains route-owned because a shared primary-media component needs a separate contract covering full-size links, aspect ratio, eager loading, and route-specific image bases.
  - `work.js` remains a legacy classic script for keyboard navigation.
  - `swipe-nav.js` remains a legacy classic script for swipe behavior.
  - Generated catalogue data schemas, public search, selected-work rendering, and visual layout were not changed.
- Improvement opportunities:
  - Extract `work.js` keyboard navigation after selected-work and work-detail routes are both stable on ES module entrypoints.
  - Consider moving `swipe-nav.js` into `catalogue/navigation/` with pointer/touch support as a focused navigation-foundation slice.
  - Design a primary-media component only after comparing selected-work, work-detail, moment, and any remaining primary media route needs.
- Remaining issues:
  - No remaining issue blocks deployment. The route is migrated; navigation helpers remain in legacy classic scripts at explicit boundaries.
- Continue decision:
  - Slice 4 is complete and leaves the public site deployable. The selected-work to work-detail contract is now proven end to end on ES module route code.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required | yes - work-detail behavior moved to `routes/work-detail-page.js` while keeping UI, URL, data, and navigation contracts stable. |
| Legacy work-detail behavior inspected before contract design | yes required | yes - the assessment records inspected behavior from legacy `work-detail-page.js`, `work.js`, `swipe-nav.js`, route shell markup, selected-work detail links, and relevant CSS. |
| Working behavior ported/adapted rather than redesigned line by line | yes required | yes - primary media, title/category, back-link, source-work lookup, detail selection, navigation, and fallback behavior were ported/adapted behind the new route boundary. |
| Public route/navigation/data contracts remain stable | yes required | yes - manual checks covered selected detail, empty detail, selected-work detail-link generation, and generated-detail navigation context; generated data schemas were not changed. |
| Selected-work to work-detail return context remains stable | yes required | yes - browser validation confirmed selected-work generated detail links and detail back-link labels/targets preserve return context without carrying the work title in the URL. |
| Completed slice leaves site functional and deployable | yes required | yes - syntax checks, `bin/site-validate`, and manual browser validation passed. |
| ES module boundaries follow target folder structure | yes required | yes - route code lives in `routes/`; existing route-independent helpers are imported from `shared/`. |
| No broad `utils.js`-style module introduced | yes required | yes - no new shared utility bucket was introduced. |
| Performance rules respected | yes required | yes - the route fetches only the related work payload needed to resolve the selected detail and navigation context. |
| Primary media ownership is explicit and not flag-heavy | yes required | yes - primary detail media remains route-owned rather than adding route-specific flags to an image component. |
| Keyboard and swipe navigation ownership remains explicit | yes required | yes - `work.js` remains keyboard owner, `swipe-nav.js` remains swipe owner, and the route only binds the existing swipe helper to local DOM. |
| Component CSS remains owned in `catalogue.css` where new selectors are introduced | yes required | yes - no new component selectors were introduced; existing route layout remains in `main.css`. |
| Search, if touched, stays structural-only | yes required | yes - search was not touched. |
| Validation stayed within agreed policy | yes required | yes - validation used syntax checks, `bin/site-validate`, and manual browser checks; automated browser smoke tests were not run. |

## Follow-On

After Slice 4, decide whether to extract `work.js` keyboard/detail/series navigation into `catalogue/navigation/`, create a focused primary-media component from the selected-work and work-detail routes, or migrate another remaining legacy public route.
