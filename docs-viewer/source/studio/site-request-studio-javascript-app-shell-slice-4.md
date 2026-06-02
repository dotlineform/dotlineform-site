---
doc_id: site-request-studio-javascript-app-shell-slice-4
title: Studio JavaScript App Shell Slice 4 Tasks
added_date: "2026-05-30 22:40"
last_updated: "2026-05-30 22:40"
ui_status: done
parent_id: site-request-studio-javascript-app-shell
viewable: true
---
# Studio JavaScript App Shell Slice 4 Tasks

This is the fourth implementation tracker for [Studio JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-studio-javascript-app-shell).

Slice 4 migrates the catalogue support routes whose bodies are compact and less form-heavy than the editor family:

- Catalogue Drafts
- Catalogue Field Registry
- Studio Works

## Status

### just done

- Added route-local shell body renderers for Catalogue Drafts, Catalogue Field Registry, and Studio Works.
- Marked `catalogue_status`, `catalogue_field_registry`, and `studio_works` as `shell_type: "javascript"` in `app.routes`.
- Changed Python dispatch so `/studio/catalogue-status/`, `/studio/catalogue-field-registry/`, and `/studio/studio-works/` serve the generic Studio app bootstrap.
- Removed the retired Python-rendered route bodies for the migrated routes.
- Kept `catalogue-status.js`, `catalogue-field-registry-review.js`, and `studio-works.js` on side-effect boot.

### boundary decisions

- The generic app shell remains a small vanilla JavaScript shell. It still owns route resolution, common chrome, Docs Viewer links, route body renderer lookup, and route script import only.
- Route body markup belongs in route-local browser modules:
  - `catalogue-status-shell.js`
  - `catalogue-field-registry-shell.js`
  - `studio-works-shell.js`
- Python still owns catalogue editor shells, catalogue APIs, source reads/writes, media attribute calculation for editor routes, validation, and filesystem mutation.
- The catalogue editor family remains outside this slice because those bodies carry more state, modals, and write workflows.

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| 1 | done | Move Catalogue Drafts route body markup from Python into a route-local browser module. |
| 2 | done | Move Catalogue Field Registry route body markup from Python into a route-local browser module. |
| 3 | done | Move Studio Works route body markup from Python into a route-local browser module. |
| 4 | done | Mark the three migrated catalogue support routes as JavaScript shell routes in `app.routes`. |
| 5 | done | Update Python route dispatch so migrated route URLs serve the generic Studio app bootstrap. |
| 6 | done | Verify route-ready state, Docs Viewer links, service/data requests, and desktop/mobile behavior with focused smokes. |
| 7 | done | Update owning runtime/request docs and record a structured implementation log. |

## Framework Checkpoint Evidence

Current evidence still favors staying with vanilla JavaScript before the catalogue editor family:

- Seven migrated routes now share the same small shell without lifecycle, render-diff, nested layout state, or component machinery.
- Route-local body modules are explicit and simple.
- Existing side-effect route controllers remain deterministic because body markup exists before controller import.
- Catalogue support routes did not introduce repeated body-render helper behavior beyond explicit module mapping.

Watch in slice 5:

- whether editor route bodies make `studio-app.js` body lookup too large
- whether editor route boot would be cleaner with explicit `mount(root, config, context)` exports
- whether media/config attributes currently calculated in Python should move into runtime config before editor routes migrate
- whether catalogue editor modals and write workflow state need a framework evaluation checkpoint before the whole family moves

## Slice 5 Handoff

Recommended next batch:

- Work editor
- Work Detail editor
- Series editor
- Moment editor

Split this batch if the first editor route exposes route boot, modal lifecycle, or media config ownership risks that are not present in the support routes.

Acceptance checks for each migrated route:

- route registry marks the route as `shell_type: "javascript"`
- Python route dispatch serves the generic Studio app bootstrap
- route body markup is owned by a route-local browser module
- route controller still reaches `data-studio-ready="true"`
- backend endpoints, activity context, modals, and write flows are unchanged
- Docs Viewer link resolves from route `doc_id`
- route smoke passes on desktop and mobile

Generated payload status: docs watcher may regenerate Studio docs/search payloads when this source doc changes; do not manually rebuild docs payloads for this slice.

## Slice 4 Closeout

Verification completed:

- `$HOME/miniconda3/bin/python3 -m json.tool studio/app/frontend/config/studio-config.json`
- `$HOME/miniconda3/bin/python3 -m py_compile studio/app/server/studio/studio_app_config.py studio/app/server/studio/studio_catalogue_views.py studio/app/server/studio/studio_app_server.py studio/tests/python/test_studio_app_server.py studio/tests/smoke/local_studio_app_catalogue_status_route.py studio/tests/smoke/local_studio_app_catalogue_field_registry_route.py studio/tests/smoke/local_studio_app_studio_works_route.py`
- `node --check studio/app/frontend/js/studio-app.js`
- `node --check studio/app/frontend/js/catalogue-status-shell.js`
- `node --check studio/app/frontend/js/catalogue-field-registry-shell.js`
- `node --check studio/app/frontend/js/studio-works-shell.js`
- `node --check studio/app/frontend/js/studio-config.js`
- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py -q`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_catalogue_status_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_catalogue_field_registry_route.py`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_studio_works_route.py`
- `git diff --check`

Generated payload status: docs watcher regenerated Studio docs/search payloads while source docs were edited; Codex did not manually rebuild docs payloads.

Known risks:

- `studio-app.js` now has explicit body renderer mappings for seven routes. Keep this until the editor family proves whether route body lookup needs a focused registry helper.
- Catalogue editor routes still rely on Python-rendered body attributes for media config and form shells. Slice 5 should decide whether those attributes move into runtime config before editor bodies migrate.
- Side-effect route boot remains workable. The editor family is the first point where a `mount()` export may become materially cleaner.
