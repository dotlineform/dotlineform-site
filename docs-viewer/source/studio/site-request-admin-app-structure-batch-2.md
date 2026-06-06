---
doc_id: site-request-admin-app-structure-batch-2
title: Admin App Structure Batch 2
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: done
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# UI Catalogue Under Admin

This is the delivery specification for Batch 2 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 2: UI Catalogue Under Admin

Summary: move UI Catalogue routes, source, scoped assets, tests, and fixtures under Admin, then retire the standalone UI Catalogue app server and launcher.

| ID | status | action |
| --- | --- | --- |
| 2.1 | done | Move UI Catalogue source, palette/reference data, demo pages, and demo assets into `admin-app/ui-catalogue/`. |
| 2.2 | done | Serve UI Catalogue through Admin routes under `/admin/ui-catalogue/...`. |
| 2.3 | done | Keep UI Catalogue demo CSS and JavaScript scoped to UI Catalogue rather than merging them into `admin.css`. |
| 2.4 | done | Move UI Catalogue tests and fixtures to Admin-owned test paths that validate Admin-hosted UI Catalogue behavior. |
| 2.5 | done | Update Admin home navigation to point to Admin-hosted UI Catalogue routes. |
| 2.6 | done | Clean up standalone UI Catalogue app server source, launcher, local-all startup entry, and UI Catalogue-specific app docs references. |

## Steer for these tasks

- Batch 1 created the Admin app skeleton, `bin/local-admin`, `bin/local-all` startup wiring, `admin.css`, focused Admin server tests, and a visible `/admin/` home with links to UI Catalogue and sibling apps.
- UI Catalogue becomes Admin-hosted but keeps distinct demo code, CSS, class names, and palette/reference data.
- The target route family is `/admin/ui-catalogue/...`.
- Verification should prove Admin-hosted UI Catalogue pages render and behave correctly.
- Retired server cleanup should be handled by source, launcher, and docs updates.

## Deliverables

- UI Catalogue source under `admin-app/ui-catalogue/`.
- Admin route handlers/views for UI Catalogue.
- Moved UI Catalogue tests and fixtures.
- Admin-hosted UI Catalogue smoke coverage.
- Cleanup of standalone UI Catalogue app server and launcher ownership.

## Implementation and policy guidance

- Keep the current UI Catalogue route behavior and visual demo behavior stable.
- Use Admin as the route/server owner.
- Keep UI Catalogue CSS scoped so Admin shell styles and demo styles remain easy to reason about.
- Update references directly to Admin paths and routes.

## Proposed verification set

- Admin server pytest covering UI Catalogue route dispatch.
- Admin UI Catalogue smoke covering demo index, representative primitive/pattern page, palette/reference page, assets, and theme behavior.
- JavaScript syntax checks for moved UI Catalogue demo scripts.
- Source review for launcher and local-all UI Catalogue cleanup.

## completed verification

- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_admin_app_server.py admin-app/tests/python/test_admin_ui_catalogue.py studio/tests/python/test_studio_app_server.py` passed.
- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/app/server/admin_app/admin_app_config.py admin-app/app/server/admin_app/admin_app_server.py admin-app/app/server/admin_app/ui_catalogue_config.py admin-app/app/server/admin_app/ui_catalogue_views.py admin-app/tests/smoke/admin_ui_catalogue_routes.py admin-app/tests/smoke/admin_ui_catalogue_modal_demo.py admin-app/tests/smoke/admin_home_route.py studio/services/media/build_palette_data.py studio/checks/risk_evidence_pack.py studio/commands/run_checks.py` passed.
- `node --check admin-app/ui-catalogue/assets/js/ui-catalogue-demo.js` passed.
- `node --check admin-app/ui-catalogue/assets/js/ui-catalogue-shell.js` passed.
- `bash -n bin/local-all bin/local-admin` passed.
- `$HOME/miniconda3/bin/python3 admin-app/tests/smoke/admin_home_route.py` passed with elevated localhost permissions.
- `$HOME/miniconda3/bin/python3 admin-app/tests/smoke/admin_ui_catalogue_routes.py` passed with elevated localhost and browser permissions.
- `$HOME/miniconda3/bin/python3 admin-app/tests/smoke/admin_ui_catalogue_modal_demo.py` passed with elevated localhost and browser permissions.
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile ui-catalogue-smoke --run-id admin-ui-catalogue-batch-2` passed; summary: `var/test-runs/admin-ui-catalogue-batch-2/summary.md`.
- `git diff --check` passed.
- Source/config review found no runtime references to `ui-catalogue-app`, `bin/local-ui-catalogue`, `UI_CATALOGUE_APP`, or the retired `/ui-catalogue/app/...` asset namespace outside intentional negative tests and historical request/tmp notes.

## follow-on tasks

- Batch 3 moves the current Studio audit, risk, and activity pages into the Admin app.

## task close

- Add a handoff note to Batch 3.
- Set `ui_status` to `done` after Admin-hosted UI Catalogue behavior is verified.
