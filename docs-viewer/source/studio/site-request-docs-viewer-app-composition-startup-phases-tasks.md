---
doc_id: site-request-docs-viewer-app-composition-startup-phases-tasks
title: Docs Viewer App Composition And Startup Phases Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: planned
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14183
viewable: true
---
# Docs Viewer App Composition And Startup Phases Tasks

This is the third child task tracker for [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture).

The slice should replace broad inline controller construction in `docs-viewer/runtime/js/docs-viewer-app-runtime.js` with an app-composition owner that wires the app session, service context, focused controllers, and startup lifecycle phases.
It follows [Docs Viewer Service Adapter Boundary Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-service-adapter-boundary-tasks), which introduced explicit service-context projection and named generated-data read methods.

This is structural frontend-app architecture work.
It should not add source editor features, semantic-reference editing, visualization features, plugin architecture, route shell markup, generated payload schema changes, or backend write behavior.

## Status

### steer for this task

- Treat this as the app-composition/startup slice, not as a broad controller rewrite.
- Inventory current startup order before creating a composition owner.
- Preserve current `/docs/`, `/library/`, and `/analysis/` behavior.
- Keep `docs-viewer-app-runtime.js` as the public `startDocsViewerRuntime(...)` compatibility entry unless this slice proves a smaller app handle is safe.
- Prefer a composition owner only if it makes lifecycle phases, controller construction order, service handoff, and public/manage startup separation clearer.
- Keep focused owners intact: route workflow, config controller, generated-data runtime, service context, document-index state, search controller, bookmark controller, document controller, info-panel controller, panel layout, and lazy management runtime.
- Public read-only startup must not gain management base URLs, backend capability probes, management-only JavaScript, or import-open-on-load behavior.
- Manage startup may initialize lazy management and capability checks only through the existing management/service flow.
- Do not let route config or query flags imply backend capability or write authority.

### backend co-evolution steer

Classify every startup phase by source of authority:

- browser route/config context
- browser-safe config asset
- generated static asset
- local generated-read service
- browser storage
- management backend capability endpoint
- management backend write endpoint

The composition owner may sequence backend-dependent startup, but it must not become a backend client or grant write authority.
Management writes must remain behind named backend endpoints with server-side validation.
If startup timing depends on retry behavior or backend availability that is not a clean contract, document the current dependency and create a cleanup task rather than hiding it behind composition.

### likely startup phases to inventory

Use the inventory to validate or revise these candidate phases:

- root/app-shell input validation
- app session creation
- service-context creation
- generated-data runtime creation
- document-index state creation
- panel layout and hosted-view registry creation
- controller construction
- lazy management runtime adapter construction
- event binding
- config load and route-global application
- viewer config/UI text load
- bookmark initialization
- management initialization and capability checks in manage context
- initial index load and current route application
- import-open-on-load in manage context
- runtime API/app handle return

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-session.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-service-context.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`
  - any new or changed app-composition modules
  - any focused owner modules whose public contract changes
- Focused module smoke coverage when app composition or startup sequencing moves:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for composition creation, controller construction order, public/manage startup phase separation, import-open-on-load gating, and returned app handle compatibility where practical
- Management route checks when management initialization, generated reads, config handoff, capability checks, status projection, import-open-on-load, route state, or initial load sequencing changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when public startup context, generated reads, document visibility, search/recent, bookmarks, reports, info panel, route normalization, or management omission changes:
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
| 1 | planned | Inventory current startup and controller construction in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`, including session/service/controller creation, event binding, config loading, bookmark initialization, management initialization, index load, import-open-on-load, and returned runtime API. Deliverable: short startup-order note in this tracker. |
| 2 | planned | Classify each startup phase by source of authority: browser route/config context, browser-safe config asset, generated static asset, local generated-read service, browser storage, management backend capability endpoint, or management backend write endpoint. Deliverable: backend/service startup contract note in this tracker. |
| 3 | planned | Decide whether this slice should introduce `docs-viewer/runtime/js/docs-viewer-app-composition.js` or keep composition in `docs-viewer-app-runtime.js` with a smaller extracted helper. Do not create a composition owner unless it reduces real coupling and clarifies lifecycle phases. |
| 4 | planned | Define target owner names and exported contracts. The composition contract should accept boot/runtime inputs, create or receive session/services/controllers, expose explicit startup phases, and preserve the current runtime API compatibility where still needed. |
| 5 | planned | Define public startup phases. Public contexts must create static generated/config/report services, bind public controllers, initialize bookmarks, load config/index/route, and omit management backend probes, management controller imports, management base URLs, and import-open-on-load. |
| 6 | planned | Define manage startup phases. Manage contexts may construct the lazy management runtime, initialize backend capability checks after route/config context is ready, and handle import-open-on-load only when management mode is active and route access allows it. |
| 7 | planned | Implement the selected app-composition/startup owner and handoff. Preserve controller object identity and callback contracts where existing owners still require compatibility inputs. |
| 8 | planned | Move startup phase sequencing only where the new owner makes order explicit. Do not move rendering, validation, generated-read internals, config normalization, bookmark storage, management writes, or report behavior into the composition owner. |
| 9 | planned | Preserve initial load behavior: config load, route-global updates, viewer config/UI text load, initial index load, default/current document resolution, search route handling, recent/bookmark state, and route history behavior must remain unchanged. |
| 10 | planned | Preserve public read-only behavior: `/library/` and `/analysis/` must stay backend-free, management-free, and free of management-only JavaScript/CSS/shell markup. |
| 11 | planned | Preserve manage-mode behavior: generated-data reads, capability checks, import-open-on-load, metadata edit flow, settings, context menu, rebuilds, imports, scope lifecycle, status pills, and backend write authority must continue through the existing management/service flow. |
| 12 | planned | Add or extend focused smoke coverage for app-composition contracts. Cover construction order, startup phases, public/manage separation, returned app handle compatibility, and any narrowed runtime/controller input contract where practical. |
| 13 | planned | Run management modal/service smoke checks if management initialization, generated reads, config handoff, capability checks, status projection, import-open-on-load, route state, or initial load sequencing changes. |
| 14 | planned | Run public read-only checks if public startup context, generated reads, route normalization, document visibility, search/recent, bookmarks, reports, info panel, or public management omission changes. |
| 15 | planned | Review touched runtime files for new compatibility scaffolding. Deliverable: short cleanup note listing temporary runtime/composition bridges kept, bridges removed, and why any bridge is acceptable. |
| 16 | planned | Update owning docs after implementation: this tracker, Docs Viewer Front-End App Architecture Request, Docs Viewer runtime boundary, Docs Viewer overview, Docs Viewer JavaScript inventory, and portable files only if runtime copy sets change. |
| 17 | planned | Create or update a structured docs-log entry when the implementation lands and record the entry id in this tracker. |

The closeout for this slice should confirm:

- app-composition/startup ownership is defined and documented
- controller construction order and startup phases are explicit
- public startup remains backend-free and management-free
- manage startup still gets backend capability checks from the management/service flow
- generated-read service fallback and capability semantics remain explicit
- management writes remain behind backend endpoints with server-side validation
- no new feature-specific panel, editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
- public read-only routes still avoid management-only shell markup, CSS, JavaScript, management base URLs, and backend capability probes
- local manage mode still gets backend capability checks and write authority from the management/service flow
