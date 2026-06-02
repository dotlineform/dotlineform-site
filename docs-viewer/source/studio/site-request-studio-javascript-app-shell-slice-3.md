---
doc_id: site-request-studio-javascript-app-shell-slice-3
title: Studio JavaScript App Shell Slice 3 Tasks
added_date: "2026-05-30 22:30"
last_updated: "2026-05-30 22:30"
ui_status: done
parent_id: site-request-studio-javascript-app-shell
viewable: true
---
# Studio JavaScript App Shell Slice 3 Tasks

This is the third implementation tracker for [Studio JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-studio-javascript-app-shell).

Slice 3 migrates the compact operational route batch after the Project State shell pattern proved workable:

- Studio Audits
- Studio Activity
- Bulk Add Work

## Status

### just done

- Added route-local shell body renderers for Audits, Activity, and Bulk Add Work.
- Marked `studio_audits`, `activity`, and `bulk_add_work` as `shell_type: "javascript"` in `app.routes`.
- Changed Python dispatch so `/studio/audits/`, `/studio/activity/`, and `/studio/bulk-add-work/` serve the generic Studio app bootstrap.
- Removed the retired Python-rendered route bodies for the migrated routes.
- Published the configured bulk-import workbook path through `app.runtime.pipeline.workbooks` so the Bulk Add Work browser shell can render the same route root attributes the existing controller expects.
- Kept `studio-audits.js`, `activity-log.js`, and `bulk-add-work.js` on side-effect boot.

### boundary decisions

- The generic app shell still only owns runtime-config load, route resolution, shared chrome, Docs Viewer link construction, body-renderer lookup, and route script import.
- Route body markup belongs in route-local browser modules:
  - `studio-audits-shell.js`
  - `activity-log-shell.js`
  - `bulk-add-work-shell.js`
- Python continues to own local audit and catalogue APIs, filesystem writes, workbook import execution, report generation, and source reads that must stay behind the local app server.
- A shared renderer registry in `studio-app.js` remains acceptable for four migrated routes. A separate registry helper can wait until route body lookup gains more behavior than explicit module mapping.

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| 1 | done | Move Audits route body markup from Python into a route-local browser module. |
| 2 | done | Move Activity route body markup from Python into a route-local browser module. |
| 3 | done | Move Bulk Add Work route body markup from Python into a route-local browser module and preserve the workbook path contract. |
| 4 | done | Mark the three migrated operational routes as JavaScript shell routes in `app.routes`. |
| 5 | done | Update Python route dispatch so migrated route URLs serve the generic Studio app bootstrap. |
| 6 | done | Verify route-ready state, Docs Viewer links, service endpoints, and desktop/mobile behavior with focused smokes. |
| 7 | done | Update owning runtime/request docs and record a structured implementation log. |

## Framework Checkpoint Evidence

Current evidence still favors staying with vanilla JavaScript through slice 4:

- Four migrated routes share the same small browser shell without needing component lifecycle, diffing, nested layout state, or route-local mount APIs.
- Side-effect route boot remains deterministic because body markup is rendered before importing each existing controller.
- The only new config handoff was Bulk Add Work's workbook path, which now uses the existing runtime-config boundary.
- The repeated body-renderer pattern is still simple module ownership rather than a framework-like lifecycle.

Watch in slice 4:

- whether catalogue support route bodies introduce repeated helper needs across Catalogue Status, Catalogue Field Registry, and Studio Works
- whether `studio-app.js` should extract body-renderer lookup before the catalogue editor family
- whether Docs Viewer URL/header helper duplication between `studio-app.js` and `studio-navigation.js` is still small enough to leave alone

## Slice 4 Handoff

Recommended next batch:

- Catalogue Status
- Catalogue Field Registry
- Studio Works

Acceptance checks for each migrated route:

- route registry marks the route as `shell_type: "javascript"`
- Python route dispatch serves the generic Studio app bootstrap
- route body markup is owned by a route-local browser module
- route controller still reaches `data-studio-ready="true"`
- backend endpoints and activity context are unchanged
- Docs Viewer link resolves from route `doc_id`
- route smoke passes on desktop and mobile

Generated payload status: docs watcher may regenerate Studio docs/search payloads when this source doc changes; do not manually rebuild docs payloads for this slice.

## Slice 3 Closeout

Verification completed:

- `$HOME/miniconda3/bin/python3 -m json.tool studio/app/frontend/config/studio-config.json`
- `$HOME/miniconda3/bin/python3 -m py_compile studio/app/server/studio/studio_app_config.py studio/app/server/studio/studio_app_views.py studio/app/server/studio/studio_app_server.py studio/tests/python/test_studio_app_server.py studio/tests/smoke/local_studio_app_audits_route.py studio/tests/smoke/local_studio_app_activity_route.py studio/tests/smoke/local_studio_app_bulk_add_work_route.py`
- `node --check studio/app/frontend/js/studio-app.js`
- `node --check studio/app/frontend/js/studio-audits-shell.js`
- `node --check studio/app/frontend/js/activity-log-shell.js`
- `node --check studio/app/frontend/js/bulk-add-work-shell.js`
- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py -q`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_audits_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_activity_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_bulk_add_work_route.py`
- `git diff --check`

Generated payload status: docs watcher regenerated Studio docs/search payloads while source docs were edited; Codex did not manually rebuild docs payloads.

Known risks:

- `studio-app.js` still keeps an explicit route body renderer map. That is acceptable for four migrated routes, but slice 4 should extract lookup if catalogue support routes make the map carry more policy than module selection.
- `studio-app.js` and `studio-navigation.js` still duplicate a small amount of Docs Viewer URL/header behavior. Leave it until the duplication becomes harder to reason about than a shared helper.
- Side-effect route boot remains workable. Revisit a `mount()` export only if route ordering or test isolation gets fragile in the catalogue support or editor slices.
