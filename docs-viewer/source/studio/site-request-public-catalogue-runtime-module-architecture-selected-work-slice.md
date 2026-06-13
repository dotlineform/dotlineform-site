---
doc_id: site-request-public-catalogue-runtime-module-architecture-selected-work-slice
title: Public Catalogue Runtime Selected Work Route Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: site-request-public-catalogue-runtime-module-architecture
viewable: true
---
# Public Catalogue Runtime Selected Work Route Slice

Status:

- planned

## Purpose

Track the selected-work route migration slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Image And Caption Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-image-caption-slice).

This slice should finish the integration that the image/caption foundation deliberately did not fit: move selected-work route behavior out of legacy `site/assets/js/work-page.js` and into an ES module route so work detail grids can reuse the thumbnail grid/list and image components without a temporary global bridge.

## Steer

- Treat the current `site/assets/js/work-page.js` behavior as the authoritative behavior reference.
- Migrate selected-work behavior at a clean route boundary.
- Do not redesign the selected-work page.
- Do not migrate the `/works/` index list behavior unless a small shell guard is needed to keep route modes separate.
- Do not pull `work.js` navigation behavior into this slice unless a focused navigation extraction becomes unavoidable.
- Reuse `thumbnail-grid-list.js`, `catalogue-image.js`, and shared thumbnail helpers for work detail grids.
- Keep primary work media route-owned unless it fits the image component without route-specific flags.
- Remove legacy `site/assets/js/work-page.js` only after no public route loads it.
- Keep the completed slice functional and deployable.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- perform manual browser testing for touched routes and component states;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 3: Selected Work Route Migration

Purpose: migrate `/works/?work=...` selected-work behavior to the target ES module route structure and reuse the existing thumbnail grid/list and image/caption foundations for detail grids.

Scope:

- inspect current selected-work behavior in:
  - `site/assets/js/work-page.js`;
  - `site/assets/js/work.js`;
  - `site/assets/js/works-index.js` only to preserve `/works/` index mode separation;
  - `site/works/index.html`;
  - relevant selected-work CSS in `site/assets/css/main.css` and component CSS in `site/assets/css/catalogue.css`;
- create `site/assets/js/catalogue/routes/work-page.js`;
- port selected-work route bootstrapping and payload handling into the new ES module route;
- preserve selected-work URL/query behavior, including `work`, `series`, `series_page`, `from`, `details_section`, and `details_page` parameters;
- preserve selected-work primary media rendering, title/meta rows, downloads/links rendering, prose rendering, back-link behavior, and the `dlf:work-metadata-applied` event used by `work.js`;
- reuse `thumbnail-grid-list.js` and `catalogue-image.js` for additional work detail thumbnail grids;
- load `catalogue.css` on `/works/` if the route uses catalogue components;
- switch the selected-work route shell script from legacy `work-page.js` to the new module;
- keep `/works/` index list behavior stable and still owned by `works-index.js`;
- remove legacy `site/assets/js/work-page.js` after the route no longer loads it.

Out of scope:

- generated catalogue data schema changes;
- redesigning the selected-work page layout;
- rewriting `/works/` index sorting/list behavior;
- migrating `work.js` keyboard/series navigation unless explicitly needed;
- migrating `/work-details/`;
- public search runtime or payload changes;
- automated smoke-test maintenance.

## Candidate Module Ownership

The exact filenames should follow the implementation, but ownership should stay narrow:

- `routes/work-page.js` owns selected-work route bootstrapping, DOM anchors, query-state wiring, payload selection, primary media wiring, metadata/prose/back-link rendering, and event dispatch.
- `components/thumbnail-grid-list.js` owns detail-grid DOM and paging if paging is used.
- `components/catalogue-image.js` owns detail-grid image DOM and fallback behavior.
- `shared/thumbnails.js` owns detail-thumbnail URL and image data projection if the existing function contract fits; otherwise add a focused helper there.
- `shared/catalogue-urls.js` may gain selected-work/detail URL helpers only when they are route-independent and not already present.
- `work.js` continues to own current keyboard/series navigation behavior until a navigation-foundation slice moves it.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 3.1 | planned | Inspect selected-work legacy behavior, loaded scripts, route shell markup, and relevant CSS. | Capture selected-work behavior only; do not fold in works-index migration. |
| 3.2 | planned | Define the selected-work route module contract and the detail-grid integration contract. | Stop for review if detail-grid reuse needs route-specific component flags. |
| 3.3 | planned | Implement `catalogue/routes/work-page.js` by porting/adapting legacy selected-work behavior. | Keep primary work media route-owned unless the image component fits cleanly. |
| 3.4 | planned | Integrate `thumbnail-grid-list.js` and `catalogue-image.js` for additional detail grids. | Preserve current detail links and query parameters exactly. |
| 3.5 | planned | Switch `/works/?work=...` to the new module while keeping `/works/` index behavior stable. | Ensure `works-index.js` still exits on selected-work URLs or otherwise avoids double rendering. |
| 3.6 | planned | Remove obsolete `site/assets/js/work-page.js` after no route loads it and update validation config. | Do not preserve an old filename compatibility alias. |
| 3.7 | planned | Record completed verification and a slice assessment with parent-design acceptance evidence. | Include concrete follow-up triggers for navigation and metadata cleanup. |

## Completed Verification

- Not started.

## Slice 3 Assessment

- Not started.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required |  |
| Legacy selected-work behavior inspected before contract design | yes required |  |
| Working behavior ported/adapted rather than redesigned line by line | yes required |  |
| Public route/navigation/data contracts remain stable | yes required |  |
| Completed slice leaves site functional and deployable | yes required |  |
| ES module boundaries follow target folder structure | yes required |  |
| No broad `utils.js`-style module introduced | yes required |  |
| Performance rules respected | yes required |  |
| Detail-grid reuse uses stable component contracts | yes required |  |
| Primary media ownership is explicit and not flag-heavy | yes required |  |
| Component CSS remains owned in `catalogue.css` where new selectors are introduced | yes required |  |
| Search, if touched, stays structural-only | yes required |  |
| Validation stayed within agreed policy | yes required |  |

## Follow-On

After Slice 3, decide whether to migrate `/work-details/` next, extract navigation behavior from `work.js`, or create a metadata panel foundation based on what the selected-work route migration exposes.
