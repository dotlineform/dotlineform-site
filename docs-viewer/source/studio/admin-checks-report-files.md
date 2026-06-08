---
doc_id: admin-checks-report-files
title: Admin Checks Files Report
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: admin-checks
viewable: true
---
# Admin Checks Files Report

This document defines the durable contract for the `files` report in [Admin Checks](/docs/?scope=studio&doc=admin-checks).

## Purpose

The `files` report provides file count, line count, and byte-size evidence for a selected checks scope and optional target filters.

It is the v1 proof-of-concept report for the Admin Checks system.

## Report Contract

Report id:

```text
files
```

Source script:

```text
admin-app/checks/reports/files.py
```

Output artifacts:

```text
var/admin/checks/<YYYYMMDD-HHMMSS>-<scope>/files/
  report.json
  report.md
```

## Inputs

The report reads the selected scope and target filters from the resolved checks config.
It should not duplicate path rules locally.

Supported v1 options:

| Option | Default | Purpose |
| --- | --- | --- |
| `limit` | `50` | Maximum number of per-file rows shown in the markdown report. |
| `sort` | `lines_desc` | Sort order for per-file rows. |

## Default Behavior

- include source, config, and documentation files selected by scope config
- apply selected file-family, functional-area, and route filters through the shared target resolver
- exclude generated payloads, dependency folders, caches, local run outputs, and build outputs
- sort rows by line count descending
- write both machine-readable and human-readable report artifacts

## Required Metrics

| Metric | Description |
| --- | --- |
| `totals.files` | Included file count. |
| `totals.lines` | Total line count across included files. |
| `totals.bytes` | Total byte size across included files. |
| `files[].path` | Repo-relative path. |
| `files[].lines` | Line count for the file. |
| `files[].bytes` | Byte size for the file. |
| `files[].family` | File family from scope config, or `_unclassified`. |
| `files[].areas` | Functional area ids matched by the file. |
| `files[].routes` | Route ids matched by the file. |
| `files[].target_match` | Whether the row matched directly, as a shared dependency, or as `_unclassified`. |

## Markdown Shape

The markdown report should include:

- report id and selected scope
- selected families, areas, and routes when present
- total file count
- total line count
- total byte size
- a per-file table sorted by the selected option

Example:

```text
Report:     files
Scope:      docs-viewer

files:      x
total lc:   x
total size: x

 lines      size  file
 -------------------------------------------------------------------------
   997       36K  ./docs-viewer/runtime/js/docs-viewer-management.js
   905       32K  ./docs-viewer/runtime/js/docs-viewer-app-runtime.js
```

## Verification

- focused tests for scope inclusion/exclusion
- focused tests for target filtering
- focused tests for line and byte counting
- focused tests for sorting and limit behavior
- focused tests for `report.json` and `report.md` shape
- orchestrator dry run and write run for `docs-viewer` / `files`
