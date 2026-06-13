---
doc_id: site-request-public-catalogue-runtime-module-architecture-navigation-slice
title: Public Catalogue Runtime Navigation Module Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Navigation Module Slice

Status:

- completed

## Purpose

Track the focused navigation module slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Metadata Panel Component Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-metadata-panel-slice).

The legacy `site/assets/js/work.js` still owns two unrelated concerns: selected-work series navigation/back-link projection and arrow-key navigation for selected works and work details. This slice should move those concerns into focused catalogue navigation modules and retire `work.js` without changing navigation semantics.

## Steer

- Treat current `work.js` behavior as the behavior reference.
- Retire `work.js` by extracting its behavior into ES modules under `site/assets/js/catalogue/navigation/`.
- Preserve selected-work series link projection, selected-work back-link label projection, series previous/next links, and series counters.
- Preserve selected-work and work-detail ArrowLeft/ArrowRight keyboard navigation.
- Preserve current navigation link IDs and route URL/query semantics.
- Keep `swipe-nav.js` ownership unchanged in this slice unless a narrow integration change is unavoidable.
- Keep `/works/` index behavior stable; do not migrate `works-index.js` or public runtime usage for works index in this slice.
- Do not change selected-work or work-detail metadata fields, primary media, prose, search, or generated data schemas.
- Keep the completed slice functional and deployable.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- run `bin/site-validate`;
- perform manual browser testing for selected-work series navigation and work-detail keyboard navigation;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 9: Navigation Modules

Purpose: extract `work.js` selected-work series navigation and keyboard navigation into focused catalogue navigation modules.

Scope:

- inspect current behavior in:
  - `site/assets/js/work.js`;
  - `site/assets/js/catalogue/routes/work-page.js`;
  - `site/assets/js/catalogue/routes/work-detail-page.js`;
  - `site/works/index.html`;
  - `site/work-details/index.html`;
  - `site/assets/js/public-catalogue-runtime.js` helper behavior used by `work.js`;
- create focused modules under `site/assets/js/catalogue/navigation/`, expected candidates:
  - `keyboard-navigation.js`;
  - `work-series-navigation.js`;
- integrate selected-work route with the selected-work series navigation module;
- integrate selected-work and work-detail routes with the keyboard navigation module;
- remove `site/assets/js/work.js` script tags from route shells;
- delete `site/assets/js/work.js` after no public route loads it;
- remove `public-catalogue-runtime.js` from work-detail shell if no remaining script on that page needs it;
- keep `public-catalogue-runtime.js` on works shell while `works-index.js` still depends on it;
- register new modules in `site-tools/config/site-tools.json`.

Out of scope:

- migrating `works-index.js`;
- migrating `recent-index.js`;
- migrating or deleting `public-catalogue-runtime.js` globally;
- migrating `swipe-nav.js`;
- changing selected-work series navigation semantics;
- changing work-detail detail navigation semantics;
- changing keyboard shortcut keys;
- changing back-link semantics;
- metadata, primary-media, or prose component changes;
- public search runtime or payload changes;
- automated smoke-test maintenance.

## Candidate Module Ownership

The exact filenames should follow the implementation, but ownership should stay narrow:

- `navigation/keyboard-navigation.js` owns ArrowLeft/ArrowRight keyboard binding and safe typing-target checks.
- `navigation/work-series-navigation.js` owns selected-work series-link projection, selected-work back-link label projection, selected-work series previous/next links, and selected-work series counters.
- `routes/work-page.js` owns selected-work payload loading, selected-work metadata extraction, selected-work route state, and composition of navigation modules.
- `routes/work-detail-page.js` owns detail navigation link projection and only imports the keyboard navigation module for key binding.
- `swipe-nav.js` remains the temporary owner of swipe behavior until a later focused slice.
- `public-catalogue-runtime.js` remains loaded only where remaining legacy scripts need it.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 9.1 | completed | Inspect `work.js` behavior, helper dependencies, route shell script order, and selected-work/work-detail navigation IDs. | Confirmed legacy selected-work behavior depended on `public-catalogue-runtime.js` projections and current DOM IDs. |
| 9.2 | completed | Define focused keyboard and selected-work series navigation module contracts. | Added narrow `keyboard-navigation.js` and `work-series-navigation.js` contracts. |
| 9.3 | completed | Implement navigation modules under `catalogue/navigation/`. | Ported projection behavior from `work.js`/runtime without changing URL or ID semantics. |
| 9.4 | completed | Integrate selected-work route with selected-work series navigation and keyboard navigation. | `work-page.js` composes the new modules after route state and metadata are available. |
| 9.5 | completed | Integrate work-detail route with keyboard navigation. | `work-detail-page.js` imports only keyboard navigation; detail link projection remains route-owned. |
| 9.6 | completed | Remove `work.js` script tags, retire `work.js`, and update validation config. | Removed route shell script tags, deleted `work.js`, kept public runtime on `/works/` for `works-index.js`, and removed it from `/work-details/`. |
| 9.7 | completed | Verify selected-work and work-detail navigation behavior and record evidence. | See Completed Verification. |

## Completed Verification

- `node --check site/assets/js/catalogue/navigation/keyboard-navigation.js`
- `node --check site/assets/js/catalogue/navigation/work-series-navigation.js`
- `node --check site/assets/js/catalogue/routes/work-page.js`
- `node --check site/assets/js/catalogue/routes/work-detail-page.js`
- `bin/site-validate`
- Browser check at `http://127.0.0.1:8176/works/?work=00001&series=009&navcheck=1`:
  - selected-work series navigation was visible;
  - counter rendered `1/4`;
  - previous link was `/works/?series=009&work=00004`;
  - next link was `/works/?series=009&work=00002`;
  - series link rendered `a poem divided into 4 parts` and linked to `/series/?series=009`;
  - back link rendered `← a poem divided into 4 parts` and linked to `/series/?series=009`;
  - script list included `public-catalogue-runtime.js`, `work-page.js`, and `works-index.js`, but not `work.js`;
  - ArrowRight navigated to `/works/?series=009&work=00002`.
- Browser check at `http://127.0.0.1:8176/work-details/?detail=00001-001&from_work=00001&from_work_title=Smoke&section=00001-1&details_section=00001-1&series=009&navcheck=1`:
  - work-detail navigation was visible;
  - counter rendered `1/17`;
  - previous link targeted detail `00001-017`;
  - next link targeted detail `00001-002`;
  - script list included `swipe-nav.js` and `work-detail-page.js`, but not `public-catalogue-runtime.js` or `work.js`;
  - ArrowRight navigated to detail `00001-002`.
- Browser console error check returned no errors after the work-detail browser check.

## Slice 9 Assessment

- Completed. Selected-work series navigation and shared ArrowLeft/ArrowRight behavior now live under `site/assets/js/catalogue/navigation/`.
- `site/assets/js/work.js` is retired, and the empty navigation-directory placeholder was removed.
- `/work-details/` no longer loads the public runtime; `/works/` still loads it because `works-index.js` remains a legacy consumer outside this slice.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | met | Extracted legacy behavior into two focused modules and route composition. |
| Current `work.js` behavior inspected before module contract design | met | Compared helper projections and keyboard binding before integration. |
| Working behavior ported/adapted rather than redesigned line by line | met | URL projections, IDs, hidden states, and ArrowLeft/ArrowRight behavior were preserved. |
| Public work and work-detail navigation contracts remain stable | met | Browser checks confirmed rendered links and counters on both routes. |
| Selected-work series navigation remains stable | met | Browser check confirmed `/series/` and `/works/` URL semantics. |
| Work-detail keyboard navigation remains stable | met | Browser check confirmed ArrowRight moves from detail `00001-001` to `00001-002`. |
| Existing navigation IDs remain stable | met | Routes still use `seriesNav*`, `workSeriesLink*`, `pageBackLink`, and `detailNav*` IDs. |
| `work.js` retired only after route shells stop loading it | met | Removed script tags from `/works/` and `/work-details/`, then deleted `work.js`. |
| Completed slice leaves site functional and deployable | met | Syntax checks and `bin/site-validate` passed. |
| Navigation module boundary follows target folder structure | met | Added modules under `site/assets/js/catalogue/navigation/`. |
| No broad navigation utility bucket introduced | met | Added one keyboard module and one selected-work series module only. |
| Performance rules respected | met | No additional generated data fetches beyond the existing selected-work series index fetch. |
| Search, if touched, stays structural-only | not touched | Search runtime was not changed. |
| Validation stayed within agreed policy | met | Used syntax checks, site validation, and manual browser checks; no automated browser smoke tests. |

## Follow-On

After Slice 9, decide whether to migrate `swipe-nav.js` into `catalogue/navigation/`, migrate `works-index.js`, or continue retiring remaining `public-catalogue-runtime.js` consumers.
