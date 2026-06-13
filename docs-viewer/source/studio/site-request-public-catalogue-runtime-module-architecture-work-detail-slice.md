---
doc_id: site-request-public-catalogue-runtime-module-architecture-work-detail-slice
title: Public Catalogue Runtime Work Detail Route Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: site-request-public-catalogue-runtime-module-architecture
viewable: true
---
# Public Catalogue Runtime Work Detail Route Slice

Status:

- planned

## Purpose

Track the `/work-details/` route migration slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Selected Work Route Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-selected-work-slice).

This slice should migrate selected work-detail behavior out of legacy `site/assets/js/work-detail-page.js` and into an ES module route, proving the selected-work to work-detail URL/context contract end to end before extracting shared navigation or primary-media foundations.

## Steer

- Treat the current `site/assets/js/work-detail-page.js` behavior as the authoritative behavior reference.
- Migrate work-detail behavior at a clean route boundary.
- Do not redesign the work-detail page.
- Preserve the selected-work return contract created by the selected-work route migration.
- Preserve `detail`, `from_work`, `from_work_title`, `section`, `details_section`, `details_page`, `series`, and `series_page` query behavior.
- Preserve primary detail media rendering, title/category rows, back-link behavior, detail previous/next navigation, and unavailable-state behavior.
- Keep `work.js` keyboard navigation behavior in place unless a focused navigation extraction becomes unavoidable.
- Keep `swipe-nav.js` ownership in place unless the route migration exposes a clean no-risk replacement.
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
- preserve work-detail URL/query behavior, including `detail`, `from_work`, `from_work_title`, `section`, `details_section`, `details_page`, `series`, and `series_page`;
- preserve fallback behavior when no detail is selected, no source work can be loaded, or the selected detail cannot be found;
- switch the `/work-details/` route shell script from legacy `work-detail-page.js` to the new module;
- keep `work.js` loaded for current keyboard navigation unless a route-local event or markup contract must change;
- keep `swipe-nav.js` loaded for current swipe behavior unless a separate decision approves moving it;
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
- `swipe-nav.js` continues to own current swipe behavior until a navigation-foundation slice moves it.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 4.1 | planned | Inspect legacy work-detail behavior, loaded scripts, route shell markup, selected-work detail links, and relevant CSS. | Capture work-detail behavior only; do not start navigation extraction unless blocked. |
| 4.2 | planned | Define the work-detail route module contract and the selected-work return-context contract. | Stop for review if primary-media reuse needs route-specific component flags. |
| 4.3 | planned | Implement `catalogue/routes/work-detail-page.js` by porting/adapting legacy work-detail behavior. | Keep primary detail media route-owned unless a focused component fits cleanly. |
| 4.4 | planned | Preserve detail previous/next navigation and keyboard-navigation markup contracts. | Keep `work.js` as the keyboard owner for this slice. |
| 4.5 | planned | Switch `/work-details/?detail=...` to the new module while keeping unavailable `/work-details/` behavior stable. | Ensure the shell is fully switched, not half-switched. |
| 4.6 | planned | Remove obsolete `site/assets/js/work-detail-page.js` after no route loads it and update validation config. | Do not preserve an old filename compatibility alias. |
| 4.7 | planned | Record completed verification and a slice assessment with parent-design acceptance evidence. | Include concrete follow-up triggers for navigation and primary-media cleanup. |

## Completed Verification

- Not started.

## Slice 4 Assessment

- Not started.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required |  |
| Legacy work-detail behavior inspected before contract design | yes required |  |
| Working behavior ported/adapted rather than redesigned line by line | yes required |  |
| Public route/navigation/data contracts remain stable | yes required |  |
| Selected-work to work-detail return context remains stable | yes required |  |
| Completed slice leaves site functional and deployable | yes required |  |
| ES module boundaries follow target folder structure | yes required |  |
| No broad `utils.js`-style module introduced | yes required |  |
| Performance rules respected | yes required |  |
| Primary media ownership is explicit and not flag-heavy | yes required |  |
| Keyboard and swipe navigation ownership remains explicit | yes required |  |
| Component CSS remains owned in `catalogue.css` where new selectors are introduced | yes required |  |
| Search, if touched, stays structural-only | yes required |  |
| Validation stayed within agreed policy | yes required |  |

## Follow-On

After Slice 4, decide whether to extract `work.js` keyboard/detail/series navigation into `catalogue/navigation/`, create a focused primary-media component from the selected-work and work-detail routes, or migrate another remaining legacy public route.
