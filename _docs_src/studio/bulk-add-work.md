---
doc_id: bulk-add-work
title: Bulk Add Work
last_updated: 2026-04-18
parent_id: studio
sort_order: 33
---

# Bulk Add Work

Route:

- `/studio/bulk-add-work/`

This page runs the fixed-workbook import flow from `data/works.xlsx` into canonical catalogue source JSON.

## Current Scope

The first implementation covers one route with two modes:

- `works`
  - import new work records only
- `work details`
  - import new work-detail records only

Current rules:

- workbook source is always `data/works.xlsx`
- imports are one-way into canonical JSON
- imported records default to `draft`
- workbook `status` fields are ignored
- existing source records are reported as duplicates, not updated
- works import requires referenced series to already exist
- work-details import requires the parent work to already exist
- blocked rows must be fixed in the workbook before apply

## Preview And Apply

Current flow:

1. choose import mode
2. `POST /catalogue/import-preview` reads `data/works.xlsx` and reports:
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
