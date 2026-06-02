---
doc_id: site-request-studio-javascript-app-shell-slice-2
title: Studio JavaScript App Shell Slice 2 Tasks
added_date: "2026-05-30 22:00"
last_updated: "2026-05-30 22:00"
ui_status: done
parent_id: site-request-studio-javascript-app-shell
viewable: true
---
# Studio JavaScript App Shell Slice 2 Tasks

This is the second implementation tracker for [Studio JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-studio-javascript-app-shell).

Slice 2 adds the minimal JavaScript Studio app shell and migrates one low-risk route: Project State.

## Status

### just done

- Added `studio/app/frontend/js/studio-app.js` as the minimal browser-owned shell renderer.
- Added `studio/app/frontend/js/project-state-shell.js` as the route-local Project State body renderer.
- Changed `project_state.shell_type` from `python` to `javascript` in `app.routes`.
- Changed `/studio/project-state/` to serve the generic Studio app bootstrap from Python.
- Kept `studio/app/frontend/js/project-state.js` on side-effect boot for this slice.
- Removed the Python `project_state_view()` route body from `studio/app/server/studio/studio_app_views.py`.
- Extended the Project State smoke to verify desktop and mobile ready-state behavior.

### boundary decisions

- The browser shell owns the common header, title row, Docs Viewer doc link, route content slot, and route module loading for `shell_type: "javascript"` routes.
- Route-specific body markup does not live in the app shell. Project State owns it in `project-state-shell.js`.
- Existing route controllers may continue side-effect boot during early migration slices. A standard `mount()` export is deferred until there is evidence that side-effect boot creates ordering or testing problems.
- Python still serves the minimal bootstrap HTML and all local write/read APIs.

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| 1 | done | Add a minimal Studio JavaScript bootstrap shell that reads runtime config, resolves the active route, renders common shell chrome, and imports the active route script. |
| 2 | done | Move Project State route body markup from Python into a route-local browser module without changing route behavior. |
| 3 | done | Mark only `project_state` as `shell_type: "javascript"` and keep other active routes on `shell_type: "python"`. |
| 4 | done | Update Python route dispatch so `/studio/project-state/` serves the generic JavaScript app bootstrap. |
| 5 | done | Preserve Project State route-ready, backend API, activity context, doc-link, and top-navigation behavior. |
| 6 | done | Extend focused tests and smokes for runtime config, shell contract, Project State route ready state, and desktop/mobile coverage. |
| 7 | done | Update owning runtime/request docs and record framework-checkpoint evidence for slices 2-3. |

## Framework Checkpoint Evidence

Current evidence favors staying with vanilla JavaScript through slice 3:

- The generic app shell is small and only owns config load, route resolution, common chrome, route body renderer lookup, and route script import.
- Project State did not need a component lifecycle or render-diff model.
- Side-effect boot remained workable once route markup existed before importing `project-state.js`.
- No build step was needed.
- Smoke-test impact was modest: the existing Project State route smoke now verifies that Python serves a bootstrap and that browser-rendered route markup reaches ready state on desktop and mobile.

Watch in slice 3:

- repeated route body renderer patterns across Audits, Activity, and Bulk Add Work
- duplicated shell/nav/doc-link helpers between `studio-app.js` and `studio-navigation.js`
- whether side-effect route boot becomes hard to order or isolate
- whether operational routes start accumulating ad hoc state/render helpers

## Slice 3 Handoff

Recommended next batch:

- Audits
- Activity
- Bulk Add Work

Acceptance checks for each migrated route:

- route registry marks only the migrated route as `shell_type: "javascript"`
- Python route dispatch serves the generic Studio app bootstrap
- route body markup is owned by a route-local browser module
- route controller still reaches `data-studio-ready="true"`
- backend endpoints and activity context are unchanged
- Docs Viewer link resolves from route `doc_id`
- route smoke passes on desktop and mobile

Generated payload status: docs watcher may regenerate Studio docs/search payloads when this source doc changes; do not manually rebuild docs payloads for this slice.

## Slice 2 Closeout

Verification completed:

- `$HOME/miniconda3/bin/python3 -m json.tool studio/app/frontend/config/studio-config.json`
- `$HOME/miniconda3/bin/python3 -m py_compile studio/app/server/studio/studio_app_config.py studio/app/server/studio/studio_app_views.py studio/app/server/studio/studio_app_server.py studio/tests/python/test_studio_app_server.py studio/tests/smoke/local_studio_app_project_state_route.py studio/tests/smoke/studio_operational_route_modules.py`
- `node --check studio/app/frontend/js/studio-app.js`
- `node --check studio/app/frontend/js/project-state-shell.js`
- `node --check studio/app/frontend/js/studio-config.js`
- `node --check studio/app/frontend/js/studio-route-registry.js`
- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py -q`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/studio_operational_route_modules.py --site-root .`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_project_state_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_navigation_adapter.py`
- `rg -n "project_state_view|projectStateRoot" studio/app/server studio/app/frontend/js docs-viewer/source/studio/site-request-studio-javascript-app-shell-slice-2.md docs-viewer/source/studio/local-studio-app.md docs-viewer/source/studio/studio-runtime.md`
- `git diff --check`

Generated payload status: docs watcher regenerated Studio docs/search payloads while source docs were edited; Codex did not manually rebuild docs payloads.

Known risks:

- `studio-app.js` currently duplicates a small amount of Docs Viewer URL building and header rendering from the Python/legacy navigation path. Slice 3 should decide whether to extract a pure shared URL/header helper before migrating several operational routes.
- Route body renderer registration is an explicit small map in `studio-app.js`. That is acceptable for one route; if slice 3 adds three more routes, keep the map simple or move route body lookup behind a focused registry helper.
- Side-effect route boot worked for Project State. Revisit a `mount()` export only if slice 3 shows ordering or test isolation friction.
