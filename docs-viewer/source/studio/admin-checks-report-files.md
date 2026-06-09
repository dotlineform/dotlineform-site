---
doc_id: admin-checks-report-files
title: Files Report
added_date: 2026-06-08
last_updated: 2026-06-09
ui_status: done
parent_id: admin-checks-reports
---
# Files Report

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

## Metrics

| Metric | Description |
| --- | --- |
| `files[].lines` | Line count for the file. |
| `files[].bytes` | Byte size for the file. |

metadata and derived fields:

| Value | Description |
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

## Calculation Method

The report has two separate phases: target selection and measurement.

Target selection is config-driven:

1. Load the run manifest written by `admin-app/checks/run_reports.py`.
2. Load `admin-app/checks/config/admin-checks.json`.
3. Resolve the selected scope, families, areas, and routes through `admin-app/checks/target_map_resolver.py`.
4. Keep files that satisfy the selected target filters, including explicit shared dependencies for selected areas or routes.
5. Exclude generated payloads, dependency folders, caches, local run outputs, build outputs, canonical data, and retired prior-art paths through the shared resolver.

Measurement is file-local:

1. For each selected file, count newline-delimited text lines.
2. For each selected file, read filesystem byte size.
3. Store those measured values as `files[].lines` and `files[].bytes`.
4. Sum the measured values to produce `totals.lines` and `totals.bytes`.
5. Count selected rows to produce `totals.files`.
6. Sort the per-file rows according to the `sort` option.
7. Limit the markdown table according to the `limit` option; the JSON artifact may retain the full selected row set.

Manual equivalent for the measurement phase:

```bash
find docs-viewer assets/docs \
  -type f \
  \( -name '*.css' -o -name '*.csv' -o -name '*.html' -o -name '*.js' -o -name '*.json' -o -name '*.md' -o -name '*.py' -o -name '*.txt' -o -name '*.yaml' -o -name '*.yml' \) \
  ! -path 'docs-viewer/generated/*' \
  ! -path '*/__pycache__/*' \
  -print0 | xargs -0 wc -l -c
```

That command is useful as a quick manual check for the broad Docs Viewer scope.
It is not the durable report contract because it does not apply the full Admin checks target map, target intersections, shared dependencies, route status rules, or report option handling.

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

Implemented verification:

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/checks/reports/files.py admin-app/tests/python/test_files_report.py admin-app/checks/run_reports.py admin-app/tests/python/test_run_reports.py`
- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_files_report.py admin-app/tests/python/test_run_reports.py admin-app/tests/python/test_admin_checks_config.py admin-app/tests/python/test_target_map_resolver.py`
- real orchestrator write run for broad `docs-viewer` / `files`

Latest local write-run artifact:

```text
var/admin/checks/20260609-190326-docs-viewer/
  run-summary.json
  run-summary.md
  files/report.json
  files/report.md
```

That run passed and produced 440 files, 86,433 lines, and 3,517,712 bytes.
