---
doc_id: site-request-docs-viewer-runtime-api-shrink-tasks
title: Docs Viewer Runtime API Shrink Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: done
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14184
viewable: true
---
This document is archived and is no longer maintained.

---

# Docs Viewer Runtime API Shrink Tasks

## Implementation Note - 2026-05-28

Implemented the runtime API shrink slice.
`startDocsViewerRuntime(...)` and `startDocsViewerApp(...)` remain stable entrypoints, but the returned app handle is now intentionally limited to:

- `root`
- `routeContext()`
- `appShellRefs`
- `initialLoadPromise`

Removed returned-handle fields:

- `appComposition`
- `appSession`
- `state`
- `loadManagementController`
- `applyCurrentRoute`
- `loadIndex`
- `loadDoc`

No replacement broad state alias was added.
Management reload behavior still uses the internal lazy-management context assembled inside `docs-viewer-app-runtime.js`, where `loadIndex` and `loadDoc` remain private runtime callbacks for the management controller.
Public `/library/` and `/analysis/` handles no longer expose management lazy loaders or route workflow bridges.

Verification run:

- `node --check docs-viewer/runtime/js/docs-viewer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-composition.js`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`

Management modal/service smokes were not run because the slice did not change management initialization, capability checks, generated-read routing, import-open-on-load, status projection, or post-write reload internals.
The only management-facing contract touched was removal of the unused returned-handle `loadManagementController` field; the private management context still receives its existing callbacks.

This is the fourth child task tracker for [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture).

The slice should retire or narrow the legacy returned runtime API from `docs-viewer/runtime/js/docs-viewer-app-runtime.js` where possible.
It follows [Docs Viewer App Composition And Startup Phases Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-composition-startup-phases-tasks), which introduced `docs-viewer/runtime/js/docs-viewer-app-composition.js` and made public/manage startup phase ownership explicit.

This is structural frontend-app architecture work.
It should not add source editor features, semantic-reference editing, visualization features, plugin architecture, route shell markup, generated payload schema changes, or backend write behavior.

## Status

### steer for this task

- Treat this as runtime API shrinkage, not as a controller rewrite.
- Inventory real callers before removing anything from the returned app handle.
- Preserve current `/docs/`, `/library/`, and `/analysis/` behavior.
- Keep `startDocsViewerRuntime(...)` and `startDocsViewerApp(...)` as stable entrypoints unless inventory proves a smaller handle is safe for all callers.
- Prefer focused owner contracts over returning broad runtime internals from the app handle.
- Do not replace removed runtime APIs with direct endpoint calls from feature modules.
- Keep route workflow ownership in `docs-viewer-route-workflow.js`, generated-data reads in `docs-viewer-generated-data-runtime.js`, app session domains in `docs-viewer-app-session.js`, app composition/startup in `docs-viewer-app-composition.js`, and management writes in existing management/service modules.
- Public read-only routes must not gain management base URLs, backend capability probes, management-only JavaScript, or write-capable service handles.
- Manage-mode callers that need backend behavior must continue through the existing management controller/client/service flow with server-side validation.

### backend co-evolution steer

Classify every returned handle field and caller by source of authority:

- browser route/config context
- app/session browser state
- generated static asset
- local generated-read service
- browser storage
- management backend capability endpoint
- management backend write endpoint

Do not remove a runtime bridge by giving public or feature modules broader backend access.
If a caller needs management behavior, the replacement should be an explicit management-controller or service-adapter contract, not a generic runtime escape hatch.
If a test currently reaches into broad `state` only to verify route or backend behavior, move that assertion to the focused owner or smoke that owns the behavior.

### current returned handle inventory

Implemented `startDocsViewerRuntime(...)` return shape:

- `root`: browser app root. Mostly diagnostic/test handle.
- `routeContext()`: browser route/config context. Useful for route-context assertions but should not imply backend write capability.
- `appShellRefs`: shell refs grouped by app shell. Mostly diagnostic/test handle.
- `initialLoadPromise`: useful public boot completion contract for tests and callers.

Removed from the returned handle:

- `appComposition`: covered through direct app-composition module tests instead of through the app handle.
- `appSession`: covered through direct app-session/domain tests instead of through the app handle.
- `state`: removed broad compatibility state bridge from the public app handle.
- `loadManagementController`: remains a private manage-only lazy runtime bridge inside `docs-viewer-app-runtime.js`.
- `applyCurrentRoute`: remains owned by `docs-viewer-route-workflow.js` and covered through focused route workflow tests.
- `loadIndex`: remains owned by `docs-viewer-route-workflow.js` and stays available only as a private callback for startup and management reload.
- `loadDoc`: remains owned by `docs-viewer-route-workflow.js` and stays available only as a private callback for route and management refresh flows.

Implemented caller map:

- `docs-viewer/runtime/js/docs-viewer-app-boot.js` returns the runtime handle from `startDocsViewerApp(...)`; it does not require broad state, composition/session internals, management loaders, or route workflow bridge fields.
- `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` now asserts the intentionally small app handle shape, single-start behavior, `routeContext()` access, `initialLoadPromise`, public/manage separation, and route completion through rendered navigation rather than `app.state`.
- `docs-viewer/runtime/js/docs-viewer-management.js` still receives `loadIndex` and `loadDoc` through the private lazy-management context for post-write reload and selected-doc refresh behavior. It does not consume those functions from the returned app handle.
- Route workflow, search, bookmark, app-composition, and app-session module tests exercise focused owner APIs directly rather than using returned runtime internals.
- Management writes, imports, rebuilds, settings, scope lifecycle, and capability checks remain behind management modules and service endpoints.

### implemented runtime API authority table

| Field | status | source of authority | contract class | caller / replacement |
| --- | --- | --- | --- | --- |
| `root` | kept | browser route/config context | diagnostic/test app handle | Used as app-root identity only. No backend authority. |
| `routeContext()` | kept | browser route/config context | public app contract / diagnostic test bridge | Used for route-context assertions. Does not expose backend write capability. |
| `appShellRefs` | kept | browser app shell DOM | diagnostic/test app handle | Used for shell-ref contract assertions. No backend authority. |
| `initialLoadPromise` | kept | app composition/startup sequencing | public boot completion contract | Smallest stable signal that initial startup phases completed. |
| `appComposition` | removed | app composition owner | former test-only bridge | Replaced by direct `docs-viewer-app-composition.js` tests. |
| `appSession` | removed | app/session browser state | former test-only bridge | Replaced by direct `docs-viewer-app-session.js` tests. |
| `state` | removed | app/session browser state, generated static assets, browser storage, management state | compatibility leftover | Boot smoke now asserts route completion through DOM projection; feature modules use focused owner/context contracts. |
| `loadManagementController` | removed from returned handle; kept private | management backend capability/write endpoints via management controller | manage-only private bridge | Management startup and import-open-on-load still call the private lazy loader inside runtime. Public app handles do not expose it. |
| `applyCurrentRoute` | removed from returned handle; kept private | route workflow owner | private route workflow bridge | Route workflow tests cover the focused owner; search/bookmark receive explicit route callbacks. |
| `loadIndex` | removed from returned handle; kept private | generated static asset or local generated-read service | private route workflow bridge | Startup and management reload use private runtime callback handoff. |
| `loadDoc` | removed from returned handle; kept private | generated static asset or local generated-read service | private route workflow bridge | Route links, bookmarks, and management refresh flows use private/focused callbacks. |

### implemented compatibility limits

Intentional returned app handle fields:

- `root`: kept as a low-risk diagnostic/test root identity while route boot remains DOM-root based.
- `routeContext()`: kept for route-context assertions and future app-context verification; it remains browser route/config context only.
- `appShellRefs`: kept as a shell-ref diagnostic contract while the JavaScript app shell is still being hardened.
- `initialLoadPromise`: kept as the stable boot completion signal for callers and smokes.

Fields deliberately not returned:

- broad app/session state
- app-composition internals
- app-session internals
- management lazy loader
- route workflow bridge methods

Later slices can consider removing `root`, `routeContext()`, or `appShellRefs` if tests move fully to route-context and shell-owner module contracts.

### likely shrink targets

Use the inventory to validate or revise these candidate changes:

- replace `state` assertions in boot smoke with focused app-session or selected app-state projection assertions
- decide whether `appComposition` should stay on the public app handle, move behind a test-only module contract, or be replaced by direct composition-owner tests
- keep `initialLoadPromise` as the smallest stable boot completion signal unless callers can avoid the returned handle entirely
- move route workflow bridge consumers toward focused route workflow contracts where practical
- keep `loadManagementController` gated for manage contexts only, or replace it with a narrower management app handle if the management controller no longer needs the generic lazy bridge
- document any remaining handle fields as intentional app handle contract rather than compatibility leftovers

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-boot.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-composition.js`
  - any focused owner modules whose public contract changes
- Focused module smoke coverage when returned handle fields change:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend coverage for returned app handle compatibility, removed fields, focused owner replacements, public/manage separation, and boot completion behavior where practical
- Management route checks when `loadManagementController`, management reload flows, generated reads, capability checks, status projection, import-open-on-load, route state, or initial load sequencing changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when public app handle shape, public startup context, generated reads, route normalization, document visibility, search/recent, bookmarks, reports, info panel, or public management omission changes:
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
| 1 | done | Inventory actual returned runtime API callers in runtime code, smoke tests, docs, and any route bootstrap code. Deliverable: implemented caller map above. |
| 2 | done | Classify each returned handle field by source of authority and by whether it is public app contract, manage-only bridge, test-only bridge, or compatibility leftover. Deliverable: runtime API authority table above. |
| 3 | done | Target app handle shape is `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`; broad `state`, route workflow bridges, composition/session handles, and management lazy loader were removed from the returned handle. |
| 4 | done | Temporary compatibility limits are documented above for each intentionally kept returned-handle field. |
| 5 | done | Updated `docs_viewer_app_shell_modules.py` to assert the intended app handle shape, public/manage separation, and route completion without relying on broad runtime internals. |
| 6 | done | Removed returned-handle fields only after caller inventory showed they were unused externally or had focused/private replacements. Management reload/write flows still consume private lazy-management context callbacks. |
| 7 | done | Removed `state` from the returned handle and replaced boot smoke state assertions with rendered navigation route projection assertions. No new broad state alias was exposed. |
| 8 | done | Removed `appComposition` from the returned handle; app-composition contracts remain covered through direct module tests. |
| 9 | done | Removed route workflow bridges from the returned handle while keeping `applyCurrentRoute`, `loadIndex`, and `loadDoc` covered by focused route workflow tests and private management/startup callback handoff. |
| 10 | done | Preserved public read-only behavior; public app handles no longer expose management lazy loaders, route workflow bridges, backend capability probes, or management service handles. |
| 11 | done | Preserved manage-mode behavior by leaving generated-data reads, capability checks, import-open-on-load, metadata edit flow, settings, context menu, rebuilds, imports, scope lifecycle, status pills, and backend write authority in the existing management/service flow. |
| 12 | done | Management modal/service smokes were not required because management initialization, lazy management loading internals, generated reads, route state, status projection, import-open-on-load, and post-write reload behavior were not changed. |
| 13 | done | Public read-only checks were run because public app handle shape changed. |
| 14 | done | Runtime cleanup note: kept `root`, `routeContext()`, `appShellRefs`, and `initialLoadPromise`; removed broad state, composition/session internals, management loader, and route workflow bridges; replacements are focused owner tests plus private management/startup callback handoff. |
| 15 | done | Updated owning docs after implementation: this tracker, Docs Viewer Front-End App Architecture Request, Docs Viewer runtime boundary, Docs Viewer overview, and Docs Viewer JavaScript inventory. Portable files were not updated because runtime copy sets did not change. |
| 16 | done | Created structured docs-log entry `change-2026-05-28-shrank-docs-viewer-runtime-api`. |

The closeout for this slice should confirm:

- returned runtime API fields are inventoried and classified
- any removed fields have focused owner replacements or proved-unused callers
- any remaining public app handle is intentional and documented
- broad `state` is not exposed to feature modules when a state domain or controller contract exists
- public startup remains backend-free and management-free
- manage startup and writes still get capability/write authority from the management/service flow
- no direct backend endpoint calls were introduced to replace runtime bridges
- no new feature-specific panel, editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
