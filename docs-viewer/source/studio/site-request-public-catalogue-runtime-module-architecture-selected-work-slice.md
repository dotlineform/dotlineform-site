---
doc_id: site-request-public-catalogue-runtime-module-architecture-selected-work-slice
title: Public Catalogue Runtime Selected Work Route Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Selected Work Route Slice

Status:

- completed

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
| 3.1 | completed | Inspected selected-work legacy behavior, loaded scripts, route shell markup, and relevant CSS. | The relevant behavior is recorded below; works-index behavior was checked only for route-mode separation. |
| 3.2 | completed | Defined the selected-work route module contract and the detail-grid integration contract. | Detail-grid reuse did not need route-specific component flags. |
| 3.3 | completed | Implemented `catalogue/routes/work-page.js` by porting/adapting legacy selected-work behavior. | Primary work media remains route-owned. |
| 3.4 | completed | Integrated `thumbnail-grid-list.js` and `catalogue-image.js` for additional detail grids. | Detail links continue to carry work, section, series, and page context. |
| 3.5 | completed | Switched `/works/?work=...` to the new module while keeping `/works/` index behavior stable. | `works-index.js` still exits on selected-work URLs; the new module does no selected-work work on bare `/works/`. |
| 3.6 | completed | Removed obsolete `site/assets/js/work-page.js` after no route loaded it and updated validation config. | No old filename compatibility alias was kept. |
| 3.7 | completed | Recorded completed verification and a slice assessment with parent-design acceptance evidence. | Use the follow-on triggers below for navigation and metadata cleanup decisions. |

## Completed Verification

- JavaScript syntax checks passed:
  - `node --check site/assets/js/catalogue/routes/work-page.js`
  - `node --check site/assets/js/catalogue/shared/catalogue-urls.js`
  - `node --check site/assets/js/catalogue/shared/text.js`
- `bin/site-validate` passed: `56 required files; 9 required directories; 44 Docs Viewer runtime modules`.
- Manual browser validation against `http://127.0.0.1:8173` covered:
  - `/works/?work=00001&series=009` renders the selected work title, primary media state, back link, series link, and series navigation with no console errors;
  - selected-work detail thumbnails render through `catalogueGridList` and `catalogueImage` classes;
  - the selected-work route loads `/assets/js/catalogue/routes/work-page.js` and no longer loads `/assets/js/work-page.js`;
  - `/works/` still renders the works index list, leaves `#selectedWorkRoot` hidden, and reports no console errors.
- Automated browser smoke tests were not run, per the slice validation policy.

## Slice 3 Assessment

- Legacy behavior inspected:
  - `site/assets/js/work-page.js` rendered selected-work payload data, primary media URLs and `srcset`, metadata rows, downloads, external links, prose HTML, detail-grid thumbnail links, back-link state, and the `dlf:work-metadata-applied` event.
  - `site/assets/js/work.js` consumed `dlf:work-metadata-applied`, fetched `series_index.json`, projected the series link/back-link label, and owns current keyboard/series navigation.
  - `site/assets/js/works-index.js` exits early when the `work` query parameter is present and continues to own bare `/works/` index list rendering.
  - `site/works/index.html` loaded the selected-work shell, legacy `work-page.js`, `work.js`, and `works-index.js`.
  - `main.css` still owns route layout, primary media, `.workDetails*`, and legacy `.seriesGrid*` selectors; `catalogue.css` owns the reused `.catalogueGridList*` and `.catalogueImage*` component selectors.
- Behavior preserved:
  - `/works/?work=...` still fetches the selected work payload from `/assets/works/index/<id>.json`.
  - Selected-work title, catalogue id, year, medium, dimensions, downloads, external links, prose, primary media, document title, and fallback unavailable state remain route-owned and behavior-equivalent.
  - Query-state behavior for `work`, `series`, `series_page`, `from`, `details_section`, and positive `details_page` is preserved for selected-work navigation and detail links.
  - The route still dispatches `dlf:work-metadata-applied` so `work.js` can project series link, back-link label, series navigation, and keyboard navigation.
  - `/works/` index list behavior remains owned by `works-index.js`.
- Normalized into module/component contracts:
  - `routes/work-page.js` now owns selected-work bootstrapping, route-state wiring, payload rendering, primary media, metadata/prose/back-link rendering, detail-grid item projection, and metadata event dispatch.
  - `shared/catalogue-urls.js` gained route-independent selected-work payload and work-detail URL helpers.
  - `shared/text.js` gained focused `toNumber` and `slug` primitives used by the route.
  - `thumbnail-grid-list.js` and `catalogue-image.js` now render selected-work additional detail thumbnails in grid mode.
- Intentionally not changed:
  - `work.js` remains a legacy classic script for series navigation, series-link projection, back-link label projection, and keyboard navigation.
  - Primary work media remains route-owned because fitting it into `catalogue-image.js` would require route-specific behavior around full-size links, aspect ratio, eager loading, and fetch priority.
  - `/work-details/`, public search, generated catalogue schemas, and the works index list implementation were not migrated.
  - Legacy `.seriesGrid*` selectors remain in `main.css` because other legacy routes still use them.
- Improvement opportunities:
  - Migrate `/work-details/` next if the goal is to reuse detail navigation or primary-detail media code.
  - Extract `work.js` navigation/back-link projection when moving keyboard and series navigation into `navigation/`.
  - Consider a focused metadata panel or primary-media component only after another route needs the same contract without route-specific flags.
- Remaining issues:
  - No remaining issue blocks deployment. The mixed runtime is still present at a clean boundary: selected-work rendering is modular, while navigation remains in `work.js`.
- Continue decision:
  - Slice 3 is complete and leaves the public site deployable. The selected-work route now follows the target ES module structure and proves detail-grid reuse without a global bridge.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required | yes - selected-work behavior moved to `routes/work-page.js` while keeping UI, URL, data, and navigation contracts stable. |
| Legacy selected-work behavior inspected before contract design | yes required | yes - the assessment records inspected behavior from legacy `work-page.js`, `work.js`, `works-index.js`, route shell markup, and relevant CSS. |
| Working behavior ported/adapted rather than redesigned line by line | yes required | yes - metadata, media, prose, downloads/links, back-link, event dispatch, and detail-grid behavior were ported/adapted behind new module boundaries. |
| Public route/navigation/data contracts remain stable | yes required | yes - manual checks covered `/works/?work=00001&series=009` and `/works/`; generated payload schemas were not changed. |
| Completed slice leaves site functional and deployable | yes required | yes - syntax checks, `bin/site-validate`, and manual browser validation passed. |
| ES module boundaries follow target folder structure | yes required | yes - route code lives in `routes/`, route-independent helpers in `shared/`, and reusable thumbnail/image DOM remains in `components/`. |
| No broad `utils.js`-style module introduced | yes required | yes - only focused URL/text helpers were added. |
| Performance rules respected | yes required | yes - selected-work rendering fetches only the selected work payload; bare `/works/` loads the route module but it exits before fetching selected-work data. |
| Detail-grid reuse uses stable component contracts | yes required | yes - detail-grid items use `thumbnail-grid-list.js` in grid mode and `catalogue-image.js` via normalized thumbnail image data. |
| Primary media ownership is explicit and not flag-heavy | yes required | yes - primary work media stays route-owned rather than adding full-size-link/aspect-ratio/eager-loading flags to the image component. |
| Component CSS remains owned in `catalogue.css` where new selectors are introduced | yes required | yes - selected-work detail grids reuse existing `.catalogueGridList*` and `.catalogueImage*` selectors in `catalogue.css`; no new component selectors were added to `main.css`. |
| Search, if touched, stays structural-only | yes required | yes - search was not touched. |
| Validation stayed within agreed policy | yes required | yes - validation used syntax checks, `bin/site-validate`, and manual browser checks; automated browser smoke tests were not run. |

## Follow-On

After Slice 3, decide whether to migrate `/work-details/` next, extract navigation behavior from `work.js`, or create a metadata panel foundation based on what the selected-work route migration exposes.
