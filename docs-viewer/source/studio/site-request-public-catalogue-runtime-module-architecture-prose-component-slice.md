---
doc_id: site-request-public-catalogue-runtime-module-architecture-prose-component-slice
title: Public Catalogue Runtime Prose Component Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Prose Component Slice

Status:

- completed

## Purpose

Track the prose/body component slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Moments Route Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-moments-route-slice).

Selected work pages and selected moment pages both render trusted generated `content_html` into constrained prose/body regions. That reuse is now real enough to justify a small catalogue component. This slice should extract only the repeated prose HTML rendering and associated CSS ownership without changing the trusted payload contract or route-specific browse/index rendering.

## Steer

- Treat selected-work prose and selected-moment body rendering as the behavior reference.
- Build a focused prose component, not a rich-text renderer or content utility bucket.
- Preserve trusted `content_html` behavior exactly.
- Do not sanitize, parse, transform, or rewrite generated HTML in this slice.
- Preserve selected-work empty prose behavior: hide the prose section when `content_html` is missing or blank.
- Preserve selected-moment body behavior: render trusted moment body HTML into the body region for selected moments.
- Keep moments browse/index rendering route-owned.
- Keep unavailable/error text route-owned unless a narrow prose component method clearly preserves existing behavior.
- Move component-owned prose CSS from `main.css` to `catalogue.css` using component-owned selectors.
- Keep generated catalogue data schemas stable.
- Keep the completed slice functional and deployable.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- run `bin/site-validate`;
- perform manual browser testing for selected work prose, selected moment prose, and moments browse mode;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 7: Prose Component

Purpose: extract trusted generated prose/body HTML rendering and component-owned prose CSS for selected works and selected moments.

Scope:

- inspect current prose/body behavior in:
  - `site/assets/js/catalogue/routes/work-page.js`;
  - `site/assets/js/catalogue/routes/moment-page.js`;
  - `site/works/index.html`;
  - `site/moments/index.html`;
  - relevant CSS in `site/assets/css/main.css` and `site/assets/css/catalogue.css`;
- create `site/assets/js/catalogue/components/prose-content.js`;
- define a compact component contract for:
  - trusted generated HTML;
  - blank/empty HTML state;
  - optional root visibility;
  - no transformation of supplied HTML;
- integrate selected-work prose rendering with the component;
- integrate selected-moment body rendering with the component;
- leave moments browse/index DOM rendering route-owned;
- move prose component CSS to `catalogue.css` with selectors such as `.catalogueProse` and route-specific modifiers where needed;
- remove old prose selectors from `main.css` after no route uses them;
- register the new component in `site-tools/config/site-tools.json`.

Out of scope:

- sanitizing generated HTML;
- parsing or rewriting `content_html`;
- redesigning prose typography, spacing, or page layout;
- moving moments browse/index list rendering into the prose component;
- changing work or moment payload schemas;
- changing markdown/projection generation;
- metadata panel extraction;
- navigation extraction;
- public search runtime or payload changes;
- automated smoke-test maintenance.

## Candidate Module Ownership

The exact filenames should follow the implementation, but ownership should stay narrow:

- `components/prose-content.js` owns trusted prose HTML insertion, empty state handling, and optional root visibility.
- `routes/work-page.js` owns selected-work payload loading, selected-work route state, and the decision to render or hide prose for a work.
- `routes/moment-page.js` owns selected/browse mode, moment payload loading, browse/index DOM rendering, unavailable text, and the decision to render selected moment body HTML.
- `catalogue.css` owns prose component selectors and any selected-work or moment prose modifiers.
- `main.css` keeps global site primitives and non-catalogue styles only after prose selectors are moved.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 7.1 | completed | Inspect current selected-work prose, selected-moment body, moments browse, and prose CSS behavior. | Preserved trusted HTML and route-specific browse/error handling. |
| 7.2 | completed | Define the prose component contract and CSS selector ownership. | Kept the contract narrow: trusted HTML insertion, empty state, and optional root visibility. |
| 7.3 | completed | Implement `components/prose-content.js`. | Component sets trusted HTML as-is and supports hidden empty state. |
| 7.4 | completed | Integrate selected-work prose rendering with the component. | Preserved section hidden state for missing/blank `content_html`. |
| 7.5 | completed | Integrate selected-moment body rendering with the component. | Preserved selected moment body HTML while leaving browse/index rendering route-owned. |
| 7.6 | completed | Move prose CSS into `catalogue.css`, update route shell classes, and remove unused legacy selectors from `main.css`. | Added `catalogueProse` selectors and removed stale `content`, `moment-body`, and `work__prose` selectors. |
| 7.7 | completed | Update validation config, verify routes, and record completed evidence. | Completed in this document. |

## Completed Verification

- `node --check site/assets/js/catalogue/components/prose-content.js`
- `node --check site/assets/js/catalogue/routes/work-page.js`
- `node --check site/assets/js/catalogue/routes/moment-page.js`
- `bin/site-validate`
  - passed: `Site validation passed: 60 required files; 9 required directories; 44 Docs Viewer runtime modules`
- Manual browser verification against `http://127.0.0.1:8176`:
  - `/works/?work=00008&prosecheck=1` renders selected-work trusted prose with 8 paragraphs in `catalogueProse catalogueProse--work`, keeps `catalogue.css`, and has no console errors.
  - `/works/?work=00001&prosecheck=1` keeps selected-work prose hidden and empty when `content_html` is absent, with no console errors.
  - `/moments/?moment=a-lemon-tart-poem&prosecheck=1` renders selected-moment trusted body HTML in `catalogueProse catalogueProse--moment`, keeps `pre.moment-text` as `pre-wrap`, and has no console errors.
  - `/moments/?prosecheck=1` keeps moments browse rendering route-owned, with 56 index links in the same body container and no console errors.
- Automated browser smoke tests were not run, per this slice's validation policy.

## Slice 7 Assessment

- Added `site/assets/js/catalogue/components/prose-content.js` as the focused owner for trusted generated prose HTML insertion, blank state handling, and optional root visibility.
- Updated selected-work prose rendering in `routes/work-page.js` to use the component while preserving hidden state for absent or blank `content_html`.
- Updated selected-moment body rendering in `routes/moment-page.js` to use the component while leaving moments browse/index and unavailable/error text route-owned.
- Updated `site/works/index.html` and `site/moments/index.html` to use `catalogueProse` component selectors.
- Moved prose CSS from `main.css` to `catalogue.css`, including constrained prose measure, selected-work prose margin, selected-moment body spacing, prose link underline behavior, and `pre.moment-text` formatting.
- Removed unused public-route prose selectors from `main.css`: `.content`, `.content a`, `.moment-body`, `.work__prose`, and global `pre.moment-text`.
- Registered the new component in `site-tools/config/site-tools.json`.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required | Extracted repeated trusted prose insertion behind existing route behavior. |
| Current prose behavior inspected before component contract design | yes required | Inspected selected-work prose, selected-moment body, moments browse, and legacy CSS selectors before implementation. |
| Working behavior ported/adapted rather than redesigned line by line | yes required | Routes now pass trusted HTML into the component; visible content and empty states are preserved. |
| Public work and moment route contracts remain stable | yes required | Route URLs, payload paths, query state, and payload schemas were not changed. |
| Trusted `content_html` behavior remains stable | yes required | Component assigns supplied trusted HTML directly with no parsing, sanitizing, or transformation. |
| Selected-work empty prose state remains stable | yes required | Browser check confirmed absent work prose remains hidden and empty. |
| Moments browse/index rendering remains route-owned and stable | yes required | Browser check confirmed moments browse still renders route-owned index links. |
| Completed slice leaves site functional and deployable | yes required | Syntax checks, `bin/site-validate`, and browser checks passed. |
| Component boundary follows target folder structure | yes required | New component lives at `assets/js/catalogue/components/prose-content.js`. |
| No broad rich-text/utility module introduced | yes required | Component owns only trusted prose HTML insertion and empty/root visibility state. |
| Catalogue CSS ownership remains explicit | yes required | Prose component selectors now live in `catalogue.css`; stale route selectors were removed from `main.css`. |
| Search, if touched, stays structural-only | yes required | Search runtime and payloads were not touched. |
| Validation stayed within agreed policy | yes required | Ran syntax checks, site validation, and manual browser checks; did not run automated smoke tests. |

## Follow-On

After Slice 7, decide whether the remaining duplication points justify metadata panel extraction or navigation extraction into `catalogue/navigation/`.
