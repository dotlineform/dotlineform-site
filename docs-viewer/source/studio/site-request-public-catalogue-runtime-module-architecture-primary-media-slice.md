---
doc_id: site-request-public-catalogue-runtime-module-architecture-primary-media-slice
title: Public Catalogue Runtime Primary Media Component Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: site-request-public-catalogue-runtime-module-architecture
viewable: true
---
# Public Catalogue Runtime Primary Media Component Slice

Status:

- planned

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
| 5.1 | planned | Inspect selected-work, work-detail, and moment primary media behavior, route shells, and relevant CSS. | Capture image/link/caption behavior only; do not fold in metadata or navigation. |
| 5.2 | planned | Define the primary-media component contract and decide whether moment integration fits cleanly. | Stop for review if moment integration needs route-specific component flags. |
| 5.3 | planned | Implement `components/primary-media.js` and any narrowly justified source projection helper. | Model link presence as optional data, not route mode. |
| 5.4 | planned | Integrate selected-work and work-detail routes with the primary-media component. | Preserve full-size links, aspect ratio, eager loading, fetch priority, and alt fallback. |
| 5.5 | planned | Integrate moment primary media if the component contract supports unlinked media, captions, and external images cleanly. | Preserve current unlinked moment behavior. |
| 5.6 | planned | Update component-owned CSS and validation config if new component files/selectors are introduced. | Do not move broad page layout CSS from `main.css` unless it becomes unused. |
| 5.7 | planned | Record completed verification and a slice assessment with parent-design acceptance evidence. | Include concrete follow-up triggers for moment route migration, navigation extraction, or metadata cleanup. |

## Completed Verification

- Not started.

## Slice 5 Assessment

- Not started.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required |  |
| Legacy primary media behavior inspected before contract design | yes required |  |
| Working behavior ported/adapted rather than redesigned line by line | yes required |  |
| Public route/navigation/data contracts remain stable | yes required |  |
| Linked selected-work and work-detail primary media remain stable | yes required |  |
| Unlinked moment primary media remains stable unless separately changed | yes required |  |
| Completed slice leaves site functional and deployable | yes required |  |
| ES module/component boundaries follow target folder structure | yes required |  |
| No broad `utils.js`-style or media-bucket module introduced | yes required |  |
| Performance rules respected | yes required |  |
| Primary media ownership is explicit and not flag-heavy | yes required |  |
| Component CSS remains owned in `catalogue.css` where new selectors are introduced | yes required |  |
| Search, if touched, stays structural-only | yes required |  |
| Validation stayed within agreed policy | yes required |  |

## Follow-On

After Slice 5, decide whether to migrate the moments route to an ES module route, extract `work.js` and `swipe-nav.js` navigation behavior into `catalogue/navigation/`, or create a metadata panel foundation based on the duplication that remains.
