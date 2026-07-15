---
doc_id: admin-checks-report-files
title: Files Report
added_date: 2026-06-08
last_updated: 2026-07-15
parent_id: admin-checks-reports
viewable: true
---
# Files Report

## Question

For the selected checks target, how much source is present and which files dominate its line/byte footprint?

Report ID `files` is produced by `admin-app/checks/reports/files.py`.

## Method

The report receives a validated run manifest, resolves files through the shared target-map resolver, counts text lines and filesystem bytes, and records target context for each row.

Supported policy comes from `admin-checks-reports.json`:

- `limit` controls the number of rows shown in Markdown;
- `sort` selects line-descending, byte-descending, or path order.

Generated data, canonical app data, Markdown source, caches, dependencies, and local runs are included/excluded by the selected scope policy, not by report-local glob lists.

## Outputs

```text
var/admin/checks/<run-id>/files/
  report.json
  report.md
  report.csv
```

- JSON contains totals and every measured row with direct/shared/unclassified target context.
- Markdown shows selected targets, totals, and the limited leading rows.
- CSV contains the full row set for filtering or spreadsheet review.

## Interpretation

Line/byte size is a navigation and concentration signal. It does not prove that a file is badly designed or that splitting it is the right change. Review dominant files in their route/workflow context and use dependency/ownership evidence before creating a refactor request.

The producer and tests are the exact authority for report schema and column names.
