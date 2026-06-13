---
doc_id: site-request-public-catalogue-runtime-module-architecture-metadata-panel-slice
title: Public Catalogue Runtime Metadata Panel Component Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Metadata Panel Component Slice

Status:

- completed

## Purpose

Track the metadata panel component slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Prose Component Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-prose-component-slice).

Selected work pages and work-detail pages both render compact metadata rows below primary media. Future catalogue surfaces, such as a series thumbnail page, may also need consistent metadata layout with different fields. This slice should extract the row layout, row rendering, and CSS ownership without creating a shared work/work-detail data model.

## Steer

- Treat current selected-work and work-detail metadata behavior as the behavior reference.
- Build a focused metadata panel component, not a catalogue schema abstraction.
- Component owns row layout, row DOM, hidden rows, text/link rendering, row separators, title-row layout, and CSS selectors.
- Routes own which fields exist, field order, labels, value derivation, link targets, and payload normalization.
- Preserve selected-work fields and behavior exactly: title, series navigation, year, medium, dimensions, cat number, series link, downloads, and links.
- Preserve work-detail fields and behavior exactly: title, detail navigation, and cat number.
- Keep `work.js` compatibility nodes present in the initial DOM until the navigation behavior is migrated.
- Do not migrate keyboard navigation, series/detail navigation projection, metadata payload schemas, prose, primary media, search, or generated data in this slice.
- Keep the completed slice functional and deployable.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- run `bin/site-validate`;
- perform manual browser testing for selected-work metadata and work-detail metadata;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 8: Metadata Panel Component

Purpose: extract compact metadata row rendering and component-owned metadata CSS while preserving route-owned field decisions.

Scope:

- inspect current metadata behavior in:
  - `site/assets/js/catalogue/routes/work-page.js`;
  - `site/assets/js/catalogue/routes/work-detail-page.js`;
  - `site/works/index.html`;
  - `site/work-details/index.html`;
  - relevant CSS in `site/assets/css/main.css` and `site/assets/css/catalogue.css`;
- create `site/assets/js/catalogue/components/metadata-panel.js`;
- define a compact component contract for:
  - rows with text segments;
  - rows with existing DOM nodes such as navigation controls or series-link wrappers;
  - rows with separated links;
  - title rows;
  - hidden/empty rows;
- integrate selected-work metadata with the component;
- integrate work-detail metadata with the component;
- move metadata component CSS to `catalogue.css` with selectors such as `.catalogueMetadata`, `.catalogueMetadata__rows`, `.catalogueMetadata__row`, and `.catalogueMetadata__titleRow`;
- remove old metadata-only selectors from `main.css` after no route uses them;
- register the new component in `site-tools/config/site-tools.json`.

Out of scope:

- changing selected-work or work-detail fields;
- changing field order or labels;
- changing route payload normalization;
- migrating `work.js`, keyboard navigation, series navigation, or detail navigation;
- metadata panel integration on series thumbnail/index pages;
- primary media or prose component changes;
- generated data schema changes;
- public search runtime or payload changes;
- automated smoke-test maintenance.

## Candidate Module Ownership

The exact filenames should follow the implementation, but ownership should stay narrow:

- `components/metadata-panel.js` owns metadata panel DOM creation, row layout primitives, hidden row handling, text/link segment rendering, link separators, and row class/modifier assignment.
- `routes/work-page.js` owns selected-work fields, labels, value derivation, download/link filtering, series-link target data, and route render order.
- `routes/work-detail-page.js` owns work-detail fields, title/detail UID values, detail navigation data, and route render order.
- `work.js` remains the temporary owner of series-link projection and keyboard navigation until a later navigation slice.
- `catalogue.css` owns metadata panel component selectors.
- `main.css` keeps global site primitives and non-catalogue styles only after metadata selectors are moved.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 8.1 | completed | Inspect selected-work and work-detail metadata DOM, route rendering, navigation dependencies, and CSS. | Preserved existing fields and kept `work.js` compatibility nodes discoverable in initial DOM. |
| 8.2 | completed | Define the metadata panel component contract and CSS selector ownership. | Routes remain responsible for field semantics and ordering. |
| 8.3 | completed | Implement `components/metadata-panel.js`. | Supports text segments, existing nodes, separated links, title rows, and hidden rows without route-specific flags. |
| 8.4 | completed | Integrate selected-work metadata with the component. | Preserved title/nav row, hidden optional rows, cat/series link row, downloads, and links. |
| 8.5 | completed | Integrate work-detail metadata with the component. | Preserved title/nav row and detail UID row. |
| 8.6 | completed | Move metadata CSS into `catalogue.css`, update route shell classes, and remove unused legacy selectors from `main.css`. | Removed stale `page__row`, `page__caption`, `page__metaList`, `work__titleRow`, and `work__titleMain` usage. |
| 8.7 | completed | Update validation config, verify routes, and record completed evidence. | Completed in this document. |

## Completed Verification

- `node --check site/assets/js/catalogue/components/metadata-panel.js`
- `node --check site/assets/js/catalogue/routes/work-page.js`
- `node --check site/assets/js/catalogue/routes/work-detail-page.js`
- `bin/site-validate`
  - passed: `Site validation passed: 61 required files; 9 required directories; 44 Docs Viewer runtime modules`
- Manual browser verification against `http://127.0.0.1:8176`:
  - `/works/?work=00008&metacheck=1` renders selected-work metadata in `catalogueMetadata` rows with title, year, medium, dimensions, cat/series link, one download link, hidden series nav, component CSS, and no console errors.
  - `/works/?work=00001&series=009&metacheck=1` renders selected-work metadata with visible series navigation, `1/4` counter, previous/next links, series link wrapper, component rows, and no console errors.
  - `/work-details/?detail=00001-001&from_work=00001&from_work_title=Smoke&section=00001-1&details_section=00001-1&series=009&metacheck=1` renders work-detail metadata with title/detail navigation row, `1/17` counter, detail UID row, component CSS, and no console errors.
- Automated browser smoke tests were not run, per this slice's validation policy.

## Slice 8 Assessment

- Added `site/assets/js/catalogue/components/metadata-panel.js` as the focused owner for metadata panel DOM creation, row classes, text segments, existing-node segments, separated links, title rows, and hidden rows.
- Updated `site/works/index.html` and `site/work-details/index.html` to expose metadata component roots and row containers while keeping `seriesNav`, `workSeriesLinkWrap`, and `detailNav` nodes present in the initial DOM for `work.js`.
- Updated `routes/work-page.js` so selected-work route code owns field definitions, value derivation, download/link filtering, and row order while delegating row DOM to the metadata component.
- Updated `routes/work-detail-page.js` so work-detail route code owns title/detail UID values and detail navigation while delegating row DOM to the metadata component.
- Moved compact metadata row CSS into `site/assets/css/catalogue.css` under `catalogueMetadata` selectors.
- Removed stale metadata-only selectors from `main.css`, including `page__row`, `page__caption`, `page__metaList`, `work__titleRow`, and `work__titleMain`.
- Registered the new component in `site-tools/config/site-tools.json`.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required | Extracted repeated metadata row DOM/CSS while preserving route-owned fields. |
| Current metadata behavior inspected before component contract design | yes required | Inspected selected-work and work-detail shells, route rendering, `work.js` dependencies, and CSS before implementation. |
| Working behavior ported/adapted rather than redesigned line by line | yes required | Existing fields now render through route-provided row definitions with current visible behavior preserved. |
| Public work and work-detail route contracts remain stable | yes required | URLs, query parameters, payload paths, and payload schemas were not changed. |
| Route-owned field semantics remain route-owned | yes required | Work and work-detail routes still decide fields, labels, values, links, and order. |
| Selected-work metadata behavior remains stable | yes required | Browser checks confirmed selected-work metadata rows, optional rows, series link, downloads, and series navigation. |
| Work-detail metadata behavior remains stable | yes required | Browser check confirmed detail title, detail UID, detail nav, and counter behavior. |
| Existing navigation nodes remain compatible with `work.js` | yes required | `seriesNav`, `workSeriesLinkWrap`, and `detailNav` remain in initial DOM and are moved into component rows at render time. |
| Completed slice leaves site functional and deployable | yes required | Syntax checks, `bin/site-validate`, and manual browser checks passed. |
| Component boundary follows target folder structure | yes required | New component lives at `assets/js/catalogue/components/metadata-panel.js`. |
| No broad schema/utility module introduced | yes required | Component knows only row/rendering primitives, not work/work-detail data semantics. |
| Catalogue CSS ownership remains explicit | yes required | Metadata row styles now live in `catalogue.css` under component selectors. |
| Search, if touched, stays structural-only | yes required | Search runtime and payloads were not touched. |
| Validation stayed within agreed policy | yes required | Ran syntax checks, site validation, and manual browser checks; did not run automated smoke tests. |

## Follow-On

After Slice 8, decide whether to migrate `work.js` and `swipe-nav.js` navigation behavior into `catalogue/navigation/`, or whether to apply the metadata panel to another catalogue surface when that surface needs metadata rows.
