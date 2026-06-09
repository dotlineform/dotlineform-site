---
doc_id: site-request-risk-evidence-producers-task-1-target-map-audit
title: Risk Evidence Producers Task 1 Target Map Audit
added_date: 2026-06-08
last_updated: 2026-06-09
ui_status: done
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 1 Target Map Audit

This is the delivery specification for Batch 1 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 1: Produce v1 target map audit

Summary: Build the initial target-map audit and use it to propose the first real file-to-target mapping.

| ID | status | action |
| --- | --- | --- |
| 1.1 | done | Add `admin-app/checks/audit_target_map.py` as the initial audit and future drift guardrail. |
| 1.2 | done | Scan real repo files for the initial scopes and proposed v1 target ids. |
| 1.3 | done | Produce `target-map.json` and `target-map.md` in dry-run output or under `var/admin/checks/target-map-audit/` for write mode. |
| 1.4 | done | Report included files, excluded files, file-family assignment, `_unclassified` files, multi-family matches, area matches, route matches, shared dependencies, stale patterns, and likely unmapped area/route files. |
| 1.5 | done | Flag likely boundary-crossing and unclear-ownership evidence, including files that cross frontend/backend, route/service, or script/config ownership boundaries. |
| 1.6 | done | Identify candidate Docs Viewer management route targets and recommend the representative v1 route once the family, area, and route map is visible. |
| 1.7 | done | Use the audit findings to propose the first `admin-checks.json` target rules. |
| 1.8 | done | Keep the first map pattern-based wherever possible; use explicit shared dependencies or overrides only for files that cannot be classified clearly by stable path/name rules. |

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

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/checks/audit_target_map.py`
- `$HOME/miniconda3/bin/python3 admin-app/checks/audit_target_map.py`
- `$HOME/miniconda3/bin/python3 admin-app/checks/audit_target_map.py --write`
- Parsed `var/admin/checks/target-map-audit/target-map.json` and confirmed schema `admin_checks_target_map_audit_v1`, all six scopes, and the proposed Docs Viewer management route `/docs/`.

## follow-on tasks

- Use the audit findings in Batch 2 to define `admin-checks.json`.

## task close

- Batch 1 is complete.
- Durable script: `admin-app/checks/audit_target_map.py`.
- Generated local artifacts: `var/admin/checks/target-map-audit/target-map.json` and `var/admin/checks/target-map-audit/target-map.md`.
- Proposed representative Docs Viewer management route: `/docs/`.
- Latest written audit summary for `all`: 5,729 included files, 5,089 excluded files, 11 unclassified files, 50 multi-family files, 128 cross-area files, 10 cross-route files, 275 shared dependency files, and 15 stale patterns.
- Task 2 should promote `proposed_admin_checks_config` from the audit JSON into durable `admin-app/checks/config/admin-checks.json`, then review the remaining unclassified and likely-unmapped findings as config refinement data.
