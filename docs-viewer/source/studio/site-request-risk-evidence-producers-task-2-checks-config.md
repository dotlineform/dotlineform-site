---
doc_id: site-request-risk-evidence-producers-task-2-checks-config
title: Risk Evidence Producers Task 2 Checks Config
added_date: 2026-06-08
last_updated: 2026-06-08
ui_status: planned
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 2 Checks Config

This is the delivery specification for Batch 2 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 2: Define checks config, target layers, and report registry

Summary: Create the Admin checks config and registry contract from the v1 target-map audit.

| ID | status | action |
| --- | --- | --- |
| 2.1 | planned | Add `admin-app/checks/config/admin-checks.json`. |
| 2.2 | planned | Define initial scopes: `admin`, `analytics`, `docs-viewer`, `public-site`, `studio`, and `all`. |
| 2.3 | planned | Define file families as technical/layer subdivisions of each scope. |
| 2.4 | planned | Define functional areas as feature/workflow subdivisions that may cross file families. |
| 2.5 | planned | Define route targets as UI/API route subdivisions that may include frontend, backend, config, tests, and docs. |
| 2.6 | planned | Define target resolution rules for direct matches, shared dependencies, `_unclassified` files, and intersections across selected families, areas, and routes. |
| 2.7 | planned | Seed the v1 target rules from the target-map audit rather than inventing them independently. |
| 2.8 | planned | Define initial report metadata for `files`, including script path, label, description, defaults, and allowed options. |
| 2.9 | planned | Include exclusions for generated payloads, dependency folders, caches, local run artifacts, and build output. |
| 2.10 | planned | Add a config loader that rejects unknown scopes, families, areas, routes, reports, script paths outside `admin-app/checks/reports/`, and unknown options. |

## Steer for these tasks

- `admin-app/checks/config/admin-checks.json` is the durable config path for this system.
- The browser may receive safe projected metadata, but this config is not browser bootstrap config.
- Target layers should remain facets inside a scope, not independent filesystem permissions.

## Deliverables

- `admin-app/checks/config/admin-checks.json`
- config loader and validation helpers
- initial report registry entry for `files`

## Implementation and policy guidance

- Include `config_id: "admin-checks"` and a numeric `version`.
- Validate paths and script ownership before the orchestrator can use the config.
- Keep shared dependencies explicit.

## Proposed verification set

- Focused config-loader tests for valid config, unknown ids, unknown options, invalid script paths, and excluded roots.
- JSON parsing/validation for `admin-checks.json`.

## completed verification

- Not started.

## follow-on tasks

- Batch 3 consumes the validated registry to build the orchestrator.

## task close

- Add a handoff note to Batch 3.
- Set this batch status and front matter `ui_status` to `done`.
