---
doc_id: site-request-docs-viewer-app-shell-header-controls-tasks
title: Docs Viewer App Shell Header Controls Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: in-progress
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12106
viewable: true
---
# Docs Viewer App Shell Header Controls Tasks

This is the tracker for implementing the second app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The second migration is the header control area.
It should move scope picker, recent/search control composition, and related route-context control ownership toward the JavaScript app shell without changing public route behavior.

## Status

### just done

- Completed the first app-shell migration slice in [Docs Viewer App Shell Management Actions Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-management-actions-tasks).
- Established `docs-viewer/runtime/js/docs-viewer-app-shell.js` as the app-shell coordinator while keeping `docs-viewer/runtime/js/docs-viewer.js` as the compatibility entrypoint.
- Moved management action markup out of `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html`, leaving only a route-provided mount.
- Verified that public routes still omit management UI and management-only JavaScript.

### steer for next task

- Implement the header controls as the next narrow app-shell-owned shell responsibility.
- Keep the slice focused on scope picker, recent button, search input composition, and any minimal mount/context needed for those controls.
- Do not move document rendering, metadata modal markup, import modal internals, index panel layout, report rendering, or management command behavior in this pass.
- Preserve existing control ids or provide a deliberate compatibility mapping so current config, search, and route modules do not need a broad rewrite.
- Treat route config as the intended route/app handoff direction; existing data attributes can remain as temporary boot compatibility where needed.
- Keep public read-only behavior for `/library/` and `/analysis/` unchanged.

### baseline verification set

Run only the checks warranted by the touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - any changed focused app-shell/header-control modules
- Focused app-shell module smoke checks when IDs, refs, or render ownership change:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend a focused header-controls module smoke if the existing app-shell smoke does not cover the moved refs
- Docs Viewer route/search smoke checks when search, recent, scope select, route mode, or query handling changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_routes.py --site-root .`
  - focused search/recent smoke if the moved behavior is not covered by `docs_viewer_routes.py`
- Public read-only smoke when shell markup or route boot changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Management service smoke when management-route header controls or scope switching are touched:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Jekyll build only when includes, route templates, or loaded assets change:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for high-risk shared runtime files.
- This slice is part of the app-shell enabling work, not a broad `docs-viewer.js` refactor.
- Keep `docs-viewer.js` as orchestration only: boot/config handoff, route readiness, existing controller wiring, and calls into focused owners.
- New shell rendering should live in `docs-viewer/runtime/js/docs-viewer-app-shell.js` or focused app-shell child modules.
- Avoid introducing a plugin architecture or speculative portable machinery.
- Public routes must not load management-only controls or management-only JavaScript.
- Backend endpoints continue to enforce writes and filesystem operations; header-control migration must not add browser-side write authority.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory current header control markup in `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html`, including search-enabled/search-disabled branches, scope select placement, recent button placement, search input labels/placeholders, control ids, and route/config/search module references. Deliverable: short implementation note in this tracker or closeout summary identifying the exact shell markup to replace. |
| 2 | planned | Define the focused app-shell surface for header controls. Decide whether to extend `docs-viewer/runtime/js/docs-viewer-app-shell.js` directly or add a child renderer such as `docs-viewer-header-controls-renderer.js`. Deliverable: clear module ownership and no new broad shell responsibility added to `docs-viewer.js`. |
| 3 | planned | Replace duplicated or app-shell-owned header-control Liquid markup with minimal mounts/context while preserving search-enabled and search-disabled route behavior. Deliverable: shell templates no longer own full header-control composition for the moved area. |
| 4 | planned | Render the scope picker, recent button, and search input from JavaScript where route options require them. Preserve current ids: `docsViewerScopeSelect`, `docsViewerRecentButton`, and `docsViewerSearchInput`, unless a deliberate compatibility mapping is documented and tested. |
| 5 | planned | Keep current config, route, and search modules working with minimal churn. If refs move behind an async app-shell render, make `docs-viewer.js` wait for the render before reading those refs or initializing dependent controllers. |
| 6 | planned | Preserve route behavior for pages with search enabled and search disabled. Public `/library/` and `/analysis/` should keep their current read-only route boot, scope assumptions, recent/search behavior, and absence of management-only imports. |
| 7 | planned | Preserve manage-mode scope switching behavior. The local `/docs/` management shell should still render the scope picker and keep scope changes, default docs, search index URLs, and browser history behavior intact. |
| 8 | planned | Add or update focused module smoke coverage for the header-control renderer. Cover search-enabled rendering, search-disabled rendering with scope picker, public route rendering, management route rendering, id preservation, and idempotent rendering. |
| 9 | planned | Run the targeted verification set for changed JS, shell templates, route/search behavior, management scope behavior, and public read-only routes. Record any checks skipped and why. |
| 10 | planned | Update owning docs after implementation. At minimum update this tracker, the app-shell request if the implemented shape changes the plan, and Docs Viewer runtime/inventory docs if `docs-viewer.js` ownership or risk materially changes. |

The closeout for this second migration should confirm:

- header control ownership moved from Liquid toward JavaScript app-shell ownership
- shell templates keep only the necessary mounts/context for the moved header-control area
- `docs-viewer.js` remains a compatibility entrypoint and does not become the long-term app-shell owner
- public read-only routes still render expected controls and omit management-only UI/JS
- management scope switching still works
- generated docs payloads were rebuilt by the watcher only if source docs changed, or intentionally not rebuilt by Codex
