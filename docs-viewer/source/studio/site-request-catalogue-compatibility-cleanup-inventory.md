---
doc_id: site-request-catalogue-compatibility-cleanup-inventory
title: Inventory
added_date: 2026-05-01
last_updated: 2026-05-01
parent_id: site-request-catalogue-compatibility-cleanup
sort_order: 1000
---
# Inventory

Status:

- Task 1 inventory complete for implementation planning
- Task 2 retention direction recorded

## Purpose

This is the Task 1 inventory for [Compatibility Cleanup](/docs/?scope=studio&doc=site-request-catalogue-compatibility-cleanup).

Use this document to record retained catalogue compatibility paths before deciding whether each path should be kept, narrowed, moved into the active JSON-source pipeline, or removed.

## Classification

Use these classifications consistently:

- `active-live`
  Part of the current canonical JSON-source workflow.
- `active-import-adapter`
  Part of a current import workflow that converts a non-canonical input into canonical JSON.
- `editor-only`
  Needed only by Studio editing or review surfaces.
- `derived`
  Generated from canonical source and not independently editable.
- `migration-only`
  Retained for a bounded migration or comparison workflow.
- `deprecated-clean-exit`
  Retained only to exit with guidance instead of running an old workflow.
- `removable`
  No current active, migration, or clean-exit role identified.
- `docs-stale`
  Documentation appears to describe a retired workflow as current, or needs wording clarified.

## Findings

| ID | Surface | Location | Live workflow? | Classification | Finding | Proposed action | Verification |
|---|---|---|---|---|---|---|---|
| CCI-001 | Bulk-import workbook input | `_data/pipeline.json`; `data/works_bulk_import.xlsx`; `studio/bulk-add-work/index.md`; `assets/studio/js/bulk-add-work.js`; `studio/app/server/studio/catalogue_write_server.py` | yes | `active-import-adapter` | `data/works_bulk_import.xlsx` is still an active staging input for new works and work details. It is distinct from retired canonical editing through `data/works.xlsx`. | Keep the workflow. Treat Excel parsing as an import adapter that must write only canonical JSON-shaped source records. | Preview/apply import still reads the configured workbook path, skips duplicate source ids, writes only canonical JSON, and never writes back to Excel. |
| CCI-002 | Workbook import implementation helpers | `scripts/catalogue_workbook_import.py`; `scripts/catalogue_source.py` | yes | `active-import-adapter` | The active bulk importer reads `Works` and `WorkDetails` sheets and previously reused workbook-era row helpers from `scripts/catalogue_source.py`. | Implemented first slice: `header_map` and `cell` now live beside `scripts/catalogue_workbook_import.py`. Keep shared normalization only where it describes canonical JSON shape, not workbook mechanics. | Bulk-import preview/apply still validates new works/details, produces normalized canonical records, and blocks invalid workbook rows. |
| CCI-003 | Deprecated canonical workbook references | docs and deprecated scripts mentioning `data/works.xlsx`, including historical pipeline docs and deleted retired scripts | no for live JSON-source workflow | `docs-stale` | Implemented for current docs: stale workbook-led guides were replaced with concise archive stubs or rewritten to route users to Studio, canonical JSON source, and scoped JSON builds. | Keep only narrow historical/change-request references. Do not preserve script files solely for habit-compatible clean exits. | Docs search for `data/works.xlsx` has no stale live-workflow references outside cleanup records and historical change-log entries. |
| CCI-004 | Direct `generate_work_pages.py` entrypoint | `scripts/generate_work_pages.py` | no direct user workflow | `deprecated-clean-exit` | Direct use without `--internal-json-source-run` exits with guidance and states direct generation is retired. | Keep the direct generator clean exit because the internal generator remains a live implementation dependency of `catalogue_json_build.py`. Do not let the clean-exit path preserve workbook helper placement or workbook-era runtime assumptions. | Running the deprecated direct command exits cleanly with guidance. |
| CCI-005 | Source metadata provenance | `assets/studio/data/catalogue/meta.json`; `scripts/catalogue_source.py` | no | `removable` | Implemented: `source.created_from` no longer records `data/works.xlsx`, and source metadata generation no longer emits workbook provenance. | Keep `meta.json` focused on current canonical JSON source metadata. Do not add replacement compatibility metadata for the retired workbook pipeline. | Catalogue source validation and generated metadata remain deterministic. |
| CCI-006 | Work file/link compatibility records | `scripts/catalogue_source.py`; `scripts/catalogue_lookup.py`; `studio/app/server/studio/catalogue_write_server.py` | no | `removable` | Implemented: live source records no longer expose derived `work_files` or `work_links` compatibility maps. `downloads` and `links` remain canonical arrays on work records. | Keep file/link editing on the parent work record. Retained workbook import helpers may read legacy `WorkFiles` / `WorkLinks` sheets only to fold them into work-owned fields. | Work editor file/link saves, work delete preview/apply, source validation, lookup export, and field-aware build previews still behave correctly without `work_files` / `work_links`. |
| CCI-007 | Workbook-shaped internal generator projection | `scripts/generate_work_pages.py` | no | removed | The live JSON-source generator previously used worksheet-like rows, header maps, and `cell(...)` access internally after loading canonical JSON. That shape was no longer justified by an external workbook contract. | Removed. `generate_work_pages.py` now builds work, series, and work-detail artifacts from canonical source records directly, and per-series sort rules come from `series.<id>.sort_fields`. | Scoped work, detail, series, and moment previews still select the same artifacts and produce deterministic output. |
| CCI-008 | Deprecated workbook-led scripts | `scripts/build_catalogue.py`; `scripts/copy_draft_media_files.py`; `scripts/export_catalogue_source.py`; `scripts/compare_catalogue_sources.py`; `scripts/backfill_recent_index_from_git_history.py`; `scripts/catalogue_preflight.py`; `scripts/delete_work.py` | no | removed | Implemented: retired workbook-led entrypoints and adjacent cleanup/backfill/preflight commands were removed. | Do not reintroduce clean-exit stubs for scripts that are not needed to directly support Studio pages. | Python script scan leaves workbook references only in the active bulk-import adapter, pipeline config, and Studio write-server wiring. |
| CCI-009 | Stale workbook workflow docs | `docs-viewer/source/studio/pipeline-use-cases.md`; `docs-viewer/source/studio/source-model.md`; `docs-viewer/source/studio/current-pipeline-map.md`; `docs-viewer/source/studio/web-system-spec.md`; script docs that mentioned retired workbook or file/link workflow input | no | `docs-stale` | Implemented for current docs: current pipeline, source-utility, script, search, and request docs no longer present retired workbook or standalone file/link source paths as live workflows. | Keep the docs surface focused on current JSON-source and Studio/import workflows. Leave detailed script-behavior cleanup to slice 5. | Docs search still finds cleanup/change-log history, but not current workflow guidance telling users to use retired workbook or standalone file/link paths. |
| CCI-010 | Activity affected keys for retired file/link maps | `scripts/activity_log.py`; `assets/studio/js/activity.js`; activity payload docs | no | `removable` | Implemented: activity feed shaping and UI summaries no longer expose `work_files` or `work_links` as affected source families. | Keep activity affected groups aligned to current source families: works, work details, series, and moments. | Catalogue activity still renders affected works/details/series/moments and does not show obsolete files/links families. |

## Bulk Import Boundary

`data/works_bulk_import.xlsx` should not be treated as the same compatibility problem as retired `data/works.xlsx` canonical editing.

Current intended boundary:

- Excel is a staging input for new works and new work details.
- Preview/apply endpoints convert workbook rows into canonical JSON records.
- Existing source records are skipped, not overwritten.
- The importer writes canonical JSON only.
- The importer does not write back to Excel.

Cleanup should therefore move workbook parsing into a clearly named import adapter, not remove the active bulk-import workflow.

## Retention Direction

Implementation should be designed as if the scripts were being created new and the old `data/works.xlsx` pipeline did not exist.

Practical consequences:

- Do not conduct a compatibility cleanup that leaves compatibility artifacts behind.
- Do not keep helpers in a location only because the workbook pipeline previously used them there.
- Place workbook-specific row parsing beside the active bulk-import adapter.
- Keep shared helpers only when they describe canonical JSON-source behavior.
- Remove `data/works.xlsx` references from current docs unless a historical request or change-log entry clearly needs it.
- Remove `work_files` and `work_links` compatibility maps rather than reclassifying them as current derived artifacts.

## Resolved Questions

- Workbook row helpers such as `header_map` and `cell` should move closer to `scripts/catalogue_workbook_import.py`.
- `assets/studio/data/catalogue/meta.json` should not continue recording original migration provenance from `data/works.xlsx`.
- Current docs should not keep `data/works.xlsx` references as useful workflow or historical context.
- `work_files` and `work_links` are not needed by current editor, lookup, delete, or validation paths after work-owned `downloads` and `links` became canonical.

## Task 3 Slices

Use this order for cleanup implementation:

1. Done: move workbook row helpers into the active bulk-import adapter boundary.
2. Done: remove `data/works.xlsx` provenance from catalogue source metadata.
3. Done: remove `work_files` and `work_links` compatibility maps and dependent lookup/delete/activity handling.
4. Done: remove or rewrite stale `data/works.xlsx`, `WorkFiles`, and `WorkLinks` docs.
5. Done: remove deprecated workbook-led scripts and their active docs surface.
6. Done: refactor internal generator worksheet/proxy access to direct JSON-record access.

## Slice Coverage

| Slice | Related findings | Coverage | Follow-up notes |
|---|---|---|---|
| 1. Bulk-import helper boundary | CCI-001, CCI-002 | Complete for row helper ownership. | Bulk import remains an active one-way adapter from the configured workbook into canonical JSON source records. |
| 2. Metadata provenance removal | CCI-005 | Complete. | Obsolete `data/works.xlsx` source provenance was removed without adding replacement compatibility metadata. |
| 3. Remove file/link compatibility maps | CCI-006, CCI-010 | Complete. | Live source records no longer include file/link compatibility maps; activity affected groups no longer show obsolete file/link families. |
| 4. Stale docs cleanup | CCI-003, CCI-009 | Complete for current docs. | Cleanup/change-log history still contains explicit retired-path terms by design; script implementation strings are deferred to slice 5. |
| 5. Deprecated script cleanup | CCI-004, CCI-008 | Complete. | Retired workbook-led scripts were removed. Direct `generate_work_pages.py` clean-exit behavior remains separately owned by CCI-004 because the file is still an internal generator dependency. |
| 6. Generator projection refactor | CCI-007 | Complete. | Source write-back no longer rebuilds from projection, proxy worksheet/cell wrappers were removed, and retained header-indexed row-list reads were replaced with direct canonical source-record access. |

## Verification Matrix

| Slice | Codex-run checks | Manual checks |
|---|---|---|
| Bulk-import adapter helper move | `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick --profile catalogue`; bulk import preview endpoint if the local catalogue server is in scope | Open `/studio/bulk-add-work/`, confirm configured workbook path displays, preview works/details import if sample rows are available |
| Metadata provenance removal | catalogue source validation; docs/search rebuild when docs change | Confirm Studio catalogue pages still load source metadata without showing obsolete `works.xlsx` provenance |
| `work_files` / `work_links` removal | source validation; lookup export; field-aware `downloads` preview; work delete preview if local server is in scope | In Work editor, add/remove a download and link; preview public update; confirm delete preview no longer reports obsolete file/link source families |
| Stale docs cleanup | `./docs-viewer/build/build_docs.rb --scope studio --write`; `./docs-viewer/build/build_search.rb --scope studio --write`; docs search for `data/works.xlsx`, `WorkFiles`, `WorkLinks` | Review Docs Viewer search results for stale workbook workflow wording |
| Deprecated script cleanup | scan Python scripts for retired workbook references; `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick` | Confirm script docs route users to current JSON-source commands |
| Generator projection refactor | `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick --profile catalogue`; representative dry-run previews for work/detail/series/moment scopes; Jekyll build if generated output changes | Spot-check public work/detail/series/moment pages touched by the representative scope |

## Task 4 Verification Result

Status:

- completed

Codex-run checks completed:

- generated representative work, work-detail, series, per-record JSON, aggregate JSON, recent index, and Studio storage artifacts into an isolated temp output
- compared generated temp artifacts against checked-in artifacts after normalizing volatile `generated_at_utc` values
- seeded the temp recent index from the checked-in recent index before comparison because that artifact intentionally retains existing recent-publication state
- confirmed deprecated workbook-led commands exited cleanly with guidance before the final removal slice
- exported a temp Studio lookup payload set and confirmed current work/detail/series contracts plus absence of retired `work_files` and `work_links` lookup folders
- confirmed catalogue field registry verification passes and retired fields are not active rule fields

Manual follow-up remains light-touch:

- open representative public work, detail, and series pages touched by work `00001` and series `009`
- open the Work, Work Detail, and Series Studio editors for the same records if UI confidence is needed before a real write run
