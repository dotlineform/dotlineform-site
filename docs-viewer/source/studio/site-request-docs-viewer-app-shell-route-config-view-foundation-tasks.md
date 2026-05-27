---
doc_id: site-request-docs-viewer-app-shell-route-config-view-foundation-tasks
title: Docs Viewer App Shell Route Config And View Foundation Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: done
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
- Completed this route config and view foundation slice.
- Added `docs-viewer/runtime/js/docs-viewer-route-config.js` as the narrow route-config resolver and scope projection helper.
- Added `docs-viewer/runtime/js/docs-viewer-access.js` for explicit public/manage/manage-local access projection without moving backend capability checks out of the existing management flow.
- Added `docs-viewer/runtime/js/docs-viewer-view-state.js` and extended `docs-viewer/runtime/js/docs-viewer-panel-layout.js` so the current two-panel behavior projects from an index/document/info state skeleton.
- Added `docs-viewer/runtime/js/docs-viewer-hosted-views.js` for minimal hosted-view registration, access checks, lifecycle method shape, built-in compatibility view records, and graceful absence.
- Kept route shell data attributes as migration compatibility; new app-shell work should consume the route config/access/view-state/hosted-view helpers instead of reading broad shell state directly.

### steer for next task

- The specific info panel remains deferred; the next slice can consume the new route/access/view/hosted-view contracts when it is ready to implement visible content.
- Route config is now a focused resolver/projection API. The current repo still uses the existing shell data attributes as migration input before scope config is loaded, while scope-specific generated/search paths continue to come from the browser-safe Docs Viewer config asset.
- Access projection is intentionally small: static route intent, public/manage gates, backend reachability status defaults, and future hosted-view access defaults. Backend reachability and write availability remain with the lazy management capability flow.
- Panel/view state can represent index, document, and info slots while projecting today's two-panel behavior. The info slot is disabled/unmounted by default.
- Hosted-view registration now exists for ordinary repo JavaScript modules. Missing, disabled, or access-blocked views resolve gracefully instead of failing route boot.
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
| 1 | done | Inventory the current route config inputs and consumers: `#docsViewerRoot` data attributes, `docs-viewer/config/defaults/docs-viewer-config.json`, `docs-viewer/config/defaults/docs-viewer-public-config.json`, scope config records, route shells, `docs-viewer-app-context.js`, `docs-viewer-config-controller.js`, router helpers, management modules, public route tests, and service shell generation. Deliverable: current durable fields are route id/type, default scope/doc, scope query allowance, viewer base URL, generated docs/search paths, config/UI/report URLs, static access defaults, panel defaults, and hosted-view availability metadata. Migration compatibility remains the shell data attributes used before browser config is loaded. |
| 2 | done | Defined the route config handoff shape in `docs-viewer-route-config.js`: route id/type, default scope/doc, scope-query allowance, viewer base URL, generated docs/search paths, UI/config/report URLs, static access defaults, panel defaults, and optional hosted-view availability metadata. |
| 3 | done | Kept the current repo on existing browser-safe config assets and route shell attributes during migration. Scope-specific records continue to load from `docs-viewer/config/defaults/*.json`; no new service endpoint or JSON script-tag route model was added. |
| 4 | done | Extended route context through `docs-viewer-route-config.js` plus `docs-viewer-app-context.js`, preserving data-attribute fallback and current `/docs/`, `/library/`, and `/analysis/` URL behavior. |
| 5 | done | Added `docs-viewer-access.js` for public, manage, and manage-local access projection while leaving backend reachability and write availability with the existing management capability flow. |
| 6 | done | Wired `docs-viewer-app-shell.js` and `docs-viewer.js` to consume route config/access projection while keeping `docs-viewer.js` as boot orchestration. Document payload fetching, search/recent rendering, report rendering, bookmark storage, and management writes stayed in their existing owners. |
| 7 | done | Added `docs-viewer-view-state.js` with an index/document/info panel skeleton that projects the current two-panel behavior. Info remains disabled/unmounted and no info-panel UI content was added. |
| 8 | done | Kept `docs-viewer-panel-layout.js` as the compatibility layout owner and delegated broader state shape to `docs-viewer-view-state.js`, giving later info-panel work explicit state without reading broad route state. |
| 9 | done | Added `docs-viewer-hosted-views.js` with id, label, panel, access, availability, load, mount, update, unmount, and dispose shape plus graceful absence for missing, disabled, or access-blocked views. |
| 10 | done | Registered only built-in compatibility records for index tree, document host, search results, recent results, report host, and a disabled metadata-info placeholder. Read-only metadata info, source editor, semantic-reference views, panel toolbar UI, and third-party visualization modules remain deferred. |
| 11 | done | Preserved current index behavior: collapsed/normal/expanded state, legacy sidebar storage migration, desktop availability, tree rendering in `docs-viewer-sidebar.js`, active doc projection, and expanded-index document-pane hiding. |
| 12 | done | Preserved current document/search/recent/report behavior: selected document projection, document pane visibility, results status, more-results clearing, hash scrolling, search route activation, recent mode activation, and generated report mounting. |
| 13 | done | Preserved public read-only behavior for `/library/` and `/analysis/`, verified by the focused public read-only smoke. |
| 14 | done | Preserved local `/docs/` management behavior, verified by the focused Docs Viewer service manage smoke. |
| 15 | done | Extended `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` for route config resolution, data-attribute compatibility, access projection, panel/view state projection, hosted-view registration, graceful absence, public omission of manage-only modules, and app-shell refs compatibility. |
| 16 | done | Ran targeted verification for changed JS, app-shell modules, route/public behavior, management behavior, service shell generation, and Jekyll build. No baseline check was skipped except management modal smoke, which was not required because modal-visible refs and metadata/status modal state were not touched. |
| 17 | done | Updated this tracker, the app-shell request, the multi-panel request, Docs Viewer runtime docs, and Docs Viewer JavaScript inventory notes. |
| 18 | done | Created structured docs-log entry `change-2026-05-27-added-docs-viewer-route-config-and-hosted-view-foundation`. |

## Implementation Notes

Route config inputs and consumers are now split into two layers:

- `docs-viewer-route-config.js` defines the durable route config shape and resolves the current app-shell context. In this repo, it uses `#docsViewerRoot` data attributes as migration input at boot and exposes an explicit record API for generated/config-driven handoff work.
- `docs-viewer-config-controller.js` still owns browser-safe scope config loading from `docs-viewer/config/defaults/docs-viewer-config.json` and `docs-viewer/config/defaults/docs-viewer-public-config.json`. Scope application now projects through `routeConfigScopeProjection()` instead of rebuilding route globals locally.

Fields made durable now: route id/type, default scope/doc, include-scope and scope-query flags, viewer base URL, generated docs/search paths, Docs Viewer config/UI text/report registry URLs, static access defaults, panel defaults, and hosted-view availability metadata.

Fields left as migration compatibility: the individual `#docsViewerRoot` data attributes emitted by `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html`.
They remain necessary boot input until route config is generated as a browser-safe config projection, but new app-shell code should consume `routeContext.routeConfig`, `routeContext.access`, `docs-viewer-view-state.js`, and `docs-viewer-hosted-views.js` rather than reading route attributes directly.

## Verification

- `node --check docs-viewer/runtime/js/docs-viewer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-context.js`
- `node --check docs-viewer/runtime/js/docs-viewer-panel-layout.js`
- `node --check docs-viewer/runtime/js/docs-viewer-access.js`
- `node --check docs-viewer/runtime/js/docs-viewer-route-config.js`
- `node --check docs-viewer/runtime/js/docs-viewer-view-state.js`
- `node --check docs-viewer/runtime/js/docs-viewer-hosted-views.js`
- `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/services/docs_viewer_service.py`
- `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`

The closeout for this slice should confirm:

- route config is the preferred durable route/app handoff for new app-shell work
- existing route data attributes are clearly migration compatibility, not the long-term architecture
- access and capability projection are explicit enough for hosted views without becoming a speculative permission framework
- panel/view state can represent the future index/document/info model while still projecting today's two-panel behavior
- hosted-view registration and graceful absence exist before specific info/source/semantic modules are implemented
- the specific info panel, panel toolbar UI, source editor, semantic-reference views, and third-party visualization modules remain deferred
- current index, document, metadata, search/recent, report, bookmark, public read-only, and management behavior still works
