---
doc_id: site-request-public-catalogue-runtime-module-architecture-swipe-navigation-slice
title: Public Catalogue Runtime Swipe Navigation Module Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Swipe Navigation Module Slice

Status:

- completed

## Purpose

Track the focused swipe-navigation module slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Navigation Module Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-navigation-slice).

The legacy `site/assets/js/swipe-nav.js` is now the remaining navigation behavior outside `site/assets/js/catalogue/navigation/`. This slice should move that behavior into an ES module consumed by the work-detail route and remove the classic script/global helper path.

## Steer

- Treat current `swipe-nav.js` behavior as the behavior reference.
- Preserve `data-swipe-nav-zone="detail-media"` semantics.
- Preserve touch/pen horizontal swipe thresholds, ignored start targets, link normalization, click suppression, and no-op unsupported-pointer behavior.
- Keep detail previous/next URL projection owned by `routes/work-detail-page.js`.
- Keep keyboard navigation ownership unchanged.
- Remove the work-detail shell script tag after the route imports the new module.
- Do not change primary media rendering, metadata, prose, selected-work navigation, list/index runtimes, generated data schemas, or CSS unless directly required.
- Keep the completed slice functional and deployable.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- run `bin/site-validate`;
- perform manual browser testing for work-detail navigation module loading, detail previous/next links, keyboard navigation, and swipe binding state;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 10: Swipe Navigation Module

Purpose: move `swipe-nav.js` behavior into a focused ES module under `catalogue/navigation/`.

Scope:

- inspect current behavior in:
  - `site/assets/js/swipe-nav.js`;
  - `site/assets/js/catalogue/routes/work-detail-page.js`;
  - `site/work-details/index.html`;
  - current CSS for `data-swipe-nav-zone`;
- create a focused module under `site/assets/js/catalogue/navigation/`, expected candidate:
  - `swipe-navigation.js`;
- integrate `routes/work-detail-page.js` with the swipe navigation module;
- remove the `swipe-nav.js` script tag from `site/work-details/index.html`;
- delete `site/assets/js/swipe-nav.js` after no public route loads it;
- register the new module in `site-tools/config/site-tools.json`.

Out of scope:

- changing detail previous/next URL projection;
- changing keyboard navigation behavior;
- changing selected-work series navigation;
- changing pointer thresholds or gesture direction semantics;
- moving swipe CSS from `main.css`;
- migrating `works-index.js`;
- migrating `recent-index.js`;
- migrating or deleting `public-catalogue-runtime.js` globally;
- automated smoke-test maintenance.

## Candidate Module Ownership

- `navigation/swipe-navigation.js` owns touch/pen swipe recognition, ignored start targets, click suppression, control normalization, and link/action bind helpers.
- `routes/work-detail-page.js` owns the detail media zone lookup and provides previous/next link getters to the swipe module.
- `components/primary-media.js` continues to render the media link and `data-swipe-nav-zone` attribute passed by the route.
- `navigation/keyboard-navigation.js` remains the keyboard owner.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 10.1 | completed | Inspect `swipe-nav.js`, work-detail binding, shell loading, and swipe-zone CSS. | Confirmed the legacy script only served work-detail swipe behavior and the route was the only global helper consumer. |
| 10.2 | completed | Define the swipe module contract. | Added narrow bind helpers without a global compatibility alias. |
| 10.3 | completed | Implement `catalogue/navigation/swipe-navigation.js`. | Ported existing thresholds, ignored targets, click suppression, link/action normalization, and unsupported-pointer no-op behavior. |
| 10.4 | completed | Integrate work-detail route with the swipe module. | Work-detail imports the module and still owns detail previous/next link projection. |
| 10.5 | completed | Remove the legacy shell script, retire `swipe-nav.js`, and update validation config. | Removed the work-detail script tag, deleted `swipe-nav.js`, and registered the new module. |
| 10.6 | completed | Verify work-detail navigation behavior and record evidence. | See Completed Verification. |

## Completed Verification

- `node --check site/assets/js/catalogue/navigation/swipe-navigation.js`
- `node --check site/assets/js/catalogue/routes/work-detail-page.js`
- `bin/site-validate`
- `node --input-type=module -e "import { bindLinkSwipeZone, isSwipeNavigationSupported } from './site/assets/js/catalogue/navigation/swipe-navigation.js'; const zone = {}; const result = bindLinkSwipeZone(zone, {}); if (isSwipeNavigationSupported() !== false || result !== false || zone.__dlfSwipeNavUnsupported !== true) throw new Error('unsupported swipe path failed');"`
- Browser check at `http://127.0.0.1:8177/work-details/?detail=00001-001&from_work=00001&from_work_title=Smoke&section=00001-1&details_section=00001-1&series=009&navcheck=1`:
  - work-detail navigation was visible;
  - counter rendered `1/17`;
  - previous link targeted detail `00001-017`;
  - next link targeted detail `00001-002`;
  - route shell script list included `work-detail-page.js`, `site-nav.js`, and `theme-toggle.js`, but not `swipe-nav.js`;
  - no `window.__dlfSwipeNav` global was present;
  - `data-swipe-nav-zone="detail-media"` remained on the primary media link;
  - ArrowRight navigated to detail `00001-002`;
  - browser console error check returned no errors.
- The in-app browser reported `PointerEvent` unsupported, so a real touch/pen swipe gesture was not exercised in that browser check.

## Slice 10 Assessment

- Completed. Work-detail swipe behavior now lives in `site/assets/js/catalogue/navigation/swipe-navigation.js`.
- `site/assets/js/swipe-nav.js` is retired and no public route shell loads it.
- The new module keeps unsupported-pointer behavior as an explicit no-op and does not expose a global compatibility alias.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | met | Moved the existing behavior into a focused ES module and imported it from the route. |
| Current `swipe-nav.js` behavior inspected before module contract design | met | Legacy helper behavior and route usage were inspected before implementation. |
| Swipe behavior ported/adapted without changing thresholds or route semantics | met | Preserved the legacy thresholds, ignored targets, click suppression, and previous/next resolution. |
| Work-detail navigation contracts remain stable | met | Browser check confirmed previous/next links, counter, and ArrowRight navigation. |
| `data-swipe-nav-zone` contract remains stable | met | Browser check confirmed the detail media link still has `data-swipe-nav-zone="detail-media"`. |
| Keyboard navigation remains stable | met | Browser check confirmed ArrowRight still navigates to detail `00001-002`. |
| `swipe-nav.js` retired only after route shell stops loading it | met | Removed the work-detail script tag, then deleted `site/assets/js/swipe-nav.js`. |
| Completed slice leaves site functional and deployable | met | Syntax checks and `bin/site-validate` passed. |
| Navigation module boundary follows target folder structure | met | Added `site/assets/js/catalogue/navigation/swipe-navigation.js`. |
| No global compatibility alias introduced | met | Browser check confirmed no `window.__dlfSwipeNav` global. |
| No broad navigation utility bucket introduced | met | Added one focused swipe navigation module only. |
| Performance rules respected | met | No new data fetches or polling were introduced. |
| Search, if touched, stays structural-only | not touched | Search runtime was not changed. |
| Validation stayed within agreed policy | met | Used syntax checks, site validation, a focused unsupported-path assertion, and manual browser checks; no automated browser smoke tests. |

## Follow-On

After Slice 10, decide whether to migrate `works-index.js`, migrate `recent-index.js`, or continue retiring remaining `public-catalogue-runtime.js` consumers.
