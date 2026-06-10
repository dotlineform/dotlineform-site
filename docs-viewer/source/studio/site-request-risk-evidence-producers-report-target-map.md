---
doc_id: site-request-risk-evidence-producers-report-target-map
title: Target Map Report
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: draft
parent_id: site-request-risk-evidence-producers
---
# Target Map Report

Status:

- draft

## Summary

Implement a `target-map` report after the Admin checks system can run the v1 `files` report.

The v1 implementation includes `admin-app/checks/audit_target_map.py` to produce and maintain the family, area, and route map.
This request turns that audit data into a normal checks report with `report.json` and `report.md` artifacts.

## Purpose

The `target-map` report should make boundary-crossing and unclear-ownership evidence visible.
It should help identify scripts, config, route files, and shared helpers that cross too many target boundaries or do not clearly belong to a configured family, area, or route.

This report should not automatically declare every cross-boundary file harmful.
Shared utilities, central config loaders, route registries, and orchestration scripts can be valid.
The report should separate expected shared dependencies from unclear ownership so subsequent risk analysis can decide what is actionable.

## Dependencies

- Risk Evidence Producers v1 is implemented and can run the `files` report.
- `admin-app/checks/config/admin-checks.json` exists with scopes, families, areas, routes, reports, exclusions, and shared dependencies.
- `admin-app/checks/audit_target_map.py` can resolve the target map from real repo files.
- The orchestrator can run allowlisted report scripts and write report artifacts.

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

The report should use the same resolver as the target-map audit.

## Required Evidence

The `target-map` report should include evidence for:

- files with `_unclassified` family ownership
- files matching multiple families
- files matching many functional areas
- files matching many route targets
- shared dependencies used by many areas or routes
- scripts or config files that cross frontend/backend or route/service boundaries
- stale patterns and patterns with unexpectedly broad matches
- likely ownership smells where filename terms imply an area or route that the target map does not include

## Required Metrics

| Metric | Description |
| --- | --- |
| `totals.files` | Included file count after scope exclusions. |
| `totals.unclassified_files` | Included files without a configured family. |
| `totals.multi_family_files` | Files matching more than one family. |
| `totals.cross_area_files` | Files matching more than one functional area. |
| `totals.cross_route_files` | Files matching more than one route target. |
| `totals.shared_dependency_files` | Files explicitly included as shared dependencies. |
| `totals.stale_patterns` | Configured target patterns that match no files. |
| `files[].path` | Repo-relative file path. |
| `files[].families` | File families matched by the file. |
| `files[].areas` | Functional areas matched by the file. |
| `files[].routes` | Route targets matched by the file. |
| `files[].boundary_flags` | Boundary-crossing or unclear-ownership flags assigned by the report. |
| `patterns[].status` | Pattern status such as active, stale, broad, or review. |

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Add `target-map` report metadata to `admin-app/checks/config/admin-checks.json`. |
| 2 | planned | Add `admin-app/checks/reports/target_map.py`. |
| 3 | planned | Reuse the target-map audit resolver rather than duplicating target resolution logic. |
| 4 | planned | Write `report.json` with target coverage, stale-pattern, shared-dependency, and boundary-flag metrics. |
| 5 | planned | Write `report.md` with a readable target-map summary and review tables. |
| 6 | planned | Add focused tests for report metrics, boundary flags, markdown rendering, and stale/broad pattern handling. |
| 7 | planned | Run the report through the normal orchestrator against at least `docs-viewer`. |
| 8 | planned | Update risk evidence metrics/docs once the report artifact shape is stable. |

## Proposed Verification

- Focused tests for `target_map.py`.
- Orchestrator dry run and write run for `docs-viewer` / `target-map`.
- Inspect `report.json` and `report.md`.
- Verify `_unclassified`, multi-family, cross-area, cross-route, shared-dependency, stale-pattern, and broad-pattern examples are represented when fixtures or real files contain them.

## Open Questions

None for request framing.
Implementation details can be refined after v1 produces the initial target-map audit output.
