---
doc_id: site-request-public-catalogue-runtime-module-architecture
title: Public Catalogue Runtime Module Architecture Request
added_date: 2026-06-13
last_updated: 2026-06-13
ui_status: planned
parent_id: change-requests
viewable: true
---
# Public Catalogue Runtime Module Architecture Request

Status:

- planned

## Summary

Design and migrate to a new public catalogue runtime module structure for the static site.

This request is not a cleanup pass over the current extracted route scripts.
The current scripts contain older inline route behavior that accumulated over time while newer modules were added around it.
They should be treated as behavior references and source material, not as the target module architecture.

The target modules should be new, documented, and built around explicit ownership.
Routes should then switch over to the new entrypoints once the equivalent behavior exists.

## Goal

Create a stable public catalogue runtime structure before deciding detailed functionality changes or optimization work.

The first design question is:

- what is the ideal module structure for public catalogue routes, and how should the site migrate to it?

Once that target is stable, follow-up work can decide:

- which detailed route behavior should stay, change, or be simplified;
- which UI differences are intentional or should be normalized;
- which payload and runtime costs are worth optimizing;
- whether public catalogue search needs a separate data/runtime redesign.

## Design Direction

Build new target modules rather than refactoring the old extracted files in place.

The migration should:

- define the target module map first;
- create new modules with documented responsibilities;
- port only the behavior needed by each route;
- prefer concise shared modules where there is real shared behavior;
- switch routes to the new entrypoints when ready;
- delete obsolete legacy route scripts once no route loads them.

This avoids preserving accidental boundaries from older inline code.
Each new module must have a clear owner and reason to exist.

## Engineering Ground Rules

New public catalogue runtime code should use ES modules.
The old classic-script and global-object pattern belongs to the legacy extracted route scripts, not the target architecture.

Code rules:

- route files are entrypoints only and should bootstrap one route or one route mode;
- imports should be explicit and static unless dynamic `import()` has a clear route or performance reason;
- shared modules must have narrow named responsibilities;
- do not create a broad `utils.js`-style module;
- do not introduce new globals;
- old extracted scripts are behavior references only, not files to gradually reshape.

Performance is a first-order requirement for this migration.
The site is small, so public catalogue routes should be extremely fast.
Do not treat the absence of quantified measurement, or the current small scale of the site, as a reason to accept avoidable runtime cost.

Performance rules:

- routes should load only the JavaScript needed for the current route or route mode;
- avoid "download then early return" as a normal routing strategy;
- avoid duplicate JSON fetches on one route;
- prefer small route entrypoints and focused shared modules;
- use lazy loading when it prevents meaningful unused work;
- consider parse and execute cost, not just transfer size;
- do not make public search payload or runtime performance worse while leaving search redesign to a separate request.

Ownership rules:

- `routes/` owns route bootstrapping and route state wiring;
- `shared/` owns primitives such as fetch, URL state, parsing, normalization, and media helpers;
- `components/` owns reusable DOM rendering where reuse is real;
- `navigation/` owns keyboard, swipe, and previous/next behavior;
- `search/` owns public catalogue search runtime modules, but not the broader search payload redesign.

## Data Constraints

The existing public catalogue data JSON structures should remain stable unless there is an obvious gap that blocks the module architecture.

In particular:

- catalogue data JSON files are probably acceptable as they are, apart from search;
- public search JSON is a known separate problem and should be addressed in detail separately;
- this request should not redesign generated catalogue payload schemas as part of the module migration;
- changing shared catalogue data structures risks forcing a Studio refactor, which is outside this request.

The runtime migration may change how route code reads existing payloads.
It should not change payload ownership or schema contracts without a separate recorded decision.

## UI Constraints

The current public catalogue UI is acceptable as the baseline.

This request is not a visual redesign.
However, if small page-to-page UI differences prevent a concise shared module from existing, the UI should adjust rather than forcing duplicated runtime code.

Allowed UI changes are small normalization changes that support clearer module ownership.
Material layout, route, or interaction changes need a separate decision.

## Candidate Target Shape

The exact shape should be confirmed during the first implementation batch, but the target should start from this ownership model:

| Area | Purpose |
| --- | --- |
| `site/assets/js/catalogue/routes/` | Route entrypoints only. Each file bootstraps one public route or route mode. |
| `site/assets/js/catalogue/shared/` | Narrow shared primitives such as URL state, JSON fetch, text normalization, media helpers, and dataset parsing. |
| `site/assets/js/catalogue/components/` | Reusable DOM renderers where reuse is real, such as cards, thumbnail grids, pagination, or empty states. |
| `site/assets/js/catalogue/navigation/` | Focused interaction modules such as keyboard navigation, swipe navigation, and previous/next catalogue navigation. |
| `site/assets/js/catalogue/search/` | Public catalogue search runtime modules. Search payload redesign remains separate. |

Route entrypoints should be thin.
Shared modules should stay narrow.
No broad utility dump should replace the current route-script tangle.

## Route Coverage

The migration must cover the public catalogue routes:

- `/series/`
- `/series/?mode=moments`
- `/recent/`
- `/works/`
- `/works/?work=...`
- `/work-details/?detail=...`
- `/moments/?moment=...`
- `/catalogue/search/`

Docs Viewer public scopes such as `/library/` and `/analysis/` are not part of this catalogue runtime architecture.
They already have their own public runtime ownership model.

## Non-Goals

- Do not introduce a public-site build, copy, bundling, or transpilation step.
- Do not redesign catalogue JSON payload schemas.
- Do not refactor Studio generated-data ownership as part of this request.
- Do not make public search JSON optimization part of the first module migration.
- Do not preserve old script filenames, globals, or boundaries for compatibility.
- Do not add compatibility aliases for old module paths.
- Do not redesign the public catalogue UI.

## Migration Strategy

The implementation should proceed in controlled slices:

1. Define and document the target module map.
2. Create the new module folders and minimal shared primitives.
3. Port one low-risk route first, likely `/recent/`, to validate the shape.
4. Port the remaining route entrypoints from least to most complex.
5. Normalize small UI differences only where they remove duplicated route logic.
6. Keep generated catalogue data structures stable.
7. Leave catalogue search payload redesign for a separate request unless an obvious module-boundary gap appears.
8. Remove old extracted route scripts after the public routes no longer load them.

Each route migration should verify behavior against the current route before deleting the legacy script it replaces.

## Temporary Workflow Change

During this refactor, the public-site GitHub Actions workflow should not run automatically on pushes to `main`.
The migration is expected to involve many local commits and local verification runs.
Automatic `main` push runs would add noise while the deploy root is being refactored.

The workflow should keep:

- `workflow_dispatch`, so the public-site validation/upload/deploy path can be run manually when needed;
- `pull_request`, so review branches can still get workflow feedback when relevant.

This is an intentional temporary change for the catalogue runtime migration.
After the refactor is complete, restore the `main` push trigger for `site/**`, `site-tools/**`, `bin/site-validate`, and `.github/workflows/public-site.yml`.

## Decisions Needed

- What is the final target module map and naming convention?
- Which current route behaviors should be ported exactly, and which small differences can be normalized?
- Which shared renderers are justified by actual reuse?
- Which route should be the first migration slice?
- Should catalogue search runtime move into the new structure before or after non-search routes?

## Verification Expectations

- Run `bin/site-validate` after route script changes.
- Run browser smoke checks for every migrated route.
- Check console errors for every migrated route.
- Compare route behavior before and after migration unless a recorded decision approves a difference.
- Confirm old extracted scripts are no longer loaded before deleting them.
- Keep public catalogue data payload schemas stable unless a separate decision changes them.
