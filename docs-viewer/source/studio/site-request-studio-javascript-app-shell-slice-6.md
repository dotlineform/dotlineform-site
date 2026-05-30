---
doc_id: site-request-studio-javascript-app-shell-slice-6
title: Studio JavaScript App Shell Slice 6 Tasks
added_date: "2026-05-30 22:15"
last_updated: "2026-05-30 22:15"
ui_status: done
parent_id: site-request-studio-javascript-app-shell
viewable: true
---
# Studio JavaScript App Shell Slice 6 Tasks

This is the sixth implementation tracker for [Studio JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-studio-javascript-app-shell).

Slice 6 retires the remaining Python route-shell contract and records the source ownership follow-through after all configured Studio-local routes moved to the JavaScript app shell.

## Status

### just done

- Removed the obsolete Python-rendered route helper from `studio_app_views.py`; Python now keeps only the Studio home page and generic JavaScript app bootstrap shells.
- Removed `python` from the accepted active Studio shell types in Python and browser route-registry validation.
- Updated the built-in Studio config fallback so all active Studio-local route fixtures use `shell_type: "javascript"`.
- Tightened focused server tests so runtime config must not expose any `python` shell routes.
- Updated Studio runtime/local-app docs for the current JavaScript-shell ownership boundary.
- Refreshed the JavaScript inventory summary and added the app shell, route-registry, navigation, theme, save utility, and route-local shell renderer rows.

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| 1 | done | Retire the obsolete Python route-specific shell helper and unused support loader. |
| 2 | done | Remove `python` as an accepted active Studio shell type from browser and Python route-registry helpers. |
| 3 | done | Update fallback config/test fixtures so they cannot reintroduce Python-shell Studio routes. |
| 4 | done | Update Studio runtime/local-app docs for the JavaScript-owned route shell boundary. |
| 5 | done | Refresh JavaScript inventory counts and rows for the app shell and route-local shell modules. |
| 6 | done | Verify config validation, syntax, server tests, and focused route smoke coverage. |
| 7 | done | Record a structured implementation log. |

## Closeout

Verification completed:

- `$HOME/miniconda3/bin/python3 -m json.tool studio/app/frontend/config/studio-config.json`
- `$HOME/miniconda3/bin/python3 -m py_compile studio/app/server/studio/studio_app_config.py studio/app/server/studio/studio_app_server.py studio/app/server/studio/studio_app_views.py studio/tests/python/test_studio_app_server.py`
- `node --check studio/app/frontend/js/studio-config.js`
- `node --check studio/app/frontend/js/studio-route-registry.js`
- `node --check studio/app/frontend/js/studio-app.js`
- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py -q`
- `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`
- `$HOME/miniconda3/bin/python3 -m json.tool studio/workflows/change-requests/logs/entries/change-2026-05-30-studio-javascript-shell-cleanup.json`
- `$HOME/miniconda3/bin/python3 studio/workflows/change-requests/services/docs_logs/build_indexes.py --write`
- `git diff --check`

Generated payload status: docs watcher may regenerate Studio docs/search payloads when source docs change; Codex did not manually rebuild docs payloads for this slice.

Known risks:

- `studio-app.js` still owns an explicit body renderer mapping. This remains acceptable for the current route count, but a future route-family migration should move lookup into a focused registry helper if the mapping grows.
