---
doc_id: public-legacy-collections-cleanup
title: Public Legacy Collections Cleanup
added_date: 2026-06-11
last_updated: 2026-06-11
parent_id: studio
viewable: true
---
# Public Legacy Collections Cleanup

This document specifies the cleanup needed to retire legacy public catalogue Jekyll collections after the public route model moved to fixed shells plus generated JSON.

The route authority is [Public Route Model](/docs/?scope=studio&doc=public-route-model).

## Status

- planned
- This is an implementation spec and task tracker for the legacy-collection cleanup.
- Source docs only; generated Docs Viewer payloads should not be rebuilt as part of routine edits to this document.

## Decision

Retire the four legacy public catalogue collection families as route-input contracts:

- `_works/`
- `_series/`
- `_work_details/`
- `_moments/`

The target public route model uses fixed shells and generated runtime payloads:

- `/series/`
- `/series/?series=<series_id>`
- `/series/?mode=moments`
- `/works/`
- `/works/?work=<work_id>`
- `/work-details/`
- `/work-details/?detail=<detail_uid>`
- `/moments/`
- `/moments/?moment=<moment_id>`
- `/catalogue/search/`

Work, series, work-detail, and moment pages must not require one generated HTML file per record.
Moments should follow the same shell, query-state, runtime JavaScript, and generated JSON model used by works.

## Scope

This cleanup is limited to the current Jekyll build layer and public catalogue route assumptions.
It should remove collection-route dependencies while preserving the current canonical public route behavior.

In scope:

- inventory active consumers of `_works`, `_series`, `_work_details`, and `_moments`
- retire work, series, and work-detail collection outputs and route-anchor stubs
- convert moments from Jekyll/Liquid collection pages to the runtime JSON model, then retire moment collection outputs and route-anchor stubs
- update builders, cleanup flows, audits, tests, route helpers, Studio public links, and docs that still depend on legacy collection stubs
- verify canonical fixed-shell routes, generated payload reads, search URLs, and public Jekyll output

Out of scope:

- replacing Jekyll with the future static public-site builder
- changing catalogue source schemas only to remove Jekyll collections
- changing public visual design
- adding compatibility redirects or aliases for retired path-style catalogue routes
- serializing derivable route URLs into generated public payloads

## Current State

The live work route uses `/works/?work=<work_id>`.
For example, `https://www.dotlineform.com/works/?series=105&work=00008` is rendered by `works/index.md`, `assets/js/public-catalogue-runtime.js`, `assets/works/index/00008.json`, and `assets/data/series_index.json`.

The earlier public route migration moved works and series off Jekyll/Liquid collection pages and onto runtime JavaScript loading generated JSON.
Moments were not converted in that slice, which is why the remaining moment cleanup is more involved than simply deleting collection files.

The legacy collection outputs still exist because `_config.yml` still defines public collections and default layouts:

- `works` with `layout: work` and permalink `/works/:name/`
- `series` with `layout: series` and permalink `/series/:name/`
- `work_details` with `layout: work_details` and permalink `/work_details/:name/`
- `moments` with `layout: moment` and permalink `/moments/:name/`

Generated stubs are intentionally minimal or empty.
They are no longer the canonical source of public page metadata or prose.

## Route Disposition

| Legacy route or input | Target disposition | Canonical replacement |
| --- | --- | --- |
| `_works/*.md` and `/works/<work_id>/` | remove as route-input contract | `/works/?work=<work_id>` |
| `_series/*.md` and `/series/<series_id>/` | remove as route-input contract | `/series/?series=<series_id>` |
| `_work_details/*.md` and `/work_details/<detail_uid>/` | remove as route-input contract | `/work-details/?detail=<detail_uid>` |
| `_moments/*.md` and `/moments/<moment_id>/` | remove as route-input contract | `/moments/?moment=<moment_id>` |
| `/moments/` | keep as fixed moments shell | `/moments/?moment=<moment_id>` for selected state |

Do not add redirects, aliases, recovery stubs, or fallback route tables for retired work, series, work-detail, or moment paths.

## Affected Surfaces

The cleanup affects more than Liquid templates.
Current references and assumptions are spread across:

- `_config.yml` collection definitions, permalinks, and defaults
- `_layouts/work.html`
- `_layouts/series.html`
- `_layouts/work_details.html`
- `_layouts/moment.html`
- `studio/services/catalogue/generate_work_pages.py`
- `studio/services/catalogue/catalogue_cleanup.py`
- `studio/services/catalogue/catalogue_transactions.py`
- public route shells such as `works/index.md`, `series/index.md`, and `work-details/index.md`
- public runtime helpers in `assets/js/public-catalogue-runtime.js`
- search URL construction in catalogue search runtime
- Studio public-link helpers and local preview links
- consistency audits under `admin-app/checks/`
- projection contracts and related tests
- docs that still describe route stubs or Jekyll collection outputs as current build constraints

## Target Ownership After Cleanup

Public catalogue route ownership should be:

| Area | Owner |
| --- | --- |
| Route contract | `docs-viewer/source/studio/public-route-model.md` |
| Shared URL helpers | `assets/js/public-catalogue-runtime.js` |
| Series browse shell | `series/index.md` |
| Work browse/selected shell | `works/index.md` |
| Work-detail shell | `work-details/index.md` |
| Moment browse/selected shell | `moments/index.md` |
| Public work payloads | `assets/works/index/<work_id>.json` |
| Public series payloads | `assets/series/index/<series_id>.json` |
| Public moment payloads | `assets/moments/index/<moment_id>.json` |
| Shared public indexes | `assets/data/series_index.json`, `assets/data/works_index.json`, `assets/data/moments_index.json` |
| Search payload | `assets/data/search/catalogue/index.json` |

## Non-Goals

- Do not add compatibility redirects for retired path-style routes.
- Do not emit recovery pages for `/works/<work_id>/`, `/series/<series_id>/`, `/work_details/<detail_uid>/`, `/moments/<moment_id>/`, or other retired path-style catalogue routes.
- Do not restore broad route aliases for `/works/<work_id>/`, `/series/<series_id>/`, `/work_details/<detail_uid>/`, or `/moments/<moment_id>/`.
- Do not make generated public payloads serialize derivable route URLs.
- Do not remove Jekyll itself in this cleanup.

## Baseline Inventory

Start the cleanup with an inventory of active consumers for each collection family:

- `_works/`
- `_series/`
- `_work_details/`
- `_moments/`

Required scans:

```bash
rg -n "_works|site\\.works|layout:\\s*work|/works/:name|workPayloadUrl|assets/works/index" . --glob '!_site/**'
rg -n "_series|site\\.series|layout:\\s*series|/series/:name|seriesPayloadUrl|assets/series/index" . --glob '!_site/**'
rg -n "_work_details|site\\.work_details|layout:\\s*work_details|/work_details/:name|workDetailUrl" . --glob '!_site/**'
rg -n "_moments|site\\.moments|layout:\\s*moment|/moments/:name|momentPayloadUrl|assets/moments/index" . --glob '!_site/**'
```

Classify every hit as one of:

- active fixed-shell runtime dependency
- generated payload dependency
- legacy collection-route dependency
- audit/test assumption
- stale documentation
- historical request context

Record the inventory results in this document before implementation starts or in a linked task note.
Do not use historical request docs alone as proof that a path is active.

## Implementation Tasks

Work through these tasks in ID order unless a task records a dependency that makes a different order safer.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | title | owner surface | acceptance |
| --- | --- | --- | --- | --- |
| 1 | planned | Complete active-consumer inventory | code, config, tests, docs | each scan hit is classified; unknown active consumers are resolved before deletion |
| 2 | planned | Retire work route-anchor stubs | `_works`, work builder, `_config.yml`, audits/tests | `_works/*.md` is no longer required or generated solely for `/works/<work_id>/`; `/works/?work=<id>` still renders from generated payloads |
| 3 | planned | Retire series route-anchor stubs | `_series`, series builder, `_config.yml`, audits/tests | `_series/*.md` is no longer required or generated solely for `/series/<series_id>/`; `/series/?series=<id>` still renders from generated payloads |
| 4 | planned | Retire work-detail route-anchor stubs | `_work_details`, detail builder, `_config.yml`, audits/tests | `_work_details/*.md` is no longer required or generated solely for `/work_details/<detail_uid>/`; `/work-details/?detail=<id>` still renders from generated payloads |
| 5 | planned | Remove unused work, series, and detail layouts and defaults | `_layouts`, `_config.yml` | `work`, `series`, and `work_details` layouts/defaults are removed only after no active collection uses them |
| 6 | planned | Retarget cleanup and delete behavior | catalogue cleanup and transaction services | delete/cleanup plans remove generated JSON, indexes, search payloads, and source-owned artifacts without depending on collection stubs |
| 7 | planned | Retarget public-link and search URL construction | public runtime, Studio helpers, catalogue search | first-party links use canonical shell/query routes through shared helpers; no retired path-style links are emitted |
| 8 | planned | Retarget audits and tests | `admin-app/checks/`, projection tests, catalogue tests | tests validate canonical shells and generated payload contracts instead of requiring route-anchor stubs |
| 9 | planned | Convert moments to shell/query runtime | `_moments`, `moments/index.md`, public runtime, moment payloads | `/moments/?moment=<id>` renders from generated JSON; `_moments/*.md` and `/moments/<id>/` are no longer route contracts |
| 10 | planned | Update docs and close stale contracts | studio docs | owning docs describe fixed shells, generated payloads, and query-state moment routing as current behavior |
| 11 | planned | Final verification and closeout | build, smokes, docs | all required checks pass or are recorded with reason; generated Docs Viewer payload status is reported |

### Task 1: Complete Active-Consumer Inventory

Create a current inventory from the baseline scans and any narrower follow-up scans needed for ambiguous hits.

Acceptance:

- every `_works`, `_series`, `_work_details`, and `_moments` hit is classified
- active fixed-shell runtime dependencies are separated from legacy collection-route dependencies
- tests and docs that intentionally remain are named
- deletion candidates are grouped by task ID before code changes begin

### Task 2: Retire Work Route-Anchor Stubs

Remove the requirement to write or consume `_works/*.md` solely to create `/works/<work_id>/` pages.

Acceptance:

- builders no longer emit `_works` route-anchor stubs for public work pages
- `_config.yml` no longer needs `works` collection output for work page routing after dependent consumers are updated
- public work selection still uses `assets/works/index/<work_id>.json`
- `/works/?work=<work_id>` remains the canonical first-party route

### Task 3: Retire Series Route-Anchor Stubs

Remove the requirement to write or consume `_series/*.md` solely to create `/series/<series_id>/` pages.

Acceptance:

- builders no longer emit `_series` route-anchor stubs for public series pages
- `_config.yml` no longer needs `series` collection output for series page routing after dependent consumers are updated
- public series selection still uses `assets/series/index/<series_id>.json` and shared indexes
- `/series/?series=<series_id>` remains the canonical first-party route

### Task 4: Retire Work-Detail Route-Anchor Stubs

Remove the requirement to write or consume `_work_details/*.md` solely to create `/work_details/<detail_uid>/` pages.

Acceptance:

- builders no longer emit `_work_details` route-anchor stubs for public work-detail pages
- `_config.yml` no longer needs `work_details` collection output for work-detail routing after dependent consumers are updated
- public detail selection still uses the generated public detail payload contract
- `/work-details/?detail=<detail_uid>` remains the canonical first-party route

### Task 5: Remove Unused Work, Series, And Detail Layouts And Defaults

After tasks 2 through 4 remove active consumers, remove or archive obsolete Jekyll collection layouts and defaults.

Acceptance:

- `_layouts/work.html`, `_layouts/series.html`, and `_layouts/work_details.html` are removed only after no active route depends on them
- `_config.yml` no longer defines retired work, series, or work-detail collection outputs
- no replacement compatibility layouts or fallback aliases are added

### Task 6: Retarget Cleanup And Delete Behavior

Update cleanup and transaction flows so they act on current generated artifacts and source-owned data rather than legacy collection stubs.

Acceptance:

- delete and cleanup plans cover generated work, series, detail, index, and search payloads that remain current
- removed collection-stub paths are not retained as compatibility cleanup targets unless a short-lived migration cleanup is explicitly documented
- dry-run or focused tests show the intended remove/update set without deleting unrelated source records

### Task 7: Retarget Public-Link And Search URL Construction

Update public runtime helpers, catalogue search rendering, and Studio public-link helpers so first-party URLs use the canonical shell/query model.

Acceptance:

- work, series, and detail links resolve through shared current route helpers or the Studio catalogue public-link helper
- catalogue search results do not emit `/works/<id>/`, `/series/<id>/`, or `/work_details/<id>/`
- generated public payloads do not gain derivable `href` fields
- missing preview-base configuration still fails visibly in Studio instead of falling back to the Studio host

### Task 8: Retarget Audits And Tests

Update audits, projections, and tests that currently assert collection-stub paths.

Acceptance:

- audits validate canonical shells and generated payloads as the current contract
- tests are retargeted to current owner contracts rather than preserving old fixture paths
- no permanent test is added solely to assert that an obsolete path does not exist when deleting the old code path is sufficient

### Task 9: Convert Moments To Shell/Query Runtime

Move moments onto the same runtime model as works.
This is more involved than tasks 2 through 4 because the earlier public route migration did not convert moments from Jekyll/Liquid collection pages to runtime JavaScript loading generated JSON.

Acceptance:

- `/moments/` is a fixed public shell that can render a browse state and a selected moment state
- `/moments/?moment=<moment_id>` renders the selected moment from `assets/moments/index/<moment_id>.json`
- public moment links resolve to `/moments/?moment=<moment_id>` through shared route helpers
- builders no longer emit `_moments` route-anchor stubs for public moment pages
- `_config.yml` no longer needs `moments` collection output for moment routing after dependent consumers are updated
- `_layouts/moment.html` is removed only after no active route depends on it
- `/moments/<moment_id>/` is retired and is not replaced with a redirect, alias, recovery page, or generated static HTML page

### Task 10: Update Docs And Close Stale Contracts

Update durable docs after implementation decisions land.
Likely affected docs:

- [Data Flow](/docs/?scope=studio&doc=data-flow)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Catalogue Source Model](/docs/?scope=studio&doc=data-models-catalogue-source)
- [Catalogue Indexes And Payloads](/docs/?scope=studio&doc=data-models-catalogue-indexes)
- [Catalogue Maintenance](/docs/?scope=studio&doc=data-models-catalogue-maintenance)
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)
- [Docs Viewer Semantic References Implementation](/docs/?scope=studio&doc=docs-viewer-semantic-references-implementation)
- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)

Acceptance:

- docs describe collection stubs as retired or historical, not current build constraints
- route examples use canonical shell/query URLs
- public static-site builder docs continue to reference this cleanup as a predecessor, not as a duplicated task list
- generated Docs Viewer payload status is recorded in closeout if source docs change

### Task 11: Final Verification And Closeout

Run the smallest verification set that covers the implementation slice.

Required checks for the full cleanup:

- public route smoke for `/series/`, `/series/?series=<id>`, `/series/?mode=moments`, `/works/`, `/works/?work=<id>`, `/work-details/`, `/work-details/?detail=<id>`, `/moments/`, and `/moments/?moment=<id>`
- catalogue search result URL smoke
- site consistency audit with retired collection paths removed from required targets
- scoped catalogue build tests for work, series, work-detail, and moment changes
- public Jekyll build with no generated collection pages for retired work, series, detail, or moment routes
- focused scan showing no active first-party links to retired work, series, work-detail, or moment path routes

No new audit is required solely for the "no work, series, or detail collection stubs are required" owner contract.
Use existing focused route, build, and test checks for the implementation slice.

## Completion Criteria

This cleanup is complete when:

- first-party public navigation uses only canonical shell routes from [Public Route Model](/docs/?scope=studio&doc=public-route-model)
- no active builder, route shell, search runtime, Studio public-link helper, audit, or test requires `_works/`, `_series/`, `_work_details/`, or `_moments/`
- moment pages use `/moments/?moment=<moment_id>` and generated moment payloads
- `_config.yml` no longer defines retired work, series, work-detail, or moment collection outputs
- stale docs no longer describe legacy collection stubs as current public route dependencies
- broad compatibility aliases or redirect tables have not been added
