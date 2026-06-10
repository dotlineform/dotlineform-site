---
doc_id: admin-checks-report-target-map
title: Target Map Report
added_date: 2026-06-10
last_updated: 2026-06-10
parent_id: admin-checks-reports
---
# Target Map Report

This document defines the durable contract for the `target-map` report in [Admin Checks](/docs/?scope=studio&doc=admin-checks).

## Purpose

The `target-map` report provides ownership, shared dependency, and boundary-crossing evidence for a selected checks scope and optional target filters.

The report is evidence, not pass/fail policy.
Cross-boundary files can be legitimate shared utilities, route registries, config loaders, or orchestration scripts.

## Report Contract

Report id:

```text
target-map
```

Source script:

```text
admin-app/checks/reports/target_map.py
```

Output artifacts:

```text
var/admin/checks/<YYYYMMDD-HHMMSS>-<scope>/target-map/
  report.json
  report.md
```

## Inputs

The report reads the selected scope and target filters from the run manifest written by `admin-app/checks/run_reports.py`.
It resolves files through `admin-app/checks/target_map_resolver.py`.
It must not duplicate target-map matching logic locally.

Supported options:

| Option | Default | Purpose |
| --- | --- | --- |
| `limit` | `20` | Maximum number of per-file rows shown per markdown review table. |
| `pattern_limit` | `20` | Maximum number of stale or broad pattern rows shown in markdown. |

## Metrics

Report schema version: `admin_checks_target_map_report_v1`

| Metric | Description |
| --- | --- |
| `totals.files` | Included file count after scope exclusions and selected target filters. |
| `totals.unclassified_files` | Included files without a configured family. |
| `totals.multi_family_files` | Included files matching more than one family. |
| `totals.cross_area_files` | Included files matching more than one direct or shared functional area. |
| `totals.cross_route_files` | Included files matching more than one direct or shared route target. |
| `totals.shared_dependency_files` | Included files explicitly matched by shared dependency rules. |
| `totals.stale_patterns` | Configured target patterns that match no current source files. |
| `totals.broad_patterns` | Configured target patterns with unusually broad match counts. |
| `totals.likely_unmapped_area_files` | Included files whose path terms imply an area not mapped for that file. |
| `totals.likely_unmapped_route_files` | Included files whose path terms imply a route not mapped for that file. |
| `files[].path` | Repo-relative file path. |
| `files[].families` | File families matched by the file. |
| `files[].areas` | Functional areas directly matched by the file. |
| `files[].routes` | Route targets directly matched by the file. |
| `files[].shared_areas` | Functional areas that include the file through shared dependency rules. |
| `files[].shared_routes` | Route targets that include the file through shared dependency rules. |
| `files[].boundary_flags` | Boundary-crossing or unclear-ownership flags assigned by the shared resolver. |
| `patterns[].status` | Pattern status, currently `active`, `stale`, or `broad`. |

## Markdown Shape

The markdown report includes:

- report id, run id, selected scope, and selected filters
- top-level target-map totals
- family, area, and route match counts
- shared dependency review rows
- boundary finding tables by flag
- stale and broad pattern rows
- interpretation notes that separate evidence from pass/fail policy

Example:

```text
# Target Map Report

- report: `target-map`
- run: `<run-id>`
- scope: `docs-viewer`
- families: _all_
- areas: _all_
- routes: _all_
- files: x
- unclassified files: x
- multi-family files: x
- cross-area files: x
- cross-route files: x
- shared dependency files: x
- stale patterns: x
- broad patterns: x
```
