---
doc_id: site-request-public-catalogue-runtime-module-architecture-primary-media-slice
title: Public Catalogue Runtime Primary Media Component Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
---
# Public Catalogue Runtime Primary Media Component Slice

Status:

- completed

## Purpose

Track the primary-media component slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Work Detail Route Slice](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-work-detail-slice).

Selected work and work-detail routes are now ES module routes and both still own near-duplicate primary media DOM and responsive image behavior. The moments route has the same primary image concept with one intended difference: moment primary images currently do not link to a full-size responsive asset. This slice should create a focused primary-media component that treats link presence as data, not as route-specific branching.

## Steer

- Treat current selected-work, work-detail, and moment primary image behavior as the authoritative behavior reference.
- Build a focused primary-media component, not a broad media utility bucket.
- Do not redesign selected-work, work-detail, or moment page layouts.
- Preserve linked primary image behavior for selected works and work details.
- Preserve unlinked primary image behavior for moments unless a separate decision changes it.
- Preserve moment hero captions and external-image behavior if moments are integrated in this slice.
- Use data shape to model optional link behavior: routes pass link data when the primary media should be clickable and omit link data when it should not.
- Keep route-specific media base, suffix, width, format, and selected record decisions route-owned unless a narrow shared projection helper is clearly justified.
- Do not migrate keyboard navigation, swipe navigation, metadata rows, prose/body rendering, search, or generated data schemas in this slice.
- Keep the completed slice functional and deployable.

## Validation Policy

Use the same lightweight validation policy as the earlier slices:

- run JavaScript syntax checks for changed modules;
- perform manual browser testing for touched routes and component states;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 5: Primary Media Component

Purpose: extract repeated primary image/link DOM and image attributes into a reusable component while preserving selected-work, work-detail, and moment primary media behavior.

Scope:

- inspect current primary media behavior in:
  - `site/assets/js/catalogue/routes/work-page.js`;
  - `site/assets/js/catalogue/routes/work-detail-page.js`;
  - `site/assets/js/moment.js`;
  - `site/works/index.html`;
  - `site/work-details/index.html`;
  - the moments route shell;
  - relevant CSS in `site/assets/css/main.css` and component CSS in `site/assets/css/catalogue.css`;
- create `site/assets/js/catalogue/components/primary-media.js`;
- define a compact component contract for:
  - image `src`, `srcset`, `sizes`, width, height, alt, loading, decoding, and fetch priority;
  - optional aspect ratio;
  - optional link `href`, target, and rel;
  - optional caption text when the route uses a primary-media caption;
  - hidden/unavailable primary media state where a route needs it;
- integrate selected-work and work-detail primary media into the component;
- integrate moment primary media if the unlinked image plus optional caption/external-image behavior fits the component contract without route-specific flags;
- add a narrow shared helper for responsive primary image source projection only if it removes real duplication without absorbing route decisions;
- keep route-specific payload normalization, media base/suffix/format parsing, and selected record decisions in route modules;
- update `catalogue.css` only for new component-owned selectors if the component introduces new selectors.

Out of scope:

- changing whether moment primary images open a full-size asset;
- redesigning primary media layout or caption presentation;
- migrating `moment.js` fully to an ES module route unless component integration makes a small route switch unavoidable and explicitly recorded;
- migrating keyboard navigation or swipe navigation;
- creating a broad media helper for thumbnails, captions, external media, and primary media together;
- generated catalogue data schema changes;
- public search runtime or payload changes;
- automated smoke-test maintenance.

## Candidate Module Ownership

The exact filenames should follow the implementation, but ownership should stay narrow:

- `components/primary-media.js` owns linked/unlinked primary media DOM, image attributes, optional caption DOM, hidden state, and image fallback handling if needed.
- `shared/primary-media-sources.js` or a similarly focused helper may own responsive primary image URL and `srcset` projection only if route-independent projection is repeated enough to justify it.
- `routes/work-page.js` owns selected-work payload normalization, primary media base/suffix/format config, full-size link decision, and route rendering order.
- `routes/work-detail-page.js` owns work-detail payload lookup, detail record normalization, primary media base/suffix/format config, full-size link decision, and route rendering order.
- `moment.js` or a later `routes/moment-page.js` owns moment payload normalization, external-image detection, unlinked primary image decision, and moment body rendering.
- `catalogue.css` owns new primary-media component selectors if introduced; `main.css` keeps existing page layout selectors until no route uses them.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 5.1 | completed | Inspect selected-work, work-detail, and moment primary media behavior, route shells, and relevant CSS. | Confirmed repeated image/link/caption DOM without folding in metadata or navigation. |
| 5.2 | completed | Define the primary-media component contract and decide whether moment integration fits cleanly. | Moment integration fits through optional link and optional caption data; no route-mode flag needed. |
| 5.3 | completed | Implement `components/primary-media.js` and any narrowly justified source projection helper. | Added the focused component only; route-specific source projection remains route-owned. |
| 5.4 | completed | Integrate selected-work and work-detail routes with the primary-media component. | Preserved full-size links, aspect ratio, eager loading, fetch priority, `srcset`, and alt fallback. |
| 5.5 | completed | Integrate moment primary media if the component contract supports unlinked media, captions, and external images cleanly. | Preserved unlinked moment behavior, captions, and external-image `srcset` omission. |
| 5.6 | completed | Update component-owned CSS and validation config if new component files/selectors are introduced. | Moved primary-media CSS ownership for existing `.page__media*` selectors and moment primary-media overrides into `catalogue.css`; added the stylesheet to routes that use the component. |
| 5.7 | completed | Record completed verification and a slice assessment with parent-design acceptance evidence. | Completed in this document. |

## Completed Verification

- `node --check site/assets/js/catalogue/components/primary-media.js`
- `node --check site/assets/js/catalogue/routes/work-page.js`
- `node --check site/assets/js/catalogue/routes/work-detail-page.js`
- `node --check site/assets/js/moment.js`
- `bin/site-validate`
  - passed: `Site validation passed: 58 required files; 9 required directories; 44 Docs Viewer runtime modules`
- Manual browser verification against `http://127.0.0.1:8176`:
  - `/works/?work=00001&series=009` renders `#selectedWorkMedia` with linked `#selectedWorkMediaLink`, `#selectedWorkImg`, full-size `href`, responsive `srcset`, eager loading, and no console errors.
  - `/work-details/?detail=00001-001&from_work=00001&from_work_title=Smoke&section=00001-1&details_section=00001-1&series=009` renders `#detailPrimaryMedia` with linked `#detailMediaLink`, `#detailPrimaryImg`, `data-swipe-nav-zone="detail-media"`, full-size `href`, responsive `srcset`, and no console errors.
  - `/moments/?moment=a-lemon-tart-poem` renders `#momentHero` with direct unlinked `#momentHeroImg`, responsive `srcset`, optional caption node, and no console errors.
  - `/moments/` keeps `#momentHero` hidden in browse state with no console errors.
- Automated browser smoke tests were not run, per this slice's validation policy.

## Slice 5 Assessment

- Added `site/assets/js/catalogue/components/primary-media.js` as the single owner for primary image DOM, optional link wrapping, optional caption DOM, image attributes, and hidden primary-media state.
- Updated selected-work and work-detail routes to pass route-owned image URLs, `srcset`, aspect ratio, full-size link data, loading attributes, and alt fallback into the component.
- Updated the work-detail route to re-bind swipe navigation after component render so the dynamically created detail media link keeps the existing swipe zone behavior.
- Updated the moments route through a dynamic component import from classic script context, preserving unlinked moment media, caption behavior, and external-image handling without requiring a full moment route migration in this slice.
- Simplified selected-work and work-detail route shells to component roots and moved primary-media CSS rules for `.page__media`, `.page__mediaLink`, `.page__mediaImg`, debug outlines, and moment primary-media overrides from `main.css` into `catalogue.css`.
- Added `catalogue.css` to work-detail and moments shells so every route using the primary-media component loads the component-owned stylesheet.
- Registered the new component with site validation in `site-tools/config/site-tools.json`.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required | Reused existing route data flow and page CSS; extracted only the repeated primary-media DOM behavior. |
| Legacy primary media behavior inspected before contract design | yes required | Inspected selected-work, work-detail, moment route shell, and `.page__media*` CSS before integration. |
| Working behavior ported/adapted rather than redesigned line by line | yes required | Routes now pass existing image/link/caption decisions into the component; layout and route decisions remain unchanged. |
| Public route/navigation/data contracts remain stable | yes required | Public URLs, query parameters, payload locations, image URL patterns, and route shells remain compatible. |
| Linked selected-work and work-detail primary media remain stable | yes required | Browser checks confirmed full-size links and responsive image attributes for selected-work and work-detail pages. |
| Unlinked moment primary media remains stable unless separately changed | yes required | Browser check confirmed selected moment primary media renders as an unlinked image. |
| Completed slice leaves site functional and deployable | yes required | Syntax checks and `bin/site-validate` passed; touched routes passed manual browser checks. |
| ES module/component boundaries follow target folder structure | yes required | New component lives under `assets/js/catalogue/components/primary-media.js`; catalogue routes import it directly. |
| No broad `utils.js`-style or media-bucket module introduced | yes required | Component owns only primary-media DOM; responsive source construction remains route-owned. |
| Performance rules respected | yes required | Preserved eager loading, async decoding, fetch priority, and responsive `srcset`/`sizes`; no added payload fetches. |
| Primary media ownership is explicit and not flag-heavy | yes required | Optional link behavior is represented by link data presence, and optional captions by caption data presence. |
| Component CSS remains owned in `catalogue.css` where new selectors are introduced | yes required | Primary-media base rules and moment primary-media overrides now live in `catalogue.css`; routes using the component explicitly load that stylesheet. |
| Search, if touched, stays structural-only | yes required | Search runtime and payloads were not touched. |
| Validation stayed within agreed policy | yes required | Ran syntax checks, site validation, and manual browser checks; did not run automated smoke tests. |

## Follow-On

After Slice 5, decide whether to migrate the moments route to an ES module route, extract `work.js` and `swipe-nav.js` navigation behavior into `catalogue/navigation/`, or create a metadata panel foundation based on the duplication that remains.
