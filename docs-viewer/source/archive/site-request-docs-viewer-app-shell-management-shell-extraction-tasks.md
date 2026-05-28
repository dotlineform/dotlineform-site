---
doc_id: site-request-docs-viewer-app-shell-management-shell-extraction-tasks
title: Docs Viewer App Shell Management Shell Extraction Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: done
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12140
viewable: true
---
# Docs Viewer App Shell Management Shell Extraction Tasks

This is the tracker for the next app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The slice should move the remaining management-only shell markup out of `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` into focused JavaScript app-shell owners.
The normal route shells should keep route id/config URL, app mounts, CSS links, and the entry script, while JavaScript renders management-only modal/context-menu hosts only when route config allows management UI.

This slice intentionally combines the management context menu, metadata modal shell, import modal shell, settings modal shell, and their required host refs because they share the same management-only route boundary and verification surface.
It should not include app boot ownership, route/document workflow extraction, source editor features, semantic-reference views, activity views, panel toolbar generalization, third-party visualization modules, plugin architecture, or backend write behavior.

## Status

### just done

- Completed this management shell extraction slice.
- Added `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` as the focused app-shell owner for management-only context-menu and modal shell markup.
- Replaced duplicated management-only shell markup in `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` with `#docsViewerManagementShellMount`.
- Kept public routes gated: management shell rendering and the new renderer import happen only when `routeContext.access.canLoadManagementUi` allows management UI.
- Extended `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` to cover management shell rendering, public omission, preserved refs, and idempotent rendering.
- Created docs-log entry `change-2026-05-27-extracted-docs-viewer-management-shell-rendering`.
- Completed [Docs Viewer Route Config Handoff Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-route-config-handoff-tasks).
- Added `docs-viewer/config/routes/docs-viewer-routes.json` as the browser-safe route-config registry.
- Thinned shared and standalone route shells to boot with `data-route-id` and `data-route-config-url`.
- Refreshed [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell) with the current completion-oriented sequence.
- Identified management shell extraction as the next concrete slice before app boot ownership.

### steer for next task

- Move app boot ownership out of `docs-viewer/runtime/js/docs-viewer.js` without changing route/document workflows.
- Preserve all existing IDs and refs consumed by `docs-viewer/runtime/js/docs-viewer-management.js`, `docs-viewer/runtime/js/docs-viewer-management-modals.js`, `docs-viewer/runtime/js/docs-html-import.js`, and related management workflow modules.
- Keep route config and access projection as the management UI gate; public routes must not render or import management-only shell/module code.
- Keep backend reachability, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, and rebuild behavior in the existing management flow.
- App boot extraction is the next slice after management shell ownership is clear.

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-management.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-management-modals.js`
  - `node --check docs-viewer/runtime/js/docs-html-import.js`
  - any new or changed focused management-shell renderer/host modules
- Focused app-shell module smoke checks:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for management shell rendering, public omission, id/ref preservation, and idempotent rendering
- Management modal and manage-mode route checks:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when shell output or management asset gating changes:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Docs-only follow-through when source docs change:
  - review generated docs payload status; let the docs watcher update generated payloads if it is running and do not revert watcher output

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for shared runtime files.
- This slice is structural app-shell work, not feature-layer management work.
- Prefer extending `docs-viewer/runtime/js/docs-viewer-app-shell.js` through a focused management-shell renderer/host module rather than adding large markup builders directly to `docs-viewer.js`.
- Keep `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` as route integration shells: CSS links, `#docsViewerRoot`, route id/config URL, app mounts, and entry script.
- Preserve public read-only behavior first-class: `/library/` and `/analysis/` should not load management CSS, management-only JavaScript, or management shell markup.
- Preserve local `/docs/` management behavior first-class: manage-mode detection, management capability messages, generated-data reads, action gating, metadata edit flow, import flow, settings flow, context menu, report rendering, browser history behavior, and info panel must continue to work.
- Backend capability checks and write authority remain in the management controller/service flow, not in static route config or shell markup.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory completed. Moved hosts/refs: `docsViewerContextMenu`; `docsViewerMetadataModal` and metadata form/input/popup/save refs; `docsViewerImportModal`, `docsHtmlImportRoot`, `docsHtmlImportBootStatus`, and the `docsHtmlImport*` import body refs; `docsViewerSettingsModal` and settings form/input/status/action refs. Consumers remain `docs-viewer-management.js`, `docs-viewer-management-modals.js`, `docs-viewer-management-interactions.js`, and `docs-html-import.js`. |
| 2 | done | Added `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` as one focused child renderer for the shared management-only route boundary: context menu, metadata modal, import modal, settings modal, and import host refs render together. |
| 3 | done | `docs-viewer/runtime/js/docs-viewer-app-shell.js` renders the management shell only when `routeContext.access.canLoadManagementUi` is true. |
| 4 | done | Preserved existing IDs, `data-*` hooks, form names, modal roles/labels, focus targets, and refs expected by management modules; metadata edit, import, settings, context action, and management modal workflows were not rewritten. |
| 5 | done | Replaced management-only markup in `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` with `#docsViewerManagementShellMount`; route shells still carry CSS links, route id/config URL, app mounts, and the entry script. |
| 6 | done | Public routes clear the management shell mount and do not dynamically import `docs-viewer-management-shell-renderer.js`; management stylesheet loading remains gated by management-enabled shell settings. |
| 7 | done | Added management shell refs to `docs-viewer-app-shell.js`; `docs-viewer.js` passes those refs to the lazy management controller after app-shell initialization, and management modules keep direct lookup fallback compatibility. |
| 8 | done | Extended focused app-shell smoke coverage for management shell rendering, public omission, ref preservation, and idempotent app-shell rendering. |
| 9 | done | Ran management modal and service smoke checks for metadata edit flow, import modal boot, settings modal, context menu/action gating, management capability status, generated-data reads, report rendering, and info-panel behavior. |
| 10 | done | Ran public read-only checks for `/library/` and `/analysis/` after a temporary Jekyll build; the public routes booted and omitted management shell/assets. |
| 11 | done | Updated this tracker, the app-shell request, Docs Viewer runtime boundary, Docs Viewer overview, Docs Viewer portable files, and Docs Viewer JavaScript inventory notes. |
| 12 | done | Created structured docs-log entry `change-2026-05-27-extracted-docs-viewer-management-shell-rendering`. |

## Closeout

Management shell rendering is now owned by `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js`, coordinated by `docs-viewer/runtime/js/docs-viewer-app-shell.js`.
The shared and standalone route shells no longer contain management-only context-menu or modal shell markup.

Verification passed:

- `node --check docs-viewer/runtime/js/docs-viewer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
- `node --check docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-management.js`
- `node --check docs-viewer/runtime/js/docs-viewer-management-modals.js`
- `node --check docs-viewer/runtime/js/docs-html-import.js`
- `node --check docs-viewer/runtime/js/docs-viewer-management-interactions.js`
- `git diff --check`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`

Generated Docs Viewer payloads were updated by the local docs watcher after source docs changed.
The docs-log generated indexes were rebuilt after the structured log entry was written.

Remaining risk: `docs-viewer/runtime/js/docs-viewer.js` still owns app boot/controller orchestration.
That remains the next planned slice; app boot ownership was deliberately not started here.

The closeout for this slice should confirm:

- shared and standalone route shells no longer contain management-only context-menu or modal shell markup
- management shell rendering is owned by focused JavaScript app-shell modules
- existing management refs and workflow behavior are preserved
- public read-only routes still avoid management-only shell markup, CSS, and JavaScript
- local manage mode still gets backend capability checks and write authority from the management/service flow
- metadata edit, import, settings, context menu, management actions, generated-data reads, reports, bookmarks, info panel, search/recent, and route history still work
- app boot ownership remains a separate next slice
