---
doc_id: site-request-docs-viewer-public-manage-app-contexts-tasks
title: Docs Viewer Public And Manage App Contexts Tasks
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: planned
parent_id: site-request-docs-viewer-frontend-app-architecture
sort_order: 14185
viewable: true
---
# Docs Viewer Public And Manage App Contexts Tasks

This is the fifth child task tracker for [Docs Viewer Front-End App Architecture Request](/docs/?scope=studio&doc=site-request-docs-viewer-frontend-app-architecture).

The slice should make public read-only and local manage mode explicit app contexts without creating a speculative permissions framework.
It follows [Docs Viewer Runtime API Shrink Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-runtime-api-shrink-tasks), which narrowed the returned runtime/app handle and removed broad state, management lazy loaders, and route workflow bridge methods from the public app handle.

This is structural frontend-app architecture work.
It should not add source editor features, semantic-reference editing, visualization features, plugin architecture, route shell markup, generated payload schema changes, or backend write behavior.

## Status

### steer for this task

- Treat this as app-context clarification and enforcement, not a new permissions framework.
- Preserve current `/docs/`, `/library/`, and `/analysis/` behavior.
- Public routes read generated/static assets, show document/search/recent/bookmark/report/info behavior, and omit management assets.
- Manage mode reads generated data through local services when available and uses backend endpoints for writes, rebuilds, imports, settings, and scope lifecycle.
- Route config and access projection should produce a clear app-context shape.
- Static route context and backend capability truth must remain separate.
- Do not let browser route config imply write authority.
- Keep public app context free of management base URLs, management-only assets, local generated-read service base URLs, backend capability probes, and write-capable service handles.
- If manage context needs finer capability fields, add them only with matching backend endpoint semantics and tests.
- Do not replace context cleanup with direct endpoint calls from feature modules.

### backend co-evolution steer

Classify every app-context field and caller by source of authority:

- browser route/config context
- generated static asset
- local generated-read service
- browser storage
- management backend capability endpoint
- management backend write endpoint

Public app context may carry browser-safe static generated/config/report asset URLs and browser storage support.
It must not carry management backend base URLs, local generated-read service base URLs, backend capability probes, or management write service handles.

Manage app context may carry local generated-read and management backend base URLs only through explicit manage route access and service-context projection.
Backend availability and write capability must still come from the management capability/service flow.

### current context inventory

Current relevant owners:

- `docs-viewer/runtime/js/docs-viewer-app-context.js`: route context and route-global update projection.
- `docs-viewer/runtime/js/docs-viewer-access.js`: static route access projection for public, manage-capable, and local manage contexts.
- `docs-viewer/runtime/js/docs-viewer-route-config.js`: browser-safe route-config registry resolution and migration fallback.
- `docs-viewer/runtime/js/docs-viewer-service-context.js`: public/manage service context projection; public contexts strip management and local generated-read service URLs.
- `docs-viewer/runtime/js/docs-viewer-app-composition.js`: service-context handoff, startup phase records, startup authority records, and public/manage startup gating.
- `docs-viewer/runtime/js/docs-viewer-app-session.js`: route-session domain projection and temporary compatibility state bridge.
- `docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js`: generated-data request option shaping, generated-read capability caching, and named generated-data reads.
- `docs-viewer/runtime/js/docs-viewer-runtime-lazy-controller.js`: neutral lazy management controller loader gated by management route access.
- `docs-viewer/runtime/js/docs-viewer-management.js` and related management modules: capability checks, writes, imports, rebuilds, settings, status projection, and scope lifecycle.

Current known context split:

- `/library/` and `/analysis/` are public read-only routes. They use static generated docs/search/report assets and must stay backend-free and management-free.
- `/docs/` is the local management-capable route. It can switch scope, preserve manage mode when allowed, load management-only shell/controller assets, use local generated-read services when available, and call management backend endpoints through existing management modules.
- A `mode=manage` query on a public read-only route is normalized away.
- Public app handles already omit broad state, management lazy loaders, route workflow bridges, backend probes, and management service handles after the runtime API shrink slice.

### likely clarification targets

Use the inventory to validate or revise these candidate changes:

- define a focused app-context projection that names static route facts separately from backend capability facts
- document which fields belong to route context, access projection, service context, app session route domain, and management capability state
- add or extend tests that assert public contexts strip management and local-service URLs
- add or extend tests that assert manage contexts keep route-config access separate from backend capability/write availability
- tighten any code that still checks scattered route/access flags where a focused context projection would be clearer
- keep public read-only startup free of management-only JavaScript, CSS, shell markup, backend probes, and management service handles
- keep manage startup and writes behind the existing management controller/client/service flow

### baseline verification set

Run only the checks warranted by touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer-app-context.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-access.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-route-config.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-service-context.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-composition.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`
  - any focused owner modules whose public contract changes
- Focused module smoke coverage when app-context/service-context contracts change:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Management route checks when management context, lazy management loading, generated reads, capability checks, status projection, import-open-on-load, route state, or backend authority changes:
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only checks when public app context, public startup context, generated reads, route normalization, document visibility, search/recent, bookmarks, reports, info panel, or public management omission changes:
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
| 1 | planned | Inventory current public/manage app-context fields and callers across route context, access projection, route config, service context, app composition, app session route domain, generated-data runtime, lazy management loading, management modules, smoke tests, and docs. Deliverable: short context map in this tracker. |
| 2 | planned | Classify each context field by source of authority: browser route/config context, generated static asset, local generated-read service, browser storage, management backend capability endpoint, or management backend write endpoint. Deliverable: app-context authority table in this tracker. |
| 3 | planned | Decide target app-context shape. Name which facts are static public route facts, static manage route facts, service-context facts, app-session browser state, and backend capability facts. |
| 4 | planned | Define public context limits. Public `/library/` and `/analysis/` contexts must not expose management base URLs, local generated-read service base URLs, backend capability probes, management-only JavaScript/CSS/shell markup, or write-capable service handles. |
| 5 | planned | Define manage context limits. Manage `/docs/` context may expose local generated-read and management backend URLs only through explicit manage route/service projection, while write availability remains controlled by backend capability and service validation. |
| 6 | planned | Update focused smoke coverage before behavior changes where practical. Tests should assert public/manage context separation, route-config versus backend-capability separation, and public management omission without relying on broad runtime internals. |
| 7 | planned | Add or refine a focused app-context projection only if the inventory shows scattered checks that would become clearer. Do not create a speculative permissions framework. |
| 8 | planned | Remove or narrow any stale context bridges, fallback fields, or duplicated public/manage checks only after caller inventory proves they are unused or replaced by focused owner contracts. |
| 9 | planned | Verify public startup remains backend-free and management-free: no management controller import, no management shell rendering, no management CSS requirement, no backend capability probes, no local generated-read service base URL, and no management service handle exposure. |
| 10 | planned | Verify manage startup and writes continue through existing management/service flow: generated-data reads, capability checks, import-open-on-load, metadata edit flow, settings, context menu, rebuilds, imports, scope lifecycle, status pills, and backend write authority. |
| 11 | planned | Run management modal/service smoke checks if management context, lazy management loading, generated reads, route state, status projection, import-open-on-load, or post-write reload behavior changes. |
| 12 | planned | Run public read-only checks if public app context, public startup context, generated reads, route normalization, document visibility, search/recent, bookmarks, reports, info panel, or public management omission changes. |
| 13 | planned | Review touched runtime files for new compatibility scaffolding. Deliverable: short cleanup note listing context fields kept, fields removed, replacement owner contracts, and any follow-up removal tasks. |
| 14 | planned | Update owning docs after implementation: this tracker, Docs Viewer Front-End App Architecture Request, Docs Viewer runtime boundary, Docs Viewer overview, Docs Viewer JavaScript inventory, service/config docs if contracts change, and portable files only if runtime copy sets change. |
| 15 | planned | Create or update a structured docs-log entry when the implementation lands and record the entry id in this tracker. |

The closeout for this slice should confirm:

- public/manage app-context fields are inventoried and classified
- static route/config facts are separate from backend capability/write facts
- public startup remains backend-free and management-free
- public app context does not expose management service handles, backend capability probes, management lazy loaders, local generated-read service base URLs, or write-capable URLs
- manage startup and writes still get capability/write authority from the management/service flow
- generated-data reads still use generated-data runtime and service-context projection rather than direct endpoint calls from feature modules
- no new feature-specific panel, editor, semantic-reference, visualization, plugin, route shell, generated schema, or backend-write behavior was added
