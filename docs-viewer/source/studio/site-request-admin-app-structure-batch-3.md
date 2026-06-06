---
doc_id: site-request-admin-app-structure-batch-3
title: Admin App Structure Batch 3
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: planned
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# Audits, Risk, and Activity Routes

This is the delivery specification for Batch 3 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 3: Audits, Risk, and Activity Routes

Summary: move existing functional audit, risk, and activity pages from Studio to Admin with the same workflow behavior.

| ID | status | action |
| --- | --- | --- |
| 3.1 | planned | Move audit route shell, route behavior, UI text, API adapter, and allowlist ownership to Admin under `/admin/audits/` and `/admin/api/audits/...`. |
| 3.2 | planned | Move risk route shell, route behavior, UI text, API adapter, producer registry, and local output ownership to Admin under `/admin/risk/`, `/admin/api/risk/...`, and `var/admin/risk/`. |
| 3.3 | planned | Move activity route shell, route behavior, UI text, feed read model, and local output ownership to Admin under `/admin/activity/` and `var/admin/activity/`. |
| 3.4 | planned | Update Admin home navigation and route config for audits, risk, and activity. |
| 3.5 | planned | Update activity-writing helpers and caller contracts so Admin-owned activity output paths are used where the unified Admin activity feed is expected. |
| 3.6 | planned | Add focused Admin tests and smokes for audits, risk, and activity route behavior. |

## Steer for these tasks

- This is a route and ownership move, not a workflow redesign.
- Existing functional pages move into the Admin destination created in Batch 1.
- Admin tests should assert each moved Admin route works, loads its expected config/data, and reaches the correct Admin API behavior.
- Activity, audit, and risk output paths move to `var/admin/...`.

## Batch 2 handoff

- UI Catalogue source and assets now live under `admin-app/ui-catalogue/`.
- Admin server code owns `/admin/ui-catalogue/`, `/admin/ui-catalogue/demos/...`, `/admin/ui-catalogue/palette/`, and `/admin/ui-catalogue/assets/...`.
- The standalone `ui-catalogue-app/` source and `bin/local-ui-catalogue` launcher were retired; `bin/local-all` no longer starts a separate UI Catalogue service.
- Admin UI Catalogue tests now live at `admin-app/tests/python/test_admin_ui_catalogue.py`, `admin-app/tests/smoke/admin_ui_catalogue_routes.py`, and `admin-app/tests/smoke/admin_ui_catalogue_modal_demo.py`.
- The `ui-catalogue-smoke` runner profile points at the Admin-hosted UI Catalogue tests and passed in `var/test-runs/admin-ui-catalogue-batch-2/summary.md`.
- Retired `/ui-catalogue/...` routes are not compatibility aliases; the Admin UI Catalogue route smoke asserts `/ui-catalogue/demos/` returns 404.

## Deliverables

- Admin-hosted `/admin/audits/`, `/admin/risk/`, and `/admin/activity/`.
- Admin API adapters for audit and risk workflows.
- Admin activity read/write ownership.
- Focused Admin route tests and smokes.
- Updated route config, UI text paths, and local output paths.

## Implementation and policy guidance

- Keep browser-controlled execution bounded by allowlisted Admin API adapters.
- Keep route modules focused on boot, event wiring, state handoff, and route-ready projection.
- Prefer moving existing focused modules over rewriting behavior.
- Use Admin-owned route paths and local output paths in tests and docs.

## Proposed verification set

- Admin server pytest for audit and risk API adapters.
- Admin activity feed pytest for Admin-owned output paths.
- Admin route smokes for `/admin/audits/`, `/admin/risk/`, and `/admin/activity/`.
- Syntax checks for moved Python and JavaScript.

## completed verification

- pending

## follow-on tasks

- Batch 4 moves the repo-scope runner, checks, tests, and fixtures.

## task close

- Add a handoff note to Batch 4.
- Set `ui_status` to `done` after Admin audit, risk, and activity behavior is verified.
