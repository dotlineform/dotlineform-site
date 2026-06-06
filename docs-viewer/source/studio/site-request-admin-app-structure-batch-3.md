---
doc_id: site-request-admin-app-structure-batch-3
title: Admin App Structure Batch 3
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: done
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# Audits, Risk, and Activity Routes

This is the delivery specification for Batch 3 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 3: Audits, Risk, and Activity Routes

Summary: move existing functional audit, risk, and activity pages from Studio to Admin with the same workflow behavior.

| ID | status | action |
| --- | --- | --- |
| 3.1 | done | Move audit route shell, route behavior, UI text, API adapter, and allowlist ownership to Admin under `/admin/audits/` and `/admin/api/audits/...`. |
| 3.2 | done | Move risk route shell, route behavior, UI text, API adapter, producer registry, and local output ownership to Admin under `/admin/risk/`, `/admin/api/risk/...`, and `var/admin/risk/`. |
| 3.3 | done | Move activity route shell, route behavior, UI text, feed read model, and local output ownership to Admin under `/admin/activity/` and `var/admin/activity/`. |
| 3.4 | done | Update Admin home navigation and route config for audits, risk, and activity. |
| 3.5 | done | Update activity-writing helpers and caller contracts so Admin-owned activity output paths are used where the unified Admin activity feed is expected. |
| 3.6 | done | Add focused Admin tests and smokes for audits, risk, and activity route behavior. |

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

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/app/server/admin_app/*.py studio/app/server/studio/*.py studio/checks/risk_evidence_pack.py`
- `node --check admin-app/app/frontend/js/admin-audits.js admin-app/app/frontend/js/admin-risk.js admin-app/app/frontend/js/admin-activity.js admin-app/app/frontend/js/admin-config.js admin-app/app/frontend/js/admin-route-state.js admin-app/app/frontend/js/admin-operational-route.js admin-app/app/frontend/js/admin-activity-context.js admin-app/app/frontend/js/admin-activity-modals.js admin-app/app/frontend/js/admin-transport.js studio/app/frontend/js/studio-transport.js studio/app/frontend/js/studio-data.js studio/app/frontend/js/studio-route-body-renderers.js studio/app/frontend/js/studio-home-shell.js`
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/admin-config.json`
- `$HOME/miniconda3/bin/python3 -m json.tool studio/app/frontend/config/studio-config.json`
- `$HOME/miniconda3/bin/python3 -m json.tool studio/data/config/runtime/activity-contract.json`
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/ui-text/admin-activity.json`
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/ui-text/admin-audits.json`
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/ui-text/admin-risk.json`
- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_admin_app_server.py admin-app/tests/python/test_admin_operations.py studio/tests/python/test_studio_app_server.py studio/tests/python/test_studio_activity_feed.py studio/tests/python/test_activity_contract.py docs-viewer/tests/python/test_docs_activity.py studio/tests/python/test_tags_data_sharing_adapter.py` passed with 50 tests.
- `$HOME/miniconda3/bin/python3 admin-app/tests/smoke/admin_operations_routes.py` passed.
- `git diff --check`
- Source review confirmed retired Studio route/API references are absent from Admin, Studio app code, Studio tests, Docs Viewer tests, and Analytics tests except for the negative Studio route-removal assertion in `studio/tests/python/test_studio_app_server.py`.

## follow-on tasks

- Batch 4 moves the repo-scope runner, checks, tests, and fixtures.
- Batch 4 should update `studio/commands/run_checks.py`, which still references retired Studio audit/risk modules and retired Studio route smokes until the runner moves to Admin.
- Batch 6 should update durable docs that still describe the old Studio-hosted audit, risk, and activity paths.

## task close

- Handoff note added to Batch 4.
- `ui_status` set to `done` after Admin audit, risk, and activity behavior was verified.
