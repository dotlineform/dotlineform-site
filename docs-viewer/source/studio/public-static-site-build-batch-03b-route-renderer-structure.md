---
doc_id: public-static-site-build-batch-03b-route-renderer-structure
title: Public Static Site Build Batch 3b Route Renderer Structure
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 3b Route Renderer Structure

This is the delivery specification for the inserted Batch 3b in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: split the Batch 3 route renderer into maintainable route-owner modules before Batch 4 adds asset-copy and smoke-test dependencies around the generated route shells.

## Steer for these tasks

- Keep the refactor behavior-preserving. Generated route files, DOM ids, data attributes, script tags, stylesheet tags, and route output paths must remain equivalent to Batch 3.
- Keep `routes.py` as the route registry so there is one small file that answers which public pages the builder emits.
- Move long route-specific HTML contracts out of `routes.py` into owner modules.
- Keep shared document helpers in `render.py`.
- Keep catalogue pipeline helpers with the catalogue route owner for this batch.
- Do not add a template engine, compatibility route aliases, bundling, generated payload ownership, or asset-copy behavior in this batch.
- Do not start Batch 4 until this structure is complete or explicitly deferred.

## Target module ownership

| module | owner |
| --- | --- |
| `public_site_builder.routes` | Thin route registry mapping output paths to route renderer calls. |
| `public_site_builder.static_routes` | `/`, `/about/`, and `/404.html`. |
| `public_site_builder.catalogue_routes` | `/series/`, `/recent/`, `/works/`, `/work-details/`, `/moments/`, and `/catalogue/search/`. |
| `public_site_builder.docs_routes` | `/library/` and `/analysis/` public Docs Viewer route shells. |
| `public_site_builder.render` | Shared document shell, head metadata, navigation, footer, asset URL helpers, script/style tags, and Docs Viewer mount helper. |

Do not create `public_site_builder.pipeline` in the first pass. Keep catalogue pipeline helpers in `catalogue_routes.py`; create a separate pipeline module in a later change only after a second non-catalogue owner needs those helpers.

## Deliverables

- Route renderer modules split according to the target ownership table.
- `routes.py` reduced to a readable registry and orchestration layer.
- Focused tests that still prove the static artifact contains the required route files and no Liquid tokens.
- A short durable guidance note in this document that names the module boundaries for future route additions.

## Implementation and policy guidance

- Prefer moving functions intact before making small naming cleanups.
- Keep imports directional: registry imports route-owner modules; route-owner modules import shared render helpers; shared render helpers do not import route-owner modules.
- Keep route-output path strings centralized in `routes.py`.
- Add a new route by choosing the owner module first, then registering its output path in `routes.py`.

## Proposed verification set

- `$HOME/miniconda3/bin/python3 -m py_compile public-site/build/build_site.py public-site/build/public_site_builder/*.py`
- `$HOME/miniconda3/bin/python3 -m pytest public-site/tests/test_build_site.py`
- `$HOME/miniconda3/bin/python3 public-site/build/build_site.py --destination _public_site --audit`
- `rg -n '\{\{|\{%' _public_site --glob '*.html'` returns no matches.
- `git diff --check`

## Tasks

### Batch 3b: Route Renderer Structure

| ID | status | action |
| --- | --- | --- |
| 3b.1 | planned | Move `/`, `/about/`, and `/404.html` rendering from `routes.py` to `static_routes.py`. |
| 3b.2 | planned | Move catalogue, work, work-detail, moment, and catalogue-search rendering from `routes.py` to `catalogue_routes.py`. |
| 3b.3 | planned | Move `/library/` and `/analysis/` public Docs Viewer rendering from `routes.py` to `docs_routes.py`. |
| 3b.4 | planned | Keep `routes.py` as a thin registry that loads shared data once and maps output files to renderer calls. |
| 3b.5 | planned | Confirm generated route HTML remains Liquid-free and script/style references remain equivalent to Batch 3. |
| 3b.6 | planned | Record durable route-renderer module guidance in this document for future route additions. |

## completed verification

- Not started.

## follow-on tasks

- Batch 4 must use the post-refactor route-owner boundaries when adding asset copy checks and browser smoke coverage.

## batch close

- Set this batch status and front matter `ui_status` to `done` after the behavior-preserving module split is verified.
- Keep Batch 4 planned until the route renderer structure is complete or an explicit deferral is recorded.
