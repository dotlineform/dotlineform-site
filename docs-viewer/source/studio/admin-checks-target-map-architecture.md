---
doc_id: admin-checks-target-map-architecture
title: Config and Target Map
added_date: 2026-06-09
last_updated: 2026-06-09
parent_id: admin-checks
---
# Config and Target Map

This document explains the relationship between the Admin checks config, the target-map audit, and the later `target-map` report.

## Core Idea

The target map has one durable source of truth:

```text
admin-app/checks/config/admin-checks.json
```

That config defines scopes, file families, functional areas, routes, exclusions, shared dependencies, and report metadata.
It should contain stable path and filename patterns, not a hand-maintained per-file inventory.

The audit and report should both use shared resolver logic.
They should not maintain separate implementations of path matching, target resolution, stale-pattern detection, shared dependency resolution, or boundary flag counts.

The intended shared module shape is:

```text
admin-app/checks/
  target_map_resolver.py
  audit_target_map.py
  reports/
    target_map.py
```

## Transitional Bootstrap

During Risk Evidence Producers Batch 1, `admin-app/checks/audit_target_map.py` temporarily owns draft target rules because `admin-checks.json` does not exist yet.

In that bootstrap role, the audit:

- scans real repo files
- proposes the first target rules
- calculates target-map findings from those draft rules
- writes generated audit artifacts under `var/admin/checks/target-map-audit/`
- includes a `proposed_admin_checks_config` payload for Batch 2

Batch 2 should promote and refine that proposed config into `admin-app/checks/config/admin-checks.json`.

After Batch 2, `audit_target_map.py` should stop owning embedded draft rules and read the durable config instead.

## Steady State

Once `admin-checks.json` exists, responsibilities should be separated like this:

| File | Role |
| --- | --- |
| `admin-app/checks/config/admin-checks.json` | Durable target map contract and report registry. |
| `admin-app/checks/target_map_resolver.py` | Shared resolver for matching files to scopes, families, areas, routes, shared dependencies, stale patterns, and boundary flags. |
| `admin-app/checks/audit_target_map.py` | Maintenance guardrail for config drift across the repo. |
| `admin-app/checks/reports/target_map.py` | Normal report producer for target-map evidence in a checks run. |

## Why Keep The Audit

The audit is a config-maintenance guardrail.
It asks whether the target map is still coherent after the repo changes.

Run it when adding or changing:

- routes
- feature areas
- app layers
- shared helpers
- report scripts
- config files
- significant file moves or renames

By default, the audit should inspect the whole config, not just one selected run scope.
It should make drift visible:

- `_unclassified` files
- files matching multiple families
- cross-area files
- cross-route files
- stale patterns
- unexpectedly broad patterns
- likely area or route files that are not mapped
- shared dependencies used by many targets
- generated, cache, dependency, build, and local run paths excluded by scope rules

The audit can later grow stricter maintenance modes such as `--strict` or `--changed-files`.
Those modes should remain config guardrails, not report-run behavior.

## Why Keep The Report

The `target-map` report is a user-facing checks report.
It should run through the normal orchestrator and write normal report artifacts:

```text
var/admin/checks/<YYYYMMDD-HHMMSS>-<scope>/target-map/
  report.json
  report.md
```

The report answers a selected evidence question for a run.
It should respect selected scope, family, area, and route filters from the run request.
Normal report runs should only allow routes whose config status is `mapped`.
Routes with status `inventory-only` are present for surface-area tracking but still need ownership review before they become route filters.

The report can expose many of the same metrics as the audit, but its contract is different:

- it is allowlisted in `admin-checks.json`
- it runs through `run_reports.py`
- it writes under a timestamped checks run
- it is displayed in `/admin/checks/`
- it reports evidence for the selected run target

If the report runs with `scope=all`, it may look similar to the audit.
The difference is interpretation: the report is evidence for a run, while the audit is a guardrail for maintaining the target map itself.

## Shared Resolver Contract

The resolver should be the only implementation of target-map mechanics.

It should provide structured data for both callers:

- included files by scope after exclusions
- excluded files and exclusion reasons
- matched families, areas, routes, and shared dependencies per file
- `_unclassified` family assignment
- multi-family, cross-area, and cross-route flags
- stale and broad pattern status
- likely unmapped area and route hints
- summary counts

The audit may request all scopes and full pattern diagnostics.
The report may request only one resolved run plan.
Both should receive their data from the same resolver.

## Artifact Ownership

Durable assets live under `admin-app/`.
Generated snapshots live under `var/`.

Use this split:

| Kind | Path |
| --- | --- |
| Durable config | `admin-app/checks/config/admin-checks.json` |
| Shared resolver | `admin-app/checks/target_map_resolver.py` |
| Maintenance audit CLI | `admin-app/checks/audit_target_map.py` |
| Report producer | `admin-app/checks/reports/target_map.py` |
| Audit snapshots | `var/admin/checks/target-map-audit/` |
| Report run artifacts | `var/admin/checks/<run-id>/target-map/` |

Do not commit a full resolved per-file target map as a permanent contract unless it is a small test fixture or an explicitly approved baseline.
