---
doc_id: site-request-docs-viewer-app-shell-route-config-view-foundation-tasks
title: Docs Viewer App Shell Route Config And View Foundation Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: planned
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12110
viewable: true
---
# Docs Viewer App Shell Route Config And View Foundation Tasks

This is the tracker for the next infrastructure-first slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The slice should reduce the current mixed ownership model before implementing a visible info panel.
It combines route config handoff, access/capability projection, a panel/view state skeleton, and a hosted-view registration shape because those contracts are tightly coupled.

This slice should align with [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell), but it should not implement the read-only info metadata view, panel toolbar UI, source editor, semantic-reference modules, or third-party visualization modules.

## Status

### just done

- Completed [Docs Viewer App Shell Route Context And Panel State Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-route-context-panel-state-tasks).
- Added `docs-viewer/runtime/js/docs-viewer-app-context.js` for current route dataset normalization and access flags.
- Added `docs-viewer/runtime/js/docs-viewer-panel-layout.js` for the compatibility index/document/search/recent projection handoff.
- Kept `docs-viewer/runtime/js/docs-viewer.js` as the compatibility entrypoint and route boot/controller orchestration layer.
- Confirmed public read-only routes and the local management route still boot through the shared app shell.

### steer for next task

- Defer the specific info panel until the app-shell foundation is less transitional.
- Move toward a route config record as the durable route/app handoff rather than depending on route data attributes as the long-term contract.
- Keep access and capability projection small: static route intent, public/manage gates, backend reachability, and future module access defaults.
- Add a panel/view state skeleton that can project the current two-panel behavior without requiring a visible info panel.
- Add a minimal hosted-view registration shape with graceful absence for unavailable modules.
- Keep document payload loading, Markdown rendering, generated report rendering, search/recent result rendering, bookmark storage, management command behavior, metadata/import modal internals, and backend writes in their existing owners.

### baseline verification set

Run only the checks warranted by the touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-context.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-panel-layout.js`
  - any changed route-config, access, panel, or hosted-view modules
- Focused module smoke checks:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend focused module smoke coverage for route config resolution, access projection, panel/view state projection, registration, graceful absence, and public/manage gating
- Route and public read-only checks when route config, route context, query/mode/scope handling, or public route boot changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
  - a focused public Library document/hash/search smoke if route behavior changes beyond static access gating
- Management checks when manage-mode access, management capability projection, status projection, or lazy management loading changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .` if modal-visible refs or metadata/status state are touched
- Jekyll build when includes, route templates, CSS, generated config assets, or loaded assets change:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when the product code is healthy.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for high-risk shared runtime files.
- This is an app-shell infrastructure slice, not an info-panel feature slice.
- Prefer focused modules over adding route config, panel state, or view lifecycle responsibility directly to `docs-viewer/runtime/js/docs-viewer.js`.
- Keep `docs-viewer/runtime/js/docs-viewer.js` readable as the compatibility boot orchestrator.
- Preserve current `/docs/`, `/library/`, and `/analysis/` URL behavior.
- Preserve public read-only management omission and do not load management-only modules on public routes.
- Keep backend endpoints as the only write authority.
- Do not add speculative plugin architecture; use a minimal hosted-view shape for ordinary repo JavaScript modules.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory the current route config inputs and consumers: `#docsViewerRoot` data attributes, `docs-viewer/config/defaults/docs-viewer-config.json`, `docs-viewer/config/defaults/docs-viewer-public-config.json`, scope config records, route shells, `docs-viewer-app-context.js`, `docs-viewer-config-controller.js`, router helpers, management modules, public route tests, and service shell generation. Deliverable: short implementation note in this tracker or closeout summary identifying the route fields to make durable now and the fields to leave as migration compatibility. |
| 2 | planned | Define the route config handoff shape for this slice. Keep it narrow: route id/type, default scope/doc, scope-query allowance, viewer base URL, generated docs/search paths, UI/config/report URLs, static access defaults, panel defaults, and optional hosted-view availability metadata only where current code can consume it. |
| 3 | planned | Decide where the route config record lives for the current repo and how it is loaded. Prefer using existing browser-safe config assets or generated config projection before adding new service endpoints. Preserve current route data attributes as migration compatibility only where needed. |
| 4 | planned | Extend `docs-viewer-app-context.js` or a focused child module to resolve the current route context from the route config record, with fallback to existing `#docsViewerRoot` attributes during migration. Preserve existing `/docs/`, `/library/`, and `/analysis/` URL behavior. |
| 5 | planned | Define an access/capability projection helper for public, manage, and manage-local decisions. Keep backend reachability and write availability in the existing management capability flow; do not add browser-side write authority or per-click permission checks. |
| 6 | planned | Wire `docs-viewer-app-shell.js` and `docs-viewer.js` to consume the route config/access projection while keeping `docs-viewer.js` as boot orchestration. Do not move document payload fetching, search/recent rendering, report rendering, bookmark storage, or management writes in this pass. |
| 7 | planned | Define a panel/view state skeleton that can represent index, document, and info panel slots while projecting the current two-panel behavior. Keep info hidden/unmounted by default and do not add info-panel UI content. |
| 8 | planned | Decide whether `docs-viewer-panel-layout.js` remains the owner or should delegate to a new focused panel/view state module. Avoid cosmetic extraction; choose the boundary that lets later info-panel work consume explicit state without reading broad route state. |
| 9 | planned | Add a minimal hosted-view registration shape for ordinary repo JavaScript modules: id, label, panel, access, availability, load, mount, update, unmount, and dispose. Implement graceful absence for unavailable or disabled modules without failing route boot. |
| 10 | planned | Register only current built-in compatibility views needed to preserve behavior, such as index tree and document/search/recent/report host placeholders. Do not implement read-only metadata info view, source editor, semantic-reference views, panel toolbar UI, or third-party visualization modules. |
| 11 | planned | Preserve current index behavior: collapsed/normal/expanded state, legacy sidebar storage migration, desktop availability, tree rendering in `docs-viewer-sidebar.js`, active doc projection, and expanded-index document-pane hiding. |
| 12 | planned | Preserve current document/search/recent/report behavior: selected document projection, document pane visibility, results status, more-results clearing, hash scrolling, search route activation, recent mode activation, and generated report mounting. |
| 13 | planned | Preserve public read-only behavior for `/library/` and `/analysis/`: route boot, document payload rendering, hash navigation, search/recent behavior, reports, bookmarks, and absence of management-only UI/JS. |
| 14 | planned | Preserve local `/docs/` management behavior: manage-mode detection, management capability messages, status pills, bookmark toggle, metadata edit flow, report rendering, browser history behavior, and management action gating. |
| 15 | planned | Add or update focused module smoke coverage for route config resolution, fallback data-attribute compatibility, access projection, panel/view state projection, hosted-view registration, graceful absence, public omission of manage-only modules, and compatibility with existing app-shell refs. |
| 16 | planned | Run the targeted verification set for changed JS, app-shell modules, route/public behavior, management behavior, and generated config/build behavior. Record skipped checks and why. |
| 17 | planned | Update owning docs after implementation. At minimum update this tracker, the app-shell request, the multi-panel request, Docs Viewer runtime docs, and Docs Viewer JavaScript inventory notes if `docs-viewer.js` ownership or risk materially changes. |
| 18 | planned | Create a structured docs-log entry when the slice is complete and record the entry id in this tracker. |

The closeout for this slice should confirm:

- route config is the preferred durable route/app handoff for new app-shell work
- existing route data attributes are clearly migration compatibility, not the long-term architecture
- access and capability projection are explicit enough for hosted views without becoming a speculative permission framework
- panel/view state can represent the future index/document/info model while still projecting today's two-panel behavior
- hosted-view registration and graceful absence exist before specific info/source/semantic modules are implemented
- the specific info panel, panel toolbar UI, source editor, semantic-reference views, and third-party visualization modules remain deferred
- current index, document, metadata, search/recent, report, bookmark, public read-only, and management behavior still works
