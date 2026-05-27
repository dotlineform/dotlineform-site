---
doc_id: site-request-docs-viewer-app-shell-management-actions-tasks
title: Docs Viewer App Shell Management Actions Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: done
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12105
viewable: true
---
# Docs Viewer App Shell Management Actions Tasks

This is the tracker for implementing the first app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The first migration is the management action area.
It should move the manage-mode action row and related capability-gated controls out of `_includes/docs_viewer_shell.html` and into the JavaScript app shell without changing public route behavior.

## Status

### just done

- Created this task tracker.
- Confirmed the first shell migration target is the management action area.
- Recorded that `docs-viewer/runtime/js/docs-viewer-app-shell.js` is the preferred app-shell owner module and `docs-viewer/runtime/js/docs-viewer.js` remains the temporary loaded entrypoint.
- Implemented the first app-shell-owned management action coordinator in `docs-viewer/runtime/js/docs-viewer-app-shell.js` and the focused renderer in `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`.
- Replaced the duplicated management action markup in `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` with a narrow mount.
- Preserved the existing management control ids so `docs-viewer/runtime/js/docs-viewer-management.js` continues to own command wiring, backend reachability, and capability-gated updates.
- Added focused app-shell module smoke coverage for management-allowed rendering, management-disallowed omission, id preservation, and idempotent rendering.

### steer for next task

- Continue the app-shell migration with the next narrow shell responsibility, likely scope picker/header controls.
- Keep document rendering, index panel layout, metadata modal markup, import modal internals, and search behavior out of the next slice unless the request explicitly changes scope.
- Keep `docs-viewer.js` as the compatibility entrypoint and orchestration layer; new shell rendering belongs in `docs-viewer-app-shell.js` or focused app-shell children.

### baseline verification set

Run only the checks warranted by the touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - any changed focused management/app-shell modules
- Focused Docs Viewer management module smoke checks when IDs, refs, or event wiring change:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only smoke when shell markup or route boot changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py`
- Jekyll build only when includes, route templates, or loaded assets change:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for high-risk shared runtime files.
- This slice is part of the app-shell enabling work, not a broad `docs-viewer.js` refactor.
- Use generated route config as the direction for route/app handoff; existing data attributes can remain as temporary compatibility only.
- Use modular hosted views, not a plugin architecture.
- Keep current repo requirements first; do not introduce speculative portable/plugin machinery.
- Public routes must not load or expose management-only controls.
- Backend endpoints continue to enforce writes and filesystem operations.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventoried the duplicated management action area in `_includes/docs_viewer_shell.html`: both search-enabled and search-disabled branches carried the full `docsViewerManageRow`, Actions menu, rebuild, normalize order, settings, scope lifecycle, import, new/edit/archive/delete, viewability, hidden toggle, and manage-only theme toggle markup. The same shell source was mirrored in `docs-viewer/shell/docs-viewer-shell.html`. |
| 2 | done | Added `docs-viewer/runtime/js/docs-viewer-app-shell.js` with `initDocsViewerAppShell()`. It imports `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js` only when route intent allows management. `docs-viewer.js` only initializes this owner before existing boot refs are read. |
| 3 | done | Replaced the full management action row markup in both shell templates with `<div id="docsViewerManageActionsMount" data-docs-viewer-management-actions-mount></div>` in the existing management-only branches. |
| 4 | done | The focused management action renderer now renders the full management action area, including the Actions menu, rebuild, normalize order, settings, scope lifecycle entries, import, new/edit/archive/delete, show/hide viewability control, hidden toggle, and current manage-only theme toggle. |
| 5 | done | Preserved the existing management ids used by `docs-viewer-management.js`, so no broad management controller ref rewrite was needed. |
| 6 | done | Kept gating narrow: the app-shell renderer only uses route intent from `data-allow-management`; the existing lazy management controller still checks mode/backend reachability and applies capability-gated visibility/disabled state. |
| 7 | done | Verified public-route behavior with the read-only smoke: `/library/` and `/analysis/` do not render management actions, load management CSS, or import management-only JavaScript. |
| 8 | done | Added `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` covering management-allowed rendering, management-disallowed omission, expected control refs, scope lifecycle hidden defaults, theme toggle refs, and idempotent render. |
| 9 | done | Ran the targeted verification set recorded below. No expected checks were skipped. |
| 10 | done | Updated this tracker, the app-shell request, Docs Viewer overview, Docs Viewer portable manifest, and Docs Viewer JavaScript inventory notes. |

## Closeout 2026-05-27

Management action area ownership moved from Liquid shell markup to `docs-viewer/runtime/js/docs-viewer-app-shell.js` and `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`.
`_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` now keep only the necessary management action mount/context for this area.
`docs-viewer/runtime/js/docs-viewer.js` remains the compatibility entrypoint and initializes the app shell without taking ownership of management action rendering.
Public routes still omit management UI and do not import the management action renderer.

Verification run:

- `node --check docs-viewer/runtime/js/docs-viewer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
- `node --check docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`
- `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py docs-viewer/tests/smoke/public_docs_viewer_readonly.py docs-viewer/services/docs_viewer_service.py`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
- `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`

Source docs were updated in this slice.
Codex did not manually rebuild docs payloads; the local docs watcher regenerated the matching `docs-viewer/generated/docs/studio/` and `docs-viewer/generated/search/studio/` payloads after source doc edits.

The closeout for this first migration should confirm:

- management action area ownership moved from Liquid to JavaScript
- `_includes/docs_viewer_shell.html` keeps only the necessary mount/context for this area
- `docs-viewer.js` remains a compatibility entrypoint and does not become the long-term app-shell owner
- public routes still omit management UI
- generated docs payloads were rebuilt by the watcher only if source docs changed, or intentionally not rebuilt by Codex
