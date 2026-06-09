---
doc_id: site-request-risk-evidence-producers-task-6-admin-checks-ui
title: Risk Evidence Producers Task 6 Admin Checks UI
added_date: 2026-06-08
last_updated: 2026-06-09
ui_status: done
parent_id: site-request-risk-evidence-producers
viewable: true
---
# Risk Evidence Producers Task 6 Admin Checks UI

This is the delivery specification for Batch 6 in [Risk Evidence Producers Request](/docs/?scope=studio&doc=site-request-risk-evidence-producers).

### Batch 6: Add `/admin/checks/` UI

Summary: Build the Admin route for selecting targets/reports, running checks, reading markdown artifacts, and deleting snapshots. Design steer is provided in the sections below.

| ID | status | action |
| --- | --- | --- |
| 6.1 | done | Add the Admin route shell, frontend module, route config, and UI text bundle. |
| 6.2 | done | Render scope, file-family, functional-area, route, and report selection from API metadata. |
| 6.3 | done | Render report-specific controls from allowlisted option metadata. |
| 6.4 | done | Support the validated write run action. |
| 6.5 | done | List recent runs and restore selected run controls from run metadata. |
| 6.6 | done | Display selected report markdown. |
| 6.7 | done | Provide confirmed deletion for a selected local run snapshot. |
| 6.8 | done | Keep the UI dense and operational; avoid explanatory landing-page copy. |

## Batch 5 handoff

- This is an operational Admin UI, not a landing page.
- Markdown is displayed as escaped preformatted text.
- The UI can create validated runs and delete validated local snapshots only.

Batch 5 added `admin-app/app/server/admin_app/admin_checks_api.py` and registered `/admin/api/checks/...` in the Admin server.

Use these endpoints:

```text
GET    /admin/api/checks/health
GET    /admin/api/checks/reports
GET    /admin/api/checks/runs
POST   /admin/api/checks/runs
GET    /admin/api/checks/runs/<run-id>/summary
GET    /admin/api/checks/runs/<run-id>/reports/<report-id>
DELETE /admin/api/checks/runs/<run-id>
```

`GET /admin/api/checks/reports` returns safe metadata for scopes, families, areas, routes, reports, default options, and allowed options.
Do not hard-code report option controls when this metadata is sufficient.

`POST /admin/api/checks/runs` accepts the same JSON shape as the CLI orchestrator.
The UI must not send command strings, script paths, output roots, environment values, or arbitrary local paths.
The response includes a top-level `status` of `dry-run`, `passed`, or `failed`.

Summary reads return:

```text
summary
summary_markdown
summary_path
```

Report reads return:

```text
report
report_markdown
report_path
report_markdown_path
report_csv_path
report_csv_exists
```

Display `summary_markdown` and `report_markdown` as escaped preformatted text.
Do not render markdown to HTML in Batch 6.

## UI design

The `/admin/checks/` page should contain 2 regions, top and bottom.

top region contains two panels:
top left panel contains:
- vertically stacked dropdowns with left aligned labels for the report and filters selections:
  - report name
  - scope
  - family
  - area
  - route
- a 'run' button which runs the selected report with the selected filters
top right panel contains:
- a list control which lists the report folders in `var/admin/checks/`
- a 'delete' button which deletes the selected folder

bottom region contains:
- the markdown artifact path.
- the markdown file contents for the selected report.

general behaviour:
- 'run' generates the report, adds the folder to the list and selects it, displays the markdown in bottom panel
- whilst the report is being generated, the mouse pointer shows 'busy' state.
- selecting a report folder from the list sets the dropdowns to the selected report and filters for that report, and displays the markdown in the bottom panel.
- 'delete' clears all the dropdowns, clears the displayed markdown, removes the selected folder from the list and deselects the list.

implementation notes:
- refer to `ui-catalogue.md` for ui guidance and framework. However, the `ui.md` child pages are stale and inconsistent because they don't reflect all the current apps, which own their own css, so a 'best attempt' will be needed until we review and update the entire UI guidance.
- The Batch 6 UI always sends `write: true`; dry-run controls stay out of scope for this route.
- Opening the artifact path in VS Code is deferred to a later enhancement using the same handler family as Docs Viewer.

## Deliverables

- `/admin/checks/` route shell: done.
- frontend JS module: done.
- Admin config entries: done.
- UI text bundle: done.

## Implementation and policy guidance

- Follow existing Admin route patterns.
- Use allowlisted metadata from the checks API for controls.
- Do not let route config imply write authority beyond validated API endpoints.

## Proposed verification set

- Focused UI smoke if lower-level tests do not cover route behavior.
- Browser verification for route boot, metadata rendering, run action, artifact display, and snapshot deletion where practical.

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile admin-app/app/server/admin_app/admin_app_config.py admin-app/app/server/admin_app/admin_app_views.py admin-app/app/server/admin_app/admin_app_server.py admin-app/tests/python/test_admin_app_server.py`
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/admin-config.json`
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/ui-text/admin-checks.json`
- `node --check admin-app/app/frontend/js/admin-checks.js`
- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_admin_app_server.py admin-app/tests/python/test_admin_checks_api.py`
- Browser smoke against `http://127.0.0.1:8899/admin/checks/`: verified route boot, metadata controls, write-run behavior, run-folder selection, report markdown display, artifact path display, and enabled Delete control. The generated smoke run `20260609-215033-docs-viewer` was removed through the validated Admin checks API after the in-app browser automation surface could not accept the native `confirm` dialog.

## follow-on tasks

- Batch 7 adds focused tests and check-profile integration.

## task close

- Batch 7 handoff note added.
- Batch status and front matter `ui_status` set to `done`.
