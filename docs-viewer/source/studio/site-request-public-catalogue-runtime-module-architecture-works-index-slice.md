---
doc_id: site-request-public-catalogue-runtime-module-architecture-works-index-slice
title: Public Catalogue Runtime Works Index Route Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Works Index Route Slice

Status:

- planned

## Purpose

Track the focused works-index route slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Swipe Navigation Module Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-swipe-navigation-slice).

The `/works/` shell now mixes the new selected-work route module with the legacy `site/assets/js/works-index.js` classic script. That legacy script is the reason `/works/` still loads `site/assets/js/public-catalogue-runtime.js`. This slice should migrate the works index behavior into an ES module route and remove the `/works/` dependency on the public runtime, without changing the visible list behavior or selected-work behavior.

## Steer

- Treat current `site/assets/js/works-index.js` behavior as the behavior reference.
- Preserve the `?work=...` short-circuit so the list route does not render over the selected-work route.
- Preserve current DOM IDs and CSS classes:
  - `worksIndexRoot`;
  - `worksEmpty`;
  - `worksList`;
  - `worksListCount`;
  - `worksIndexBackNav`;
  - `worksIndexBackLink`;
  - `.worksList__sortBtn`;
  - `.worksList__item`;
  - `.worksList__cat`;
  - `.worksList__year`;
  - `.worksList__title`;
  - `.worksList__series`;
  - `.worksList__sortIcon`.
- Preserve list data sources:
  - `/assets/data/works_index.json`;
  - `/assets/data/series_index.json`, optional fallback to `null` on fetch failure.
- Preserve sort keys and query semantics:
  - `sort=cat|year|title|series`;
  - internal `seriessort` behavior for series-filtered views;
  - `dir=asc|desc`;
  - `series=...`.
- Preserve series-filtered count/back-link behavior.
- Preserve return-state query params written into work links:
  - `from=works_index`;
  - `return_sort`;
  - `return_dir`;
  - `return_series` when filtered by series.
- Preserve row data attributes used by sorting.
- Remove `public-catalogue-runtime.js` from `site/works/index.html` only after the migrated works-index route no longer depends on it.
- Keep selected-work route behavior stable and avoid editing selected-work rendering unless shell script order requires a narrow adjustment.
- Do not migrate `recent-index.js` in this slice.
- Do not change generated data schemas, CSS, metadata, prose, primary media, navigation modules, search runtime, or selected-work payload rendering.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- run `bin/site-validate`;
- perform manual browser testing for:
  - unfiltered `/works/`;
  - series-filtered `/works/?series=009`;
  - sorted `/works/?sort=year&dir=desc`;
  - selected-work `/works/?work=00001&series=009`;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 11: Works Index Route Module

Purpose: migrate `works-index.js` into a focused ES module route and remove `/works/` from the remaining public-runtime consumers.

Scope:

- inspect current behavior in:
  - `site/assets/js/works-index.js`;
  - `site/works/index.html`;
  - `site/assets/js/catalogue/routes/work-page.js`;
  - shared helpers under `site/assets/js/catalogue/shared/`;
  - current works list CSS in `main.css`/`catalogue.css` only as needed for DOM contract awareness;
- create a focused route module, expected candidate:
  - `site/assets/js/catalogue/routes/works-index.js`;
- reuse existing shared helpers where they already match behavior:
  - `parseRouteState`;
  - `trimBaseurl`;
  - `catalogueIndexUrl`;
  - `workUrl`;
  - `worksIndexUrl`;
  - `seriesIndexUrl`;
  - `fetchJson`;
  - text normalization helpers;
- port or locally retain works-index-specific sorting helpers where they are not generally useful;
- update `site/works/index.html` to load the module route and remove the legacy classic script;
- remove `public-catalogue-runtime.js` from `site/works/index.html` after no remaining `/works/` script needs it;
- delete `site/assets/js/works-index.js` after the shell stops loading it;
- register the new route module in `site-tools/config/site-tools.json`.

Out of scope:

- migrating `recent-index.js`;
- deleting `site/assets/js/public-catalogue-runtime.js` globally;
- changing selected-work rendering or selected-work navigation behavior;
- changing works list markup, sort labels, visible text, or CSS classes;
- moving works-list CSS between `main.css` and `catalogue.css`;
- changing generated data schemas;
- adding thumbnails to the works index;
- changing search runtime behavior;
- automated smoke-test maintenance.

## Candidate Module Ownership

- `routes/works-index.js` owns `/works/` list boot, data loading, row rendering, sort state, URL persistence, series-filtered count/back-link projection, and work-link return params.
- `routes/work-page.js` continues to own selected-work rendering when `?work=...` is present.
- `shared/catalogue-urls.js` owns catalogue, works, work, and data URL construction.
- `shared/fetch-json.js` owns JSON fetch response validation.
- `shared/text.js` owns generic text and numeric normalization.
- `public-catalogue-runtime.js` remains available only for routes that still load legacy scripts, expected after this slice to be `recent-index.js`.

## Handoff / Steer Note

Start the implementation by preserving behavior, not by redesigning the list route.

Current `works-index.js` behavior observed before this doc was created:

- It exits immediately when `window.__dlfPublicCatalogueRuntime.parseRouteState(window.location).work` is truthy, so selected-work pages on `/works/?work=...` can use the same shell without the list route rendering.
- It requires `window.__dlfPublicCatalogueRuntime`; that dependency is the reason `site/works/index.html` still loads `public-catalogue-runtime.js`.
- It reads `baseurl` from `#selectedWorkRoot[data-baseurl]`.
- It fetches `works_index.json` and attempts `series_index.json`, treating series fetch failure as `null`.
- It builds list rows entirely in JS using the current `worksList__*` classes and row `data-*` attributes.
- It counts all rendered works and distinct primary series IDs for the unfiltered count.
- It uses the first `series_ids` entry as the primary series for display, filtering, and series links.
- It derives series metadata from `series_index.json`, including:
  - label;
  - `sort_fields`;
  - primary visual sort hint;
  - custom series sort detection;
  - rank map from the `series.works` order.
- It defaults sort to `cat` for unfiltered views and `seriessort` for `?series=...` views unless an explicit valid sort is present.
- It persists `sort` and `dir` into `history.replaceState` after initialization and sort clicks.
- It maps internal `seriessort` back to a visible active sort button using either `cat` or the series primary sort hint.
- It updates work title links with `from=works_index`, `return_sort`, `return_dir`, and optional `return_series`.
- It shows `worksIndexBackNav` only for series-filtered views and links back to `/series/?series=...`.

Implementation steer for the next session:

- Prefer moving the code into `site/assets/js/catalogue/routes/works-index.js` first, with small helper substitutions for shared URL/fetch/text functions.
- Keep works-index-specific sort helpers local unless a second route actually needs them.
- Wire the new module in `site/works/index.html` beside `work-page.js`; both route modules may load on `/works/`, but the works-index module must keep the `?work` short-circuit.
- Remove `public-catalogue-runtime.js` from the `/works/` shell only after browser verification proves selected-work and list states still work without it.
- Use exact route checks for both list and selected-work states before deleting the legacy script.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 11.1 | planned | Inspect `works-index.js`, `/works/` shell script order, selected-work coexistence, shared helper equivalents, and works-list CSS contracts. | Preserve route coexistence and DOM contracts. |
| 11.2 | planned | Define the works-index route module contract. | Keep route-specific sort/render helpers local; no global compatibility alias. |
| 11.3 | planned | Implement `catalogue/routes/works-index.js`. | Port behavior with shared helper substitutions only where exact enough. |
| 11.4 | planned | Update `/works/` shell script tags. | Load the new module and remove `public-catalogue-runtime.js` only when the route no longer needs it. |
| 11.5 | planned | Retire legacy `works-index.js` and update validation config. | Delete only after the shell stops loading it. |
| 11.6 | planned | Verify list, series-filtered, sorted, and selected-work `/works/` states. | Include exact routes and only checks actually performed. |

## Completed Verification

- Not started.

## Slice 11 Assessment

- Not started.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required |  |
| Current `works-index.js` behavior inspected before module contract design | yes required |  |
| Works index behavior ported without changing visible list contracts | yes required |  |
| Selected-work `/works/?work=...` route remains stable | yes required |  |
| Series-filtered works list remains stable | yes required |  |
| Sort query and history semantics remain stable | yes required |  |
| Work-link return params remain stable | yes required |  |
| Existing works-list IDs/classes remain stable | yes required |  |
| `works-index.js` retired only after route shell stops loading it | yes required |  |
| `/works/` no longer loads `public-catalogue-runtime.js` after migration | yes required |  |
| Completed slice leaves site functional and deployable | yes required |  |
| Route module boundary follows target folder structure | yes required |  |
| No global compatibility alias introduced | yes required |  |
| No broad utility bucket introduced | yes required |  |
| Performance rules respected | yes required |  |
| Search, if touched, stays structural-only | yes required |  |
| Validation stayed within agreed policy | yes required |  |

## Follow-On

After Slice 11, `recent-index.js` should be the clearest remaining public-runtime consumer. Decide whether to migrate `recent-index.js` next or audit `public-catalogue-runtime.js` for any remaining deploy-root callers before deleting it.
