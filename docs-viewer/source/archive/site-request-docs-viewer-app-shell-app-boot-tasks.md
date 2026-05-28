---
doc_id: site-request-docs-viewer-app-shell-app-boot-tasks
title: Docs Viewer App Shell App Boot Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: done
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12150
viewable: true
---
# Docs Viewer App Shell App Boot Tasks

This is the tracker for the next app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The slice should extract app boot orchestration from `docs-viewer/runtime/js/docs-viewer.js` into a focused app boot owner while keeping `docs-viewer.js` as the stable ES module entrypoint loaded by the shared and standalone route shells.

This slice should make route-config resolution, app-shell initialization, controller construction, initial config/index/payload load, and initial management import-open behavior readable as one boot workflow outside the entrypoint.
It should not move route/document workflow ownership, URL/history behavior, search/recent orchestration, bookmark orchestration, source editor features, semantic-reference views, activity views, panel-toolbar generalization, third-party visualization modules, plugin architecture, or backend write behavior.

## Status

### just done

- Added `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the focused app boot owner.
- Kept `docs-viewer/runtime/js/docs-viewer.js` as the stable ES module entrypoint loaded by shared and standalone route shells; it now imports and starts the boot owner.
- Added `docs-viewer/runtime/js/docs-viewer-app-runtime.js` as the compatibility owner for the existing route/document runtime workflow until the next extraction slice.
- Moved route-config resolution, route-context creation, app-shell initialization, shell-ref handoff, management-safe theme toggle loading, controller/runtime startup, and initial load handoff out of the entrypoint.
- Preserved existing route/document workflow behavior in the compatibility runtime: `applyCurrentRoute`, `loadIndex`, `loadDoc`, URL/history behavior, search/recent handoff, bookmark orchestration, generated-data reads, reports, and lazy management loading remain together for the next slice.
- Kept public routes gated: public boot does not render management shell markup or dynamically import management-only shell modules because app boot still uses route access projection.
- Extended `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` with app boot owner coverage for exported boot context, route-config handoff, shell initialization before ref reads, public management omission, management-capable boot, and single-start behavior.
- Verification passed: JavaScript syntax checks, focused app-shell module smoke, management modal smoke, management service shell smoke, isolated Jekyll build, public read-only smoke, JSON validation, and `git diff --check`.
- Structured docs-log entry: `change-2026-05-27-extracted-docs-viewer-app-boot`.

### previous slice

- Completed [Docs Viewer App Shell Management Shell Extraction Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-management-shell-extraction-tasks).
- Added `docs-viewer/runtime/js/docs-viewer-management-shell-renderer.js` as the focused app-shell owner for management-only context-menu and modal shell markup.
- Replaced duplicated management-only shell markup in `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` with `#docsViewerManagementShellMount`.
- Kept public routes gated: management shell rendering and the renderer import happen only when `routeContext.access.canLoadManagementUi` allows management UI.
- Preserved existing management workflows, backend capability checks, generated-data reads, reports, bookmarks, info panel, search/recent, and route history behavior.
- Identified app boot ownership as the next concrete slice before route/document workflow ownership.

### steer for next task

- Move route/document workflow ownership out of `docs-viewer/runtime/js/docs-viewer-app-runtime.js` without changing URL/history behavior.
- Prefer a focused route/document workflow owner that builds on `docs-viewer/runtime/js/docs-viewer-router.js` and `docs-viewer/runtime/js/docs-viewer-document-controller.js`.
- Keep `docs-viewer/runtime/js/docs-viewer.js` as the compatibility entrypoint and `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the boot owner.
- Preserve the existing controller boundaries: config, document, search, sidebar, panel layout, info-panel host, bookmarks, and lazy management loading should remain focused owners rather than being reimplemented in the route/document workflow module.
- Preserve route config and access projection as the app-shell gate; public routes must still avoid management-only CSS, JavaScript, and shell markup.
- Keep backend reachability, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, and generated-data capability checks in the existing management/service flow.
- Do not start source editor, semantic-reference view, activity view, panel toolbar generalization, third-party visualization, plugin architecture, or backend write behavior in the route/document extraction slice.

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-context.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-route-config.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-config-controller.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-document-controller.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-search-controller.js`
  - any new or changed focused app boot/runtime modules
- Focused app-shell module smoke checks when boot context, refs, or app-shell initialization changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for app boot owner exports, route-config handoff, shell initialization ordering, public management omission, and idempotent boot behavior
- Management route checks when lazy management loading, import-open on load, or controller construction changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when route boot, route config, public omission, or shell output changes:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Docs-only follow-through when source docs change:
  - review generated docs payload status; let the docs watcher update generated payloads if it is running and do not revert watcher output

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for shared runtime files.
- This slice is structural app boot work, not feature-layer management, route, search, bookmark, or document workflow work.
- Keep `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` as route integration shells: CSS links, `#docsViewerRoot`, route id/config URL, app mounts, and entry script.
- Keep `docs-viewer/runtime/js/docs-viewer.js` readable and stable as the script entrypoint during the migration.
- New boot orchestration should call focused owners rather than absorb their implementation details.
- Preserve public read-only behavior first-class: `/library/` and `/analysis/` should not load management CSS, management-only JavaScript, or management shell markup.
- Preserve local `/docs/` management behavior first-class: manage-mode detection, management capability messages, generated-data reads, action gating, metadata edit flow, import flow, settings flow, context menu, report rendering, browser history behavior, and info panel must continue to work.
- Backend capability checks and write authority remain in the management controller/service flow, not in static route config or app boot.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory current app boot responsibilities in `docs-viewer/runtime/js/docs-viewer.js`, `docs-viewer/runtime/js/docs-viewer-app-shell.js`, `docs-viewer/runtime/js/docs-viewer-app-context.js`, `docs-viewer/runtime/js/docs-viewer-route-config.js`, controller initializers, route-start calls, initial config/index/payload load, lazy management loading, theme toggle loading, and import-open on load. Moved route-config/shell boot and runtime startup out of the entrypoint; left route/document workflows in `docs-viewer/runtime/js/docs-viewer-app-runtime.js` for the next extraction slice. |
| 2 | done | Defined `docs-viewer/runtime/js/docs-viewer-app-boot.js` with `resolveDocsViewerAppBootContext()`, `initDocsViewerBootThemeToggle()`, and `startDocsViewerApp()`. The boot context requires root/document/window inputs or defaults, returns route context, app-shell refs, app-shell readiness, and asset version, and delegates route/document workflow to the compatibility runtime. |
| 3 | done | Moved route-config resolution and initial route-context/app-shell initialization orchestration into `docs-viewer-app-boot.js`; `docs-viewer.js` is now a small import-and-start wrapper. |
| 4 | done | Moved runtime startup sequencing out of the entrypoint while preserving controller APIs and construction order inside `docs-viewer-app-runtime.js`: panel layout, info panel host, sidebar renderer, document controller, search controller, config controller, bookmarks, and lazy management controller remain ordered as before. |
| 5 | done | Preserved initial config/index/payload load behavior, default route handling, generated-data capability checks, report registry reads, info-panel state, bookmark setup, and management import-open-on-load behavior. Route/document workflow internals remain together in `docs-viewer-app-runtime.js` for the next slice. |
| 6 | done | Kept public management omission intact: public app boot still uses route access projection before rendering management shell refs, importing management shell modules, or starting lazy management behavior. |
| 7 | done | Kept local manage mode intact: backend capability checks, management busy/status projection, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, and generated-data reads stay in the existing management/service modules. |
| 8 | done | Extended `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` with focused app boot coverage for exported boot context, route-config handoff, app-shell initialization before ref reads, public omission, management-capable boot, and single-start behavior. |
| 9 | done | Ran management modal/service smoke checks to verify metadata edit flow, import modal boot, settings modal, context menu/action gating, management capability status, generated-data reads, report rendering, bookmarks, info panel, search/recent, route history, and import-open-on-load behavior still work. |
| 10 | done | Ran public read-only checks for `/library/` and `/analysis/` to verify route boot, document rendering, search/recent, info panel, report behavior where applicable, and absence of management-only shell/assets. |
| 11 | done | Updated owning docs after implementation: this tracker, the app-shell request, Docs Viewer runtime boundary, Docs Viewer overview, portable files, and Docs Viewer JavaScript inventory notes for new/changed owner modules. |
| 12 | done | Created structured docs-log entry `change-2026-05-27-extracted-docs-viewer-app-boot` and recorded the entry id in this tracker. |

## Verification

Passed on 2026-05-27:

- `node --check docs-viewer/runtime/js/docs-viewer.js docs-viewer/runtime/js/docs-viewer-app-boot.js docs-viewer/runtime/js/docs-viewer-app-runtime.js docs-viewer/runtime/js/docs-viewer-app-shell.js docs-viewer/runtime/js/docs-viewer-app-context.js docs-viewer/runtime/js/docs-viewer-route-config.js docs-viewer/runtime/js/docs-viewer-config-controller.js docs-viewer/runtime/js/docs-viewer-document-controller.js docs-viewer/runtime/js/docs-viewer-search-controller.js`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- `$HOME/miniconda3/bin/python3 -m json.tool studio/workflows/change-requests/logs/entries/change-2026-05-27-extracted-docs-viewer-app-boot.json`
- `git diff --check`

The closeout for this slice should confirm:

- `docs-viewer/runtime/js/docs-viewer.js` is a stable compatibility entrypoint that imports and starts the boot owner
- app boot orchestration is owned by a focused JavaScript module
- route-config resolution, app-shell initialization, controller construction, initial config/index/payload load, and initial management import-open behavior are readable as one boot workflow outside the entrypoint
- existing route/document workflow behavior is preserved and remains a separate next slice
- public read-only routes still avoid management-only shell markup, CSS, and JavaScript
- local manage mode still gets backend capability checks and write authority from the management/service flow
- metadata edit, import, settings, context menu, management actions, generated-data reads, reports, bookmarks, info panel, search/recent, and route history still work
