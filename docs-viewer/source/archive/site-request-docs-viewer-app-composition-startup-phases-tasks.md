---
doc_id: site-request-docs-viewer-app-composition-startup-phases-tasks
title: Docs Viewer App Composition And Startup Phases Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: done
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14183
viewable: true
---
This document is archived and is no longer maintained.

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
| 1 | done | Inventory current startup and controller construction in `docs-viewer/runtime/js/docs-viewer-app-runtime.js`, including session/service/controller creation, event binding, config loading, bookmark initialization, management initialization, index load, import-open-on-load, and returned runtime API. Deliverable: short startup-order note in this tracker. |
| 2 | done | Classify each startup phase by source of authority: browser route/config context, browser-safe config asset, generated static asset, local generated-read service, browser storage, management backend capability endpoint, or management backend write endpoint. Deliverable: backend/service startup contract note in this tracker. |
| 3 | done | Decide whether this slice should introduce `docs-viewer/runtime/js/docs-viewer-app-composition.js` or keep composition in `docs-viewer-app-runtime.js` with a smaller extracted helper. Do not create a composition owner unless it reduces real coupling and clarifies lifecycle phases. |
| 4 | done | Define target owner names and exported contracts. The composition contract should accept boot/runtime inputs, create or receive session/services/controllers, expose explicit startup phases, and preserve the current runtime API compatibility where still needed. |
| 5 | done | Define public startup phases. Public contexts must create static generated/config/report services, bind public controllers, initialize bookmarks, load config/index/route, and omit management backend probes, management controller imports, management base URLs, and import-open-on-load. |
| 6 | done | Define manage startup phases. Manage contexts may construct the lazy management runtime, initialize backend capability checks after route/config context is ready, and handle import-open-on-load only when management mode is active and route access allows it. |
| 7 | done | Implement the selected app-composition/startup owner and handoff. Preserve controller object identity and callback contracts where existing owners still require compatibility inputs. |
| 8 | done | Move startup phase sequencing only where the new owner makes order explicit. Do not move rendering, validation, generated-read internals, config normalization, bookmark storage, management writes, or report behavior into the composition owner. |
| 9 | done | Preserve initial load behavior: config load, route-global updates, viewer config/UI text load, initial index load, default/current document resolution, search route handling, recent/bookmark state, and route history behavior must remain unchanged. |
| 10 | done | Preserve public read-only behavior: `/library/` and `/analysis/` must stay backend-free, management-free, and free of management-only JavaScript/CSS/shell markup. |
| 11 | done | Preserve manage-mode behavior: generated-data reads, capability checks, import-open-on-load, metadata edit flow, settings, context menu, rebuilds, imports, scope lifecycle, status pills, and backend write authority must continue through the existing management/service flow. |
| 12 | done | Add or extend focused smoke coverage for app-composition contracts. Cover construction order, startup phases, public/manage separation, returned app handle compatibility, and any narrowed runtime/controller input contract where practical. |
| 13 | done | Run management modal/service smoke checks if management initialization, generated reads, config handoff, capability checks, status projection, import-open-on-load, route state, or initial load sequencing changes. |
| 14 | done | Run public read-only checks if public startup context, generated reads, route normalization, document visibility, search/recent, bookmarks, reports, info panel, or public management omission changes. |
| 15 | done | Review touched runtime files for new compatibility scaffolding. Deliverable: short cleanup note listing temporary runtime/composition bridges kept, bridges removed, and why any bridge is acceptable. |
| 16 | done | Update owning docs after implementation: this tracker, Docs Viewer Front-End App Architecture Request, Docs Viewer runtime boundary, Docs Viewer overview, Docs Viewer JavaScript inventory, and portable files only if runtime copy sets change. |
| 17 | done | Create or update a structured docs-log entry when the implementation lands and record the entry id in this tracker. |

## Implementation Notes

Implemented 2026-05-28.

Startup order inventory:

1. App boot validates root/window/document, resolves route config, creates route context, initializes the app shell, gathers shell refs, and calls `startDocsViewerRuntime(...)`.
2. The runtime reads route/app-shell inputs, then delegates foundational composition to `docs-viewer/runtime/js/docs-viewer-app-composition.js`.
3. Composition creates runtime defaults, service context, hosted-view registry, panel layout, app session, document-index state, and generated-data runtime.
4. The compatibility runtime constructs focused controllers in the existing order: sidebar renderer, info-panel controller, document controller, route workflow, search controller, config controller, lazy management runtime adapter, bookmark controller.
5. Route popstate/window listeners and bookmark controller construction remain in the runtime because they still depend on function-scoped controller callbacks.
6. Startup sequencing is now explicit through `startDocsViewerStartupPhases(...)`: bind events, start busy state, load Docs Viewer config, render index-panel state, load viewer config/UI text, initialize bookmarks, initialize management only when the composition says manage mode is active, load the initial index/route, then open the import modal only when route access and current mode permit it.
7. The returned runtime API keeps the compatibility shape: `root`, `routeContext()`, `appShellRefs`, `appSession`, `state`, `initialLoadPromise`, `loadManagementController`, `applyCurrentRoute`, `loadIndex`, and `loadDoc`. It also returns `appComposition` for focused contract checks and future slices.

Backend/service startup contract:

- Root/app-shell validation, app session creation, service-context creation, hosted-view registration, panel layout, document-index state, event binding, route globals, and returned runtime API are browser route/config context.
- Docs Viewer config and UI text loads are browser-safe config asset reads.
- Generated docs index, payload, search, references, and reference-target reads use generated static assets in public contexts and the local generated-read service only when management route access allows it.
- Bookmark initialization remains browser storage through IndexedDB.
- Management initialization is a manage-context phase whose capability truth comes from the existing management backend capability endpoint, not from route config alone.
- Import-open-on-load is a manage-context phase gated by route access and current `mode=manage`; the write authority remains behind the existing management backend write endpoints.
- Public `/library/` and `/analysis/` startup records omit management backend surfaces, local generated-read service base URLs, management capability probes, management controller imports, and import-open-on-load.

Owner/contract decision:

- Added `docs-viewer/runtime/js/docs-viewer-app-composition.js` because the slice moved real coupling: foundational owner construction, startup phase records, backend/service authority records, public/manage startup gating, runtime defaults, and initial startup sequencing no longer live inline in `docs-viewer-app-runtime.js`.
- Kept focused controller construction in `docs-viewer-app-runtime.js` because existing controllers still consume function-scoped compatibility callbacks. Moving those controllers in this slice would either create a broad callback bag or hide the same coupling behind a larger module.
- The next runtime API shrink slice should decide whether `appComposition` remains part of the returned handle or is replaced by narrower test/export contracts.

Compatibility cleanup note:

- Kept: the broad `state` compatibility bridge, function-scoped controller callback bridges, lazy management runtime adapter, and returned runtime API. These are acceptable because they preserve current controller contracts while the composition owner takes over foundational startup responsibilities.
- Removed from inline runtime ownership: runtime default constants, service-context creation, hosted-view registry creation, panel layout creation, app-session creation, document-index state creation, generated-data runtime creation, startup phase sequencing, and import-open-on-load gating.
- No management write, generated-read internals, config normalization, bookmark storage, rendering, report behavior, panel feature behavior, source editor behavior, semantic-reference behavior, visualization behavior, plugin behavior, route shell markup, generated schema, or backend write behavior was added.

Structured docs-log entry:

- `change-2026-05-28-added-docs-viewer-app-composition-startup-phases`

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
