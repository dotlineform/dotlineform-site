---
doc_id: site-request-catalogue-compatibility-cleanup-inventory
title: Inventory
added_date: 2026-05-01
last_updated: 2026-05-01
parent_id: site-request-catalogue-compatibility-cleanup
sort_order: 10
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
| CCI-001 | Bulk-import workbook input | `_data/pipeline.json`; `data/works_bulk_import.xlsx`; `studio/bulk-add-work/index.md`; `assets/studio/js/bulk-add-work.js`; `scripts/studio/catalogue_write_server.py` | yes | `active-import-adapter` | `data/works_bulk_import.xlsx` is still an active staging input for new works and work details. It is distinct from retired canonical editing through `data/works.xlsx`. | Keep the workflow. Treat Excel parsing as an import adapter that must write only canonical JSON-shaped source records. | Preview/apply import still reads the configured workbook path, skips duplicate source ids, writes only canonical JSON, and never writes back to Excel. |
| CCI-002 | Workbook import implementation helpers | `scripts/catalogue_workbook_import.py`; `scripts/catalogue_source.py` | yes | `active-import-adapter` | The active bulk importer reads `Works` and `WorkDetails` sheets and reuses workbook-era helpers such as `header_map`, `cell`, `WORK_FIELDS`, `DETAIL_FIELDS`, and source normalization helpers. | Move workbook row helpers such as `header_map` and `cell` closer to `scripts/catalogue_workbook_import.py`. Keep shared normalization only where it describes canonical JSON shape, not workbook mechanics. | Bulk-import preview/apply still validates new works/details, produces normalized canonical records, and blocks invalid workbook rows. |
| CCI-003 | Deprecated canonical workbook references | docs and deprecated scripts mentioning `data/works.xlsx`, including historical pipeline docs and clean-exit scripts | no for live JSON-source workflow | `docs-stale` | `data/works.xlsx` is no longer part of intended workflow and has little ongoing historical value in user-facing docs. It remains in the repo only as a backup of historical data state until a formal catalogue backup is defined. | Remove or rewrite doc references so current docs no longer present `data/works.xlsx` as useful workflow context. Keep only unavoidable deprecated-command guidance if a command must explain why it exits. | Docs search for `data/works.xlsx` has no stale live-workflow references. |
| CCI-004 | Direct `generate_work_pages.py` entrypoint | `scripts/generate_work_pages.py` | no direct user workflow | `deprecated-clean-exit` | Direct use without `--internal-json-source-run` exits with guidance and states workbook-led direct generation is retired. | Keep only if still needed as a user-facing clean exit during cleanup. Do not let the clean-exit path preserve workbook helper placement or workbook-era runtime assumptions. | Running the deprecated direct command exits cleanly with guidance until the clean-exit contract is intentionally retired. |
| CCI-005 | Source metadata provenance | `assets/studio/data/catalogue/meta.json` | no | `removable` | `source.created_from` still records `data/works.xlsx`, but `works.xlsx` is no longer in use and is kept only as a backup of historical data state. | Remove this provenance or replace it with current canonical JSON ownership metadata that does not refer to `data/works.xlsx`. | Catalogue source validation and generated metadata remain deterministic. |
| CCI-006 | Work file/link compatibility records | `scripts/catalogue_source.py`; `scripts/catalogue_lookup.py`; `scripts/studio/catalogue_write_server.py` | no | `removable` | `downloads` and `links` are canonical arrays on work records. `work_files` and `work_links` are no longer needed by current editor, lookup, delete, or validation paths. | Remove retained `work_files` and `work_links` compatibility maps rather than preserving them as derived compatibility artifacts. | Work editor file/link saves, work delete preview/apply, source validation, lookup export, and field-aware build previews still behave correctly without `work_files` / `work_links`. |
| CCI-007 | Workbook-shaped internal generator projection | `scripts/generate_work_pages.py` | yes, as internal implementation shape | `active-live` needing refactor | The live JSON-source generator still uses worksheet-like rows, header maps, and `cell(...)` access internally after loading canonical JSON. That shape is no longer justified by an external workbook contract. | Refactor toward direct JSON-record access in focused slices. Do not preserve worksheet/proxy abstractions simply because the old pipeline used them. | Scoped work, detail, series, and moment previews still select the same artifacts and produce deterministic output. |
| CCI-008 | Deprecated workbook-led scripts | `scripts/build_catalogue.py`; `scripts/copy_draft_media_files.py`; `scripts/export_catalogue_source.py`; `scripts/compare_catalogue_sources.py` | no live workflow, except explicit migration/comparison if still retained | `deprecated-clean-exit` / `removable` | Several retained scripts still default to, describe, or compare against `data/works.xlsx`. Some are already deprecated reference entrypoints; others may only remain for transition diagnostics. | Either keep a minimal clean-exit path with current guidance or remove the script from active docs. Do not keep full workbook-led behavior as hidden compatibility. | Deprecated commands that remain exit cleanly with guidance; active docs no longer route users to workbook-led flows. |
| CCI-009 | Stale workbook workflow docs | `_docs_src/pipeline-use-cases.md`; `_docs_src/source-model.md`; `_docs_src/current-pipeline-map.md`; `_docs_src/web-system-spec.md`; script docs that still mention `data/works.xlsx` as workflow input | no | `docs-stale` | Current docs still contain many `data/works.xlsx`, worksheet, `WorkFiles`, and `WorkLinks` workflow references. The retained workbook file has no intended future operational role. | Remove or rewrite stale references. Prefer current JSON-source and Studio/import workflows. Keep only narrow deprecated-command notes where necessary. | Docs search for `data/works.xlsx`, `WorkFiles`, and `WorkLinks` no longer suggests current workflow usage. |
| CCI-010 | Activity affected keys for retired file/link maps | `scripts/catalogue_activity.py`; `assets/studio/js/catalogue-activity.js`; activity payload docs | partial display only | `removable` | Activity summaries still know about `work_files` and `work_links` affected collections. Once compatibility maps are removed, these keys should not remain as current affected-source families. | Remove affected-key handling for `work_files` and `work_links`, or replace with work-owned `downloads` / `links` field reporting if still useful. | Catalogue activity still renders affected works/details/series/moments and does not show obsolete files/links families. |

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
- Remove `data/works.xlsx` references from current docs unless a deprecated command must explain its clean exit.
- Remove `work_files` and `work_links` compatibility maps rather than reclassifying them as current derived artifacts.

## Resolved Questions

- Workbook row helpers such as `header_map` and `cell` should move closer to `scripts/catalogue_workbook_import.py`.
- `assets/studio/data/catalogue/meta.json` should not continue recording original migration provenance from `data/works.xlsx`.
- Current docs should not keep `data/works.xlsx` references as useful workflow or historical context.
- `work_files` and `work_links` are not needed by current editor, lookup, delete, or validation paths after work-owned `downloads` and `links` became canonical.

## Task 3 Slices

Use this order for cleanup implementation:

1. Move workbook row helpers into the active bulk-import adapter boundary.
2. Remove `data/works.xlsx` provenance from catalogue source metadata.
3. Remove `work_files` and `work_links` compatibility maps and dependent lookup/delete/activity handling.
4. Remove or rewrite stale `data/works.xlsx`, `WorkFiles`, and `WorkLinks` docs.
5. Simplify deprecated workbook-led scripts to clean exits or remove their active docs surface.
6. Refactor internal generator worksheet/proxy access toward direct JSON-record access in smaller follow-up slices.

## Verification Matrix

| Slice | Codex-run checks | Manual checks |
|---|---|---|
| Bulk-import adapter helper move | `./scripts/run_checks.py --profile quick --profile catalogue`; bulk import preview endpoint if the local catalogue server is in scope | Open `/studio/bulk-add-work/`, confirm configured workbook path displays, preview works/details import if sample rows are available |
| Metadata provenance removal | catalogue source validation; docs/search rebuild when docs change | Confirm Studio catalogue pages still load source metadata without showing obsolete `works.xlsx` provenance |
| `work_files` / `work_links` removal | source validation; lookup export; field-aware `downloads` preview; work delete preview if local server is in scope | In Work editor, add/remove a download and link; preview public update; confirm delete preview no longer reports obsolete file/link source families |
| Stale docs cleanup | `./scripts/build_docs.rb --scope studio --write`; `./scripts/build_search.rb --scope studio --write`; docs search for `data/works.xlsx`, `WorkFiles`, `WorkLinks` | Review Docs Viewer search results for stale workbook workflow wording |
| Deprecated script cleanup | run retained deprecated commands and confirm clean-exit guidance; `./scripts/run_checks.py --profile quick` | Confirm script docs route users to current JSON-source commands |
| Generator projection refactor | `./scripts/run_checks.py --profile quick --profile catalogue`; representative dry-run previews for work/detail/series/moment scopes; Jekyll build if generated output changes | Spot-check public work/detail/series/moment pages touched by the representative scope |
