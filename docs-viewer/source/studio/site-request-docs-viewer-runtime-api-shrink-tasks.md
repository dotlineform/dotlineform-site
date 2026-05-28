---
doc_id: site-request-docs-viewer-runtime-api-shrink-tasks
title: Docs Viewer Runtime API Shrink Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: planned
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14184
viewable: true
---
# Docs Viewer Runtime API Shrink Tasks

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

Current `startDocsViewerRuntime(...)` return shape:

- `root`: browser app root. Mostly diagnostic/test handle.
- `routeContext()`: browser route/config context. Useful for route-context assertions but should not imply backend write capability.
- `appShellRefs`: shell refs grouped by app shell. Mostly diagnostic/test handle.
- `appComposition`: temporary composition contract handle introduced for focused tests and future slices.
- `appSession`: app-session/domain owner. Useful if tests verify state-domain contracts through the app handle, but broad controller callers should prefer focused domain inputs.
- `state`: broad compatibility state bridge. This is the largest remaining API shrink target.
- `initialLoadPromise`: useful public boot completion contract for tests and callers.
- `loadManagementController`: manage-only lazy management bridge. Keep gated and avoid exposing it to public contexts.
- `applyCurrentRoute`: route workflow bridge.
- `loadIndex`: route workflow bridge.
- `loadDoc`: route workflow bridge.

Current known callers and reasons:

- `docs-viewer/runtime/js/docs-viewer-app-boot.js` returns the runtime handle from `startDocsViewerApp(...)`.
- `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` uses `initialLoadPromise`, `state`, and `routeContext()` in the boot single-start contract.
- `docs-viewer/runtime/js/docs-viewer-management.js` receives `loadIndex` and `loadDoc` through the lazy management context for post-write reload and selected-doc refresh behavior.
- Route workflow, search, and bookmark module tests already exercise focused owner APIs directly and should not need the broad runtime handle.
- Management writes, imports, rebuilds, settings, scope lifecycle, and capability checks already live behind management modules and service endpoints; this slice must not bypass those owners.

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
| 1 | planned | Inventory actual returned runtime API callers in runtime code, smoke tests, docs, and any route bootstrap code. Deliverable: short caller map in this tracker. |
| 2 | planned | Classify each returned handle field by source of authority and by whether it is public app contract, manage-only bridge, test-only bridge, or compatibility leftover. Deliverable: runtime API authority table in this tracker. |
| 3 | planned | Decide target app handle shape. Preserve `initialLoadPromise` if it remains the cleanest boot completion signal; remove or narrow broad `state`, route workflow bridges, and composition/session handles only where callers have focused replacements. |
| 4 | planned | Define temporary compatibility limits. Name each field intentionally kept on the returned handle, why it remains, which later slice should remove it, and what focused tests guard it. |
| 5 | planned | Update focused smoke coverage before removals where practical. Tests should assert the intended app handle shape, public/manage separation, and focused owner replacements without relying on broad runtime internals. |
| 6 | planned | Remove or narrow runtime handle fields only after the caller inventory proves they are unused or replaced. Do not remove fields that management reload/write flows still consume through the lazy management context. |
| 7 | planned | If `state` is removed from the returned handle, replace boot smoke assertions with focused app-session/domain or user-visible state assertions. Do not expose a new broad state alias under another name. |
| 8 | planned | If `appComposition` remains returned, document why it is an intentional app contract or test bridge. If it is removed, ensure app-composition contracts remain covered through direct module tests. |
| 9 | planned | If route workflow bridges are removed from the returned handle, verify route workflow module tests and any management reload paths still cover `applyCurrentRoute`, `loadIndex`, and `loadDoc` through focused contracts. |
| 10 | planned | Preserve public read-only behavior: `/library/` and `/analysis/` must stay backend-free, management-free, and free of management-only JavaScript/CSS/shell markup. Public app handles must not expose management service handles or backend capability probes. |
| 11 | planned | Preserve manage-mode behavior: generated-data reads, capability checks, import-open-on-load, metadata edit flow, settings, context menu, rebuilds, imports, scope lifecycle, status pills, and backend write authority must continue through the existing management/service flow. |
| 12 | planned | Run management modal/service smoke checks if management initialization, lazy management loading, generated reads, route state, status projection, import-open-on-load, or post-write reload behavior changes. |
| 13 | planned | Run public read-only checks if public app handle shape, public startup context, generated reads, route normalization, document visibility, search/recent, bookmarks, reports, info panel, or public management omission changes. |
| 14 | planned | Review touched runtime files for new compatibility scaffolding. Deliverable: short cleanup note listing runtime API fields kept, fields removed, replacement owner contracts, and any follow-up removal tasks. |
| 15 | planned | Update owning docs after implementation: this tracker, Docs Viewer Front-End App Architecture Request, Docs Viewer runtime boundary, Docs Viewer overview, Docs Viewer JavaScript inventory, and portable files only if runtime copy sets change. |
| 16 | planned | Create or update a structured docs-log entry when the implementation lands and record the entry id in this tracker. |

The closeout for this slice should confirm:

- returned runtime API fields are inventoried and classified
- any removed fields have focused owner replacements or proved-unused callers
- any remaining public app handle is intentional and documented
- broad `state` is not exposed to feature modules when a state domain or controller contract exists
- public startup remains backend-free and management-free
- manage startup and writes still get capability/write authority from the management/service flow
- no direct backend endpoint calls were introduced to replace runtime bridges
- no new feature-specific panel, editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
