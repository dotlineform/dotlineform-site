---
doc_id: site-request-docs-viewer-app-shell-route-document-workflow-tasks
title: Docs Viewer App Shell Route Document Workflow Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: planned
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12160
viewable: true
---
# Docs Viewer App Shell Route Document Workflow Tasks

This is the tracker for the next app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The slice should extract route/document workflow ownership from `docs-viewer/runtime/js/docs-viewer-app-runtime.js` into a focused route/document owner while keeping `docs-viewer/runtime/js/docs-viewer.js` as the stable entrypoint and `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the boot owner.

This slice should make route application, current-doc resolution, document index load orchestration, document payload loading, missing-doc/error behavior, and history synchronization readable outside the compatibility runtime.
It should not move search/recent orchestration, bookmark orchestration, source editor features, semantic-reference views, activity views, panel-toolbar generalization, third-party visualization modules, plugin architecture, or backend write behavior.

## Status

### just done

- Completed [Docs Viewer App Shell App Boot Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-app-boot-tasks).
- Added `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the focused app boot owner.
- Kept `docs-viewer/runtime/js/docs-viewer.js` as the stable ES module entrypoint loaded by shared and standalone route shells.
- Added `docs-viewer/runtime/js/docs-viewer-app-runtime.js` as the compatibility owner for the existing route/document runtime workflow until this slice.
- Preserved existing `applyCurrentRoute`, `loadIndex`, `loadDoc`, URL/history behavior, search/recent handoff, bookmark orchestration, generated-data reads, reports, lazy management loading, and management import-open-on-load behavior.
- Verified the app boot slice with JavaScript syntax checks, focused app-shell module smoke, management modal smoke, management service shell smoke, isolated Jekyll build, public read-only smoke, JSON validation, and `git diff --check`.

### steer for next task

- Move route/document workflow ownership out of `docs-viewer/runtime/js/docs-viewer-app-runtime.js` without changing URL/history behavior.
- Prefer a focused module such as `docs-viewer/runtime/js/docs-viewer-route-workflow.js` unless inventory shows a clearer existing owner.
- Build on `docs-viewer/runtime/js/docs-viewer-router.js` and `docs-viewer/runtime/js/docs-viewer-document-controller.js`; do not duplicate their route parsing, URL building, history, or document pane rendering responsibilities.
- Keep `docs-viewer/runtime/js/docs-viewer-app-runtime.js` as controller/runtime wiring during this slice, but remove ownership of `applyCurrentRoute`, `loadIndex`, `loadDoc`, URL canonicalization, current-doc resolution, and route-driven document/search/recent switching from it.
- Keep search/recent and bookmark controllers focused owners; this slice may pass callbacks through the new route workflow but should not absorb their UI state transitions.
- Preserve public read-only behavior first-class: `/library/` and `/analysis/` should keep route boot, canonical URLs, document rendering, search/recent, info panel, reports, and management omission.
- Preserve local `/docs/` management behavior first-class: manage-mode route detection, generated-data capability checks, lazy management loading, import-open-on-load, metadata edit flow, context menu, reports, bookmarks, info panel, search/recent, and route history must continue to work.
- Do not start source editor, semantic-reference view, activity view, panel toolbar generalization, third-party visualization, plugin architecture, or backend write behavior in this slice.

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-router.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-document-controller.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-search-controller.js`
  - any new or changed focused route/document workflow modules
- Focused module smoke coverage when route workflow ownership moves:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for route workflow exports, current-doc resolution, canonical route handling, index-load handoff, payload-load handoff, missing-doc handling, history mode, and public/manage mode gating where practical
- Management route checks when route workflow, payload loading, import-open on load, or management route state changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when route boot, route config, URL/history, payload loading, public omission, or shell output changes:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Docs-only follow-through when source docs change:
  - review generated docs payload status; let the docs watcher update generated payloads if it is running and do not revert watcher output

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for shared runtime files.
- This slice is structural route/document workflow work, not feature-layer management, search, bookmark, source editor, semantic-reference, activity, or panel-toolbar work.
- Keep `docs-viewer/runtime/js/docs-viewer.js` as the stable compatibility entrypoint.
- Keep `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the boot owner.
- Keep `docs-viewer/runtime/js/docs-viewer-app-runtime.js` as runtime/controller wiring, but shrink it by moving coherent route/document workflow ownership to a focused module.
- Keep route config and access projection as the app-shell gate; public routes must still avoid management-only CSS, JavaScript, and shell markup.
- Keep backend reachability, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, and generated-data capability checks in the existing management/service flow.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory current route/document workflow responsibilities in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`, `docs-viewer/runtime/js/docs-viewer-router.js`, `docs-viewer/runtime/js/docs-viewer-document-controller.js`, `docs-viewer/runtime/js/docs-viewer-search-controller.js`, `docs-viewer/runtime/js/docs-viewer-bookmarks.js`, route-start calls, index load, payload load, canonical route correction, popstate behavior, and management import-open-on-load. Deliverable: short implementation note listing what moves, what stays in the compatibility runtime, and what remains deferred to search/recent/bookmark cleanup. |
| 2 | planned | Define the focused route/document workflow owner surface. Prefer `docs-viewer/runtime/js/docs-viewer-route-workflow.js` unless inventory shows a better focused name. Document exported functions, required inputs, returned controller shape, and boundaries with existing router, document controller, search controller, bookmark controller, panel layout, info panel host, and management controller. |
| 3 | planned | Move current URL/query helpers and current-doc resolution into the route workflow owner without changing canonical URL behavior, manage-mode query behavior, scope query behavior, hash handling, or default-doc fallback behavior. |
| 4 | planned | Move `applyCurrentRoute` ownership into the route workflow owner while preserving callbacks to document rendering, search/recent projection, bookmark UI, sidebar rendering, management UI, info-panel updates, and status projection. |
| 5 | planned | Move document index load orchestration and index initialization handoff into the route workflow owner where practical, while preserving docs visibility filtering, non-loadable doc handling, manage-only tree roots, default route handling, sidebar rendering, and initial route application behavior. |
| 6 | planned | Move document payload load ownership into the route workflow owner while preserving generated-data read capability checks, management reload paths, busy state, missing-doc behavior, payload error behavior, report registry reads, info-panel updates, and bookmark UI updates. |
| 7 | planned | Move popstate and route link handling orchestration into the route workflow owner where it is a complete responsibility. Preserve native-link escape behavior, cross-route navigation, scope reload behavior, route history modes, hash navigation, and management context-menu delegation. |
| 8 | planned | Keep search/recent orchestration out of this slice except for explicit route workflow callbacks. Do not move search result rendering, search debounce state, recent rendering, more-results behavior, or search controller ownership into the route workflow owner. |
| 9 | planned | Keep bookmark orchestration out of this slice except for explicit route workflow callbacks. Do not move bookmark storage, bookmark list rendering, edit state, IndexedDB helpers, or bookmark controller ownership into the route workflow owner. |
| 10 | planned | Keep local manage mode intact: backend capability checks, management busy/status projection, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, generated-data reads, context menu, metadata edit, and import-open-on-load stay in the existing management/service modules or runtime handoff. |
| 11 | planned | Add or extend focused smoke coverage for the route/document workflow owner. Cover exported workflow contract, current-doc resolution, canonical public route correction, management-mode route retention, hash handling, missing-doc fallback, payload load handoff, popstate behavior, and public management omission where practical. |
| 12 | planned | Run management modal/service smoke checks to verify metadata edit flow, import modal boot, settings modal, context menu/action gating, management capability status, generated-data reads, report rendering, bookmarks, info panel, search/recent, route history, and import-open-on-load behavior still work. |
| 13 | planned | Run public read-only checks for `/library/` and `/analysis/` to verify route boot, document rendering, canonical URL behavior, hash handling where practical, search/recent, info panel, report behavior where applicable, and absence of management-only shell/assets. |
| 14 | planned | Update owning docs after implementation: this tracker, the app-shell request, Docs Viewer runtime boundary, Docs Viewer overview, and Docs Viewer JavaScript inventory notes for new/changed owner modules. Update portable files/setup only if the copy set or shell expectations change. |
| 15 | planned | Create or update the structured docs-log entry for this slice and record the entry id in this tracker. |

The closeout for this slice should confirm:

- route/document workflow orchestration is owned by a focused JavaScript module
- `docs-viewer/runtime/js/docs-viewer.js` remains the stable entrypoint
- `docs-viewer/runtime/js/docs-viewer-app-boot.js` remains the app boot owner
- `docs-viewer/runtime/js/docs-viewer-app-runtime.js` no longer owns `applyCurrentRoute`, `loadIndex`, `loadDoc`, URL canonicalization, or route-driven document/search/recent switching
- existing search/recent and bookmark behavior is preserved and remains a separate follow-on cleanup slice
- public read-only routes still avoid management-only shell markup, CSS, and JavaScript
- local manage mode still gets backend capability checks and write authority from the management/service flow
- metadata edit, import, settings, context menu, management actions, generated-data reads, reports, bookmarks, info panel, search/recent, and route history still work
