---
doc_id: site-request-docs-viewer-app-shell-route-context-panel-state-tasks
title: Docs Viewer App Shell Route Context And Panel State Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: done
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12109
viewable: true
---
# Docs Viewer App Shell Route Context And Panel State Tasks

This is the tracker for implementing the fifth app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The fifth migration is the route context and panel state layer.
It should introduce a small app-shell-owned context/projection surface for route dataset normalization, public/manage access flags, stable shell refs, and the current index/document/search/recent panel visibility model without moving document payload loading, routing behavior, generated-data reads, search result rendering, report rendering, bookmark behavior, or management write workflows.

This slice should align with [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell), but it should not implement the full info-panel, panel-toolbar, or hosted-view architecture.
The goal is to create the narrow state/context owner that later info-panel work can build on.

## Status

### just done

- Implemented this route context and panel state slice.
- Completed [Docs Viewer App Shell Management Actions Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-management-actions-tasks).
- Completed [Docs Viewer App Shell Header Controls Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-header-controls-tasks).
- Completed [Docs Viewer App Shell Index Panel Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-index-panel-tasks).
- Completed [Docs Viewer App Shell Document Mount And Metadata Shell Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-document-metadata-tasks).
- Established `docs-viewer/runtime/js/docs-viewer-app-shell.js` as the app-shell coordinator while keeping `docs-viewer/runtime/js/docs-viewer.js` as the compatibility entrypoint.
- Moved management actions, header controls, index panel chrome, document shell chrome, read-only metadata chrome, and document/search/recent result mounts out of `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html`.
- Added `docs-viewer/runtime/js/docs-viewer-app-context.js` for route dataset normalization and access flags.
- Added `docs-viewer/runtime/js/docs-viewer-panel-layout.js` for the current compatibility index/document/search/recent projection handoff.

### implementation note

Moved the narrow state surface only:

- route context: management intent, scope query allowance, viewer base URL, viewer scope, default doc id, generated/config URLs, report/UI text URLs, management/generated base URLs, import-on-load intent, viewer pathname, and bookmark storage scope
- access flags: public read-only, allow management, allow scope query, requested mode, management requested, and import requested
- shell refs: header controls, index panel refs, document shell refs, status/bookmark refs, and management action refs
- panel projection: index collapsed/normal/expanded storage/projection and document/search/recent/results-status visibility projection

Left in place:

- document payload loading, Markdown rendering, generated report loading, search/recent result rendering, bookmark storage behavior, management writes, metadata/import modal internals, and route handling
- broader info panel, panel toolbar, hosted-view registry, optional-module lifecycle, and full multi-panel model

### steer for next task

- Implement a focused app-shell route context and panel state/projection layer as the next narrow app-shell-owned responsibility.
- Keep the slice focused on normalizing route context from `#docsViewerRoot`, exposing public/manage access flags, preserving shell refs, and consolidating current index/document/search/recent visibility projection.
- Keep `docs-viewer/runtime/js/docs-viewer.js` as the compatibility entrypoint and boot orchestrator: initialize app shell, load config, wire controllers, apply routes, and hand off to focused owners.
- Do not move document payload fetching, Markdown rendering, generated report rendering, search/recent result rendering, bookmark storage behavior, management command behavior, metadata edit modal internals, import modal internals, or broad route loading in this pass.
- Do not add the full info panel, panel toolbar, hosted-view registry, or optional module lifecycle in this pass.
- Prefer a focused module such as `docs-viewer-app-context.js`, `docs-viewer-panel-layout.js`, or another clearly named app-shell child module over adding context/state ownership directly to `docs-viewer.js`.
- Preserve current `/docs/`, `/library/`, and `/analysis/` URL behavior and public read-only management omission.

### baseline verification set

Run only the checks warranted by the touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - any changed focused app-shell/context/panel modules
- Focused module smoke checks when context normalization, app-shell refs, or panel projection ownership changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend focused context/panel-layout module smoke coverage if existing app-shell coverage does not pin the new owner contract
- Route behavior smoke checks when route context, query/mode/scope handling, history, hash navigation, search/recent panes, or route loading changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_routes.py --site-root .`
  - focused public Library document/hash/search smoke if the broad route smoke cannot run against the current isolated build shape
- Public read-only smoke when route context, app-shell boot, management omission, or public shell behavior changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Management service smoke when management-mode route context, status projection, bookmarks, or management availability state are touched:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .` if metadata/status refs or modal-visible behavior are touched
- Jekyll build only when includes, route templates, CSS, or loaded assets change:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when the product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for high-risk shared runtime files.
- This slice is part of the app-shell enabling work, not a broad `docs-viewer.js` refactor.
- The new owner should make the existing route context and panel projection easier to inspect and test before the first info-panel slice starts.
- Keep app-shell state explicit and small: route context, access flags, shell refs, and compatibility panel projection are enough for this pass.
- Keep index tree rendering in `docs-viewer/runtime/js/docs-viewer-sidebar.js`.
- Keep document body rendering and search/recent/report host behavior in `docs-viewer/runtime/js/docs-viewer-document-controller.js` and existing search/report modules.
- Keep backend endpoints as the only write authority; route context and panel state must not add browser-side write capability.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory current route context and panel projection ownership in `docs-viewer/runtime/js/docs-viewer.js`, `docs-viewer/runtime/js/docs-viewer-app-shell.js`, `docs-viewer/runtime/js/docs-viewer-index-panel.js`, `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`, `docs-viewer/runtime/js/docs-viewer-document-controller.js`, config/controller modules, and management modules that consume mode/scope/access state. Deliverable: short implementation note in this tracker or closeout summary identifying the exact state and refs to move. |
| 2 | done | Define the focused app-shell context/panel surface. Decide whether to add `docs-viewer-app-context.js`, `docs-viewer-panel-layout.js`, or another focused child module. Deliverable: clear module ownership and no new broad state responsibility added to `docs-viewer.js`. |
| 3 | done | Normalize route context from `#docsViewerRoot` into a small object for existing boot values such as management intent, scope-query allowance, viewer base URL, viewer scope, default doc id, generated/config URLs, and management/generated base URLs. Preserve current data attributes and URL behavior. |
| 4 | done | Define public/manage access flags for app-shell decisions without loading management-only modules on public routes. Keep backend capability checks and write availability in the existing management/generation capability flow. |
| 5 | done | Define a compatibility shell refs object that groups header controls, index panel refs, document shell refs, status/bookmark refs, and management action refs as needed. Preserve existing ids and controller expectations. |
| 6 | done | Consolidate current panel projection handoffs into a narrow owner for index state plus document/search/recent/results-status visibility. Do not implement info-panel visibility, panel toolbar controls, or hosted-view registration in this pass. |
| 7 | done | Wire `docs-viewer.js` to consume the new route context, refs, and projection helpers while keeping route boot, config loading, controller wiring, and existing route handling readable. |
| 8 | done | Preserve current index panel behavior: collapsed/normal/expanded state, legacy sidebar state projection, local storage migration keys, desktop availability behavior, and tree rendering ownership. |
| 9 | done | Preserve current document/search/recent behavior: selected document projection, document pane visibility, results status, more-results mount clearing, hash scrolling, search route activation, recent mode activation, and generated report mounting. |
| 10 | done | Preserve public route behavior for `/library/` and `/analysis/`: read-only boot, document payload rendering, hash navigation, metadata visibility, search/recent behavior, report rendering, bookmarks, and absence of management-only imports. |
| 11 | done | Preserve local `/docs/` management behavior: manage-mode detection, status pills, bookmark toggle, metadata edit flow, report rendering, browser history behavior, management availability messages, and management action gating. |
| 12 | done | Add or update focused module smoke coverage for context normalization and panel projection. Cover public and management route context, id/ref preservation, idempotent shell initialization, management-only omission, index projection, document/search/recent projection, and compatibility with existing app-shell renderer refs where practical. |
| 13 | done | Run the targeted verification set for changed JS, app-shell/context/panel behavior, public read-only routes, and management routes. Record any checks skipped and why. |
| 14 | done | Update owning docs after implementation. At minimum update this tracker, the app-shell request, the multi-panel request if the projection contract changes, and Docs Viewer runtime/inventory docs if `docs-viewer.js` ownership or risk materially changes. |

## Verification

Passed:

- `node --check docs-viewer/runtime/js/docs-viewer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-context.js`
- `node --check docs-viewer/runtime/js/docs-viewer-panel-layout.js`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`

Skipped/replaced:

- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_routes.py --site-root .` and the same command against `/tmp/dlf-jekyll-build` could not exercise `/docs/` because `/docs/` is a local-service management route and is not present in the raw source tree or temporary public Jekyll build. Public route coverage came from `public_docs_viewer_readonly.py`; management route coverage came from `docs_viewer_service_manage.py`.

Docs-log entry:

- `change-2026-05-27-added-docs-viewer-route-context-panel-layout`

The closeout for this fifth migration should confirm:

- route context and compatibility panel projection ownership moved toward focused app-shell modules
- `docs-viewer.js` remains a compatibility entrypoint and readable boot orchestrator
- current shell refs and public/manage access gates are explicit enough for the next info-panel slice
- the broader info-panel, panel-toolbar, hosted-view, and optional-module lifecycle architecture remains deferred
- current index, document, metadata, search/recent, report, bookmark, and status-pill behavior still works
- public read-only routes still render expected document shell and omit management-only UI/JS
- management document and metadata interactions still work
- generated docs payloads were rebuilt by the watcher only if source docs changed, or intentionally not rebuilt by Codex
