---
doc_id: site-request-risk-evidence-producers-task-1-target-map-audit
title: Risk Evidence Producers Task 1 Target Map Audit
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 1 Target Map Audit

This is the delivery specification for Batch 1 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 1: Produce v1 target map audit

Summary: Build the initial target-map audit and use it to propose the first real file-to-target mapping.

| ID | status | action |
| --- | --- | --- |
| 1.1 | planned | Add `admin-app/checks/audit_target_map.py` as the initial audit and future drift guardrail. |
| 1.2 | planned | Scan real repo files for the initial scopes and proposed v1 target ids. |
| 1.3 | planned | Produce `target-map.json` and `target-map.md` in dry-run output or under `var/admin/checks/target-map-audit/` for write mode. |
| 1.4 | planned | Report included files, excluded files, file-family assignment, `_unclassified` files, multi-family matches, area matches, route matches, shared dependencies, stale patterns, and likely unmapped area/route files. |
| 1.5 | planned | Flag likely boundary-crossing and unclear-ownership evidence, including files that cross frontend/backend, route/service, or script/config ownership boundaries. |
| 1.6 | planned | Identify candidate Docs Viewer management route targets and recommend the representative v1 route once the family, area, and route map is visible. |
| 1.7 | planned | Use the audit findings to propose the first `admin-checks.json` target rules. |
| 1.8 | planned | Keep the first map pattern-based wherever possible; use explicit shared dependencies or overrides only for files that cannot be classified clearly by stable path/name rules. |

## Steer for these tasks

- Treat the audit output as report and mapping data, not pass/fail policy.
- The first target map should come from real repo files, not an unverified hand-written taxonomy.
- Preserve scope as the safety boundary; families, areas, and routes are lower-level target facets.
- The next batch consumes this audit to seed `admin-app/checks/config/admin-checks.json`.

## Deliverables

- `admin-app/checks/audit_target_map.py`
- target-map dry-run output
- optional write output under `var/admin/checks/target-map-audit/`
- proposed target rules for `admin-checks.json`

## Implementation and policy guidance

- Prefer stable path and filename patterns over per-file inventories.
- Keep `_unclassified`, multi-family, cross-area, cross-route, stale-pattern, and likely-unmapped findings visible for later risk reports.
- Do not let the audit silently pull broad shared app surfaces into route or area reports.

## Proposed verification set

- Run the target-map audit in dry-run mode.
- Review target-map output for representative scope coverage and obvious stale patterns.
- Run a Python syntax check for the audit script after implementation.

## completed verification

- Not started.

## follow-on tasks

- Use the audit findings in Batch 2 to define `admin-checks.json`.

## task close

- Add a handoff note to Batch 2.
- Set this batch status and front matter `ui_status` to `done`.
