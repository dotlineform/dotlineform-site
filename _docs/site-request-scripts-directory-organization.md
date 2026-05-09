---
doc_id: site-request-scripts-directory-organization
title: Scripts Directory Organization Request
added_date: 2026-05-09
last_updated: "2026-05-09 15:32"
ui_status: proposed
parent_id: change-requests
sort_order: 212
viewable: true
---
# Scripts Directory Organization Request

Status: proposed.

## Purpose

Review and rationalize the `scripts/` directory layout so script location communicates ownership.
The immediate trigger is that `scripts/studio/catalogue_write_server.py` is catalogue-domain code, but most other catalogue modules live directly under `scripts/`.
That split makes the folder structure look accidental: some files are grouped by Studio runtime, some by data domain, and some are top-level because they predate the newer package-style boundaries.

The goal is to choose the right long-term structure rather than the lowest-churn structure.
After this request is implemented, the user should be able to look at `scripts/` and understand which code belongs to Catalogue, Analytics, Docs, Search, Studio runtime, local checks, media tooling, and shared script infrastructure.

## Current Problem

The current layout has useful subfolders, but their rule is inconsistent:

- `scripts/docs/` is a coherent Docs domain package containing the docs-management server, docs source-model helpers, import/export helpers, generated-read helpers, rebuild helpers, and docs route constants.
- `scripts/search/` currently contains search configuration, while the search builder entrypoint remains top-level as `scripts/build_search.rb`.
- `scripts/studio/` contains local Studio services such as `catalogue_write_server.py`, `tag_write_server.py`, and `audit_service.py`, but catalogue and Analytics tag domain helpers mostly do not live there.
- Catalogue has many top-level modules: `catalogue_source.py`, `catalogue_json_build.py`, `catalogue_lookup.py`, `catalogue_transactions.py`, `catalogue_routes.py`, `catalogue_publication.py`, and related helpers.
- Shared helpers such as `script_logging.py`, `studio_activity.py`, `pipeline_config.py`, and `display_paths.py` also live at top level, which is reasonable only if top level is explicitly treated as shared infrastructure plus stable entrypoints.

The result is not technically broken, but it creates avoidable navigation friction and makes future structural reviews harder.

## Desired Rule

Organize script files by ownership first, not by the UI page or local process that happens to call them.

UI/domain routing is the stronger architectural signal.
Script folders should follow the product/domain model rather than force it.
If a script's folder is hard to choose, treat that as useful evidence: either the domain model is still blurry, or the script mixes responsibilities that need to be separated before moving files.
For example, if Studio routes and docs say tags belong to Analytics but the local service still lives under `scripts/studio/`, that can be acceptable as historical placement, but it should not be mistaken for the target architecture.

Target rule:

- Domain packages own domain behavior.
- Runtime/server entrypoints live with the domain they mutate or serve, unless they are truly cross-domain Studio infrastructure.
- Top-level `scripts/` is reserved for stable cross-domain entrypoints and shared script infrastructure.
- Subfolders should be few, meaningful, and documented.
- Imports should point at the owning module path directly; do not keep broad compatibility re-exports after a move.

This implies that `catalogue_write_server.py` belongs with Catalogue code, not in a generic Studio folder.
It also implies that `tag_write_server.py` belongs with Analytics code, not in a generic Studio folder, because tags are the first implemented Analytics metadata layer over catalogue works and series.

## Target Structure Spec

Proposed target folders:

- `scripts/catalogue/`
  - Catalogue source model, lookup, field registry, save/build planning, publication/delete planning, prose import, workbook import, catalogue write server, catalogue route constants, catalogue transactions, and catalogue-specific validation/export helpers.
  - Candidate moves include current `catalogue_*` modules, `generate_work_pages.py` if it remains the internal catalogue JSON engine, `validate_catalogue_source.py`, `verify_catalogue_field_registry.py`, `export_catalogue_lookup.py`, and `migrate_catalogue_media_sections.py`.
- `scripts/docs/`
  - Keep as the Docs domain package.
  - Review whether `build_docs.rb` should move under `scripts/docs/` or remain a top-level stable entrypoint with clear documentation.
- `scripts/search/`
  - Search build configuration and search builder ownership.
  - Review whether `build_search.rb` should move under `scripts/search/` or remain a top-level stable entrypoint.
- `scripts/analytics/`
  - Analytics metadata and analysis services over catalogue works and series.
  - Candidate moves include `tag_write_server.py` and future tag helper modules extracted by the structural review.
  - Tags should be treated as the first implemented Analytics metadata layer, not as the whole Analytics model.
  - If broader Analytics registries and scoring workflows share the same local service, consider renaming `tag_write_server.py` to `analytics_server.py` instead of creating separate one-off servers.
- `scripts/studio/`
  - Studio runtime services that are not domain-specific, such as the audit service if it remains a Studio-resource service rather than a general checks command.
  - General-purpose admin and shared Studio functionality only; avoid placing domain-owned Catalogue or Analytics services here.
  - Do not use this folder as a catch-all for any localhost service.
- top-level `scripts/`
  - Cross-domain entrypoints such as `run_checks.py`.
  - Shared infrastructure modules such as script logging, shared Studio activity helpers, pipeline config loading, path display helpers, and other intentionally common utilities.
  - Small shell wrappers only when they are the stable public command surface and the implementation clearly lives under a domain package.

## Non-Goals

- Do not change runtime behavior, endpoint URLs, ports, request payloads, response payloads, backup behavior, generated output semantics, or dry-run behavior.
- Do not combine this with another large extraction of script internals.
- Do not move files only to reduce top-level file count.
- Do not leave permanent compatibility modules that make ownership ambiguous.
- Do not reorganize docs source folders, Studio route folders, generated data folders, or tests unless a script move requires test path updates.

## Implementation Plan

### Slice 1: inventory and move map

Produce a table of every current file under `scripts/`, excluding ignored generated caches, with:

- current path
- runnable entrypoint versus imported helper
- domain owner
- proposed target path
- public command examples that will need doc updates
- tests and docs that reference the path
- risk rating for import churn

Acceptance checks:

- the move map is reviewed before moving files
- every proposed top-level survivor has a reason
- every proposed subfolder has a short ownership rule

### Slice 2: catalogue package move

Move Catalogue-owned modules into `scripts/catalogue/`.
This is the highest-value slice because it resolves the observed inconsistency around `catalogue_write_server.py`.

Expected work:

- move catalogue source/model/build/helper modules into `scripts/catalogue/`
- move `scripts/studio/catalogue_write_server.py` into `scripts/catalogue/`
- update imports, `bin/dev-studio`, tests, script docs, request docs, and command examples
- choose one import style and apply it consistently
- keep endpoint contracts and local service behavior unchanged

Acceptance checks:

- catalogue check profile passes
- `catalogue_write_server.py` still starts from its new path
- `bin/dev-studio` starts the catalogue service through the new path
- no duplicate catalogue route constants or broad compatibility re-export modules remain
- docs examples use the new command path

### Slice 3: Analytics tags and Studio runtime boundary

Review `scripts/studio/tag_write_server.py` and `scripts/studio/audit_service.py`.

Expected decision:

- move tag behavior to `scripts/analytics/`, because tags are conceptually Analytics metadata applied to catalogue works and series
- keep audit service under `scripts/studio/` only if it is genuinely Studio-runtime infrastructure
- document why any service remains under `scripts/studio/`

Acceptance checks:

- tag-service command paths and `bin/dev-studio` wiring are updated if moved
- route migration from `/studio/tag-registry/` and `/studio/series-tags/` to `/studio/analytics/...` is either explicitly implemented in a UI/routing request or deliberately deferred
- focused tag tests still pass
- Studio audit docs still point at the correct path

### Slice 4: docs and search entrypoint consistency

Review top-level `build_docs.rb` and `build_search.rb`.

Decision options:

- move the implementation commands under `scripts/docs/` and `scripts/search/`, updating docs and callers
- keep top-level commands as stable cross-domain entrypoints, but document that they are top-level because they are common operational commands

Acceptance checks:

- docs/search build commands in repo docs match the chosen target
- docs and search check profiles still pass
- no stale command paths remain in `_docs/`, tests, or `bin/`

### Slice 5: shared infrastructure and final closeout

Review top-level shared modules and entrypoints after domain moves are complete.

Expected work:

- confirm which helpers should remain top-level shared infrastructure
- decide whether any shared package name is clearer than top-level helper modules
- update [Scripts](/docs/?scope=studio&doc=scripts) with the final folder rules
- update relevant script reference docs
- run targeted checks plus `./scripts/run_checks.py` profiles proportional to moved domains
- rebuild Studio docs/search payloads

Acceptance checks:

- `scripts/` root is small enough to scan and every remaining file has a documented reason
- domain packages have coherent ownership
- command examples use project-local paths
- no moved behavior is still tested through old path compatibility wrappers
- no stale path references remain in docs, tests, `bin/`, or CI-like check scripts

## Benefits

- makes script ownership visible from the filesystem
- removes the current Catalogue/Studio placement ambiguity
- gives future structural reviews a cleaner package boundary
- reduces the chance that new Catalogue helpers are added at top level by inertia
- clarifies whether top-level scripts are public entrypoints or shared infrastructure

## Risks

- moving many files can create import churn without behavior changes
- path updates can miss docs, tests, local service startup commands, or smoke helpers
- package-style imports may behave differently when scripts are run directly unless entrypoint patterns are chosen carefully
- command path changes can break local notes outside the repo
- broad compatibility wrappers would reduce short-term pain but undermine the ownership goal if left in place

## Open Questions

- Should `build_docs.rb` and `build_search.rb` move into domain folders, or are they stable enough operational entrypoints to remain top-level?
- Should Analytics tag scripts move directly under `scripts/analytics/`, or should temporary top-level `scripts/tag_*.py` modules be allowed during structural extraction?
- Should Studio tag UI routes be migrated under `/studio/analytics/` in the same broader sequence or tracked as a separate UI/routing request?
- Should shared helpers remain as top-level modules or move under a small `scripts/shared/` package?
- Are any root-level script command paths used outside the repo strongly enough to justify temporary deprecation wrappers?

## Recommended First Slice

Start with the inventory and move map.
Do not move files in that slice.
The first implementation slice should then move Catalogue-owned files together, because the current `scripts/studio/catalogue_write_server.py` placement is the clearest mismatch and Catalogue already has a completed ownership map from the script structural review.
