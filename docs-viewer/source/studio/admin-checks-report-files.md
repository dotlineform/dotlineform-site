---
doc_id: admin-checks-report-files
title: Files Report
added_date: 2026-06-08
last_updated: 2026-06-10
parent_id: admin-checks-reports
---
# Files Report

This document defines the durable contract for the `files` report in [Admin Checks](/docs/?scope=studio&doc=admin-checks).

## Purpose

The `files` report provides file count, line count, and byte-size evidence for code/data files in a selected checks scope and optional target filters.

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
  report.csv
```

## Inputs

The report reads the selected scope and target filters from the resolved checks config `admin-app/checks/config/admin-checks.json`.
It should not duplicate path rules locally.

Supported options:

| Option | Default | Purpose |
| --- | --- | --- |
| `limit` | `20` | Maximum number of per-file rows shown in the markdown report. |
| `sort` | `lines_desc` | Sort order for per-file rows. |

Supported `sort` values:

- `lines_desc`
- `bytes_desc`
- `path_asc`

## Default Behavior

- include code, config, and structured data files selected by scope config
- exclude Markdown source documents from checks input
- apply selected file-family, functional-area, and route filters through the shared target resolver
- exclude generated payloads, dependency folders, caches, local run outputs, and build outputs
- sort rows by line count descending
- write machine-readable JSON, human-readable markdown, and a full CSV file list

## Metrics

Report schema version: `admin_checks_files_report_v1`

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
| `files[].target_match` | Whether the row matched directly, as a shared dependency, or as `_unclassified`; included in JSON and CSV, not the markdown table. |

`target_match` values:

| Value | Meaning |
| --- | --- |
| `direct` | The file matched the selected target rules itself. For example, it matched the selected scope and any selected family, area, or route include rules. |
| `shared` | The file was included because it is explicitly listed as a shared dependency for a selected area or route. |
| `_unclassified` | The file is inside the selected scope but matched no configured file family. |

`direct` does not mean the file is unique to one route or area.
It means the row was selected by direct target matching rather than only by a shared dependency rule.

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
7. Limit the markdown table according to the `limit` option.
8. Write the full selected row set to both `report.json` and `report.csv`.

Manual equivalent for the measurement phase:

```bash
find docs-viewer assets/docs \
  -type f \
  \( -name '*.css' -o -name '*.csv' -o -name '*.html' -o -name '*.js' -o -name '*.json' -o -name '*.py' -o -name '*.txt' -o -name '*.yaml' -o -name '*.yml' \) \
  ! -path 'docs-viewer/generated/*' \
  ! -path '*/__pycache__/*' \
  -print0 | xargs -0 wc -l -c
```

That command is useful as a quick manual check for the broad Docs Viewer scope.
It is not the durable report contract because it does not apply the full Admin checks target map, target intersections, shared dependencies, route status rules, or report option handling.

## Markdown Shape

The markdown report includes:

- report id and selected scope
- selected families, areas, and routes when present
- total file count
- total line count
- total size in rounded KB
- a per-file table sorted by the selected option
- per-file sizes in rounded KB

The markdown table intentionally omits `target_match` and other row-level targeting fields.
Those fields belong in `report.json` and `report.csv` so the Admin UI can remain simple while still allowing manual filtering and sorting in spreadsheet tools.

Example:

```text
# Files Report

- report: `files`
- run: `<run-id>`
- scope: `docs-viewer`
- families: _all_
- areas: _all_
- routes: _all_
- files: x
- total lines: x
- total size: x KB

## Largest Files

| lines | size | family | path |
| ---: | ---: | --- | --- |
| 997 | 36 KB | runtime-js | `docs-viewer/runtime/js/docs-viewer-management.js` |
```

## CSV Shape

`report.csv` contains the full selected file row set for manual review in spreadsheet tools:

```text
path,lines,bytes,size_kb,family,families,areas,routes,shared_areas,shared_routes,target_match
```
