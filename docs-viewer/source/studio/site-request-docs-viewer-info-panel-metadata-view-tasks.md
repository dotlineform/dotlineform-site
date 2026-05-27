---
doc_id: site-request-docs-viewer-info-panel-metadata-view-tasks
title: Docs Viewer Info Panel Metadata View Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: done
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

- Completed this first visible info-panel slice.
- Added `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js` as the app-shell-owned info-panel chrome renderer.
- Added `docs-viewer/runtime/js/docs-viewer-info-panel-host.js` as the focused hosted-view lifecycle owner for info panel open/update/close/dispose behavior.
- Added `docs-viewer/runtime/js/docs-viewer-view-context.js` as the focused selected-document hosted-view context projector for metadata and planned future info views.
- Added `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js` as the public-safe read-only metadata hosted view.
- Extended `docs-viewer/runtime/js/docs-viewer-panel-layout.js` and `docs-viewer/runtime/js/docs-viewer-view-state.js` so the info panel projects `data-info-panel-state` and `data-viewer-layout` while preserving index expanded behavior.
- Registered `metadata-info` as an available public built-in hosted view in `docs-viewer/runtime/js/docs-viewer-hosted-views.js`.
- Added a document metadata info button in `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`; existing sidebar/read-only metadata, status pills, bookmarks, search/recent, reports, and management edit flows remain separate.
- Updated public and manage smoke coverage for the visible info panel, hosted-view lifecycle, selected-doc updates, graceful absence, desktop/mobile public layout, and manage-mode selected-doc context.
- Created structured docs-log entry `change-2026-05-27-added-docs-viewer-info-panel-metadata-view`.

### steer for next task

- This request slice is complete.
- Follow-up work should keep source editing, editable metadata saves, semantic-reference views, activity views, panel toolbar generalization, third-party visualization modules, and plugin architecture out of the first metadata view boundary unless a new tracker explicitly takes one of those responsibilities.

## Implementation Notes

The first metadata info view renders only public-safe fields that already exist in generated index rows and loaded document payloads:

- selected document title and `doc_id`
- current viewer scope
- summary, when present
- parent path from the visible docs tree
- added and updated dates
- UI status label when configured
- visibility as visible/hidden from `viewable` and `hidden`
- canonical viewer route link built through the existing Docs Viewer URL helper

Deferred fields and actions:

- source paths and local filesystem actions
- editable metadata controls and saves
- semantic-reference and generated relationship data
- activity history
- source editor and management-only write endpoints

Ownership boundary:

- `docs-viewer-info-panel-renderer.js` owns info-panel DOM chrome and projection.
- `docs-viewer-info-panel-host.js` owns hosted-view lifecycle and graceful absence.
- `docs-viewer-view-context.js` owns selected-document hosted-view context projection.
- `docs-viewer-metadata-info-view.js` owns read-only metadata rendering inside its assigned mount.
- `docs-viewer.js` only passes explicit route/viewer inputs into the context helper and wires the info toggle, close action, and route/update orchestration.

Verification completed:

- `node --check` for changed Docs Viewer runtime modules.
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`

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
| 1 | done | Inventory current metadata sources and consumers: generated docs index rows, loaded document payload fields, `docs-viewer-sidebar.js` read-only metadata rendering, status-pill rendering, bookmark state, metadata modal refs, search/recent result rows, and report mount context. Deliverable: short implementation note in this tracker identifying which metadata fields the first info view can render from existing public-safe data and which fields are deferred. |
| 2 | done | Define the first info-panel product surface. Include selected document title, doc id, scope, summary, parent/path, updated/added date where available, UI status/viewable/hidden indicators where public-safe, and canonical route link/copy target if already available through existing helpers. Defer source path, local filesystem actions, edit controls, semantic references, activity, and generated relationship data. |
| 3 | done | Define the panel host ownership boundary. Decide whether to extend `docs-viewer-document-shell-renderer.js`, create a focused `docs-viewer-info-panel-renderer.js`, or create a small panel-host renderer module. Avoid adding DOM composition directly to `docs-viewer.js`. |
| 4 | done | Add an info-panel mount and chrome through the app shell: stable container, accessible label/title, close/hide control, and hosted-view body mount. Keep the panel hidden/unmounted by default until selected through view state. |
| 5 | done | Extend `docs-viewer-view-state.js` and `docs-viewer-panel-layout.js` only as needed to project visible/hidden info-panel state, active info view id, and layout attributes such as `data-info-panel-state` and `data-viewer-layout`. Preserve existing index expanded behavior that hides the document pane. |
| 6 | done | Wire a minimal info-panel action path: open metadata info for the current selected document, close/hide info, and update panel projection when selection, document load state, search mode, recent mode, or route popstate changes. Keep browser history behavior unchanged unless a clear URL-state requirement is documented. |
| 7 | done | Implement the first hosted view module for read-only metadata, using the existing hosted-view lifecycle shape: load, mount, update, unmount, and dispose. The module should render only inside its assigned info-panel container and tolerate missing document context. |
| 8 | done | Register the metadata info view as an available built-in compatibility view instead of the current disabled placeholder, gated as public access. Preserve graceful absence behavior if the module fails to load or is disabled by route config. |
| 9 | done | Define the metadata view context shape passed from Docs Viewer core to the hosted view: selected doc row, loaded payload metadata if available, viewer scope, route/access projection, URL helpers, and display text helpers. Avoid passing broad mutable `state` directly. |
| 10 | done | Preserve current read-only document metadata rendering in `docs-viewer-sidebar.js` and the existing document pane. The info panel should complement, not replace, current title/path/summary/status/bookmark display in this slice. |
| 11 | done | Preserve search/recent/report behavior. Opening the info panel must not clear search results, more-results state, recent mode, generated reports, hash scrolling, or selected document projection unless an explicit user action selects a new document. |
| 12 | done | Preserve public read-only behavior for `/library/` and `/analysis/`: route boot, document rendering, hash navigation, search/recent behavior, reports, bookmarks, and absence of management-only UI/JS. |
| 13 | done | Preserve local `/docs/` management behavior: manage-mode detection, management capability messages, status pills, bookmark toggle, metadata edit flow, report rendering, browser history behavior, and management action gating. |
| 14 | done | Add focused module smoke coverage for info-panel render/projection, metadata hosted-view lifecycle, selected-doc updates, missing/empty metadata, close/hide behavior, public availability, and graceful absence. |
| 15 | done | Add or update route-level browser smoke coverage for desktop and mobile layouts. Verify the info panel does not overlap controls or document content, can close reliably, and remains usable with long metadata values. |
| 16 | done | Run targeted verification for changed JS, app-shell modules, public read-only behavior, manage-mode behavior, Jekyll build, and any changed CSS/layout. Record skipped checks and why. |
| 17 | done | Update owning docs after implementation. At minimum update this tracker, the app-shell request, the multi-panel request, Docs Viewer runtime docs, and Docs Viewer JavaScript inventory notes if ownership or risk materially changes. |
| 18 | done | Create a structured docs-log entry when the slice is complete and record the entry id in this tracker: `change-2026-05-27-added-docs-viewer-info-panel-metadata-view`. |

The closeout for this slice should confirm:

- the info panel is a real app-shell panel, not a one-off document-pane widget
- the metadata info view is public-safe and works without management-only modules
- hosted-view lifecycle and graceful absence are exercised by a visible view
- selected-document metadata context is explicit and does not expose broad mutable route state
- current index, document, search/recent, report, bookmark, public read-only, and management behavior still works
- source editor, editable metadata, semantic-reference views, activity views, panel toolbar generalization, third-party visualization modules, and plugin architecture remain deferred
