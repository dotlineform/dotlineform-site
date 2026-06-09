---
doc_id: site-request-risk-evidence-producers-task-2-checks-config
title: Risk Evidence Producers Task 2 Checks Config
added_date: 2026-06-08
last_updated: 2026-06-09
ui_status: done
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 2 Checks Config

This is the delivery specification for Batch 2 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 2: Define checks config, target layers, and report registry

Summary: Create the Admin checks config and registry contract from the v1 target-map audit.

| ID | status | action |
| --- | --- | --- |
| 2.1 | done | Add `admin-app/checks/config/admin-checks.json`. |
| 2.2 | done | Define initial scopes: `admin`, `analytics`, `docs-viewer`, `public-site`, `studio`, and `all`. |
| 2.3 | done | Define file families as technical/layer subdivisions of each scope. |
| 2.4 | done | Define functional areas as feature/workflow subdivisions that may cross file families. |
| 2.5 | done | Define route targets as UI/API route subdivisions that may include frontend, backend, config, tests, and docs. |
| 2.6 | done | Define target resolution rules for direct matches, shared dependencies, `_unclassified` files, and intersections across selected families, areas, and routes. |
| 2.7 | done | Seed the v1 target rules from the target-map audit rather than inventing them independently. |
| 2.8 | done | Define initial report metadata for `files`, including script path, label, description, defaults, and allowed options. |
| 2.9 | done | Include exclusions for generated payloads, dependency folders, caches, local run artifacts, and build output. |
| 2.10 | done | Add a config loader that rejects unknown scopes, families, areas, routes, reports, script paths outside `admin-app/checks/reports/`, and unknown options. |
| 2.11 | done | Add `admin-app/checks/target_map_resolver.py` as the shared implementation for path matching, target resolution, stale-pattern detection, shared dependencies, and boundary flag counts. |
| 2.12 | done | Refactor `admin-app/checks/audit_target_map.py` to read `admin-app/checks/config/admin-checks.json` and call `target_map_resolver.py` instead of owning embedded draft target rules. |

## Steer for these tasks

- `admin-app/checks/config/admin-checks.json` is the durable config path for this system.
- The browser may receive safe projected metadata, but this config is not browser bootstrap config.
- Target layers should remain facets inside a scope, not independent filesystem permissions.
- The resolver is part of Batch 2 because Batch 3 orchestrator and Batch 4 report producers should consume shared target resolution rather than duplicating audit logic.
- The deferred `target-map` report should reuse this resolver later, but `admin-app/checks/reports/target_map.py` is not part of Batch 2.

## Deliverables

- `admin-app/checks/config/admin-checks.json`
- `admin-app/checks/target_map_resolver.py`
- refactored `admin-app/checks/audit_target_map.py`
- config loader and validation helpers
- initial report registry entry for `files`

## Implementation and policy guidance

- Include `config_id: "admin-checks"` and a numeric `version`.
- Validate paths and script ownership before the orchestrator can use the config.
- Keep shared dependencies explicit.
- Keep target-map mechanics in `target_map_resolver.py`; `audit_target_map.py` should be a maintenance CLI wrapper around the resolver.
- Do not create `admin-app/checks/reports/target_map.py` in this batch; that remains deferred to [Target Map Report Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers-report-target-map).

## Proposed verification set

- Focused config-loader tests for valid config, unknown ids, unknown options, invalid script paths, and excluded roots.
- Focused resolver tests for scope inclusion/exclusion, family assignment, `_unclassified`, direct matches, shared dependency matches, intersected target filters, stale patterns, and boundary flags.
- Run the refactored target-map audit in dry-run mode and confirm it reads `admin-checks.json`.
- JSON parsing/validation for `admin-checks.json`.

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/checks/admin_checks_config.py admin-app/checks/target_map_resolver.py admin-app/checks/audit_target_map.py admin-app/tests/python/test_admin_checks_config.py admin-app/tests/python/test_target_map_resolver.py`
- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_admin_checks_config.py admin-app/tests/python/test_target_map_resolver.py`
- `$HOME/miniconda3/bin/python3 admin-app/checks/audit_target_map.py`
- `$HOME/miniconda3/bin/python3 admin-app/checks/audit_target_map.py --write`
- Parsed `var/admin/checks/target-map-audit/target-map.json` and confirmed audit version `2`, config path `admin-app/checks/config/admin-checks.json`, all six scopes, and the `files` report registry.

## follow-on tasks

- Batch 3 consumes the validated registry and shared resolver to build the orchestrator.
- Batch 4 consumes the shared resolver for the `files` report.

## task close

- Batch 2 is complete.
- Durable config: `admin-app/checks/config/admin-checks.json`.
- Config loader: `admin-app/checks/admin_checks_config.py`.
- Shared resolver: `admin-app/checks/target_map_resolver.py`.
- Refactored audit CLI: `admin-app/checks/audit_target_map.py`.
- Batch 3 should use `load_checks_config()` and `validate_run_request()` from `admin_checks_config.py` to validate orchestrator run requests.
- Batch 3 should use `resolve_run_files()` from `target_map_resolver.py` for resolved target files and should not duplicate path matching.
- Batch 4 should use the same resolver for the `files` report.
