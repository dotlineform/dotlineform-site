---
doc_id: site-request-docs-viewer-controller-view-lifecycle-tasks
title: Docs Viewer Controller And View Lifecycle Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: done
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

Completed 2026-05-28 as a lifecycle clarification and owner-contract documentation slice.

Runtime behavior was not changed in this slice.
The inventory found that the current owners already expose the practical lifecycle needed for the near-term Docs Viewer app architecture:

- `docs-viewer-app-composition.js` owns startup phase sequencing and startup authority records.
- `docs-viewer-app-session.js` owns state-domain facades and the temporary broad-state compatibility bridge.
- `docs-viewer-route-workflow.js`, `docs-viewer-search-controller.js`, `docs-viewer-bookmarks.js`, and `docs-viewer-info-panel-controller.js` own focused event binding or update handoff for their route/controller surfaces.
- `docs-viewer-info-panel-host.js`, `docs-viewer-hosted-views.js`, `docs-viewer-view-context.js`, and `docs-viewer-metadata-info-view.js` already provide the hosted-view lifecycle model for current info-panel behavior.
- Management lifecycle remains behind the lazy management controller, management capability controller, management client, and management action/modal/interactions modules.

Durable lifecycle guidance was copied to [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview), and [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory).

Structured docs-log entry: `change-2026-05-28-documented-docs-viewer-controller-and-hosted-view-lifecycle`.

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

## Working Lifecycle Map

This map is the implementation inventory for this task.
The durable owner rules live in [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).

| Owner | Current lifecycle role | Authority source | Decision |
| --- | --- | --- | --- |
| `docs-viewer-app-runtime.js` | Creates focused controllers, assembles callback bridges, defines top-level document/header handlers, and hands startup phases to composition. | Browser route/config context plus focused owner callbacks. | Keep as compatibility coordinator for now; do not add new feature lifecycle ownership here. |
| `docs-viewer-app-composition.js` | Creates foundational owners and runs `bind -> load config -> initialize optional contexts -> load index -> open import` startup sequencing. | Browser route/config context, browser-safe config assets, generated reads, browser storage, management capability/write endpoints in manage context. | Keep startup sequencing and authority records here. Controller-specific behavior stays outside it. |
| `docs-viewer-app-session.js` | Creates broad compatibility state plus named state domains. | Mixed by domain: route/config, generated data, browser storage, browser-only UI state, management backend flow. | Keep the compatibility bridge explicit until controller families are narrowed to domain inputs. |
| `docs-viewer-route-workflow.js` | Owns URL helpers, route application, route-link binding, popstate binding, index load handoff, and document payload load handoff. | Browser URL/history and generated static/local generated-read data. | Keep route/document workflow here; do not return route bridges on the public app handle. |
| `docs-viewer-search-controller.js` | Owns search/recent binding, generated search-index reads, debounce, result/recent rendering, and route callback consumption. | Generated static asset or local generated-read service plus browser query state. | Keep `bind` and render methods; no additional lifecycle methods needed. |
| `docs-viewer-bookmarks.js` | Owns bookmark storage initialization, bookmark binding, list/toggle rendering, and document-load callback consumption. | Browser storage plus route workflow callback handoff. | Keep `initialize`, `bind`, and render methods; no disposal needed for current route lifetime. |
| `docs-viewer-info-panel-controller.js` | Owns selected-document context projection, info toggle/toolbar binding, host open/close/update handoff, and toggle state projection. | Browser route/access context, selected-document state, generated payload cache, panel layout projection. | Keep as the info-panel controller; future info views should use its explicit context path rather than broad runtime state. |
| `docs-viewer-info-panel-host.js` | Owns info hosted-view resolution, load, mount, update, unmount, close, dispose, option projection, and graceful absence. | Hosted-view registry plus explicit context passed by the controller. | Keep as the concrete hosted-view lifecycle model; do not expand into a plugin platform. |
| `docs-viewer-hosted-views.js` | Owns hosted-view record shape, access/availability checks, panel-specific listing, compatibility records, and lifecycle method defaults. | Static route access projection. | Keep registration shape minimal and repo-local. Availability or visibility does not create backend authority. |
| `docs-viewer-view-context.js` | Projects selected-document hosted-view context. | Selected-doc state, payload cache, route access, viewer URL helpers, UI status config. | Keep context explicit; extend this or create a sibling view-model helper before any future view reads broad state. |
| `docs-viewer-metadata-info-view.js` | Renders the public-safe metadata hosted view through `mount`, `update`, `unmount`, and `dispose`. | Explicit hosted-view context only. | Keep public-safe and read-only; no source paths, write handles, or backend calls. |
| `docs-viewer-management.js` and child modules | Lazily loaded manage-mode controller; binds management UI, initializes capability checks, coordinates actions, modals, imports, settings, scope lifecycle, status pills, and write flows. | Management backend capability endpoint and management backend write endpoints, with generated-read fallback where advertised. | Keep management authority here and in `docs-viewer-management-client.js`; hosted views must not infer write authority from visibility. |

## Lifecycle Authority Table

| Participant | Responsibility | Authority classification |
| --- | --- | --- |
| Route boot and app shell refs | Root discovery, route-config resolution, shell creation, and ref handoff. | Browser route/config context. |
| App composition startup records | Public/manage startup phase descriptions and initial startup orchestration. | Browser route/config context plus phase-specific authorities. |
| Config controller | Docs Viewer config, UI text, scope config handoff, route globals. | Browser-safe config assets. |
| Generated data runtime | Docs index, document payload, search index, references, retry/reload reads. | Generated static assets or local generated-read service. |
| Route workflow | URL normalization, history, route application, index/payload workflow handoff. | Browser URL/history plus generated data runtime. |
| Search/recent controller | Search query state, generated search reads, recent list rendering. | Generated static asset or local generated-read service plus browser-only query state. |
| Bookmark controller | Bookmark persistence, rename/edit state, bookmark route handoff. | Browser storage. |
| Info-panel controller and host | Info-panel visibility, selected-doc context, hosted-view lifecycle. | Browser route/access context plus generated selected-doc/payload state. |
| Public metadata hosted view | Read-only metadata presentation. | Explicit public-safe hosted-view context. |
| Management capability controller | Capability refresh, generated-read capability flag, management availability. | Management backend capability endpoint. |
| Management action/modal/interactions controllers | Metadata writes, rebuilds, imports, settings, source opening, scope lifecycle, drag/drop. | Management backend write endpoints with server-side validation. |

## Lifecycle Vocabulary And Owner Rules

Controllers:

- `create`: assemble a controller and capture explicit refs, callbacks, state-domain inputs, services, and config values.
- `initialize`: perform asynchronous or stateful startup that should not happen at construction time, such as loading bookmarks or checking management backend capabilities.
- `bind`: attach DOM/window event listeners for the controller's owned surface. Bind should be called once during app startup.
- `update` or `project`: re-render or project current state after selected document, route state, panel state, or capability state changes.
- `dispose`: optional cleanup for controllers with independent lifetime or external subscriptions. Current route-lifetime controllers do not need it unless they start owning detachable listeners, timers, workers, observers, or hosted resources.

Hosted views:

- `load`: optional lazy module load or factory step. The registry record may return lifecycle methods directly or via `load`.
- `mount`: render into an explicit mount element from an explicit hosted-view context.
- `update`: refresh the mounted view from a new explicit context without re-registering the view.
- `unmount`: clear the active mounted view when switching or closing the panel.
- `close`: host action that marks the panel closed and unmounts the active view.
- `dispose`: final cleanup for the active view if the host itself is discarded.

Owner rules:

- Use lifecycle methods only where they reduce coupling or clarify phase ownership.
- Keep stateless render/project helpers as stateless helpers.
- Public-safe hosted views must mount without management services, backend probes, local generated-read service base URLs, write-capable service handles, or management CSS/JS.
- Manage-only hosted views may receive explicit management service or capability inputs, but visibility and registration do not imply write authority.
- Backend writes remain behind named management endpoints and server-side validation.
- Future feature views should attach through panel/controller contracts and explicit context or service inputs, not by modifying route shell markup or reading broad runtime state.

## Implementation Decisions

- No top-level event binding was moved in this slice. Existing binding already sits with route workflow, search, bookmarks, info-panel controller, and lazy management controller where practical.
- No controller lifecycle method was added. Current `initialize`/`bind`/`update` phases are clearer than adding a uniform lifecycle interface to stateless helpers.
- No hosted-view lifecycle method was added. `load`, `mount`, `update`, `unmount`, `close`, and `dispose` already cover the current info-panel model.
- Generated-data behavior, route/config behavior, public hosted-view behavior, and management behavior were intentionally preserved.
- Existing focused smoke coverage already asserts startup phase order, public/manage access separation, app-session domains, hosted-view context shape, hosted-view registry access states, info-panel lifecycle order, and the management lazy adapter contract.

## Cleanup Note

Compatibility scaffolding kept:

- `docs-viewer-app-runtime.js` remains the compatibility coordinator for focused controller construction, callback handoff, route-global updates, private management startup callbacks, and the intentionally small returned app handle.
- `docs-viewer-app-session.js` keeps `compatibilityBridge.state` because existing controllers still consume the broad state object.
- Route workflow callbacks, search/bookmark route callback bundles, and management runtime adapter callbacks remain private handoffs until a later slice narrows complete controller families to domain and service inputs.

No compatibility fields or lifecycle methods were removed in this slice because no runtime behavior changed.
No new compatibility scaffold was added.

Follow-up:

- When a future feature needs an info-panel view, first decide whether it is public metadata, manage metadata, local diagnostics, semantic/reference info, or another separately-shaped view contract.
- When a future controller change touches broad state, narrow one complete controller family to explicit state-domain and service inputs rather than adding another route-runtime callback.

## Verification

Docs/source verification for this documentation-only slice:

- reviewed the current runtime modules and focused app-shell smoke coverage listed in the inventory targets
- updated this tracker and durable Docs Viewer reference docs
- created structured docs-log entry `change-2026-05-28-documented-docs-viewer-controller-and-hosted-view-lifecycle`
- no Docs Viewer generated payload rebuild was run; if the docs watcher is active it may update generated payloads separately

Commands run:

- `node --check` for the inventoried runtime modules
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `$HOME/miniconda3/bin/python3 -m json.tool studio/workflows/change-requests/logs/entries/change-2026-05-28-documented-docs-viewer-controller-and-hosted-view-lifecycle.json`
- `$HOME/miniconda3/bin/python3 studio/workflows/change-requests/services/docs_logs/build_indexes.py --write`
- `git diff --check`

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory current controller and hosted-view lifecycle behavior across app runtime, app composition, app session, route workflow, search, bookmarks, info panel, hosted views, metadata info view, management modules, smoke tests, and docs. Deliverable recorded in Working Lifecycle Map and durable Docs Viewer reference docs. |
| 2 | done | Classify each lifecycle participant by responsibility and source of authority. Deliverable recorded in Lifecycle Authority Table and durable Docs Viewer reference docs. |
| 3 | done | Define lifecycle vocabulary and target owner rules for controllers and hosted views. Durable contract recorded in Docs Viewer Runtime Boundary and summarized in Docs Viewer Overview. |
| 4 | done | Decide which controllers need explicit lifecycle phases. Current route-lifetime controllers keep existing `initialize`, `bind`, and `update` methods where useful; stateless helpers stay stateless. |
| 5 | done | Define hosted-view context shape. Current context uses explicit selected-document, route/access, payload, viewer-scope, URL, trail, and status-label inputs. Future service inputs must be explicit. |
| 6 | done | Define public-safe hosted-view limits. Public views mount without management services, backend probes, local generated-read base URLs, write-capable handles, or management assets. |
| 7 | done | Define manage-only hosted-view limits. Manage-only views may consume explicit management service/capability inputs, but write authority remains server-enforced. |
| 8 | done | Reviewed focused smoke coverage. Existing smoke coverage already pins lifecycle order, repeated update/close behavior, hosted-view mount/update/unmount, public/manage access separation, explicit hosted-view context, app-session domains, and lazy management adapter contracts. |
| 9 | done | Reviewed top-level event binding. No move was warranted in this slice; clear owners already bind route links/popstate, search/recent, bookmarks, info-panel controls, and lazy management interactions. |
| 10 | done | Reviewed controller lifecycle contracts. No broad controller rewrite was warranted. |
| 11 | done | Reviewed hosted-view lifecycle contracts. Current info-panel host lifecycle supports the concrete model without creating a plugin platform. |
| 12 | done | Preserved generated-data behavior; no runtime code changed. |
| 13 | done | Preserved config and route behavior; no runtime code changed. |
| 14 | done | Preserved public hosted-view behavior; no runtime code changed. |
| 15 | done | Preserved management behavior and backend write authority; no runtime code changed. |
| 16 | done | Management modal/service smokes were not required because management lifecycle/runtime behavior did not change. |
| 17 | done | Public read-only smokes were not required because public startup/runtime behavior did not change. |
| 18 | done | Cleanup note recorded. No new compatibility scaffolding was added; existing compatibility bridge and private callback handoffs remain explicit follow-up targets. |
| 19 | done | Updated this tracker, parent request, Docs Viewer Runtime Boundary, Docs Viewer Overview, and Docs Viewer JavaScript Inventory. No service/config or portable copy-set docs changed because no contracts or copy sets changed. |
| 20 | done | Created structured docs-log entry `change-2026-05-28-documented-docs-viewer-controller-and-hosted-view-lifecycle`. |

The closeout for this slice should confirm:

- controller and hosted-view lifecycle fields/methods are inventoried and classified
- lifecycle vocabulary is documented and matches the implementation
- static route/config facts, browser state, generated reads, local generated-read capability, and backend capability/write facts remain separate
- public-safe hosted views mount without management services, backend probes, local generated-read service base URLs, or write-capable service handles
- manage-only hosted views and management actions still get capability/write authority from the management/service flow
- generated-data reads still use generated-data runtime and service-context projection rather than direct endpoint calls from feature modules
- top-level event binding is owned by focused controllers where practical and not scattered across unrelated modules
- no new source editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
