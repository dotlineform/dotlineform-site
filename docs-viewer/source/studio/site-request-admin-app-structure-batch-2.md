---
doc_id: site-request-admin-app-structure-batch-2
title: Admin App Structure Batch 2
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: planned
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# UI Catalogue Under Admin

This is the delivery specification for Batch 2 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 2: UI Catalogue Under Admin

Summary: move UI Catalogue routes, source, scoped assets, tests, and fixtures under Admin, then retire the standalone UI Catalogue app server and launcher.

| ID | status | action |
| --- | --- | --- |
| 2.1 | planned | Move UI Catalogue source, palette/reference data, demo pages, and demo assets into `admin-app/ui-catalogue/`. |
| 2.2 | planned | Serve UI Catalogue through Admin routes under `/admin/ui-catalogue/...`. |
| 2.3 | planned | Keep UI Catalogue demo CSS and JavaScript scoped to UI Catalogue rather than merging them into `admin.css`. |
| 2.4 | planned | Move UI Catalogue tests and fixtures to Admin-owned test paths that validate Admin-hosted UI Catalogue behavior. |
| 2.5 | planned | Update Admin home navigation to point to Admin-hosted UI Catalogue routes. |
| 2.6 | planned | Clean up standalone UI Catalogue app server source, launcher, local-all startup entry, and UI Catalogue-specific app docs references. |

## Steer for these tasks

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

- pending

## follow-on tasks

- Batch 3 moves the current Studio audit, risk, and activity pages into the Admin app.

## task close

- Add a handoff note to Batch 3.
- Set `ui_status` to `done` after Admin-hosted UI Catalogue behavior is verified.
