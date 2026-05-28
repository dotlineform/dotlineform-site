---
doc_id: site-request-docs-viewer-controller-view-lifecycle-tasks
title: Docs Viewer Controller And View Lifecycle Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: planned
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14186
viewable: true
---
# Docs Viewer Controller And View Lifecycle Tasks

This is the sixth child task tracker for [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture).

The slice should define a practical lifecycle for Docs Viewer controllers and hosted views.
It follows [Docs Viewer Public And Manage App Contexts Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-app-contexts-tasks), which made public read-only and local manage app contexts explicit and kept static route/config facts separate from backend capability and write authority.

This is structural frontend-app architecture work.
It should not add source editor features, semantic-reference editing, visualization features, plugin architecture, route shell markup, generated payload schema changes, or backend write behavior.

## Status

### steer for this task

- Treat this as lifecycle clarification and controller/view ownership cleanup, not a plugin platform.
- Preserve current `/docs/`, `/library/`, and `/analysis/` behavior.
- Build on existing hosted-view lifecycle methods rather than inventing a separate extension system.
- Keep route shells and route boot focused on config resolution, shell creation, lifecycle orchestration, and startup handoff.
- Keep controller responsibilities explicit: `initialize`, `bind`, `update`, and optional `dispose` should mean the same thing across owners where those phases are needed.
- Avoid moving backend authority into view visibility, route config, or hosted-view registration.
- Hosted views should receive explicit route, app-context, state-domain, and service inputs; they should not reach into broad runtime state or private controller internals.
- Future feature views should attach through focused host/controller contracts without modifying route shell markup or broad runtime state.
- Do not replace lifecycle cleanup with direct endpoint calls from feature modules.

### backend co-evolution steer

Classify any lifecycle participant that consumes data or services by source of authority:

- browser route/config context
- generated static asset
- local generated-read service
- browser storage
- management backend capability endpoint
- management backend write endpoint

Public-safe views must be able to mount without backend services.
Manage-only views must declare the management service adapter, generated-read capability, or backend capability they consume.
View visibility, hosted-view availability, or current mode must not imply write authority; management writes remain behind backend endpoints with server-side validation.
Local diagnostic, source-related, or filesystem-adjacent views should remain local/manage-only until their data contracts are safe and documented.

### current lifecycle inventory targets

Inventory these current owners before editing:

- `docs-viewer/runtime/js/docs-viewer-app-runtime.js`: controller creation, top-level event binding, startup handoff, private management lazy-controller bridge, and compatibility runtime state handoff.
- `docs-viewer/runtime/js/docs-viewer-app-composition.js`: startup phase orchestration, service-context handoff, app-session creation, hosted-view registry creation, panel layout creation, generated-data runtime creation, and startup authority records.
- `docs-viewer/runtime/js/docs-viewer-app-session.js`: state domains and temporary broad-state compatibility bridge.
- `docs-viewer/runtime/js/docs-viewer-route-workflow.js`: route link and popstate binding, route application, index initialization, URL state, and document payload workflow handoff.
- `docs-viewer/runtime/js/docs-viewer-search-controller.js`: search/recent event binding, generated search reads, rendering handoff, and route callbacks.
- `docs-viewer/runtime/js/docs-viewer-bookmarks.js`: bookmark storage initialization, binding, update/render callbacks, and browser-storage ownership.
- `docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`: info-panel binding, selected-document context projection, hosted-view host update handoff, and panel layout projection.
- `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`: info hosted-view load, mount, update, unmount, close, dispose, view option projection, and graceful absence.
- `docs-viewer/runtime/js/docs-viewer-hosted-views.js`: hosted-view registration shape, access/availability checks, panel-specific listing, compatibility view records, and lifecycle method names.
- `docs-viewer/runtime/js/docs-viewer-view-context.js`: explicit selected-document hosted-view context projection.
- `docs-viewer/runtime/js/docs-viewer-management.js` and management child modules: manage-mode bind/initialize behavior, capability checks, action/menu/modal coordination, imports, settings, scope lifecycle, and write orchestration.
- `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`: focused module smoke coverage for app composition, route workflow, search/bookmark controllers, info-panel lifecycle, hosted-view context, and management runtime adapter contracts.
- Current owning docs: [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview), and [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory).

### likely clarification targets

Use the inventory to validate or revise these candidate changes:

- Treat any lifecycle map, authority table, vocabulary, or owner contract as a working draft in this tracker unless it is explicitly copied into a durable Docs Viewer reference doc.
- Define a small lifecycle vocabulary for controllers and views: create, initialize, bind, update/project, unmount/close, and dispose.
- Decide which controllers need explicit `initialize`, `bind`, `update`, and `dispose` phases, and which should stay as simple stateless helpers.
- Reduce scattered top-level event binding where a focused controller already owns the behavior.
- Make hosted-view context and service inputs explicit enough that future public-safe and manage-only views can mount without reaching into broad runtime state.
- Keep info-panel hosted-view lifecycle as the first concrete model rather than creating a general plugin platform.
- Keep management actions, capability checks, and writes behind the existing management controller/client/service flow.
- Add or extend focused smoke coverage before behavior changes where practical, especially for lifecycle ordering, repeated bind/update calls, view switching, disposal, and public/manage access separation.

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-composition.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-session.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-route-workflow.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-search-controller.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-bookmarks.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-info-panel-controller.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-info-panel-host.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-hosted-views.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-view-context.js`
  - any focused owner modules whose public contract changes
- Focused module smoke coverage when lifecycle or controller contracts change:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for controller lifecycle ordering, idempotent binding, hosted-view mount/update/unmount/dispose behavior, public/manage access separation, and explicit context/service inputs where practical
- Management route checks when management lifecycle, lazy loading, capabilities, imports, settings, rebuilds, scope lifecycle, route state, status projection, or write service contracts change:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when public startup, public hosted views, document visibility, search/recent, bookmarks, reports, info panel, or public management omission changes:
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
| 1 | planned | Inventory current controller and hosted-view lifecycle behavior across app runtime, app composition, app session, route workflow, search, bookmarks, info panel, hosted views, metadata info view, management modules, smoke tests, and docs. Deliverable: short working lifecycle map in this tracker; if the map is intended as future-development reference, add the durable version under the owning Docs Viewer reference doc such as [Docs Viewer](/docs/?scope=studio&doc=docs-viewer), [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), or [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory), then link it here. |
| 2 | planned | Classify each lifecycle participant by responsibility and source of authority: browser route/config context, generated static asset, local generated-read service, browser storage, management backend capability endpoint, or management backend write endpoint. Deliverable: working lifecycle authority table in this tracker; if the table is intended as future-development reference, add the durable version under the owning Docs Viewer reference doc and link it here. |
| 3 | planned | Define lifecycle vocabulary and target owner rules. Name what `initialize`, `bind`, `update`, `unmount`, `close`, and `dispose` mean for controllers versus hosted views. If these terms become a lasting contract, document them in a durable Docs Viewer reference section and link that section here. |
| 4 | planned | Decide which controllers need explicit lifecycle phases and which should stay as stateless render/project helpers. Do not add lifecycle methods where they do not reduce coupling or clarify ownership. |
| 5 | planned | Define hosted-view context shape. Hosted views should receive explicit selected-document, route/access, state-domain, panel, and service inputs rather than broad runtime state or private controller handles. |
| 6 | planned | Define public-safe hosted-view limits. Public views must mount without management services, backend capability probes, write-capable service handles, management CSS/JS, or local-only data. |
| 7 | planned | Define manage-only hosted-view limits. Manage-only views may consume explicit management service/capability inputs, but visibility must not imply write authority and backend writes must remain server-validated. |
| 8 | planned | Update focused smoke coverage before behavior changes where practical. Tests should assert lifecycle ordering, repeated bind/update behavior, hosted-view mount/update/unmount/dispose behavior, public/manage access separation, and explicit context/service inputs without relying on broad runtime internals. |
| 9 | planned | Move or narrow top-level event binding only where ownership is clear. Keep route shell/runtime orchestration focused on app startup and handoff between focused owners. |
| 10 | planned | Refine controller lifecycle contracts only after caller inventory proves the new contract is smaller and clearer. Avoid broad controller rewrites in this slice. |
| 11 | planned | Refine hosted-view lifecycle contracts only if they support current info-panel behavior or a near-term documented view need. Do not create a speculative plugin platform. |
| 12 | planned | Preserve generated-data behavior: initial index load, document payload load, reload nonce behavior, generated-search reads, and local generated-read capability fallback must remain unchanged. |
| 13 | planned | Preserve config and route behavior: docs viewer config, scope config handoff, UI text, UI status values, recently-added limit, viewer options, route globals, URL history, and route normalization must remain unchanged. |
| 14 | planned | Preserve public hosted-view behavior: metadata info view, info-panel toggle/close, view switching, report links, document context projection, search/recent, and bookmarks must remain unchanged on `/library/` and `/analysis/`. |
| 15 | planned | Preserve management behavior: capability checks, import-open-on-load, metadata edit flow, settings, context menu, rebuilds, imports, scope lifecycle, status pills, and backend write authority must continue through existing management/service flow. |
| 16 | planned | Run management modal/service smoke checks if management lifecycle, lazy loading, generated reads, route state, status projection, import-open-on-load, or post-write reload behavior changes. |
| 17 | planned | Run public read-only checks if public startup, hosted-view lifecycle, document visibility, search/recent, bookmarks, reports, info panel, or public management omission changes. |
| 18 | planned | Review touched runtime files for new compatibility scaffolding. Deliverable: short cleanup note listing lifecycle fields/methods kept, fields/methods removed, replacement owner contracts, and any follow-up removal tasks. |
| 19 | planned | Update owning docs after implementation: this tracker, Docs Viewer Front-End App Architecture Request, Docs Viewer runtime boundary, Docs Viewer overview, Docs Viewer JavaScript inventory, service/config docs if contracts change, and portable files only if runtime copy sets change. Any lifecycle map, authority table, vocabulary, or owner contract that is meant to guide future development must be recorded in those durable docs rather than only in this task tracker. |
| 20 | planned | Create or update a structured docs-log entry when the implementation lands and record the entry id in this tracker. |

The closeout for this slice should confirm:

- controller and hosted-view lifecycle fields/methods are inventoried and classified
- lifecycle vocabulary is documented and matches the implementation
- static route/config facts, browser state, generated reads, local generated-read capability, and backend capability/write facts remain separate
- public-safe hosted views mount without management services, backend probes, local generated-read service base URLs, or write-capable service handles
- manage-only hosted views and management actions still get capability/write authority from the management/service flow
- generated-data reads still use generated-data runtime and service-context projection rather than direct endpoint calls from feature modules
- top-level event binding is owned by focused controllers where practical and not scattered across unrelated modules
- no new source editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
