---
doc_id: site-request-public-catalogue-runtime-module-architecture-image-caption-slice
title: Public Catalogue Runtime Image And Caption Slice
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: done
parent_id: site-request-public-catalogue-runtime-module-architecture
viewable: true
---
# Public Catalogue Runtime Image And Caption Slice

Status:

- done

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
| 2.1 | completed | Inspected current image, thumbnail, and caption behavior in the touched and candidate legacy scripts and CSS. | The relevant behavior is recorded below; do not expand this into a broad route inventory. |
| 2.2 | completed | Defined the image/media component contract around normalized media data with source, `srcset`, sizes, dimensions, alt text, loading/decoding, placeholder behavior, and caption ownership. | No route-specific flags were needed. |
| 2.3 | completed | Implemented focused shared thumbnail projection and component modules by porting/adapting existing logic. | Keep future shared media additions narrow; do not create a broad media utility bucket. |
| 2.4 | completed | Integrated `components/catalogue-image.js` and `components/catalogue-caption.js` into `thumbnail-grid-list.js` and moved thumbnail projection details into `shared/thumbnails.js`. | `/series/` behavior stayed stable. |
| 2.5 | completed | Selected `/series/` as the first integration route for the image/caption foundation. `work-page.js` detail grids were inspected but not switched because that would require either a global bridge or a full selected-work route migration. | Migrate `work-page.js` detail grids only when the selected-work route is ready to move to ES modules. |
| 2.6 | completed | Recorded completed verification and a slice assessment with parent-design acceptance evidence. | Use the follow-on triggers below for the next slice. |

## Completed Verification

- JavaScript syntax checks passed with `node --check` for all modules under `site/assets/js/catalogue/`.
- `bin/site-validate` passed: `56 required files; 9 required directories; 44 Docs Viewer runtime modules`.
- `git diff --check` passed.
- Manual browser validation against `http://127.0.0.1:4000` covered:
  - `/series/` loads the migrated module route and renders grid/list items through `catalogueImage` and `catalogueCaption`;
  - list mode renders captions through `catalogueCaption` and no console errors were reported;
  - `/series/?series=105` renders real work thumbnail images through `catalogueImage--grid`, including `src`, `srcset`, `width`, `height`, and `alt` values;
  - selected-series link targets remained stable, for example `/works/?series=105&work=00008`.
- Automated browser smoke tests were not run, per the slice validation policy.

## Slice 2 Assessment

- Legacy behavior inspected:
  - `routes/series-index.js` projected thumbnail source, `srcset`, sizes, width, height, and alt text for thumbnail grid/list items.
  - `thumbnail-grid-list.js` rendered image DOM, missing-image placeholders, image error fallbacks, and list captions.
  - Legacy `recent-index.js` rendered compact thumbnail images, placeholders, title text, and caption text.
  - Legacy `work-page.js` rendered primary work media and detail-grid thumbnail links with `seriesGrid` classes.
  - Legacy `work-detail-page.js` rendered primary detail media and responsive `srcset` values.
  - Legacy `moment.js` rendered hero images, external-image handling, `srcset`, dimensions, alt text, and optional figcaption text.
  - `main.css` and `catalogue.css` selectors for `figcaption`, `recentIndexItem__img`, `recentIndexItem__caption`, `seriesGrid__img`, `page__mediaImg`, `page__caption`, `catalogueGridList__image`, and `catalogueGridList__caption` were inspected.
- Behavior preserved:
  - `/series/`, `/series/?mode=moments`, and `/series/?series=...` route behavior, link targets, mode/view/page persistence, and generated payload schemas remain stable.
  - Thumbnail image attributes remain equivalent for the migrated component path: `src`, `srcset`, `sizes`, `width`, `height`, `alt`, `loading`, and `decoding`.
  - Missing thumbnails and image load errors still render inert placeholder spans.
  - List captions still render as text and remain absent when caption text is empty.
- Normalized into component contracts:
  - `components/catalogue-image.js` owns reusable image DOM, image placeholders, image error fallback, dimensions, loading/decoding attributes, and alt text fallback.
  - `components/catalogue-caption.js` owns reusable caption DOM for catalogue image/list captions.
  - `shared/thumbnails.js` owns thumbnail URL, `srcset`, default grid sizes, and normalized thumbnail image data projection.
  - `thumbnail-grid-list.js` now owns item composition but delegates image and caption DOM to the new components.
- Route still owns:
  - `routes/series-index.js` still owns route bootstrapping, DOM anchors, mode/view/sort/page state, payload selection, and deciding which thumbnail base applies to works versus moments.
  - The route still reads thumbnail data attributes from its route shell; only source construction and image-data projection moved to `shared/thumbnails.js`.
- Intentionally not changed:
  - `work-page.js`, `work-detail-page.js`, `recent-index.js`, and `moment.js` remain legacy scripts for now.
  - `work-page.js` detail grids were not switched in this slice because using the ES module image component from a classic script would require a new global bridge, while switching the full selected-work route belongs in a separate route migration.
  - Primary work/detail/moment hero media were inspected but not migrated.
  - Search runtime and payload behavior were not touched.
  - Legacy image/caption selectors remain in `main.css` until their routes migrate.
- Improvement opportunities:
  - If the selected-work route is migrated next, switch `work-page.js` to an ES module route and reuse `thumbnail-grid-list.js` plus `catalogue-image.js` for detail grids before removing `seriesGrid` usage there.
  - If primary work/detail/moment hero media need shared ownership, add a focused primary-media component instead of expanding `catalogue-image.js` with route-specific flags.
  - If another route needs external-image handling like `moment.js`, add that as a narrow media-source helper before integrating that route.
  - If repeated figcaption-style markup appears in migrated routes, extend `catalogue-caption.js` with a `figure`/`figcaption` contract before moving moment hero captions.
- Remaining issues:
  - No remaining issue blocks the architecture. The selected-work detail grid migration is later cleanup tied to a route migration trigger, not a blocker for the image/caption foundation.
- Continue decision:
  - The image/caption foundation is good enough to continue the migration. It created reusable image and caption component ownership without broad route migration or new globals.

Acceptance checklist:

| Parent design criterion | Required status | Evidence |
| --- | --- | --- |
| Module-level refactor, not greenfield rewrite | yes required | yes - working image/caption behavior was moved behind focused component and shared module boundaries without redesigning public UI. |
| Legacy image/caption behavior inspected before contract design | yes required | yes - the assessment records inspected behavior from migrated `/series/` modules, legacy `recent-index.js`, `work-page.js`, `work-detail-page.js`, `moment.js`, and CSS selectors. |
| Working behavior ported/adapted rather than redesigned line by line | yes required | yes - thumbnail URL, `srcset`, placeholder, error fallback, image attributes, and caption behavior were ported/adapted from existing route/component code. |
| Public route/navigation/data contracts remain stable | yes required | yes - manual checks covered `/series/` and `/series/?series=105`; selected-series links and generated data schemas stayed unchanged. |
| Completed slice leaves site functional and deployable | yes required | yes - `bin/site-validate`, syntax checks, `git diff --check`, and manual browser validation passed. |
| ES module boundaries follow target folder structure | yes required | yes - reusable DOM lives in `components/`, source projection lives in `shared/thumbnails.js`, and route wiring remains in `routes/series-index.js`. |
| No broad `utils.js`-style module introduced | yes required | yes - new modules are narrowly named `catalogue-image.js`, `catalogue-caption.js`, and focused thumbnail projection functions. |
| Performance rules respected | yes required | yes - no new route loads or duplicate fetches were introduced; `/series/` continues to load the same migrated route entrypoint with smaller delegated component modules. |
| Image/caption normalization uses stable component contracts | yes required | yes - normalized media data is passed to `catalogue-image.js`, and text captions are passed to `catalogue-caption.js`. |
| Thumbnail grid/list delegates image DOM without route-local forks | yes required | yes - `thumbnail-grid-list.js` delegates image and caption DOM to the new components for both grid and list modes. |
| Component CSS remains owned in `catalogue.css` where new selectors are introduced | yes required | yes - new `.catalogueImage*` and `.catalogueCaption` selectors live in `site/assets/css/catalogue.css`. |
| Search, if touched, stays structural-only | yes required | yes - search was not touched. |
| Validation stayed within agreed policy | yes required | yes - validation used syntax checks, `bin/site-validate`, `git diff --check`, and manual browser checks; automated browser smoke tests were not run. |

## Follow-On

After Slice 2, the next slice should probably migrate the selected-work route enough to reuse the thumbnail grid/list and image component for work detail grids, or start the navigation foundation if previous/next and keyboard behavior are a higher priority.
