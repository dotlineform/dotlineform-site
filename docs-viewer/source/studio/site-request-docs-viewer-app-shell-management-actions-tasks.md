---
doc_id: site-request-docs-viewer-app-shell-management-actions-tasks
title: Docs Viewer App Shell Management Actions Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: draft
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12105
viewable: true
---
# Docs Viewer App Shell Management Actions Tasks

This is the tracker for implementing the first app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The first migration is the management action area.
It should move the manage-mode action row and related capability-gated controls out of `_includes/docs_viewer_shell.html` and into the JavaScript app shell without changing public route behavior.

## Status

### just done

- Created this task tracker.
- Confirmed the first shell migration target is the management action area.
- Recorded that `docs-viewer/runtime/js/docs-viewer-app-shell.js` is the preferred app-shell owner module and `docs-viewer/runtime/js/docs-viewer.js` remains the temporary loaded entrypoint.

### steer for next task

- Implement the management action area as the first app-shell-owned shell responsibility.
- Keep the slice narrow: do not move document rendering, index panel layout, metadata modal markup, import modal internals, or search controls in the same pass.
- Preserve existing control ids or provide a deliberate compatibility mapping so current management modules do not need a broad rewrite.
- Keep capability handling narrow: route config supplies static route intent, and manage-mode boot checks only whether the local Docs Viewer backend is reachable.
- Avoid adding new complete responsibilities to `docs-viewer.js`; it should delegate to `docs-viewer-app-shell.js` or a focused management-action renderer.

### baseline verification set

Run only the checks warranted by the touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - any changed focused management/app-shell modules
- Focused Docs Viewer management module smoke checks when IDs, refs, or event wiring change:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Public read-only smoke when shell markup or route boot changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py`
- Jekyll build only when includes, route templates, or loaded assets change:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for high-risk shared runtime files.
- This slice is part of the app-shell enabling work, not a broad `docs-viewer.js` refactor.
- Use generated route config as the direction for route/app handoff; existing data attributes can remain as temporary compatibility only.
- Use modular hosted views, not a plugin architecture.
- Keep current repo requirements first; do not introduce speculative portable/plugin machinery.
- Public routes must not load or expose management-only controls.
- Backend endpoints continue to enforce writes and filesystem operations.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory current management action area markup in `_includes/docs_viewer_shell.html`, including duplicated search-enabled/search-disabled branches, theme toggle placement, control ids, and management module references. Deliverable: short implementation note in this tracker or closeout summary identifying the exact shell markup to replace. |
| 2 | planned | Define the first `docs-viewer-app-shell.js` surface. It should expose an app-shell initializer or focused renderer that `docs-viewer.js` can call while `docs-viewer.js` remains the loaded script entrypoint. Deliverable: clear module ownership and no new broad shell responsibility added to `docs-viewer.js`. |
| 3 | planned | Replace the management action row Liquid markup with a minimal app-shell mount/container. Preserve route behavior for pages with search enabled and pages with search disabled. Deliverable: `_includes/docs_viewer_shell.html` no longer duplicates full management action markup across branches. |
| 4 | planned | Render the management action area from JavaScript. Include the Actions menu, rebuild, normalize order, settings, scope lifecycle entries, import, new/edit/archive/delete, show/hide viewability control, hidden toggle, and current manage-only theme toggle unless a separate route/header decision moves the theme toggle elsewhere. |
| 5 | planned | Keep current management modules working with minimal churn. Prefer preserving existing element ids used by `docs-viewer-management.js`; if ids change, update refs deliberately in one focused pass with smoke coverage. |
| 6 | planned | Apply static route/config and reachability gating narrowly. Show management controls only when route config or current boot compatibility says manage mode is allowed and the local Docs Viewer backend is reachable. Do not add per-click capability checks or speculative capability fields. |
| 7 | planned | Verify public-route behavior. `/library/` and `/analysis/` should not render or lazy-load management-only controls; public read-only shell boot should remain unchanged except for the absence of now-retired Liquid management markup. |
| 8 | planned | Add or update focused module smoke coverage for the management action renderer. Cover manage allowed/unavailable states, public route omission, and preservation of expected control refs. |
| 9 | planned | Run the targeted verification set for changed JS, include markup, management boot, and public read-only routes. Record any checks skipped and why. |
| 10 | planned | Update owning docs after implementation. At minimum update this tracker, the app-shell request if the implemented shape changes the plan, and Docs Viewer runtime/inventory docs if `docs-viewer.js` ownership or risk materially changes. |

The closeout for this first migration should confirm:

- management action area ownership moved from Liquid to JavaScript
- `_includes/docs_viewer_shell.html` keeps only the necessary mount/context for this area
- `docs-viewer.js` remains a compatibility entrypoint and does not become the long-term app-shell owner
- public routes still omit management UI
- generated docs payloads were rebuilt by the watcher only if source docs changed, or intentionally not rebuilt by Codex
