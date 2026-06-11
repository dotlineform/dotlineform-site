---
doc_id: public-legacy-collections-cleanup
title: Public Legacy Collections Cleanup
added_date: 2026-06-11
last_updated: 2026-06-11
parent_id: studio
viewable: true
---
# Public Legacy Collections Cleanup

This document tracks the cleanup needed to retire legacy public catalogue Jekyll collections after the public route model moved to fixed shells plus generated JSON.

The route authority is [Public Route Model](/docs/?scope=studio&doc=public-route-model).

## Objective

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
- `/moments/<moment_id>/`
- `/catalogue/search/`

Work, series, and work-detail pages should not require one generated HTML file per record.
Moment path pages may remain public routes, but they should be generated from public moment records or generated public moment payloads, not from `_moments` stubs as a durable contract.

## Current State

The live work route uses `/works/?work=<work_id>`.
For example, `https://www.dotlineform.com/works/?series=105&work=00008` is rendered by `works/index.md`, `assets/js/public-catalogue-runtime.js`, `assets/works/index/00008.json`, and `assets/data/series_index.json`.

The legacy collection outputs still exist because `_config.yml` still defines public collections and default layouts:

- `works` with `layout: work` and permalink `/works/:name/`
- `series` with `layout: series` and permalink `/series/:name/`
- `work_details` with `layout: work_details` and permalink `/work_details/:name/`
- `moments` with `layout: moment` and permalink `/moments/:name/`

Generated stubs are intentionally minimal or empty.
They are no longer the canonical source of public page metadata or prose.

## Why This Is Wide

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

## Target Ownership

After cleanup, public catalogue route ownership should be:

| Area | Owner |
| --- | --- |
| Route contract | `docs-viewer/source/studio/public-route-model.md` |
| Shared URL helpers | `assets/js/public-catalogue-runtime.js` |
| Series browse shell | `series/index.md` |
| Work browse/selected shell | `works/index.md` |
| Work-detail shell | `work-details/index.md` |
| Moment page shell | replacement moment route generator, without `_moments` as a required input contract |
| Public work payloads | `assets/works/index/<work_id>.json` |
| Public series payloads | `assets/series/index/<series_id>.json` |
| Public moment payloads | `assets/moments/index/<moment_id>.json` |
| Shared public indexes | `assets/data/series_index.json`, `assets/data/works_index.json`, `assets/data/moments_index.json` |
| Search payload | `assets/data/search/catalogue/index.json` |

## Non-Goals

- Do not add compatibility redirects for retired path-style routes.\
- Do not emit recovery pages for `/works/<work_id>/`, `/series/<series_id>/`, `/work_details/<detail_uid>/`, or other retired path-style catalogue routes.
- Do not restore broad route aliases for `/works/<work_id>/`, `/series/<series_id>/`, or `/work_details/<detail_uid>/`.
- Do not make generated public payloads serialize derivable route URLs.
- Do not remove Jekyll itself in this cleanup.

## Cleanup Plan

### Phase 1: Inventory

Confirm active consumers for each collection family:

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

### Phase 2: Work, Series, And Detail Route Retirement

Retire the legacy work, series, and work-detail collection outputs first.
These have direct canonical query-state replacements:

- `/works/<work_id>/` -> retired; canonical route is `/works/?work=<work_id>`
- `/series/<series_id>/` -> retired; canonical route is `/series/?series=<series_id>`
- `/work_details/<detail_uid>/` -> retired; canonical route is `/work-details/?detail=<detail_uid>`

Implementation work:

- stop writing `_works/*.md`, `_series/*.md`, and `_work_details/*.md` where they are only route anchors
- remove collection defaults and output rules for those retired route families from `_config.yml`
- remove or archive `_layouts/work.html`, `_layouts/series.html`, and `_layouts/work_details.html` after no active collection uses them
- update cleanup and delete plans so they remove generated JSON/index/search artifacts, not collection stubs
- update audits to validate canonical shells and generated payloads instead of requiring route-anchor stubs
- update tests that assert `_works`, `_series`, or `_work_details` artifact paths
- update docs that describe those stubs as current build constraints

Verification:

- public route smoke for `/series/`, `/series/?series=<id>`, `/works/?work=<id>`, and `/work-details/?detail=<id>`
- catalogue search result URL smoke
- site consistency audit with the retired collection paths removed from required targets
- scoped catalogue build tests for work, series, and work-detail changes
- public Jekyll build with no generated collection pages for retired work, series, and detail routes

### Phase 3: Moment Route Replacement

The cleanup target is not "delete moment pages"; it is "stop treating `_moments` stubs as the route-input contract." `/moments/<moment_id>/` should move to generated non-collection pages.

- move moment page generation into a non-collection fixed build step. generate moment pages from `assets/moments/index/<moment_id>.json` without writing `_moments/*.md`

Verification:

- replacement public builder validation

### Phase 4: Docs And Contract Cleanup

Update the durable docs after implementation decisions land.
Likely affected docs:

- [Data Flow](/docs/?scope=studio&doc=data-flow)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Catalogue Source Model](/docs/?scope=studio&doc=data-models-catalogue-source)
- [Catalogue Indexes And Payloads](/docs/?scope=studio&doc=data-models-catalogue-indexes)
- [Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Site Consistency Audit](/docs/?scope=studio&doc=scripts-audit-site-consistency)
- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)

- No new audit is required solely for the "no work, series, or detail collection stubs are required" owner contract.
  Use the existing focused route, build, and test checks for the implementation slice.

## Completion Criteria

This cleanup is complete when:

- first-party public navigation uses only canonical shell routes from [Public Route Model](/docs/?scope=studio&doc=public-route-model)
- no active builder, route shell, search runtime, Studio public-link helper, audit, or test requires `_works/`, `_series/`, or `_work_details/`
- moment pages no longer require `_moments/` as a durable route-input contract
- `_config.yml` no longer defines retired work, series, or work-detail collection outputs
- stale docs no longer describe legacy collection stubs as current public route dependencies
- broad compatibility aliases or redirect tables have not been added
