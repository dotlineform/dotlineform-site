---
doc_id: site-request-docs-viewer-app-session-state-domains-tasks
title: Docs Viewer App Session State Domains Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: done
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14181
viewable: true
---
# Docs Viewer App Session State Domains Tasks

This is the first child task tracker for [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture).

The slice should define the app-session/state-domain shape that lets Docs Viewer move away from one broad `state` object in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`.
It should make state ownership explicit before later slices tackle service adapters, app composition, runtime API shrinkage, public/manage app contexts, and lifecycle cleanup.

This is structural architecture work.
It should not add source editor features, semantic-reference editing, new visualization features, plugin architecture, route shell markup, generated payload schema changes, or backend write behavior.

## Status

### steer for this task

- Treat this as the first frontend-app architecture slice, not as another cosmetic helper split.
- Define app-session and state-domain contracts before moving code.
- Preserve current `/docs/`, `/library/`, and `/analysis/` behavior.
- Keep public read-only routes first-class and free of management-only assets, management base URLs, and backend capability probes.
- Keep local manage mode first-class and preserve backend authority for writes, imports, settings, scope lifecycle, rebuilds, source opening, and local-only data.
- Keep existing focused owners intact unless this slice defines a clearly better ownership boundary.
- Prefer facades or domain objects that reduce broad state access for real owners; do not wrap the same broad state object behind a new name unless there is a concrete removal path.
- Keep route/document workflow in `docs-viewer-route-workflow.js`, generated-data request shaping in `docs-viewer-generated-data-runtime.js`, document visibility/loadability projection in `docs-viewer-document-index-state.js`, info-panel coordination in `docs-viewer-info-panel-controller.js`, and lazy management loading in `docs-viewer-runtime-lazy-controller.js`.

### backend co-evolution steer

This slice must classify each proposed state domain by source of authority:

- browser-only state
- generated static data
- local generated-read service data
- browser storage
- management backend capability state
- management backend write state

Do not move backend-derived management capability state into generic browser state in a way that makes client visibility look like write authority.
If a state domain exposes backend-managed facts, the task must name the backend/service contract and preserve server-side enforcement.

### likely state domains to inventory

Use the inventory to validate or revise these candidate domains:

- route/session context: route config, current route globals, access projection, requested mode/import intent, bookmark scope
- scope/config context: docs viewer config, scope configs, UI text/status config, viewer options
- document index: all docs, visible docs, doc maps, children maps, non-loadable ids, manage-only roots, hidden/viewable projection
- selected document: selected doc id, payload cache, current payload/load state, selected-document context for hosted views
- search/recent: search index entries, query, loaded state, request promise, debounce id, result count, route/recent modes
- bookmarks: bookmark support, loaded state, records, editing state, pending focus
- panel/view state: index panel state, document/search/recent projection, info-panel open/view state, hosted-view registry
- management state: mode, availability, busy state, capabilities, messages, status ownership, metadata edit state, status menu state
- busy/status state: pending busy count, root `aria-busy`, viewer status text/error state, results status projection

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - any new or changed app-session/state-domain modules
  - any existing owner modules whose public contract changes
- Focused module smoke coverage when state/domain ownership moves:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for app-session creation, state-domain shape, state-domain facade behavior, public/manage context separation, and any narrowed controller inputs where practical
- Management route checks when management state, capability state, generated reads, config handoff, status projection, info panel, route state, or initial load sequencing changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when public app context, generated reads, document visibility, panel/info projection, search/recent, bookmarks, reports, or management omission changes:
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
| 1 | done | Inventory the current broad runtime `state` object in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`. Group each field into a candidate state domain and record which controllers/modules read or mutate it. Deliverable: short inventory note in this tracker. |
| 2 | done | Classify each candidate state domain by source of authority: browser-only, generated static data, local generated-read service, browser storage, management backend capability, or management backend write flow. Deliverable: backend/service contract note in this tracker. |
| 3 | done | Define the target app-session owner name and exported contract. Prefer `docs-viewer/runtime/js/docs-viewer-app-session.js` unless inventory shows a better name. The contract should create named domains without forcing every controller to change in one slice. |
| 4 | done | Decide which state domains move in this first slice and which remain temporarily bridged through the existing broad state object. Avoid moving a domain unless it reduces broad state access, clarifies authority, or creates a useful facade for a later slice. |
| 5 | done | Define compatibility limits for any temporary bridge. Name what remains in `docs-viewer-app-runtime.js`, why it remains, which child slice should remove it, and what tests guard the current boundary. |
| 6 | done | Implement app-session/state-domain creation only after the inventory and target contract are clear. Preserve existing object identity where controllers still require it; do not break route/search/bookmark/document/management owners in the same slice. |
| 7 | done | Move state defaults into the app-session owner where that is safe. Keep constants and text config in their existing owning config/text modules unless the inventory shows a clear state-domain reason to move them. |
| 8 | done | Narrow controller inputs only where the state domain provides an explicit facade and the affected controller contract remains readable. Do not perform broad controller rewrites in this first slice. |
| 9 | done | Preserve public read-only behavior: route boot, document rendering, search/recent, bookmarks, reports, metadata info, and management omission must remain unchanged. Public routes must not gain backend capability probes or management-only assets. |
| 10 | done | Preserve manage-mode behavior: generated-data reads, management capability checks, import-open-on-load, metadata edit flow, context menu, reports, bookmarks, info panel, search/recent, status pills, route history, and backend write authority must continue through the existing management/service flow. |
| 11 | done | Add or extend focused smoke coverage for app-session/state-domain contracts. Cover creation, public/manage context separation, state-domain defaults, and any narrowed controller input contract where practical. |
| 12 | done | Run management modal/service smoke checks if management state, capability state, generated reads, config handoff, status projection, info panel, route state, or initial load sequencing changes. |
| 13 | done | Run public read-only checks if public app context, generated reads, document visibility, panel/info projection, search/recent, bookmarks, reports, or public omission changes. |
| 14 | done | Review touched runtime files for new compatibility scaffolding. Deliverable: short cleanup note listing temporary bridges kept, bridges removed, and why any bridge is acceptable. |
| 15 | done | Update owning docs after implementation: this tracker, Docs Viewer Front-End App Architecture Request, Docs Viewer runtime boundary, Docs Viewer overview, Docs Viewer JavaScript inventory, and portable files only if runtime copy sets change. |
| 16 | done | Create or update a structured docs-log entry when the implementation lands and record the entry id in this tracker. |

## Implementation Notes

### State Inventory

`docs-viewer/runtime/js/docs-viewer-app-session.js` now owns app-session creation and the state defaults previously inline in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`.
The session creates the existing broad compatibility state object plus named domain facades.
The facades expose only their declared fields through `get`, `set`, direct property accessors, and `snapshot`; unknown-field writes are rejected so a domain cannot mutate unrelated state accidentally.

Current domain grouping:

| domain | fields | current readers/mutators |
| --- | --- | --- |
| route/session | route context and access projection, not broad state fields | `docs-viewer-app-runtime.js`, `docs-viewer-app-context.js`, route config/access helpers, config route-global handoff |
| scope/config | docs viewer config load flags/promises, scope configs/maps, default scope, viewer config flags/promises, UI statuses, recent limit, show-updated option, management text | config controller, document controller, management context, document-index status projection, sidebar metadata |
| document index | all docs/maps, visible docs/maps, children map, expanded ids, hidden/manage-only/loadability sets, show-hidden/show-updated flags, status map | route workflow, document-index state owner, sidebar renderer, search controller, bookmark controller, document controller, info-panel controller |
| selected document | selected doc id, payload cache, request id, reload nonce and expected doc id | route workflow, document controller, info panel, bookmarks, generated-data runtime |
| search/recent | search index entries, load flag/promise, query, visible count, debounce id, search-route flag, recent-mode flag, recent limit | search controller, route workflow, bookmarks, document controller, runtime debounce/recent helpers |
| bookmarks | bookmark records, load/support flags, edit/focus keys | bookmark controller and selected-document bookmark UI |
| panel/view | index panel state, hosted-view registry, projected view state, expanded ids | panel layout, sidebar renderer, info-panel controller, hosted-view modules |
| management | mode, availability/check/busy/capability flags, capability check id, messages, status ownership, metadata edit focus, status menu, management text | lazy management context, generated-data runtime, management controller, sidebar/status-pill rendering, route workflow |
| generated data | generated-read capability flags/promise, management capabilities, reload nonce and expected doc id | generated-data runtime, route workflow, document controller, search controller |
| busy/status | pending busy count, management status/message ownership | runtime busy/status helpers, management controller status handoff |

### Authority Classification

- Route/session context is browser URL plus browser-safe route-config authority. It can project public/manage intent, but it is not backend write authority.
- Scope/config and document-index state are generated static data by default. In local manage mode, generated docs/search reads may come through the local generated-read service when capability checks allow it.
- Selected-document payload state and search/recent state are generated static data or local generated-read service data plus browser-only transient state such as current query and debounce.
- Bookmark state is browser storage authority through IndexedDB and remains local to the browser.
- Panel/view and busy/status state are browser-only UI state.
- Management state combines browser UI state with management backend capability and write-flow state. Visibility or mode flags do not grant write authority; backend endpoints and server-side validation remain the source of truth.
- Generated-data capability state is local generated-read service state. It may cache backend-advertised capabilities but does not grant write authority.

### App-Session Contract

The target owner is `docs-viewer/runtime/js/docs-viewer-app-session.js`.
It exports `createDocsViewerAppSession(options)`, returning:

- `state`: the existing compatibility state object consumed by current controllers
- `domains`: named domain facades for route/session, scope/config, document index, selected document, search/recent, bookmarks, panel/view, management, generated data, and busy/status
- `compatibilityBridge`: a named bridge containing the same state object and the reason it remains

`docs-viewer/runtime/js/docs-viewer-app-runtime.js` now imports this owner, creates the session after route context, hosted views, and panel layout exist, passes `appSession.state` into existing controllers, updates `domains.routeSession` when route globals change, and returns `appSession` from the runtime API.

### First-Slice Move And Bridge Limits

Moved in this slice:

- broad state default construction
- management text defaults that were already broad runtime state defaults
- hosted-view, index-panel, and view-state default handoff
- public/manage route-session projection into an explicit domain
- focused smoke coverage for domain names, authority strings, defaults, facade mutation, route-session updates, and compatibility state identity

Kept as temporary compatibility bridge:

- existing controller inputs still receive the broad `state` object
- `docs-viewer-app-runtime.js` still coordinates controller construction, event binding, initial load sequencing, config handoff, and the returned compatibility API
- management/backend capability state remains in the shared state object because management, generated-data reads, and status projection still share those fields

The bridge is acceptable for this slice because every existing focused owner keeps object identity and behavior while new work can target named domains.
The next child slice should narrow one complete controller family to domain inputs, starting with a low-risk family such as busy/status or search/recent, and should remove that family's broad-state dependency from the runtime handoff once the controller contract is clear.

No source editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added.

### Verification

- `node --check docs-viewer/runtime/js/docs-viewer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-session.js`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`

Structured docs-log entry:

- `change-2026-05-28-docs-viewer-app-session-state-domains`

The closeout for this slice should confirm:

- app-session/state-domain ownership is defined and documented
- broad state access is reduced or clearly bounded by named temporary bridges
- backend/service authority for each moved domain is explicit
- no new feature-specific panel, editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
- public read-only routes still avoid management-only shell markup, CSS, JavaScript, management base URLs, and backend capability probes
- local manage mode still gets backend capability checks and write authority from the management/service flow
- metadata edit, import, settings, context menu, management actions, generated-data reads, reports, bookmarks, info panel, search/recent, status pills, and route history still work
