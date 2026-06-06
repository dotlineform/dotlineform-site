---
doc_id: site-request-admin-app-structure-batch-1
title: Admin App Structure Batch 1
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: done
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# Admin Foundation

This is the delivery specification for Batch 1 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 1: Admin Foundation

Summary: create the Admin app skeleton, visible home, route shell, stylesheet, launcher, and baseline tests.

| ID | status | action |
| --- | --- | --- |
| 1.1 | planned | Create `admin-app/app/server/admin_app/` with a local Python app server, `/health`, `/admin/`, and static serving for Admin assets. |
| 1.2 | planned | Create `admin-app/app/frontend/` with Admin route config, route shell modules, navigation helpers, and UI text config needed for the visible home. |
| 1.3 | planned | Create `admin-app/app/assets/css/admin.css` for Admin shell, navigation, route layout, and Admin-owned page structure. |
| 1.4 | planned | Add visible `/admin/` home navigation for audits, risk, activity, testing, UI Catalogue, Studio, Analytics, and Docs Viewer. |
| 1.5 | planned | Add `bin/local-admin` and update `bin/local-all` so Admin starts as a focused sibling service. |
| 1.6 | planned | Add focused Admin server tests and a route smoke that proves `/admin/` renders the expected navigation and local-only route contract. |

## Steer for these tasks

- This batch creates the destination before moving existing functional pages.
- Admin is a focused app; process supervision remains with `bin/local-all`.
- Admin routes use plain `/admin/...` paths.
- The first smoke should prove the Admin home works and links to planned Admin route families.

## Deliverables

- Admin app source skeleton.
- Admin CSS at `admin-app/app/assets/css/admin.css`.
- Local Admin launcher.
- `bin/local-all` startup entry for Admin.
- Admin home route.
- Focused Admin server and home-route checks.

## Implementation and policy guidance

- Follow the existing Python local app server style used by Studio, Analytics, and UI Catalogue.
- Keep Admin UI text and route config in Admin-owned files.
- Keep sibling app links as navigation targets.
- Add positive tests for Admin server responses, route config, static asset serving, and visible home navigation.

## Proposed verification set

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/app/server/admin_app/*.py`
- focused Admin pytest for server/config behavior
- focused Admin smoke for `/admin/`
- source review for `bin/local-all` Admin startup entry

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/app/server/admin_app/admin_app_config.py admin-app/app/server/admin_app/admin_app_views.py admin-app/app/server/admin_app/admin_app_server.py admin-app/tests/python/test_admin_app_server.py admin-app/tests/smoke/admin_home_route.py`
- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_admin_app_server.py -q`
- `node --check admin-app/app/frontend/js/admin-home.js`
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/admin-config.json`
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/ui-text/admin-home.json`
- `bash -n bin/local-admin bin/local-all`
- `$HOME/miniconda3/bin/python3 admin-app/tests/smoke/admin_home_route.py`
- Browser check of `http://127.0.0.1:8791/admin/` confirmed Admin title, ready state, desktop links, Admin CSS colors, and mobile 390px layout without horizontal overflow.

## follow-on tasks

- Batch 2 can move UI Catalogue under the visible Admin home.
- Batch 3 can move audits, risk, and activity after the Admin destination exists.

## task close

- done
