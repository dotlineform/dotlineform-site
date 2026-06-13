---
doc_id: site-request-public-catalogue-runtime-module-architecture-image-caption-slice
title: Public Catalogue Runtime Image And Caption Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: site-request-public-catalogue-runtime-module-architecture
viewable: true
---
# Public Catalogue Runtime Image And Caption Slice

Status:

- planned

## Purpose

Track the next implementation slice for [Public Catalogue Runtime Module Architecture Request](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture), after [Public Catalogue Runtime Module Architecture Slices](/docs/?scope=studio&doc=site-request-public-catalogue-runtime-module-architecture-slices).

This slice creates the image and caption foundation exposed by the thumbnail grid/list work.
It should reduce media projection ownership in `routes/series-index.js` only where a durable shared owner is clear.
It should not become a standalone cleanup pass over the route file.

## Steer

- Treat Slice 1 as the behavior reference for the migrated `/series/` route.
- Carefully inspect legacy image and caption behavior before defining component contracts.
- Create focused media/image modules only where route or component reuse is real.
- Port or adapt working logic rather than redesigning image behavior.
- Keep generated catalogue data schemas stable.
- Do not migrate every route.
- Choose a first integration route only after the image/caption contract is visible.
- Keep the completed slice functional and deployable.

## Validation Policy

Use the same lightweight validation policy as Slice 1:

- run JavaScript syntax checks for changed modules;
- perform manual browser testing for touched routes and component states;
- do not run automated browser smoke tests by default;
- do not update smoke tests as part of this refactor unless a separate decision makes them part of the work.

Record only validation actually performed.

## Slice 2: Image And Image Caption Foundation

Purpose: create focused image/media and caption ownership so catalogue routes and components do not each build thumbnail paths, `srcset`, dimensions, alt text, and caption markup differently.

Scope:

- inspect image and caption behavior in:
  - `site/assets/js/catalogue/routes/series-index.js`;
  - `site/assets/js/catalogue/components/thumbnail-grid-list.js`;
  - legacy `site/assets/js/work-page.js`;
  - legacy `site/assets/js/work-detail-page.js`;
  - legacy `site/assets/js/recent-index.js`;
  - legacy `site/assets/js/moment.js` where relevant;
  - relevant image/caption CSS in `site/assets/css/main.css` and `site/assets/css/catalogue.css`;
- define the shared media/image contract for public catalogue images;
- define the caption contract only where captions are part of catalogue image rendering;
- implement focused modules under `shared/` and `components/` by porting or adapting existing logic;
- integrate the image component into `thumbnail-grid-list.js`;
- move thumbnail/media projection out of `routes/series-index.js` where the new owner is clear;
- select one first integration route after the contract is visible, probably `work-page.js` detail grids if it proves the contract with low unrelated migration work;
- update component-owned CSS only where image/caption selectors need ownership in `catalogue.css`;
- leave legacy selectors in `main.css` until no public route uses them.

Out of scope:

- generated catalogue data schema changes;
- media generation or R2 publishing changes;
- public search payload optimization;
- broad route migration;
- visual redesign;
- automated smoke-test maintenance.

## Candidate Module Ownership

The exact filenames should follow the implementation, but the ownership should stay narrow:

- `shared/thumbnails.js` may continue to own thumbnail URL and `srcset` construction if it stays focused.
- A new shared media module may own image-size parsing or common media attribute projection if that responsibility grows beyond thumbnails.
- `components/catalogue-image.js` should own reusable image DOM, image error placeholders, dimensions, loading/decoding attributes, and alt text fallback.
- `components/catalogue-caption.js` should exist only if repeated caption markup needs a component owner.
- `components/thumbnail-grid-list.js` should keep owning grid/list item composition, but delegate image DOM to the image component.
- Route files should pass normalized media data and route-specific links; they should not render reusable image markup.

## Tasks

| ID | Status | Action | Next-session steer |
| --- | --- | --- | --- |
| 2.1 | planned | Inspect current image, thumbnail, and caption behavior in the touched and candidate legacy scripts and CSS. | Capture only behavior needed for the image/caption contract; do not create a broad route inventory. |
| 2.2 | planned | Define the image/media component contract, including source, `srcset`, sizes, dimensions, alt text, loading/decoding, placeholder behavior, link ownership, and caption ownership. | Stop for review if the contract needs route-specific flags. |
| 2.3 | planned | Implement focused shared media/image helpers and component modules by porting or adapting existing logic. | Keep `shared/` modules narrow; do not create a broad media utility bucket. |
| 2.4 | planned | Integrate the image component into `thumbnail-grid-list.js` and reduce media projection in `routes/series-index.js` where ownership is clear. | Preserve `/series/` behavior and validation results from Slice 1. |
| 2.5 | planned | Select and integrate one first route after the image/caption contract is visible. | Prefer `work-page.js` detail grids if they prove image/link behavior with little unrelated migration work. |
| 2.6 | planned | Record completed verification and a slice assessment with parent-design acceptance evidence. | Include specific cleanup triggers rather than vague risk notes. |

## Completed Verification

- Not started.

## Slice 2 Assessment

- Not started.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required |  |
| Legacy image/caption behavior inspected before contract design | yes required |  |
| Working behavior ported/adapted rather than redesigned line by line | yes required |  |
| Public route/navigation/data contracts remain stable | yes required |  |
| Completed slice leaves site functional and deployable | yes required |  |
| ES module boundaries follow target folder structure | yes required |  |
| No broad `utils.js`-style module introduced | yes required |  |
| Performance rules respected | yes required |  |
| Image/caption normalization uses stable component contracts | yes required |  |
| Thumbnail grid/list delegates image DOM without route-local forks | yes required |  |
| Component CSS remains owned in `catalogue.css` where new selectors are introduced | yes required |  |
| Search, if touched, stays structural-only | yes required |  |
| Validation stayed within agreed policy | yes required |  |

## Follow-On

After Slice 2, decide whether the next foundation should be navigation or metadata panel based on what the image/caption work exposes.
