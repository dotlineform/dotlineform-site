---
doc_id: site-request-public-catalogue-runtime-module-architecture-moments-route-slice
title: Public Catalogue Runtime Moments Route Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Moments Route Slice

Status:

- planned

## Purpose

Track the moments route completion slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Primary Media Component Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-primary-media-slice).

The primary-media slice integrated moments through a dynamic component import from the classic `site/assets/js/moment.js` script. That was an acceptable bridge for the component extraction, but it should not be the final runtime shape. This slice should make moments a first-class catalogue route module while preserving current public behavior.

## Steer

- Treat the current moments route as the behavior reference.
- Migrate moments to the catalogue ES module route structure.
- Keep public moments URLs and query behavior stable.
- Preserve selected moment rendering, browse rendering, moment dates, body HTML rendering, back-link behavior, and unavailable/error behavior.
- Preserve unlinked moment primary media behavior from the primary-media slice.
- Preserve moment primary media captions and external-image handling.
- Preserve `catalogue.css` as the owner of catalogue component and moment primary-media CSS.
- Keep generated moments data schemas stable.
- Keep this slice focused on the moments route; do not fold in search, navigation extraction, metadata-panel work, or broader CSS cleanup.
- Delete or retire the legacy `moment.js` script only after no route loads it.
- Keep the completed slice functional and deployable.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- run `bin/site-validate`;
- perform manual browser testing for moments browse and selected-moment states;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 6: Moments Route Completion

Purpose: migrate moments from the classic script bridge to a catalogue ES module route while preserving existing moments behavior and component ownership.

Scope:

- inspect current moments behavior in:
  - `site/assets/js/moment.js`;
  - `site/moments/index.html`;
  - `site/assets/js/public-catalogue-runtime.js` helpers used by moments;
  - `site/assets/css/main.css` moment route styles;
  - `site/assets/css/catalogue.css` primary-media component styles;
- create `site/assets/js/catalogue/routes/moment-page.js`;
- move route bootstrapping, route-state reading, selected moment loading, browse loading, date formatting, metadata rendering, body rendering, and back-link wiring into the module route;
- keep the primary-media component integration static from the route module rather than dynamic from a classic script;
- keep moment-specific data normalization route-owned unless a narrow shared primitive is already established and appropriate;
- keep current local data paths:
  - selected moments load from `assets/moments/index/<moment_id>.json`;
  - browse mode loads from `assets/data/moments_index.json`;
- keep selected moments driven by the existing `moment` query parameter and route data fallback;
- update `site/moments/index.html` to load the module route and keep required route data attributes;
- keep `catalogue.css` loaded on the moments route;
- register the new route module in `site-tools/config/site-tools.json`;
- remove `site/assets/js/moment.js` only if no public route still loads it and site validation passes.

Out of scope:

- changing whether moment primary images open a full-size asset;
- redesigning moments browse or selected moment layout;
- changing moment prose/body HTML rendering semantics;
- changing moment JSON schemas or generated data;
- extracting date formatting or body rendering into broad shared helpers unless another route already requires the exact same primitive;
- public search runtime or payload changes;
- navigation extraction;
- metadata panel extraction;
- broad `main.css` cleanup beyond CSS directly needed to complete the moments route migration;
- automated smoke-test maintenance.

## Candidate Module Ownership

The exact filenames should follow the implementation, but ownership should stay narrow:

- `routes/moment-page.js` owns moments route bootstrapping, mode selection, payload loading, moment-specific normalization, date display, body rendering, back-link wiring, unavailable state, and composition of components.
- `components/primary-media.js` continues to own primary image DOM, optional caption DOM, image attributes, and hidden media state.
- `shared/fetch-json.js`, `shared/text.js`, and `shared/catalogue-urls.js` may be used where their current contracts fit without adding route flags.
- `public-catalogue-runtime.js` remains a compatibility source only until the route no longer needs classic global helpers.
- `catalogue.css` owns catalogue component CSS and moment primary-media CSS.
- `main.css` may continue to own broader moment prose, page, and global site styles unless this slice proves a selector is strictly part of the catalogue component contract.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 6.1 | planned | Inspect current moments selected and browse behavior, including data attributes, payload paths, date formatting, body rendering, back-link behavior, primary media, and CSS dependencies. | Capture behavior before changing the route shell. |
| 6.2 | planned | Define the moments route module contract and decide which current runtime helpers should be imported versus kept route-owned. | Avoid creating broad shared helpers for one route. |
| 6.3 | planned | Implement `routes/moment-page.js` as the ES module entrypoint. | Use static imports for established catalogue modules and keep payload fetches route-specific. |
| 6.4 | planned | Update `site/moments/index.html` to load the module route and keep required `catalogue.css` and route data attributes. | Preserve public URL and visible behavior. |
| 6.5 | planned | Retire `site/assets/js/moment.js` if no route loads it after migration. | Delete only after validation confirms no remaining references. |
| 6.6 | planned | Update site validation config for the new route module and removed legacy script. | Keep validation config aligned with deploy-root runtime files. |
| 6.7 | planned | Verify selected moment and browse mode in browser and record completed evidence. | Include exact routes and only checks actually performed. |

## Completed Verification

- Not started.

## Slice 6 Assessment

- Not started.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required |  |
| Current moments behavior inspected before route contract design | yes required |  |
| Working behavior ported/adapted rather than redesigned line by line | yes required |  |
| Public moments route, query, navigation, and data contracts remain stable | yes required |  |
| Selected moment rendering remains stable | yes required |  |
| Moments browse rendering remains stable | yes required |  |
| Unlinked moment primary media remains stable | yes required |  |
| Moment captions and external-image behavior remain stable | yes required |  |
| Completed slice leaves site functional and deployable | yes required |  |
| ES module route boundary follows target folder structure | yes required |  |
| No broad `utils.js`-style or route-flag-heavy shared module introduced | yes required |  |
| Performance rules respected | yes required |  |
| Catalogue CSS ownership remains explicit | yes required |  |
| Search, if touched, stays structural-only | yes required |  |
| Validation stayed within agreed policy | yes required |  |

## Follow-On

After Slice 6, decide whether the remaining duplication points justify extracting `work.js` and `swipe-nav.js` navigation behavior into `catalogue/navigation/`, or whether metadata panel extraction should come first.
