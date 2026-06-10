---
doc_id: admin-checks-target-map-architecture
title: Config and Target Map
added_date: 2026-06-09
last_updated: 2026-06-10
parent_id: admin-checks
---
# Config and Target Map

This document explains the relationship between the Admin checks config, the target-map resolver, the target-map audit, and the later `target-map` report.

## Core Idea

The target map has one durable source of truth:

```text
admin-app/checks/config/admin-checks.json
```

Report metadata and defaults live in:

```text
admin-app/checks/config/admin-checks-reports.json
```

The target-map config defines scopes, file families, functional areas, routes, exclusions, and shared dependencies.
It should contain stable path and filename patterns, not a hand-maintained per-file inventory.

The audit and report use shared resolver logic.
They must not maintain separate implementations of path matching, target resolution, stale-pattern detection, shared dependency resolution, or boundary flag counts.

The current module shape is:

```text
admin-app/checks/
  admin_checks_config.py
  target_map_resolver.py
  audit_target_map.py
  reports/
    target_map.py
```

## Current State

Risk Evidence Producers Batch 2 promoted the draft target rules into `admin-app/checks/config/admin-checks.json`.
`admin-app/checks/audit_target_map.py` now reads that durable target-map config and calls `admin-app/checks/target_map_resolver.py`.

Current durable implementation:

- `admin-app/checks/config/admin-checks.json` defines the target map.
- `admin-app/checks/config/admin-checks-reports.json` defines the report registry and defaults.
- `admin-app/checks/admin_checks_config.py` validates the config and run requests.
- `admin-app/checks/target_map_resolver.py` resolves scopes, families, areas, routes, shared dependencies, stale patterns, broad patterns, and boundary flags.
- `admin-app/checks/audit_target_map.py` is a maintenance CLI wrapper around the config loader and resolver.
- `admin-app/checks/reports/target_map.py` is the normal run-scoped checks report producer for target-map evidence.

## Target Layers

The current target map has six scopes:

```text
admin
analytics
docs-viewer
public-site
studio
all
```

Families are the most deterministic layer because they follow technical structure:

```text
admin-route
build
config
public-route
runtime-assets
runtime-js
services
tests
```

Areas are workflow/product concepts and are intentionally less complete:

```text
activity
catalogue
config
docs-build
import-export
management
search
```

Routes are deterministic inventory entries derived from route configs, server dispatch, and public route files.
Routes may be `mapped` or `inventory-only`.

`mapped` routes have reviewed ownership patterns and can be selected by normal checks runs.
`inventory-only` routes are present for surface-area tracking but still need ownership review before they become route filters.

Current route status counts:

```text
mapped: 5
inventory-only: 40
```

Docs Viewer management uses one route path, `/docs/`.
The query state such as `?scope=studio&doc=...&mode=manage` is route state, not separate route ids.

## Responsibility Split

| File | Role |
| --- | --- |
| `admin-app/checks/config/admin-checks.json` | Durable target map contract. |
| `admin-app/checks/config/admin-checks-reports.json` | Report registry, default options, allowed options, and artifact metadata. |
| `admin-app/checks/admin_checks_config.py` | Config and run-request validation. |
| `admin-app/checks/target_map_resolver.py` | Shared resolver for matching files to scopes, families, areas, routes, shared dependencies, stale patterns, and boundary flags. |
| `admin-app/checks/audit_target_map.py` | Maintenance guardrail for config drift across the repo. |
| `admin-app/checks/reports/target_map.py` | Normal report producer for target-map evidence in a checks run. |

Docs Viewer publish-gate files are classified with the existing `/docs/` route plus the `management` and `docs-build` areas.
Do not add a separate publishing area unless the workflow grows beyond the local management/build boundary.

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
- Markdown source documents are excluded from checks input; report artifacts such as `report.md` remain normal outputs.

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

- it is allowlisted in `admin-checks-reports.json`
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
| Target-map config | `admin-app/checks/config/admin-checks.json` |
| Report registry | `admin-app/checks/config/admin-checks-reports.json` |
| Shared resolver | `admin-app/checks/target_map_resolver.py` |
| Maintenance audit CLI | `admin-app/checks/audit_target_map.py` |
| Report producer | `admin-app/checks/reports/target_map.py` |
| Audit snapshots | `var/admin/checks/target-map-audit/` |
| Report run artifacts | `var/admin/checks/<run-id>/target-map/` |

Do not commit a full resolved per-file target map as a permanent contract unless it is a small test fixture or an explicitly approved baseline.
