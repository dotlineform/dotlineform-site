---
doc_id: site-request-docs-viewer-service-adapter-boundary-tasks
title: Docs Viewer Service Adapter Boundary Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: done
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14182
viewable: true
---
This document is archived and is no longer maintained.

---

# Docs Viewer Service Adapter Boundary Tasks

This is the second child task tracker for [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture).

The slice should define service-adapter boundaries for Docs Viewer generated/config/backend reads so controllers do not need ad hoc `fetch`, retry, capability, URL option, or management endpoint bundles.
It follows [Docs Viewer App Session State Domains Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-session-state-domains-tasks), which introduced `docs-viewer/runtime/js/docs-viewer-app-session.js`, named state domains, and the temporary compatibility state bridge.

This is structural frontend-app architecture work.
It should not add new source editor features, semantic-reference editing, visualization features, plugin architecture, route shell markup, generated payload schema changes, or backend write behavior.

## Status

Implemented 2026-05-28.

Structured docs-log entry:

- `change-2026-05-28-defined-docs-viewer-service-adapter-boundaries`

### inventory note

Current browser/service reads and writes were inventoried across the runtime:

- `docs-viewer-app-runtime.js`: app composition bridge; receives route config URLs, creates app/session/controllers, and now creates the public/manage service context.
- `docs-viewer-generated-data-runtime.js`: generated docs index, document payload, generated search, cross-scope docs index, references index, and reference-target reads. It owns reload nonce, expected-doc retry, static fallback, generated-read capability checks, and generated-search capability checks.
- `docs-viewer-config-controller.js`: browser-safe Docs Viewer config and UI text reads; it remains the config normalization and route-global handoff owner.
- `docs-viewer-route-workflow.js`: route and history workflow; it now asks the generated-data service for index and payload reads instead of assembling fetch/reload options itself.
- `docs-viewer-search-controller.js`: search/recent UI owner; it now asks the generated-data service for search-index reads.
- `docs-viewer-document-controller.js`: document pane and report-context owner; it now asks the generated-data service for cross-scope index/reference reads used by reports.
- `docs-viewer-reports.js`: browser-visible report registry read and allowlisted report module loading; it remains the report owner.
- `docs-viewer-management.js` and child controllers: local manage-mode orchestration; management capability checks and write actions remain behind the existing management client and backend endpoints.
- `docs-viewer-management-client.js`: management backend adapter for capability and write endpoints.
- Browser storage reads/writes remain in bookmark and panel-state owners; this slice did not move storage ownership.

### backend/service contract note

Current authority classification:

- Generated static asset: public docs index, payload JSON, search index, references index, and reference-target buckets when no generated-read service capability is available.
- Local generated-read service: `/docs/generated/index`, `/docs/generated/payload`, `/docs/generated/search`, `/docs/generated/references`, and `/docs/generated/reference-target` when local capability checks allow the read.
- Browser-safe config asset: Docs Viewer config, scope config records, UI text, and report registry JSON.
- Browser storage: bookmarks and panel state.
- Management backend capability endpoint: `/capabilities`, including per-scope generated-read and management availability truth.
- Management backend write endpoint: create/update/rebuild/archive/delete/viewability/move/order/source/settings/scope lifecycle endpoints in `docs-viewer-management-client.js`.

### implementation note

Moved in this slice:

- Added `docs-viewer/runtime/js/docs-viewer-service-context.js` to create an explicit public/manage service context. Public contexts drop management base URLs and generated-read service base URLs; manage contexts keep local generated-read and management backend base URLs separate from capability truth.
- Extended `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` with explicit read methods for docs index, document payload, search index, cross-scope docs index, references index, and reference-target JSON.
- Updated route workflow, search controller, and document controller to consume those generated-data read methods instead of assembling fetch/reload/capability options locally.

Kept with existing owners:

- Config reads remain in `docs-viewer-config-controller.js` because moving them would only wrap the same config normalization/handoff responsibility.
- Report registry reads remain in `docs-viewer-reports.js` because registry lookup, access checks, and allowlisted module loading are already one focused report responsibility.
- Management writes remain in `docs-viewer-management-client.js` and the management action controllers; no browser code gained write authority.
- Browser storage remains with bookmark and panel-state owners.

Compatibility scaffolding kept:

- `dataRequestOptions(...)` remains exported by `docs-viewer-generated-data-runtime.js` for existing config/UI-text compatibility and as an internal helper behind the generated-data read methods. Route workflow, search controller, and document controller no longer receive it as their generated-read contract.
- The broad app-session compatibility state bridge remains from the previous slice so this service-boundary work does not become a broad controller rewrite.

Verification run:

- `node --check docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`
- `node --check docs-viewer/runtime/js/docs-viewer-service-context.js`
- `node --check docs-viewer/runtime/js/docs-viewer-route-workflow.js`
- `node --check docs-viewer/runtime/js/docs-viewer-search-controller.js`
- `node --check docs-viewer/runtime/js/docs-viewer-document-controller.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`

### steer for this task

- Treat this as the service-boundary slice, not a broad controller rewrite.
- Inventory current browser reads, local generated-read service reads, config reads, report registry reads, and management backend reads before creating adapters.
- Keep `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` as the generated-read owner where it already has the right responsibility.
- Introduce a viewer config service only if it removes real config handoff coupling rather than moving the same broad controller state behind another name.
- Introduce a management service adapter only if it narrows management context shape while preserving existing backend endpoint authority and validation.
- Preserve current `/docs/`, `/library/`, and `/analysis/` behavior.
- Public read-only routes must not gain backend service requirements, management-only JavaScript, management base URLs, or backend capability probes.
- Local manage mode must continue to get backend capability checks and write authority through the existing management/service flow.
- Do not make route config imply backend capability. Static route/app context and backend capability truth remain separate.
- Prefer direct browser reads for browser-safe static assets; do not add local server read endpoints merely to preserve a frontend module boundary.

### backend co-evolution steer

Classify every proposed service adapter by source of authority:

- generated static asset
- local generated-read service
- browser-safe config asset
- browser storage
- management backend capability endpoint
- management backend write endpoint

Do not introduce an adapter that hides unclear backend ownership.
If an endpoint shape is awkward because of old compatibility needs, name the backend cleanup task instead of baking that awkward shape into the app contract.
Management writes must remain behind named backend endpoints with server-side validation.

### likely service surfaces to inventory

Use the inventory to validate or revise these candidate adapter surfaces:

- generated docs index reads: scope index JSON, reload options, non-loadable/manage-only/viewability projection inputs
- generated document payload reads: by-id payload JSON, retry and reload behavior
- generated search reads: search index JSON, generated-search read capability behavior
- viewer config reads: docs viewer config, scope config records, viewer options, UI status values, recently-added limits
- UI text reads: UI text config, management text overrides, import/settings/status copy
- report registry reads: browser-visible report metadata and access defaults
- management capability reads: management availability, generated-data read capability, scope capability records
- management backend reads/writes: metadata, settings, import, rebuild, scope lifecycle, archive/delete/viewability/order actions
- browser storage reads/writes: bookmarks and panel-state persistence; inventory only unless this slice finds a real service-boundary issue

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-session.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`
  - any new or changed service-adapter modules
  - any existing owner modules whose public contract changes
- Focused module smoke coverage when service ownership moves:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for adapter creation, static-read fallback, generated-read service options, capability separation, and public/manage service context separation where practical
- Management route checks when management capabilities, generated reads, config handoff, management context, settings, imports, rebuilds, scope lifecycle, or write service contracts change:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when public service context, generated reads, document visibility, search/recent, report registry reads, config reads, or management omission changes:
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
| 1 | done | Inventory current browser/service reads in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`, `docs-viewer-generated-data-runtime.js`, `docs-viewer-config-controller.js`, `docs-viewer-route-workflow.js`, `docs-viewer-search-controller.js`, `docs-viewer-document-controller.js`, `docs-viewer-reports.js`, `docs-viewer-management.js`, and `docs-viewer-management-client.js`. Deliverable: short inventory note in this tracker. |
| 2 | done | Classify each current read/write path by source of authority: generated static asset, local generated-read service, browser-safe config asset, browser storage, management backend capability endpoint, or management backend write endpoint. Deliverable: backend/service contract note in this tracker. |
| 3 | done | Decide which service adapters move in this slice and which remain with existing owners. Do not move a service surface unless it reduces coupling, clarifies authority, narrows controller inputs, or creates a useful facade for the next app-composition slice. |
| 4 | done | Define target owner names and exported contracts. Prefer extending `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js` for generated docs/search/payload reads where appropriate; introduce new modules only for distinct config/report/management service responsibilities. |
| 5 | done | Define public/manage service-context separation. Public contexts must use static generated/config/report assets only and must not receive management base URLs, backend probes, or management-only service adapters. |
| 6 | done | Define manage-mode service-context separation. Manage contexts may use local generated-read and management capability endpoints, but backend write authority must remain with existing management backend endpoints and server-side validation. |
| 7 | done | Implement adapter creation and context handoff for the selected service surfaces. Preserve existing request behavior, retry/reload semantics, capability checks, and object identity where current controllers still require compatibility inputs. |
| 8 | done | Narrow controller inputs only where the adapter contract is explicit and the affected controller remains readable. Do not perform broad controller rewrites in this service-boundary slice. |
| 9 | done | Preserve generated-data behavior: initial index load, document payload load, reload nonce behavior, generated-search reads, and local generated-read capability fallback must remain unchanged. |
| 10 | done | Preserve config behavior: docs viewer config, scope config handoff, UI text, UI status values, recently-added limit, viewer options, and route-global updates must remain unchanged. |
| 11 | done | Preserve report behavior: report registry reads, report access checks, report module allowlist, and report route/query state must remain unchanged. |
| 12 | done | Preserve management behavior: capability checks, import-open-on-load, metadata edit flow, settings, context menu, rebuilds, imports, scope lifecycle, status pills, and backend write authority must continue through existing management/service flow. |
| 13 | done | Add or extend focused smoke coverage for adapter contracts. Cover static fallback, generated-read service options, capability separation, public/manage service context separation, and any narrowed controller input contract where practical. |
| 14 | done | Run management modal/service smoke checks if management capabilities, generated reads, config handoff, management context, settings, imports, rebuilds, scope lifecycle, or write service contracts change. |
| 15 | done | Run public read-only checks if public service context, generated reads, document visibility, search/recent, report registry reads, config reads, or public management omission changes. |
| 16 | done | Review touched runtime files for new compatibility scaffolding. Deliverable: short cleanup note listing temporary adapters/bridges kept, adapters/bridges removed, and why any bridge is acceptable. |
| 17 | done | Update owning docs after implementation: this tracker, Docs Viewer Front-End App Architecture Request, Docs Viewer runtime boundary, Docs Viewer overview, Docs Viewer JavaScript inventory, service/config/script docs if contracts change, and portable files only if runtime copy sets change. |
| 18 | done | Create or update a structured docs-log entry when the implementation lands and record the entry id in this tracker. |

The closeout for this slice should confirm:

- service-adapter ownership is defined and documented
- every moved adapter names its source of authority
- public/static reads remain backend-free
- generated-read service fallback and capability semantics remain explicit
- management capability state is not treated as generic browser state or write authority
- management writes remain behind backend endpoints with server-side validation
- no new feature-specific panel, editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
- public read-only routes still avoid management-only shell markup, CSS, JavaScript, management base URLs, and backend capability probes
- local manage mode still gets backend capability checks and write authority from the management/service flow
