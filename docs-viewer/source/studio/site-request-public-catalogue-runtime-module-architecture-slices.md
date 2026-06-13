---
doc_id: site-request-public-catalogue-runtime-module-architecture-slices
title: Public Catalogue Runtime Module Architecture Slices
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: in-progress
parent_id: site-request-public-catalogue-runtime-module-architecture
viewable: true
---
# Public Catalogue Runtime Module Architecture Slices

Status:

- in-progress

## Purpose

Track the implementation slices for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture).

This is not a comprehensive inventory of every public route.
The work should proceed from the agreed module structure and the first foundation refactor: thumbnail grid/list.
The work is not a greenfield rewrite.
The existing route code is the authoritative behavior reference for this refactor.

## Steer

- Set up the defined folder structure before moving behavior.
- Start with the thumbnail grid/list foundation.
- Carefully inspect existing legacy route code before defining the component contract.
- Port and adapt working logic into new ES module boundaries instead of redesigning behavior line by line.
- Change code only where needed for modularity, ownership, consistency, or the agreed component contract.
- Do not batch a full public-site route migration.
- Do not create a giant inventory before implementing the first foundation.
- Keep each completed slice functional and deployable.
- Each task must leave a short next-session steer if it is not complete.

## Validation Policy

Use lightweight validation for implementation slices:

- run JavaScript syntax checks for changed modules;
- perform manual browser testing for touched routes and component states;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation that was actually performed and materially relevant.
Do not maintain an exhaustive list of every possible validation command.

## Slice Assessment Requirement

Each implementation slice must end with a written assessment in this document.
The assessment should be specific enough that no separate state inventory is needed later.
The parent request is a design guide, not just a request for work.
Its sections are acceptance criteria for each slice.

For each completed slice, record:

- what legacy behavior was inspected;
- what behavior was preserved;
- what was normalized into the component contract;
- what the new component or module owns;
- what the route still owns;
- what was intentionally not changed;
- what specific improvement opportunities remain;
- whether any remaining issue blocks the architecture or is later cleanup;
- whether the component or module is good enough to continue the migration.

Each assessment must also include a parent-design acceptance checklist with concrete `yes` evidence against the key design principles.
Do not merely say that the parent request was followed.
Record evidence for each criterion.
The design principles are requirements, not suggestions.
If a criterion cannot be answered `yes`, the slice is not complete and the assessment must record the blocking correction needed before continuing.

Required acceptance checks:

- module-level refactor, not greenfield rewrite;
- legacy behavior was carefully inspected before contract design;
- working behavior was ported or adapted rather than redesigned line by line;
- public navigation, URL/query, route state, persistence, history, localStorage, link targets, and data schemas remain stable;
- completed slice leaves the site functional and deployable;
- ES module boundaries follow the target folder structure;
- no broad `utils.js`-style module was introduced;
- performance rules were respected, including no unnecessary loads or duplicate fetches introduced;
- component normalization uses a stable component contract rather than route-local forks;
- thumbnail grid/list remains one component family with grid/list modes;
- component CSS is owned in `catalogue.css` with component-owned selectors;
- search work, if touched, stays structural-only;
- validation stayed within syntax checks and manual browser testing unless a separate decision changed that.

Avoid vague risk language without a condition and action.
Do not write notes such as "this may become a maintenance problem and should be watched."

Use concrete follow-up triggers instead.
Example:

- `thumbnail-grid-list.js` currently owns pagination button rendering and page-state persistence. If the next route needs server-sized pages or infinite loading, split page-state persistence into `shared/page-state.js` before integrating that route.

## Slice 1: Thumbnail Grid/List Foundation

Purpose: create the first low-level component foundation and prove that the new structure can absorb a complex existing UI concept without changing public behavior.

Scope:

- create `site/assets/js/catalogue/routes/`;
- create `site/assets/js/catalogue/shared/`;
- create `site/assets/js/catalogue/components/`;
- create `site/assets/js/catalogue/navigation/`;
- create `site/assets/js/catalogue/search/`;
- create `site/assets/css/catalogue.css`;
- carefully inspect the existing thumbnail grid/list behavior in the relevant legacy route scripts;
- carefully inspect the relevant legacy grid/list CSS in `site/assets/css/main.css`;
- define the thumbnail grid/list component contract;
- define component-owned thumbnail grid/list CSS selectors;
- implement the first component modules under `components/` by porting or adapting existing working logic where it fits the contract;
- copy or adapt only the needed grid/list CSS into `catalogue.css` under the new component selectors;
- add only shared helpers required by the thumbnail grid/list component;
- do not switch every route;
- choose the first integration route only after the component contract is visible.

Out of scope:

- search payload optimization;
- generated catalogue data schema changes;
- public navigation redesign;
- broad route migration;
- automated smoke-test maintenance.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 1.1 | completed | Created `site/assets/js/catalogue/routes/`, `shared/`, `components/`, `navigation/`, and `search/`. Only behavior-bearing folders received modules; empty `navigation/` and `search/` are retained with `.gitkeep`. | No naming concern found. Keep adding files only when the ownership area has real behavior. |
| 1.2 | completed | Created `site/assets/css/catalogue.css` for public catalogue component CSS. | `main.css` remains the global stylesheet and still owns legacy selectors until their routes migrate. |
| 1.3 | completed | Inspected legacy thumbnail grid/list behavior in `site/assets/js/series-index.js`, `recent-index.js`, `works-index.js`, `work-page.js`, and the grid/list selectors in `main.css`. | The relevant behavior has been captured below; do not expand this slice into a broad route inventory. |
| 1.4 | completed | Defined the thumbnail grid/list component contract around normalized item data, grid/list modes, paging, item links, captions, current/selected state hooks, and `.catalogueGridList*` selectors. | No route-specific flags were needed. |
| 1.5 | completed | Implemented `components/thumbnail-grid-list.js`, focused shared modules, and component-owned CSS by porting/adapting the working series index grid/list logic. | Keep future component additions similarly focused; do not add a broad shared utility module. |
| 1.6 | completed | Selected `/series/` as the first integration route after the component contract was visible. Switched it to `catalogue/routes/series-index.js` and removed the obsolete legacy `site/assets/js/series-index.js`. | Continue with another foundation or a route that can reuse this component without broad migration. |

## Completed Verification

- JavaScript syntax checks passed with `node --check` for:
  - `site/assets/js/catalogue/shared/text.js`
  - `site/assets/js/catalogue/shared/fetch-json.js`
  - `site/assets/js/catalogue/shared/catalogue-urls.js`
  - `site/assets/js/catalogue/shared/local-storage.js`
  - `site/assets/js/catalogue/shared/thumbnails.js`
  - `site/assets/js/catalogue/components/thumbnail-grid-list.js`
  - `site/assets/js/catalogue/routes/series-index.js`
- `bin/site-validate` passed after the route switch and after removing the obsolete legacy script: `54 required files; 9 required directories; 44 Docs Viewer runtime modules`.
- `git diff --check` passed.
- Manual browser validation against `http://127.0.0.1:4000` covered:
  - `/series/` loads `catalogue/routes/series-index.js` as a module and no longer loads `public-catalogue-runtime.js` or legacy `series-index.js`;
  - grid mode renders 80 items on page 1 and page 2 paging renders the remaining items;
  - list mode switches with `aria-pressed` state and persists across reload;
  - grid page state persists across reload;
  - `/series/?mode=moments` updates URL state, disables the recent link, and renders moment links;
  - `/series/?series=105` renders selected-series work links such as `/works/?series=105&work=00008`;
  - no browser console errors were reported.
- Automated browser smoke tests were not run, per the slice validation policy.

## Slice 1 Assessment

- Legacy behavior inspected:
  - `series-index.js` owned the active grid/list implementation, including stored mode/view/sort/page state, sort comparison, series/moments payload fetches, thumbnail URL construction, list card rendering, grid thumbnail rendering, view toggles, pager wrapping, mode switching, recent-link disabling, and error/empty states.
  - `recent-index.js` showed the current compact thumbnail list pattern with date, thumbnail, title, caption, and placeholder behavior.
  - `works-index.js` showed route-owned list sorting and URL persistence that should not be pulled into the thumbnail component.
  - `work-page.js` showed another `seriesGrid` thumbnail use for detail links, confirming the component should support link-only grid thumbnails without route-specific flags.
  - `main.css` selectors inspected included `.seriesIndexItem*`, `.recentIndexItem*`, `.workIndexItem*`, `.seriesGrid*`, `.gridPager*`, and `.seriesIndex__pager--list`.
- Behavior preserved:
  - `/series/`, `/series/?mode=moments`, and `/series/?series=...` URL/query behavior remains stable.
  - Existing localStorage keys for mode, view, sort, and page state remain unchanged, including legacy read keys for view/sort/page migration.
  - Sort keys, sort directions, numeric-aware title fallback, year fallback, page size `80`, wrapping pager behavior, moment links, selected-series work links, recent-link disabling, empty text, and fetch targets remain stable.
  - Generated data schemas remain unchanged.
- Normalized into the component contract:
  - Thumbnail grid/list rendering now receives normalized items with `id`, `title`, `caption`, `href`, `thumbnail`, and optional `current`/`selected` state.
  - Grid and list are one component family with `grid` and `list` modes, not separate route-local renderers.
  - Paging buttons, pager status, page clamping, page wrapping, image attributes, image error placeholders, item link DOM, captions, and component-owned selectors moved into `thumbnail-grid-list.js`.
- New component/module ownership:
  - `components/thumbnail-grid-list.js` owns the reusable DOM contract for thumbnail grid/list items, image fallback placeholders, mode visibility, and pager rendering/interaction.
  - `shared/fetch-json.js`, `shared/catalogue-urls.js`, `shared/local-storage.js`, `shared/text.js`, and `shared/thumbnails.js` own narrow primitives needed by the route and component.
  - `catalogue.css` owns `.catalogueGridList*` component selectors.
  - `routes/series-index.js` owns only the `/series/` route bootstrapping, route state, payload selection, sorting, toolbar wiring, and persistence keys.
- Intentionally not changed:
  - Public route URLs, generated catalogue payloads, search runtime/payloads, global navigation, toolbar visual design, sort semantics, and other catalogue routes were not changed.
  - Legacy grid/list selectors remain in `main.css` because `work-page.js`, `recent-index.js`, `works-index.js`, and other routes still depend on legacy CSS.
- Improvement opportunities:
  - `routes/series-index.js` still owns more than the desired end-state route entrypoint. This is acceptable for Slice 1 because reusable grid/list DOM and pager behavior moved to `thumbnail-grid-list.js`, but later slices should reduce the route file when reuse creates a clear owner.
  - If another route needs the same year/title sort semantics, extract sort normalization and comparison from `routes/series-index.js` into a focused shared sorting module before integrating that route.
  - If another route or component needs the same mode/view/page localStorage behavior, extract the persistence contract from `routes/series-index.js` into a focused shared state module before integrating that route.
  - If the image and caption foundation is next, move thumbnail/media projection out of `routes/series-index.js` into the agreed media/image modules before adding a second route that builds the same thumbnail data.
  - If another route needs similar view-mode toolbar controls, extract only the reusable toolbar control wiring after comparing that route's current behavior; do not extract it preemptively.
  - If the next migrated route needs date/prefix columns like `recentIndexItem`, extend the normalized item contract with a neutral `prefix` slot before integrating that route.
  - If the next migrated route needs keyboard, swipe, or previous/next behavior, create a focused module under `navigation/` before switching the route.
  - If `work-page.js` detail grids migrate next, reuse `thumbnail-grid-list.js` in grid mode and keep metadata/detail payload parsing route-owned.
  - Remove legacy selectors from `main.css` only after the routes that still use them have been switched and verified.
- Remaining issues:
  - No remaining issue blocks the architecture. The empty `navigation/` and `search/` folders are placeholders for later ownership areas and contain no runtime behavior.
- Continue decision:
  - The component is good enough to continue the migration. It absorbed the complex `/series/` grid/list behavior without route-specific flags and left the public site deployable.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required | yes - `/series/` was switched to new ES module boundaries while preserving the existing behavior reference; obsolete `site/assets/js/series-index.js` was removed only after the route no longer loaded it. |
| Legacy behavior inspected before contract design | yes required | yes - the assessment records inspected behavior from `series-index.js`, `recent-index.js`, `works-index.js`, `work-page.js`, and relevant `main.css` selectors. |
| Working behavior ported/adapted rather than redesigned line by line | yes required | yes - sorting, paging, storage keys, fetch targets, route mode handling, and link generation were ported from the legacy route into focused route/shared/component modules. |
| Public route/navigation/data contracts remain stable | yes required | yes - manual checks covered `/series/`, `/series/?mode=moments`, `/series/?series=105`, persisted view/page state, link targets, and unchanged generated payload schemas. |
| Completed slice leaves site functional and deployable | yes required | yes - `bin/site-validate` passed and manual browser validation found no console errors. |
| ES module boundaries follow target folder structure | yes required | yes - route code lives in `catalogue/routes/`, reusable DOM in `components/`, narrow primitives in `shared/`, and empty future ownership folders exist for `navigation/` and `search/`. |
| No broad `utils.js`-style module introduced | yes required | yes - shared modules are named for one responsibility each: fetch, URL construction, local storage, text normalization, and thumbnails. |
| Performance rules respected | yes required | yes - `/series/` now loads the new route module and no longer loads the old global public runtime or legacy route script; no duplicate fetches were introduced. |
| Component normalization uses stable component contract | yes required | yes - the component receives normalized item data and owns DOM/pager rendering without route-specific flags. |
| Thumbnail grid/list remains one component family with grid/list modes | yes required | yes - `thumbnail-grid-list.js` renders both `grid` and `list` modes under the `.catalogueGridList*` selector family. |
| Component CSS is owned in `catalogue.css` with component-owned selectors | yes required | yes - `.catalogueGridList*` selectors live in `site/assets/css/catalogue.css`; legacy selectors remain in `main.css` for unmigrated routes. |
| Search, if touched, stays structural-only | yes required | yes - search runtime and payload behavior were not touched; only the empty future `catalogue/search/` ownership folder was created. |
| Validation stayed within agreed policy | yes required | yes - syntax checks, `bin/site-validate`, `git diff --check`, and manual browser testing were run; automated browser smoke tests were not run. |

## Follow-On

After Slice 1, decide whether the next foundation should be navigation, image and image caption, or metadata panel based on what the grid/list work exposes.
Do not run a standalone cleanup pass over `routes/series-index.js` just because it is large; split it when the next route or foundation provides a concrete reuse trigger and destination owner.
