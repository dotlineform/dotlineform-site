---
doc_id: site-request-docs-viewer-app-shell-panel-toolbar-view-switching-tasks
title: Docs Viewer App Shell Panel Toolbar View Switching Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: done
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12180
viewable: true
---
# Docs Viewer App Shell Panel Toolbar View Switching Tasks

This is the tracker for the next app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The slice should add the minimal panel toolbar and hosted-view switching contract after route/document workflow ownership and search/recent/bookmark orchestration moved into focused owners.

This slice should make document/info hosted-view availability, access-gated view switching, disabled/missing view handling, toolbar projection, and selected-view state readable through focused owners.
It should not add source editor features, semantic-reference views, activity views, third-party visualization modules, plugin architecture, backend write behavior, route application, document payload loading, search/recent orchestration, or bookmark feature expansion.

## Status

### just done

- Completed [Docs Viewer App Shell Search Recent Bookmark Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-search-recent-bookmark-tasks).
- Kept `docs-viewer/runtime/js/docs-viewer.js` as the stable ES module entrypoint loaded by shared and standalone route shells.
- Kept `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the app boot owner.
- Kept `docs-viewer/runtime/js/docs-viewer-route-workflow.js` as the route/document workflow owner.
- Kept `docs-viewer/runtime/js/docs-viewer-search-controller.js` as the inline-search and recently-added controller owner.
- Kept `docs-viewer/runtime/js/docs-viewer-bookmarks.js` as the bookmark controller owner.
- Preserved public `/library/` and `/analysis/` behavior plus local `/docs/?mode=manage` behavior through focused module, management, public read-only, and isolated build checks.

### completed this slice

- Added panel-specific hosted-view listing through `docs-viewer/runtime/js/docs-viewer-hosted-views.js`.
- Added the info-panel toolbar shell and projection in `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`.
- Extended `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` so projected info-panel state includes available, disabled, unavailable, and access-blocked info views.
- Wired `docs-viewer/runtime/js/docs-viewer-app-runtime.js` so clicking an info toolbar view opens that hosted view through the existing info-panel host.
- Preserved `metadata-info` as the default public-safe info hosted view and kept source editor, semantic-reference, activity, visualization, plugin, route/document, search/recent, bookmark, and backend-write work out of this slice.
- Added focused module smoke coverage for toolbar rendering/projection, hosted-view panel listing, selected info view state, disabled/access-blocked view buttons, hosted-view switching, update handoff, close behavior, missing view behavior, and metadata-info continuity.
- Structured docs-log entry: `change-2026-05-27-added-docs-viewer-panel-toolbar-view-switching`.

### implementation note

- Moved: info hosted-view toolbar projection now comes from `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`; info view options now come from `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`; panel-specific hosted-view listing now comes from `docs-viewer/runtime/js/docs-viewer-hosted-views.js`.
- Stays in the compatibility runtime: app state, selected-document context creation, info toggle wiring, toolbar click handoff, controller construction, config handoff, visibility rules, generated-data capability checks, and lazy management loading.
- Stays in panel/view owners: index/document/info projection in `docs-viewer/runtime/js/docs-viewer-panel-layout.js`, active view-state projection in `docs-viewer/runtime/js/docs-viewer-view-state.js`, hosted-view access/availability checks in `docs-viewer/runtime/js/docs-viewer-hosted-views.js`, and info hosted-view lifecycle in `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`.
- Stays in route/document/search/bookmark owners: URL/history, route application, index/payload loading, document pane rendering, report mounting, search/recent rendering, bookmark storage/list rendering, and IndexedDB helpers.
- Deferred: source editor views, semantic-reference/activity views, third-party visualization modules, plugin architecture, broader document-panel toolbar behavior, and backend write behavior.

### steer for this task

- Inventory current panel/view responsibilities in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`, `docs-viewer/runtime/js/docs-viewer-panel-layout.js`, `docs-viewer/runtime/js/docs-viewer-view-state.js`, `docs-viewer/runtime/js/docs-viewer-hosted-views.js`, `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`, `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`, `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`, and `docs-viewer/runtime/js/docs-viewer-document-controller.js`.
- Prefer extending the existing panel layout, view-state, hosted-view registry, and info-panel host before creating a broader module system.
- Keep route/history primitives in `docs-viewer/runtime/js/docs-viewer-route-workflow.js` and `docs-viewer/runtime/js/docs-viewer-router.js`.
- Keep final payload rendering, missing-doc rendering, payload error rendering, report mount handoff, metadata rendering, and hash scrolling in `docs-viewer/runtime/js/docs-viewer-document-controller.js`.
- Keep shell chrome rendering in the existing shell renderers unless the toolbar needs a focused renderer with stable ownership.
- Preserve `metadata-info` as the first public-safe hosted info view.
- Preserve public read-only behavior first-class: `/library/` and `/analysis/` should keep route boot, document rendering, search/recent, bookmark support, metadata info, reports, and management omission.
- Preserve local `/docs/?mode=manage` behavior first-class: generated-data reads, management capability checks, import-open-on-load, metadata edit flow, context menu, reports, bookmarks, info panel, search/recent, status pills, and route history must continue to work.

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-panel-layout.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-view-state.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-hosted-views.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-info-panel-host.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-document-controller.js`
  - any new or changed focused panel toolbar/view-switching modules
- Focused module smoke coverage when panel/view ownership changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for toolbar rendering/projection, hosted-view listing, selected view state, missing/disabled/access-blocked view handling, metadata-info continuity, document/info panel switching, close behavior, and public/manage access assumptions where practical
- Management route checks when panel/view state, hosted-view access, management route state, generated-data reads, import-open on load, or shell output changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when route boot, shell output, panel/view state, info panel, public omission, document rendering, search/recent, or bookmarks change:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Docs-only follow-through when source docs change:
  - review generated docs payload status; let the docs watcher update generated payloads if it is running and do not revert watcher output

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for shared runtime files.
- This slice is structural panel toolbar/view-switching work, not feature-layer source editor, semantic-reference, activity, third-party visualization, plugin, management write, route/document workflow, search/recent, or bookmark work.
- Keep `docs-viewer/runtime/js/docs-viewer.js` as the stable compatibility entrypoint.
- Keep `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the boot owner.
- Keep `docs-viewer/runtime/js/docs-viewer-route-workflow.js` as the route/document workflow owner.
- Keep `docs-viewer/runtime/js/docs-viewer-document-controller.js` as the document pane/rendering owner.
- Keep `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` as the info hosted-view lifecycle owner unless inventory shows a tighter focused owner is needed.
- Keep `docs-viewer/runtime/js/docs-viewer-hosted-views.js` as a minimal hosted-view registry, not a plugin system.
- Keep route config and access projection as the app-shell gate; public routes must still avoid management-only CSS, JavaScript, and shell markup.
- Keep backend reachability, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, and generated-data capability checks in the existing management/service flow.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory current panel/view responsibilities in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`, `docs-viewer/runtime/js/docs-viewer-panel-layout.js`, `docs-viewer/runtime/js/docs-viewer-view-state.js`, `docs-viewer/runtime/js/docs-viewer-hosted-views.js`, `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`, `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`, `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`, and `docs-viewer/runtime/js/docs-viewer-document-controller.js`. Deliverable: short implementation note listing what moves, what stays in compatibility runtime/panel layout/info host, and what remains deferred to source editor or future hosted-view feature work. |
| 2 | done | Define the focused panel toolbar/view-switch owner surface. Prefer extending existing panel/view modules unless inventory shows a clearer focused module name. Document exported functions, required inputs, returned controller shape, and boundaries with route workflow, document controller, info panel host, hosted-view registry, app shell renderers, management controller, and access projection. |
| 3 | done | Define the toolbar rendering/projection contract for document/info hosted views. Preserve existing shell refs and avoid moving payload rendering, report mounting, or metadata-info presentation into the toolbar owner. |
| 4 | done | Define selected-view state transitions for document and info panels using `docs-viewer/runtime/js/docs-viewer-view-state.js` and `docs-viewer/runtime/js/docs-viewer-panel-layout.js` where practical. Preserve current index/document/info visibility projection and current info-panel close behavior. |
| 5 | done | Add or extend hosted-view listing/filtering helpers so view switch controls can consume available, disabled, missing, and access-blocked view states without duplicating registry rules. Preserve graceful absence behavior. |
| 6 | done | Add minimal toolbar/view-switch UI for existing hosted views, starting with `metadata-info`, without adding source editor, semantic-reference, activity, visualization, or plugin views. |
| 7 | done | Preserve public-safe metadata info behavior: selected-document context projection, canonical URL display, parent trail, cached payload fields, route access labels, and public-read-only availability should continue to work. |
| 8 | done | Keep route/document workflow ownership out of this slice except for explicit callbacks consumed by panel/view owners. Do not move `applyCurrentRoute`, `loadIndex`, `loadDoc`, current URL/query helpers, canonical URL correction, route-link handling, or popstate ownership out of `docs-viewer-route-workflow.js`. |
| 9 | done | Keep document pane rendering out of this slice except for explicit view/pane projection callbacks. Do not move payload rendering, missing-doc rendering, payload error rendering, report mount handoff, metadata rendering, or hash scrolling out of `docs-viewer-document-controller.js`. |
| 10 | done | Keep search/recent and bookmark behavior intact and out of this slice. Do not move search result rendering, recent rendering, search debounce state, more-results behavior, bookmark storage, bookmark list rendering, edit state, or IndexedDB helpers. |
| 11 | done | Keep management behavior intact: backend capability checks, management busy/status projection, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, generated-data reads, context menu, metadata edit, status pills, and import-open-on-load stay in existing management/service modules or runtime handoff. |
| 12 | done | Add or extend focused smoke coverage for panel toolbar/view switching. Cover exported controller contracts, toolbar rendering/projection, selected-view state, metadata-info switching, disabled/missing/access-blocked view states, close behavior, public management omission, and route workflow callback compatibility where practical. |
| 13 | done | Run management modal/service smoke checks to verify metadata edit flow, import modal boot, settings modal, context menu/action gating, management capability status, generated-data reads, report rendering, bookmarks, info panel, search/recent, route history, status pills, and import-open-on-load behavior still work. |
| 14 | done | Run public read-only checks for `/library/` and `/analysis/` to verify route boot, document rendering, canonical URL behavior, search/recent, bookmark support, info panel toolbar/view switching, report behavior where applicable, and absence of management-only shell/assets. |
| 15 | done | Update owning docs after implementation: this tracker, the app-shell request, Docs Viewer runtime boundary, Docs Viewer overview, and Docs Viewer JavaScript inventory notes for new/changed owner modules. Update portable files/setup only if the copy set or shell expectations change. |
| 16 | done | Create or update the structured docs-log entry for this slice and record the entry id in this tracker. |

## Verification Completed

- `node --check docs-viewer/runtime/js/docs-viewer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
- `node --check docs-viewer/runtime/js/docs-viewer-panel-layout.js`
- `node --check docs-viewer/runtime/js/docs-viewer-view-state.js`
- `node --check docs-viewer/runtime/js/docs-viewer-hosted-views.js`
- `node --check docs-viewer/runtime/js/docs-viewer-info-panel-host.js`
- `node --check docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-document-controller.js`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`

The closeout for this slice should confirm:

- panel toolbar/view switching has a focused owner surface
- hosted views can be listed, selected, disabled, missing, and access-gated through explicit contracts
- `metadata-info` remains public-safe and keeps its selected-document context behavior
- `docs-viewer/runtime/js/docs-viewer.js` remains the stable entrypoint
- `docs-viewer/runtime/js/docs-viewer-app-boot.js` remains the app boot owner
- `docs-viewer/runtime/js/docs-viewer-route-workflow.js` remains the route/document workflow owner
- `docs-viewer/runtime/js/docs-viewer-document-controller.js` remains the document pane/rendering owner
- route/history behavior for document links, search, recent, and bookmarks is preserved
- existing route/document, search/recent, and bookmark behavior is preserved and remains outside this slice
- public read-only routes still avoid management-only shell markup, CSS, and JavaScript
- local manage mode still gets backend capability checks and write authority from the management/service flow
- metadata edit, import, settings, context menu, management actions, generated-data reads, reports, bookmarks, info panel, search/recent, status pills, and route history still work
