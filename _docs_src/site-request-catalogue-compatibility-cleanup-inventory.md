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

- initial findings started

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
| CCI-002 | Workbook import implementation helpers | `scripts/catalogue_workbook_import.py`; `scripts/catalogue_source.py` | yes | `active-import-adapter` | The active bulk importer reads `Works` and `WorkDetails` sheets and reuses workbook-era helpers such as `header_map`, `cell`, `WORK_FIELDS`, `DETAIL_FIELDS`, and source normalization helpers. | Keep normalization shared where it defines canonical JSON shape, but consider moving workbook parsing helpers behind an import-adapter boundary so live source helpers are not workbook-shaped by default. | Bulk-import preview/apply still validates new works/details, produces normalized canonical records, and blocks invalid workbook rows. |
| CCI-003 | Deprecated canonical workbook references | docs and deprecated scripts mentioning `data/works.xlsx`, including historical pipeline docs and clean-exit scripts | no for live JSON-source workflow | `docs-stale` or `deprecated-clean-exit` | Some references are historical or clean-exit guidance, while others may still read like live workflow documentation. These need classification before editing. | Classify each reference as historical, deprecated clean-exit, or stale live-doc wording. Update only stale live-doc wording. | Docs search for `data/works.xlsx` shows only historical, migration, or deprecated-clean-exit references after cleanup. |
| CCI-004 | Direct `generate_work_pages.py` entrypoint | `scripts/generate_work_pages.py` | no direct user workflow | `deprecated-clean-exit` | Direct use without `--internal-json-source-run` exits with guidance and states workbook-led direct generation is retired. | Keep unless the clean-exit contract is intentionally retired. Ensure docs route users through `./scripts/catalogue_json_build.py`. | Running the deprecated direct command exits cleanly with guidance. |
| CCI-005 | Source metadata provenance | `assets/studio/data/catalogue/meta.json` | yes, as metadata | `migration-only` | `source.created_from` still records `data/works.xlsx`, reflecting original migration provenance rather than current canonical ownership. | Decide whether to keep as historical provenance, rename to clearer migration metadata, or remove if it causes confusion. | Catalogue source validation and generated metadata remain deterministic. |
| CCI-006 | Work file/link compatibility records | `scripts/catalogue_source.py`; `scripts/catalogue_lookup.py`; `scripts/studio/catalogue_write_server.py` | partial derived compatibility | `derived` / `migration-only` | `downloads` and `links` are canonical arrays on work records, but `work_files` and `work_links` maps are still derived and passed through source records, lookup cleanup, delete planning, and validation. | Decide whether these maps are still needed as derived compatibility rows or can be narrowed/removed after confirming editor and delete-flow dependencies. | Work editor file/link saves, work delete preview/apply, source validation, and lookup export still behave correctly. |

## Bulk Import Boundary

`data/works_bulk_import.xlsx` should not be treated as the same compatibility problem as retired `data/works.xlsx` canonical editing.

Current intended boundary:

- Excel is a staging input for new works and new work details.
- Preview/apply endpoints convert workbook rows into canonical JSON records.
- Existing source records are skipped, not overwritten.
- The importer writes canonical JSON only.
- The importer does not write back to Excel.

Cleanup should therefore move any reusable legacy parsing into a clearly named import adapter, not remove the active bulk-import workflow.

## Open Questions

- Should workbook row helpers such as `header_map` and `cell` remain in `scripts/catalogue_source.py`, or move closer to `scripts/catalogue_workbook_import.py`?
- Should `assets/studio/data/catalogue/meta.json` continue recording original migration provenance from `data/works.xlsx`?
- Which `data/works.xlsx` doc references are historical context and which are stale live-workflow guidance?
- Are `work_files` and `work_links` still needed by any current editor, lookup, delete, or validation path after work-owned `downloads` and `links` became canonical?
