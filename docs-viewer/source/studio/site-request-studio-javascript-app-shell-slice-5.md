---
doc_id: site-request-studio-javascript-app-shell-slice-5
title: Studio JavaScript App Shell Slice 5 Tasks
added_date: "2026-05-30 22:06"
last_updated: "2026-05-30 22:06"
ui_status: done
parent_id: site-request-studio-javascript-app-shell
viewable: true
---
# Studio JavaScript App Shell Slice 5 Tasks

This is the fifth implementation tracker for [Studio JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-studio-javascript-app-shell).

Slice 5 migrates the catalogue editor family:

- Work editor
- Work Detail editor
- Series editor
- Moment editor

## Status

### just done

- Added route-local shell body renderers for Work, Work Detail, Series, and Moment editor routes.
- Added a shared catalogue editor shell media helper that derives preview media attributes from runtime config instead of Python-rendered body attributes.
- Marked `catalogue_work_editor`, `catalogue_work_detail_editor`, `catalogue_series_editor`, and `catalogue_moment_editor` as `shell_type: "javascript"` in `app.routes`.
- Changed Python dispatch so `/studio/catalogue-work/`, `/studio/catalogue-work-detail/`, `/studio/catalogue-series/`, and `/studio/catalogue-moment/` serve the generic Studio app bootstrap.
- Removed the retired Python-rendered catalogue editor body module.
- Kept the existing side-effect route controllers, catalogue APIs, activity context, modals, and write workflows unchanged.

### boundary decisions

- `studio-app.js` still owns only route resolution, common chrome, Docs Viewer links, body renderer lookup, and side-effect route script import.
- Editor route body markup belongs in route-local browser modules:
  - `catalogue-work-shell.js`
  - `catalogue-work-detail-shell.js`
  - `catalogue-series-shell.js`
  - `catalogue-moment-shell.js`
- Catalogue preview media shell attributes are browser-rendered from `app.runtime.media` and `app.runtime.pipeline`.
- Python still owns catalogue APIs, source reads/writes, validation, backups, activity records, and filesystem mutation.

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| 1 | done | Move Work editor route body markup from Python into a route-local browser module. |
| 2 | done | Move Work Detail editor route body markup from Python into a route-local browser module. |
| 3 | done | Move Series editor route body markup from Python into a route-local browser module. |
| 4 | done | Move Moment editor route body markup from Python into a route-local browser module. |
| 5 | done | Move catalogue editor media body attributes to a browser-side helper backed by runtime config. |
| 6 | done | Mark the four migrated editor routes as JavaScript shell routes in `app.routes`. |
| 7 | done | Update Python route dispatch so migrated route URLs serve the generic Studio app bootstrap. |
| 8 | done | Verify route-ready state, Docs Viewer links, service/data requests, public links, and desktop/mobile behavior with focused smokes. |
| 9 | done | Update owning runtime/request docs and record a structured implementation log. |

## Framework Checkpoint Evidence

Current evidence still favors staying with vanilla JavaScript:

- The editor family migrated without adding route lifecycle, render diffing, nested layout state, or component machinery.
- Route body renderers remain static HTML functions that run before existing side-effect controllers import.
- Editor modal lifecycle and write workflows stayed in their existing focused modules.
- The only shared editor-shell behavior added in this slice is media attribute projection from runtime config.

Follow-up watch item:

- `studio-app.js` now has explicit body renderer mappings for the migrated route set. If the next route-family migration adds more entries, consider moving renderer lookup into a focused registry helper.

## Slice 5 Closeout

Verification completed:

- `$HOME/miniconda3/bin/python3 -m json.tool studio/app/frontend/config/studio-config.json`
- `$HOME/miniconda3/bin/python3 -m py_compile studio/app/server/studio/studio_app_config.py studio/app/server/studio/studio_app_server.py studio/tests/python/test_studio_app_server.py studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`
- `node --check studio/app/frontend/js/studio-app.js`
- `node --check studio/app/frontend/js/catalogue-editor-shell-media.js`
- `node --check studio/app/frontend/js/catalogue-work-shell.js`
- `node --check studio/app/frontend/js/catalogue-work-detail-shell.js`
- `node --check studio/app/frontend/js/catalogue-series-shell.js`
- `node --check studio/app/frontend/js/catalogue-moment-shell.js`
- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py -q`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`
- `$HOME/miniconda3/bin/python3 -m json.tool studio/workflows/change-requests/logs/entries/change-2026-05-30-studio-catalogue-editor-js-shells.json`
- `$HOME/miniconda3/bin/python3 studio/workflows/change-requests/services/docs_logs/build_indexes.py --write`
- `git diff --check`

Generated payload status: docs watcher may regenerate Studio docs/search payloads when source docs change; Codex did not manually rebuild docs payloads for this slice.

Known risks:

- Editor shell body markup remains static HTML; future behavior should continue to live in the existing focused editor modules, not in shell renderers.
- Public media preview behavior depends on `app.runtime.media` and `app.runtime.pipeline` staying aligned with `_data/pipeline.json`.
