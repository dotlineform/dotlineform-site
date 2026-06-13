---
doc_id: site-request-public-catalogue-runtime-module-architecture-moments-route-slice
title: Public Catalogue Runtime Moments Route Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Moments Route Slice

Status:

- completed

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
| 6.1 | completed | Inspect current moments selected and browse behavior, including data attributes, payload paths, date formatting, body rendering, back-link behavior, primary media, and CSS dependencies. | Captured the current classic route behavior before changing the shell. |
| 6.2 | completed | Define the moments route module contract and decide which current runtime helpers should be imported versus kept route-owned. | Used existing shared helpers where already narrow; kept moment-specific normalization, date formatting, and body rendering route-owned. |
| 6.3 | completed | Implement `routes/moment-page.js` as the ES module entrypoint. | Added static imports for catalogue URL/fetch/text/thumbnail helpers and the primary-media component. |
| 6.4 | completed | Update `site/moments/index.html` to load the module route and keep required `catalogue.css` and route data attributes. | Replaced classic runtime scripts with the module route while preserving route data attributes. |
| 6.5 | completed | Retire `site/assets/js/moment.js` if no route loads it after migration. | Deleted the legacy script after confirming no site or validation references remained. |
| 6.6 | completed | Update site validation config for the new route module and removed legacy script. | Added `assets/js/catalogue/routes/moment-page.js` to site validation config. |
| 6.7 | completed | Verify selected moment and browse mode in browser and record completed evidence. | Completed in this document. |

## Completed Verification

- `node --check site/assets/js/catalogue/routes/moment-page.js`
- `node --check site/assets/js/catalogue/shared/catalogue-urls.js`
- `bin/site-validate`
  - passed: `Site validation passed: 59 required files; 9 required directories; 44 Docs Viewer runtime modules`
- Manual browser verification against `http://127.0.0.1:8176`:
  - `/moments/?moment=a-lemon-tart-poem&routecheck=1` renders the selected moment title, date, unlinked primary media, responsive `srcset`, prose body HTML, visible back link to `/series/?mode=moments`, `catalogue.css`, and no console errors.
  - `/moments/?routecheck=1` renders browse mode with hidden primary media, hidden date, hidden back nav, 56 moment links from `assets/data/moments_index.json`, `catalogue.css`, and no console errors.
  - Both checked moments states load `/assets/js/catalogue/routes/moment-page.js?v=static` and no longer load `/assets/js/public-catalogue-runtime.js` or `/assets/js/moment.js`.
- Automated browser smoke tests were not run, per this slice's validation policy.

## Slice 6 Assessment

- Added `site/assets/js/catalogue/routes/moment-page.js` as the first-class ES module route for `/moments/`.
- Added `momentPayloadUrl()` to `site/assets/js/catalogue/shared/catalogue-urls.js`, matching the existing route URL helper boundary without reusing the legacy global runtime.
- Updated `site/moments/index.html` to load only the module route for moments while keeping route data attributes and `catalogue.css`.
- Deleted `site/assets/js/moment.js` after confirming no public route loads it.
- Registered the new route module in `site-tools/config/site-tools.json`.
- Preserved moment-specific normalization, selected/browse mode decisions, date formatting, body HTML rendering, back-link behavior, unavailable state, external image handling, caption handling, and unlinked primary media behavior.
- Did not extract prose/body rendering in this slice. Selected works also render prose, so a focused prose/body component is a reasonable follow-on foundation if it can preserve trusted `content_html` behavior without turning into a general rich-content utility.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required | Ported the current moments behavior into a route module and reused established shared helpers/components. |
| Current moments behavior inspected before route contract design | yes required | Inspected legacy `moment.js`, route shell, shared runtime helper equivalents, and CSS dependencies before implementation. |
| Working behavior ported/adapted rather than redesigned line by line | yes required | Selected and browse behavior were moved into the module route with current visible output preserved. |
| Public moments route, query, navigation, and data contracts remain stable | yes required | `/moments/?moment=...`, browse `/moments/`, payload paths, and back-link target remain stable. |
| Selected moment rendering remains stable | yes required | Browser check confirmed title, date, primary media, body HTML, and back-link behavior. |
| Moments browse rendering remains stable | yes required | Browser check confirmed browse title, hidden media/date/back nav, and indexed moment links. |
| Unlinked moment primary media remains stable | yes required | Browser check confirmed selected moment primary media has no wrapping link. |
| Moment captions and external-image behavior remain stable | yes required | Route preserves optional caption rendering and external-image `srcset` omission logic from the legacy route. |
| Completed slice leaves site functional and deployable | yes required | Syntax checks, `bin/site-validate`, and manual browser checks passed. |
| ES module route boundary follows target folder structure | yes required | New entrypoint lives at `assets/js/catalogue/routes/moment-page.js`. |
| No broad `utils.js`-style or route-flag-heavy shared module introduced | yes required | Added only `momentPayloadUrl()` to an existing URL helper; moment-specific behavior stayed route-owned. |
| Performance rules respected | yes required | Moments no longer downloads `public-catalogue-runtime.js` and `moment.js`; the route uses focused static imports. |
| Catalogue CSS ownership remains explicit | yes required | Moments keeps loading `catalogue.css`; no new CSS ownership changes were needed. |
| Search, if touched, stays structural-only | yes required | Search runtime and payloads were not touched. |
| Validation stayed within agreed policy | yes required | Ran syntax checks, site validation, and manual browser checks; did not run automated smoke tests. |

## Follow-On

After Slice 6, decide whether the remaining duplication points justify extracting `work.js` and `swipe-nav.js` navigation behavior into `catalogue/navigation/`, whether metadata panel extraction should come first, or whether selected-work and moment prose/body rendering should become a focused catalogue prose component.
