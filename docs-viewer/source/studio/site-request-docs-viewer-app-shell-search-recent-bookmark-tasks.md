---
doc_id: site-request-docs-viewer-app-shell-search-recent-bookmark-tasks
title: Docs Viewer App Shell Search Recent Bookmark Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: planned
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12170
viewable: true
---
# Docs Viewer App Shell Search Recent Bookmark Tasks

This is the tracker for the next app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The slice should clean up search/recent and bookmark orchestration around `docs-viewer/runtime/js/docs-viewer-app-runtime.js` after route/document workflow ownership moved to `docs-viewer/runtime/js/docs-viewer-route-workflow.js`.

This slice should make inline search, recently-added mode, bookmark loading, bookmark UI updates, bookmark route handoff, and their route/history callbacks readable through focused owners.
It should not move route application, document index loading, document payload loading, source editor features, semantic-reference views, activity views, panel-toolbar generalization, third-party visualization modules, plugin architecture, or backend write behavior.

## Status

### just done

- Completed [Docs Viewer App Shell Route Document Workflow Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-route-document-workflow-tasks).
- Added `docs-viewer/runtime/js/docs-viewer-route-workflow.js` as the focused route/document workflow owner.
- Kept `docs-viewer/runtime/js/docs-viewer.js` as the stable ES module entrypoint loaded by shared and standalone route shells.
- Kept `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the app boot owner.
- Kept `docs-viewer/runtime/js/docs-viewer-app-runtime.js` as compatibility runtime wiring for app state, controller construction, config handoff, visibility rules, search/recent and bookmark controller handoff, panel/info updates, generated-data capability checks, and lazy management loading.
- Preserved public `/library/` and `/analysis/` behavior plus local `/docs/?mode=manage` behavior through focused route workflow, management modal, management service, public read-only, and isolated build checks.
- Completed this search/recent and bookmark orchestration slice.
- Added explicit route callback factory exports to `docs-viewer/runtime/js/docs-viewer-search-controller.js` and `docs-viewer/runtime/js/docs-viewer-bookmarks.js`.
- Reduced `docs-viewer/runtime/js/docs-viewer-app-runtime.js` search/bookmark handoff to controller-owned route callback bundles plus narrow pane callbacks.
- Kept route/history primitives in `docs-viewer/runtime/js/docs-viewer-route-workflow.js` and document pane rendering in `docs-viewer/runtime/js/docs-viewer-document-controller.js`.
- Added focused module smoke coverage for search route activation, search clear route restoration, debounce handoff, more-results behavior, recent mode, bookmark route handoff, bookmark toggle/list rendering hooks, and bookmark rename state.
- Structured docs-log entry: `change-2026-05-27-focused-docs-viewer-search-bookmark-orchestration`.

### implementation note

- Moved: search route callback bundling now comes from `createDocsViewerSearchRouteCallbacks(...)`; bookmark route callback bundling now comes from `createDocsViewerBookmarkRouteCallbacks(...)`; recent-mode active-state projection is explicit in the search controller before pane projection.
- Stays in the compatibility runtime: mutable shared app state, controller construction order, config handoff, visibility rules, generated-data capability checks, panel/info handoff, lazy management loading, and compatibility wrappers needed by management/config/document controllers.
- Stays in route/document owners: URL construction, browser history, route application, index/payload loading, route-link handling, popstate, pane visibility, payload rendering, missing/error states, report mount handoff, metadata rendering, and hash scrolling.
- Deferred: panel toolbar/view switching, source editor views, semantic-reference/activity views, third-party visualization modules, plugin architecture, broader bookmark features such as grouping/sync/export, and backend write behavior.

### steer for next task

- Inventory the current search/recent and bookmark responsibilities in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`, `docs-viewer/runtime/js/docs-viewer-search-controller.js`, `docs-viewer/runtime/js/docs-viewer-bookmarks.js`, `docs-viewer/runtime/js/docs-viewer-favourites.js`, `docs-viewer/runtime/js/docs-viewer-route-workflow.js`, and `docs-viewer/runtime/js/docs-viewer-document-controller.js`.
- Prefer extending the existing search controller and bookmark controller before creating new coordination modules.
- Keep route/history primitives in `docs-viewer/runtime/js/docs-viewer-route-workflow.js` and `docs-viewer/runtime/js/docs-viewer-router.js`; search and bookmark owners should call explicit route callbacks rather than own URL construction broadly.
- Keep document pane visibility and final payload rendering in `docs-viewer/runtime/js/docs-viewer-document-controller.js`; search/recent owners may request search or recent pane projection through explicit callbacks.
- Keep management writes, generated-data capability checks, metadata edit, import, settings, context menu, source opening, rebuild, archive/delete/move, and scope lifecycle behavior outside this slice.
- Preserve public read-only behavior first-class: `/library/` and `/analysis/` should keep route boot, inline search, recently-added list, bookmark support, info panel, reports, and management omission.
- Preserve local `/docs/?mode=manage` behavior first-class: generated-data reads, management capability checks, import-open-on-load, metadata edit flow, context menu, reports, bookmarks, info panel, search/recent, and route history must continue to work.

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-route-workflow.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-search-controller.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-search.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-bookmarks.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-favourites.js`
  - any new or changed focused search/recent/bookmark modules
- Focused module smoke coverage when search/recent or bookmark ownership moves:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for search controller exports, recent mode route/history behavior, search debounce handoff, more-results behavior, bookmark controller callbacks, bookmark route handoff, public/manage access assumptions, and route workflow callback compatibility where practical
- Management route checks when search/recent, bookmarks, generated-data reads, import-open on load, or management route state changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when search/recent, bookmarks, route boot, URL/history, payload loading, public omission, or shell output changes:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Docs-only follow-through when source docs change:
  - review generated docs payload status; let the docs watcher update generated payloads if it is running and do not revert watcher output

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for shared runtime files.
- This slice is structural search/recent/bookmark orchestration cleanup, not feature-layer management, route/document workflow, source editor, semantic-reference, activity, panel-toolbar, visualization, plugin, or backend-write work.
- Keep `docs-viewer/runtime/js/docs-viewer.js` as the stable compatibility entrypoint.
- Keep `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the boot owner.
- Keep `docs-viewer/runtime/js/docs-viewer-route-workflow.js` as the route/document workflow owner.
- Keep `docs-viewer/runtime/js/docs-viewer-app-runtime.js` as runtime/controller wiring, but reduce search/recent and bookmark handoff where a focused owner can take a complete responsibility.
- Keep search result scoring and recently-added ordering helpers in `docs-viewer/runtime/js/docs-viewer-search.js`.
- Keep bookmark record and IndexedDB helpers in `docs-viewer/runtime/js/docs-viewer-favourites.js`.
- Keep route config and access projection as the app-shell gate; public routes must still avoid management-only CSS, JavaScript, and shell markup.
- Keep backend reachability, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, and generated-data capability checks in the existing management/service flow.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory current search/recent and bookmark responsibilities in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`, `docs-viewer/runtime/js/docs-viewer-search-controller.js`, `docs-viewer/runtime/js/docs-viewer-search.js`, `docs-viewer/runtime/js/docs-viewer-bookmarks.js`, `docs-viewer/runtime/js/docs-viewer-favourites.js`, `docs-viewer/runtime/js/docs-viewer-route-workflow.js`, and `docs-viewer/runtime/js/docs-viewer-document-controller.js`. Deliverable: short implementation note listing what moves, what stays in the compatibility runtime, and what remains deferred to panel toolbar or bookmark feature work. |
| 2 | done | Define the focused search/recent owner surface. Prefer extending `docs-viewer/runtime/js/docs-viewer-search-controller.js` unless inventory shows a clearer focused name. Document exported functions, required inputs, returned controller shape, and boundaries with route workflow, document controller, panel layout, config controller, and management controller. |
| 3 | done | Define the focused bookmark owner surface. Prefer extending `docs-viewer/runtime/js/docs-viewer-bookmarks.js` unless inventory shows a clearer focused name. Document exported functions, required inputs, returned controller shape, and boundaries with route workflow, document controller, status pills, info panel, IndexedDB helpers, and management controller. |
| 4 | done | Move search/recent route callback bundling out of the compatibility runtime where it is a complete responsibility, while preserving current search query state, debounce behavior, search index loading, generated-data read fallback, busy state, result status messages, more-results behavior, and route history modes. |
| 5 | done | Move recently-added mode orchestration into the focused search/recent owner where practical, while preserving active document fallback, recent limit config, result metadata, route history updates, button pressed state, search query clearing, and pane projection. |
| 6 | done | Move bookmark route callback bundling and selected-document bookmark UI handoff out of the compatibility runtime where it is a complete responsibility, while preserving bookmark loading, IndexedDB support detection, list/toggle rendering, edit state, pending focus, status-pill fallback, route history, and document-load handoff. |
| 7 | done | Keep route/document workflow ownership out of this slice except for explicit callbacks consumed by search/recent and bookmark owners. Do not move `applyCurrentRoute`, `loadIndex`, `loadDoc`, current URL/query helpers, canonical URL correction, route-link handling, or popstate ownership out of `docs-viewer-route-workflow.js`. |
| 8 | done | Keep document pane rendering out of this slice except for explicit pane-projection callbacks. Do not move payload rendering, missing-doc rendering, payload error rendering, report mount handoff, metadata rendering, or hash scrolling out of `docs-viewer-document-controller.js`. |
| 9 | done | Keep management behavior intact: backend capability checks, management busy/status projection, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, generated-data reads, context menu, metadata edit, status pills, and import-open-on-load stay in existing management/service modules or runtime handoff. |
| 10 | done | Add or extend focused smoke coverage for search/recent and bookmark ownership. Cover exported controller contracts, search route activation, search clear route restoration, debounce handoff, search index load handoff, more-results behavior, recent mode route/history behavior, bookmark route handoff, bookmark toggle/list rendering hooks, and public management omission where practical. |
| 11 | done | Run management modal/service smoke checks to verify metadata edit flow, import modal boot, settings modal, context menu/action gating, management capability status, generated-data reads, report rendering, bookmarks, info panel, search/recent, route history, status pills, and import-open-on-load behavior still work. |
| 12 | done | Run public read-only checks for `/library/` and `/analysis/` to verify route boot, document rendering, canonical URL behavior, search/recent, bookmark support, info panel, report behavior where applicable, and absence of management-only shell/assets. |
| 13 | done | Update owning docs after implementation: this tracker, the app-shell request, Docs Viewer runtime boundary, Docs Viewer overview, and Docs Viewer JavaScript inventory notes for new/changed owner modules. Update portable files/setup only if the copy set or shell expectations change. |
| 14 | done | Create or update the structured docs-log entry for this slice and record the entry id in this tracker. |

The closeout for this slice should confirm:

- search/recent orchestration has a focused owner surface and no longer depends on broad compatibility-runtime callback bundles
- bookmark orchestration has a focused owner surface and no longer depends on broad compatibility-runtime callback bundles
- `docs-viewer/runtime/js/docs-viewer.js` remains the stable entrypoint
- `docs-viewer/runtime/js/docs-viewer-app-boot.js` remains the app boot owner
- `docs-viewer/runtime/js/docs-viewer-route-workflow.js` remains the route/document workflow owner
- route/history behavior for search, recent, bookmarks, and document links is preserved
- existing route/document workflow behavior is preserved and remains outside this slice
- public read-only routes still avoid management-only shell markup, CSS, and JavaScript
- local manage mode still gets backend capability checks and write authority from the management/service flow
- metadata edit, import, settings, context menu, management actions, generated-data reads, reports, bookmarks, info panel, search/recent, status pills, and route history still work
