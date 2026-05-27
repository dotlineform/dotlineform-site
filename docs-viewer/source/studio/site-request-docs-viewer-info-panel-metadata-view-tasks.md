---
doc_id: site-request-docs-viewer-info-panel-metadata-view-tasks
title: Docs Viewer Info Panel Metadata View Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: planned
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12120
viewable: true
---
# Docs Viewer Info Panel Metadata View Tasks

This is the tracker for the next visible app-shell slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The slice should deliver the first usable info panel by combining the panel host/chrome work, hosted-view activation path, selected-document context projection, and a public-safe read-only metadata view.
Those deliverables are tightly coupled enough to implement together, and separating them further would leave either invisible infrastructure or a visible panel without the contracts it needs.

This slice should align with [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell).
It should not implement source editing, editable metadata saves, semantic-reference views, activity views, third-party visualization modules, plugin architecture, or broader route-config generation.

## Status

### just done

- Completed [Docs Viewer App Shell Route Config And View Foundation Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-route-config-view-foundation-tasks).
- Added `docs-viewer/runtime/js/docs-viewer-route-config.js` for route config resolution and route/scope projection.
- Added `docs-viewer/runtime/js/docs-viewer-access.js` for static public/manage/manage-local access projection.
- Added `docs-viewer/runtime/js/docs-viewer-view-state.js` and extended `docs-viewer/runtime/js/docs-viewer-panel-layout.js` so the current two-panel behavior projects from an index/document/info state skeleton.
- Added `docs-viewer/runtime/js/docs-viewer-hosted-views.js` for minimal hosted-view registration, built-in compatibility records, lifecycle method shape, access checks, and graceful absence.
- Preserved current public read-only and local manage-mode behavior while keeping route data attributes as migration compatibility.

### steer for next task

- Deliver a visible info panel that can open beside the document panel and show metadata for the selected document.
- Keep the first info view read-only and public-safe; it should use data already available from generated docs index rows and loaded document payloads.
- Use the existing route config, access projection, view-state skeleton, and hosted-view registry instead of adding another route-state path.
- Add only the panel chrome needed for this slice: an info-panel region, stable title/label, a metadata hosted-view mount, and a hide/close control. Broader toolbar/view-selection design can stay minimal unless needed to switch registered views.
- Preserve current index collapsed/normal/expanded behavior and document/search/recent/report behavior.
- Do not move metadata edit modal internals, source editor behavior, report rendering, search/recent rendering, bookmark storage, or management writes in this pass.

### baseline verification set

Run only the checks warranted by the touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-panel-layout.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-view-state.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-hosted-views.js`
  - any changed info-panel, panel-host, renderer, or metadata-view modules
- Focused module smoke checks:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend focused module smoke coverage for info-panel state projection, hosted-view mount/update/unmount, metadata rendering, empty selection, missing metadata, and graceful absence
- Route/public read-only checks when visible panel behavior, layout, or route boot changes:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
  - a focused desktop/mobile public Library smoke for selecting a document, opening/closing the info panel, and preserving hash/search/recent behavior
- Management checks when the panel appears in manage mode or shares selected-doc/status metadata with management UI:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .` only if metadata modal refs, status-pill state, or editable metadata flows are touched

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when the product code is healthy.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for high-risk shared runtime files.
- This is the first visible panel slice. Keep it focused on panel hosting, metadata display, selected-document projection, and proof that public/manage routes still share one app-shell path.
- Prefer focused modules over adding info-panel rendering or hosted-view lifecycle responsibility directly to `docs-viewer/runtime/js/docs-viewer.js`.
- Keep `docs-viewer/runtime/js/docs-viewer.js` readable as the compatibility boot orchestrator.
- Keep public read-only behavior first-class. The metadata info view should work on `/library/` and `/analysis/` without management-only modules.
- Keep management editing flows separate. The info panel may show read-only metadata in manage mode, but edits still belong to the existing metadata modal and backend write endpoints.
- Keep the metadata view compact, scannable, and resilient to missing optional fields.
- Do not add speculative plugin architecture; hosted views remain ordinary repo JavaScript modules.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory current metadata sources and consumers: generated docs index rows, loaded document payload fields, `docs-viewer-sidebar.js` read-only metadata rendering, status-pill rendering, bookmark state, metadata modal refs, search/recent result rows, and report mount context. Deliverable: short implementation note in this tracker identifying which metadata fields the first info view can render from existing public-safe data and which fields are deferred. |
| 2 | planned | Define the first info-panel product surface. Include selected document title, doc id, scope, summary, parent/path, updated/added date where available, UI status/viewable/hidden indicators where public-safe, and canonical route link/copy target if already available through existing helpers. Defer source path, local filesystem actions, edit controls, semantic references, activity, and generated relationship data. |
| 3 | planned | Define the panel host ownership boundary. Decide whether to extend `docs-viewer-document-shell-renderer.js`, create a focused `docs-viewer-info-panel-renderer.js`, or create a small panel-host renderer module. Avoid adding DOM composition directly to `docs-viewer.js`. |
| 4 | planned | Add an info-panel mount and chrome through the app shell: stable container, accessible label/title, close/hide control, and hosted-view body mount. Keep the panel hidden/unmounted by default until selected through view state. |
| 5 | planned | Extend `docs-viewer-view-state.js` and `docs-viewer-panel-layout.js` only as needed to project visible/hidden info-panel state, active info view id, and layout attributes such as `data-info-panel-state` and `data-viewer-layout`. Preserve existing index expanded behavior that hides the document pane. |
| 6 | planned | Wire a minimal info-panel action path: open metadata info for the current selected document, close/hide info, and update panel projection when selection, document load state, search mode, recent mode, or route popstate changes. Keep browser history behavior unchanged unless a clear URL-state requirement is documented. |
| 7 | planned | Implement the first hosted view module for read-only metadata, using the existing hosted-view lifecycle shape: load, mount, update, unmount, and dispose. The module should render only inside its assigned info-panel container and tolerate missing document context. |
| 8 | planned | Register the metadata info view as an available built-in compatibility view instead of the current disabled placeholder, gated as public access. Preserve graceful absence behavior if the module fails to load or is disabled by route config. |
| 9 | planned | Define the metadata view context shape passed from Docs Viewer core to the hosted view: selected doc row, loaded payload metadata if available, viewer scope, route/access projection, URL helpers, and display text helpers. Avoid passing broad mutable `state` directly. |
| 10 | planned | Preserve current read-only document metadata rendering in `docs-viewer-sidebar.js` and the existing document pane. The info panel should complement, not replace, current title/path/summary/status/bookmark display in this slice. |
| 11 | planned | Preserve search/recent/report behavior. Opening the info panel must not clear search results, more-results state, recent mode, generated reports, hash scrolling, or selected document projection unless an explicit user action selects a new document. |
| 12 | planned | Preserve public read-only behavior for `/library/` and `/analysis/`: route boot, document rendering, hash navigation, search/recent behavior, reports, bookmarks, and absence of management-only UI/JS. |
| 13 | planned | Preserve local `/docs/` management behavior: manage-mode detection, management capability messages, status pills, bookmark toggle, metadata edit flow, report rendering, browser history behavior, and management action gating. |
| 14 | planned | Add focused module smoke coverage for info-panel render/projection, metadata hosted-view lifecycle, selected-doc updates, missing/empty metadata, close/hide behavior, public availability, and graceful absence. |
| 15 | planned | Add or update route-level browser smoke coverage for desktop and mobile layouts. Verify the info panel does not overlap controls or document content, can close reliably, and remains usable with long metadata values. |
| 16 | planned | Run targeted verification for changed JS, app-shell modules, public read-only behavior, manage-mode behavior, Jekyll build, and any changed CSS/layout. Record skipped checks and why. |
| 17 | planned | Update owning docs after implementation. At minimum update this tracker, the app-shell request, the multi-panel request, Docs Viewer runtime docs, and Docs Viewer JavaScript inventory notes if ownership or risk materially changes. |
| 18 | planned | Create a structured docs-log entry when the slice is complete and record the entry id in this tracker. |

The closeout for this slice should confirm:

- the info panel is a real app-shell panel, not a one-off document-pane widget
- the metadata info view is public-safe and works without management-only modules
- hosted-view lifecycle and graceful absence are exercised by a visible view
- selected-document metadata context is explicit and does not expose broad mutable route state
- current index, document, search/recent, report, bookmark, public read-only, and management behavior still works
- source editor, editable metadata, semantic-reference views, activity views, panel toolbar generalization, third-party visualization modules, and plugin architecture remain deferred
