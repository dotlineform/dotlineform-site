---
doc_id: site-request-admin-app-structure-batch-5
title: Admin App Structure Batch 5
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: planned
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# Studio Local Route Cleanup and App Script Cleanup

This is the delivery specification for Batch 5 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 5: Studio Local Route Cleanup and App Script Cleanup

Summary: clean retained Studio local routes, Studio route config, moved app scripts, and launcher/script references after Admin owns the moved surfaces.

| ID | status | action |
| --- | --- | --- |
| 5.1 | planned | Update retained Studio route config and navigation so local Studio routes use plain paths without `?mode=manage`. |
| 5.2 | planned | Keep `/studio/catalogue-field-registry/` and `/studio/project-state/` in Studio with focused route checks. |
| 5.3 | planned | Move or remove Studio app server dispatch, runtime config entries, UI text references, and frontend route modules for surfaces now owned by Admin. |
| 5.4 | planned | Clean existing app scripts and launchers whose ownership moved to Admin, including runner references and retired UI Catalogue service startup. |
| 5.5 | planned | Update Studio tests and smokes so retained Studio checks prove catalogue-maintenance routes work through the current Studio route contract. |
| 5.6 | planned | Review active docs/source references that point at moved Admin routes, scripts, output paths, and fixtures. |

## Steer for these tasks

- Studio remains the catalogue/public-site data maintenance app.
- Retained Studio routes use plain local paths.
- Cleanup is source, config, docs, and launcher ownership work after Admin behavior is already verified.
- Studio tests should assert retained Studio catalogue-maintenance behavior.

## Deliverables

- Updated Studio local route config.
- Retained Studio route checks for catalogue field registry and project state.
- Cleaned Studio app server/frontend ownership for moved routes.
- Cleaned app scripts and launcher references.
- Updated source references for Admin routes, runner, output paths, and fixtures.

## Implementation and policy guidance

- Keep Studio route checks focused on Studio routes that remain.
- Keep Admin route checks in Admin.
- Update direct route links and command references to current owner paths.
- Use source/config review for cleanup evidence.

## Proposed verification set

- focused Studio server/config pytest
- focused Studio route smoke for `/studio/catalogue-field-registry/`
- focused Studio route smoke for `/studio/project-state/`
- syntax checks for changed Studio Python and JavaScript
- source/config review for route registry and launcher references

## completed verification

- pending

## follow-on tasks

- Batch 6 updates durable docs, runs final verification, and closes the request.

## task close

- Add a handoff note to Batch 6.
- Set `ui_status` to `done` after retained Studio routes and app script cleanup are verified.
