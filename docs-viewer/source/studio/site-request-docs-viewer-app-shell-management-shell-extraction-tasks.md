---
doc_id: site-request-docs-viewer-app-shell-management-shell-extraction-tasks
title: Docs Viewer App Shell Management Shell Extraction Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: planned
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

- Completed [Docs Viewer Route Config Handoff Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-route-config-handoff-tasks).
- Added `docs-viewer/config/routes/docs-viewer-routes.json` as the browser-safe route-config registry.
- Thinned shared and standalone route shells to boot with `data-route-id` and `data-route-config-url`.
- Refreshed [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell) with the current completion-oriented sequence.
- Identified management shell extraction as the next concrete slice before app boot ownership.

### steer for next task

- Move management-only shell/chrome ownership into JavaScript without changing management workflows.
- Preserve all existing IDs and refs consumed by `docs-viewer/runtime/js/docs-viewer-management.js`, `docs-viewer/runtime/js/docs-viewer-management-modals.js`, `docs-viewer/runtime/js/docs-html-import.js`, and related management workflow modules.
- Keep route config and access projection as the management UI gate; public routes must not render or import management-only shell/module code.
- Keep backend reachability, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, and rebuild behavior in the existing management flow.
- Do not start the app boot extraction in this slice; that is the next slice after management shell ownership is clear.

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
| 1 | planned | Inventory remaining management-only shell markup and refs in `_includes/docs_viewer_shell.html`, `docs-viewer/shell/docs-viewer-shell.html`, `docs-viewer/runtime/js/docs-viewer.js`, `docs-viewer/runtime/js/docs-viewer-app-shell.js`, `docs-viewer/runtime/js/docs-viewer-management.js`, `docs-viewer/runtime/js/docs-viewer-management-modals.js`, `docs-viewer/runtime/js/docs-html-import.js`, and current smoke tests. Deliverable: short implementation note listing each shell host/ref to move and which module consumes it. |
| 2 | planned | Define the focused owner surface for management shell rendering. Prefer a route-gated app-shell child module such as `docs-viewer-management-shell-renderer.js` or `docs-viewer-management-shell-host.js`; document whether it renders context menu, metadata modal, import modal, settings modal, and management modal hosts together or as smaller children. |
| 3 | planned | Implement management shell rendering behind route/access projection. Render the existing context menu, metadata modal shell, import modal shell, settings modal shell, and required import root/status refs only when `routeContext.access.canLoadManagementUi` is true. |
| 4 | planned | Preserve existing IDs, `data-*` hooks, form names, modal semantics, focus targets, and refs expected by management modules. Avoid rewriting metadata edit, import, settings, context action, or management modal workflow behavior. |
| 5 | planned | Replace management-only markup in `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` with JavaScript-rendered hosts or narrow mounts. Keep route shells at route id/config URL plus app mounts, CSS links, and entry script. |
| 6 | planned | Ensure public routes do not render management shell markup and do not import management-only renderer modules. Keep management stylesheet loading gated by shell include settings or route/service context as currently appropriate. |
| 7 | planned | Update app-shell refs so `docs-viewer.js` and management modules read the JavaScript-rendered management shell refs after app-shell initialization. Keep `docs-viewer.js` as orchestration only for this responsibility. |
| 8 | planned | Extend focused app-shell smoke coverage for management shell rendering, public omission, ref preservation, and idempotent app-shell rendering. |
| 9 | planned | Run management modal/service smoke checks to verify metadata edit flow, import modal boot, settings modal, context menu/action gating, management capability status, generated-data reads, report rendering, and info-panel behavior still work. |
| 10 | planned | Run public read-only checks for `/library/` and `/analysis/` to verify route boot, document rendering, search/recent, info panel, report behavior where applicable, and absence of management-only shell/assets. |
| 11 | planned | Update owning docs after implementation: this tracker, the app-shell request, Docs Viewer runtime boundary, Docs Viewer overview/config docs if shell ownership changes materially, portable setup/files docs if install copy set or shell expectations change, and Docs Viewer JavaScript inventory notes for new/changed owner modules. |
| 12 | planned | Create or update the structured docs-log entry for this slice and record the entry id in this tracker. |

The closeout for this slice should confirm:

- shared and standalone route shells no longer contain management-only context-menu or modal shell markup
- management shell rendering is owned by focused JavaScript app-shell modules
- existing management refs and workflow behavior are preserved
- public read-only routes still avoid management-only shell markup, CSS, and JavaScript
- local manage mode still gets backend capability checks and write authority from the management/service flow
- metadata edit, import, settings, context menu, management actions, generated-data reads, reports, bookmarks, info panel, search/recent, and route history still work
- app boot ownership remains a separate next slice
