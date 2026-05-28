---
doc_id: site-request-docs-viewer-app-shell-compatibility-runtime-tasks
title: Docs Viewer App Shell Compatibility Runtime Tasks
added_date: 2026-05-27
last_updated: 2026-05-28
ui_status: done
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12190
viewable: true
---
# Docs Viewer App Shell Compatibility Runtime Tasks

This is the tracker for the remaining pure migration/risk-reduction slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-javascript-app-shell).

The slice should reduce `docs-viewer/runtime/js/docs-viewer-app-runtime.js` after boot ownership, route/document workflow ownership, search/recent and bookmark callback ownership, management shell rendering, and minimal info-panel toolbar/view switching have moved into focused modules.

This slice should make the compatibility runtime read as a small coordinator for existing owners.
It should not add source editor features, semantic-reference views, activity views, third-party visualization modules, plugin architecture, portable fixture setup, route shell markup, or backend write behavior.

## Status

### completion note

- Completed the pure migration/risk-reduction pass around `docs-viewer/runtime/js/docs-viewer-app-runtime.js`.
- Moved generated-data request option shaping and generated-read capability caching to `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`.
- Moved document visibility/loadability projection to `docs-viewer/runtime/js/docs-viewer-document-index-state.js`.
- Moved selected-document info-panel coordination to `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`.
- Moved lazy controller loading and management context assembly to neutral `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js`; this intentionally avoids a `docs-viewer-management*` module name so public read-only routes do not fetch management-only JS.
- `docs-viewer/runtime/js/docs-viewer-app-runtime.js` remains the compatibility coordinator for state defaults, controller construction, config handoff, event binding, initial load sequencing, and the returned runtime API.
- Structured docs-log entry: `change-2026-05-28-extracted-docs-viewer-compatibility-runtime-owners`.

Implementation note:

- Moved: generated-data reads/options, document visibility/loadability/default-doc projection, info-panel selected-document/toggle/toolbar/update coordination, and lazy management loading/context assembly.
- Stayed: boot, route/document workflow, search/recent callbacks and rendering, bookmark callbacks/storage/rendering, document payload/render/report handling, management workflows, backend writes, source edits, imports, settings, scope lifecycle, delete/archive/move, rebuild behavior, app startup sequencing, and public/manage route context.
- Deferred intentionally: source editor features, semantic-reference views, activity views, third-party visualization modules, plugin architecture, portable fixture setup, route shell markup, backend write behavior, and broader feature-specific panel surfaces.

Cleanup note:

- Removed stale compatibility helpers from the runtime for generated-data capability reads, info-panel context/toggle/open/close coordination, document visibility/loadability projection, and direct management-controller request caching.
- Kept compatibility shims for `loadManagementController`, document/search/recent pane update callbacks, and runtime API return shape because callers and tests still consume those stable handoffs.

### steer for this task

- Treat this as pure migration/risk reduction. The product behavior should remain unchanged.
- Prefer extracting complete responsibilities from `docs-viewer-app-runtime.js` only when the target module has a stable owner name and a narrow API.
- Keep `docs-viewer/runtime/js/docs-viewer.js` as the stable entrypoint.
- Keep `docs-viewer/runtime/js/docs-viewer-app-boot.js` as the boot owner.
- Keep `docs-viewer/runtime/js/docs-viewer-route-workflow.js` as the route/document workflow owner.
- Keep `docs-viewer/runtime/js/docs-viewer-document-controller.js` as the document pane/rendering owner.
- Keep `docs-viewer/runtime/js/docs-viewer-search-controller.js` and `docs-viewer/runtime/js/docs-viewer-bookmarks.js` as search/recent and bookmark owners.
- Keep `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`, `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`, `docs-viewer/runtime/js/docs-viewer-hosted-views.js`, and `docs-viewer/runtime/js/docs-viewer-view-context.js` as info panel and hosted-view owners.
- Keep backend write authority, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, and management modal workflows in the existing management/service modules.
- Preserve public read-only behavior first-class: `/library/` and `/analysis/` should keep route boot, document rendering, search/recent, bookmark support, metadata info, reports, and management omission.
- Preserve local `/docs/?mode=manage` behavior first-class: generated-data reads, management capability checks, import-open-on-load, metadata edit flow, context menu, reports, bookmarks, info panel, search/recent, status pills, and route history must continue to work.

### candidate extraction boundaries

Use the inventory to validate or reject these candidates:

- generated-data read capability and data-request option shaping
- lazy management-controller loading and management runtime context assembly
- info-panel coordination around selected-document context, toggle state, toolbar click handoff, open/update/close, and projection callbacks
- document index visibility/loadability projection around hidden/manage-only trees, default document selection, trails, and tree maps
- runtime state/default initialization only if it reduces coupling for another complete extraction
- controller construction sequencing only if it becomes a readable orchestration helper instead of moving the same broad coupling into a new file

Avoid extracting tiny wrappers that only move line count without reducing ownership ambiguity.

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - any new or changed focused runtime modules
  - any existing owner modules whose public contract changes
- Focused module smoke coverage when runtime ownership moves:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for any new runtime owner exports, generated-data option shaping, management lazy-boundary handoff, info-panel coordination, document visibility projection, and public/manage access assumptions where practical
- Management route checks when management lazy loading, generated-data reads, status pills, info panel, config handoff, or route state changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when route boot, generated-data reads, panel/info projection, document visibility, search/recent, bookmarks, reports, or public omission changes:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Docs-only follow-through when source docs change:
  - review generated docs payload status; let the docs watcher update generated payloads if it is running and do not revert watcher output

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory current responsibilities in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`: mutable state, constants/defaults, controller construction, config handoff, generated-data capability reads, management lazy loading, info-panel coordination, document visibility projection, compatibility wrappers, initial load sequencing, event binding, and returned runtime API. Deliverable: short implementation note listing what moves, what stays, and what is intentionally deferred. |
| 2 | done | Define the target compatibility-runtime boundary. The end state should keep `startDocsViewerRuntime(...)` as the coordinator that receives boot inputs, constructs focused owners, starts initial loading, and returns the small runtime API needed by tests or callers. |
| 3 | done | Decide whether generated-data read capability and `dataRequestOptions(...)` belong in a focused module. If they move, preserve scope capability semantics, retry/reload options, generated base URL behavior, and management capability compatibility. |
| 4 | done | Decide whether lazy management-controller loading and management context assembly belong in a focused runtime adapter. If they move, preserve dynamic import gating, app-shell readiness ordering, existing management controller inputs, backend capability checks, status ownership, source writes, modal workflows, and import-open-on-load behavior. |
| 5 | done | Decide whether info-panel coordination belongs in a focused controller. If it moves, preserve selected-document hosted-view context, metadata-info default behavior, toggle labels/pressed state, toolbar click handoff, close behavior, update-on-document-change behavior, and public-safe availability. |
| 6 | done | Decide whether document visibility/loadability projection belongs in a focused document-index state module. If it moves, preserve hidden/manage-only filtering, `showHidden` behavior, manage-only tree roots, non-loadable docs, default doc resolution, first-loadable descendant logic, trails, sidebar tree maps, and status projection. |
| 7 | done | Decide whether runtime state/default initialization should move. Only extract it if it supports another complete boundary; do not create a separate state file just to reduce line count. |
| 8 | done | Keep route/document workflow ownership out of this slice except for explicit callbacks consumed by extracted runtime owners. Do not move URL/query helpers, route application, index/payload loading, canonical URL correction, route-link handling, or popstate ownership out of `docs-viewer-route-workflow.js`. |
| 9 | done | Keep search/recent and bookmark ownership out of this slice except for explicit callback wiring. Do not move search result rendering, recent rendering, search debounce state, more-results behavior, bookmark storage, bookmark list rendering, edit state, or IndexedDB helpers back into runtime-owned code. |
| 10 | done | Keep document pane rendering out of this slice except for explicit projection callbacks. Do not move payload rendering, missing-doc rendering, payload error rendering, report mount handoff, metadata rendering, or hash scrolling out of `docs-viewer-document-controller.js`. |
| 11 | done | Keep management workflow behavior intact. Backend capability checks, management busy/status projection, source writes, imports, settings saves, scope lifecycle, delete/archive/move behavior, rebuild behavior, generated-data reads, context menu, metadata edit, status pills, and import-open-on-load must continue to work through the existing management/service flow. |
| 12 | done | Add or extend focused smoke coverage for any new runtime owner modules. Cover exported contracts, public omission, manage-mode initialization, generated-data option/capability behavior, info-panel updates, document visibility projection, and route workflow callback compatibility where practical. |
| 13 | done | Run management modal/service smoke checks if management loading, generated-data reads, config handoff, status pills, info panel, route state, or initial load sequencing changes. |
| 14 | done | Run public read-only checks if route boot, generated-data reads, document visibility, panel/info projection, search/recent, bookmarks, reports, or public omission changes. |
| 15 | done | Review the documentation touched by this app-shell migration for architectural drift. Include at least `docs-viewer/source/studio/development-workflow.md`, the app-shell request, runtime boundary, overview, JavaScript inventory, portable files/setup notes if relevant, and completed child trackers. Confirm future work guidance matches the new route config, route workflow, app boot, hosted-view, management-shell, and compatibility-runtime roles. |
| 16 | done | Review the runtime files touched by this migration for stale compatibility scaffolding, deprecated helpers, duplicate route/config/visibility logic, obsolete fallback paths, and broad callback bundles that are no longer needed after focused owners exist. Deliverable: short cleanup note listing removals made, removals deferred, and any compatibility shims intentionally kept. |
| 17 | done | Update owning docs after implementation: this tracker, the app-shell request, Docs Viewer runtime boundary, Docs Viewer overview, and Docs Viewer JavaScript inventory notes for new/changed owner modules. Update portable files/setup only if the copy set or runtime asset expectations change. |
| 18 | done | Create or update a structured docs-log entry for this slice and record the entry id in this tracker. |

The closeout for this slice should confirm:

- `docs-viewer/runtime/js/docs-viewer-app-runtime.js` is smaller and reads as compatibility coordination rather than a mixed owner of complete workflows
- each extracted responsibility has a focused owner, explicit inputs, and explicit return/callback contracts
- no feature-specific panel, editor, semantic-reference, activity, visualization, plugin, portable fixture, or backend-write behavior was added
- existing route/document, search/recent, bookmark, document rendering, info-panel, and management behaviors remain owned by their focused modules
- touched documentation has been reviewed so future development guidance matches the current app-shell, routing, hosted-view, management, and compatibility-runtime architecture
- touched runtime files have been reviewed for obsolete compatibility functions, duplicate logic, and deprecated fallback paths
- public read-only routes still avoid management-only shell markup, CSS, and JavaScript
- local manage mode still gets backend capability checks and write authority from the management/service flow
- metadata edit, import, settings, context menu, management actions, generated-data reads, reports, bookmarks, info panel, search/recent, status pills, and route history still work

## Verification

- `node --check docs-viewer/runtime/js/docs-viewer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
- `node --check docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`
- `node --check docs-viewer/runtime/js/docs-viewer-document-index-state.js`
- `node --check docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`
- `node --check docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`

Docs source was updated only; Docs Viewer generated docs/search payloads were not rebuilt manually.
