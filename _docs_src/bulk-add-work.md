---
doc_id: bulk-add-work
title: Bulk Add Work
last_updated: 2026-04-19
parent_id: studio
sort_order: 33
---

# Bulk Add Work

Route:

- `/studio/bulk-add-work/`

This page runs the configured bulk-import workbook flow from `data/works_bulk_import.xlsx` into canonical catalogue source JSON.

## Current Scope

The first implementation covers one route with two modes:

- `works`
  - import new work records only
- `work details`
  - import new work-detail records only

Current rules:

- workbook source is configured in `_data/pipeline.json` and currently points to `data/works_bulk_import.xlsx`
- imports are one-way into canonical JSON
- imported records default to `draft`
- workbook `status` fields are ignored
- existing source records are reported as duplicates, not updated
- works import requires referenced series to already exist
- work-details import requires the parent work to already exist
- blocked rows must be fixed in the workbook before apply
- future workbook column changes are treated as explicit pipeline change requests rather than something the importer is expected to discover and adapt to automatically

Current workbook check:

- `Works` retains the required headers `work_id`, `series_ids`, and `title`
- `WorkDetails` retains the required headers `work_id`, `detail_id`, and `title`
- every additional retained header in the current workbook is already an eligible import field
- no current workbook headers fall outside the importer's recognized field set

## Preview And Apply

Current flow:

1. choose import mode
2. `POST /catalogue/import-preview` reads the configured workbook path and reports:
   - candidate row count
   - importable row count
   - duplicate row count
   - blocked row count
   - blocked reasons and sample rows
3. if the preview has blocked rows, apply is disabled
4. `POST /catalogue/import-apply` re-runs the same plan and writes only new records into canonical source JSON
5. successful apply refreshes derived lookup payloads and writes an aggregated Catalogue Activity entry

This page does not upload workbook files, edit workbook rows, or write anything back into Excel.

## Related References

- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
