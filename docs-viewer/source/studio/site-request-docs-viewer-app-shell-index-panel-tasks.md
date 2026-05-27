---
doc_id: site-request-docs-viewer-app-shell-index-panel-tasks
title: Docs Viewer App Shell Index Panel Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: planned
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12107
viewable: true
---
# Docs Viewer App Shell Index Panel Tasks

This is the tracker for implementing the third app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The third migration is the index panel shell.
It should move the sidebar/index panel container, toolbar controls, and panel-state projection toward the JavaScript app shell without changing document loading, search/recent behavior, or public route behavior.

This slice should align with [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell), but it should not implement the full multi-panel architecture unless the narrow index-panel migration requires a small enabling piece.

## Status

### just done

- Completed [Docs Viewer App Shell Management Actions Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-management-actions-tasks).
- Completed [Docs Viewer App Shell Header Controls Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-header-controls-tasks).
- Established `docs-viewer/runtime/js/docs-viewer-app-shell.js` as the app-shell coordinator while keeping `docs-viewer/runtime/js/docs-viewer.js` as the compatibility entrypoint.
- Moved header control composition out of `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html`, leaving only route-provided mounts/context for that area.

### steer for next task

- Implement the index panel shell as the next narrow app-shell-owned shell responsibility.
- Keep the slice focused on the sidebar/index panel container, collapse/restore/expand controls, nav mount, and index panel state projection.
- Preserve the current `docs-viewer/runtime/js/docs-viewer-index-panel.js` state contract unless a small, tested replacement is clearly needed.
- Keep `docs-viewer/runtime/js/docs-viewer-sidebar.js` as the tree renderer inside the index panel body.
- Do not move document rendering, metadata/report rendering, search/recent result rendering, bookmark behavior, management command behavior, or info-panel views in this pass.
- Preserve existing ids or provide a deliberate compatibility mapping for `docsViewerSidebarToggle`, `docsViewerSidebarExpand`, and `docsViewerNav`.
- Keep public read-only behavior for `/library/` and `/analysis/` unchanged.

### baseline verification set

Run only the checks warranted by the touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-index-panel.js`
  - any changed focused app-shell/index-panel modules
- Focused module smoke checks when index panel state, IDs, refs, or render ownership change:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend a focused index-panel module smoke if existing coverage does not pin the moved refs and state projection
- Route/index behavior smoke checks when sidebar layout, nav refs, history, or route loading changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_routes.py --site-root .`
  - focused index-panel desktop/mobile smoke if the broad route smoke cannot run against the current isolated build shape
- Public read-only smoke when shell markup or route boot changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Management service smoke when management-route index behavior is touched:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Jekyll build only when includes, route templates, CSS, or loaded assets change:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for high-risk shared runtime files.
- This slice is part of the app-shell enabling work, not a broad `docs-viewer.js` refactor.
- Keep `docs-viewer.js` as orchestration only: boot/config handoff, route readiness, existing controller wiring, and calls into focused owners.
- New shell rendering should live in `docs-viewer/runtime/js/docs-viewer-app-shell.js` or focused app-shell child modules.
- Treat the index panel as a shell/layout responsibility and the docs tree as a body renderer responsibility.
- Avoid creating a general plugin architecture or implementing the full info/document panel model in this slice.
- Public routes must not load management-only controls or management-only JavaScript.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Inventory current index panel markup and ownership in `_includes/docs_viewer_shell.html`, `docs-viewer/shell/docs-viewer-shell.html`, `docs-viewer/runtime/js/docs-viewer.js`, `docs-viewer/runtime/js/docs-viewer-index-panel.js`, and `docs-viewer/runtime/js/docs-viewer-sidebar.js`. Deliverable: short implementation note in this tracker or closeout summary identifying the exact shell markup and refs to move. |
| 2 | planned | Define the focused app-shell surface for the index panel. Decide whether to extend `docs-viewer/runtime/js/docs-viewer-app-shell.js` directly or add a child renderer such as `docs-viewer-index-panel-renderer.js`. Deliverable: clear module ownership and no new broad shell responsibility added to `docs-viewer.js`. |
| 3 | planned | Decide the narrow relationship to the multi-panel request. If a small panel projection helper is needed, keep it limited to representing the existing index/document visibility states and defer info-panel or view-host architecture. |
| 4 | planned | Replace Liquid-owned index panel shell markup with minimal mounts/context while preserving the existing sidebar/nav behavior. Deliverable: shell templates no longer own full index panel chrome composition for the moved area. |
| 5 | planned | Render the index panel container, sidebar header, collapse/restore button, expand button, and nav mount from JavaScript. Preserve current ids: `docsViewerSidebarToggle`, `docsViewerSidebarExpand`, and `docsViewerNav`, unless a deliberate compatibility mapping is documented and tested. |
| 6 | planned | Keep `docs-viewer-sidebar.js` as the tree renderer inside `docsViewerNav`. Do not move tree row rendering, drag/drop behavior, management context menus, or tree visibility filtering in this pass. |
| 7 | planned | Keep current index panel state behavior working with minimal churn: collapsed, normal, expanded, per-scope storage, legacy sidebar storage migration, desktop-only controls, and mobile normalization. |
| 8 | planned | If refs move behind app-shell rendering, make `docs-viewer.js` wait for or receive those refs before initializing sidebar rendering, index-panel state, nav event delegation, and route handling. |
| 9 | planned | Preserve public route behavior for `/library/` and `/analysis/`: read-only boot, expected index controls, document pane visibility, search/recent behavior, and absence of management-only imports. |
| 10 | planned | Preserve local `/docs/` management behavior: index panel controls, tree interactions, manage-mode context menus, drag/drop wiring, scope switching, and browser history behavior. |
| 11 | planned | Add or update focused module smoke coverage for the index panel renderer/state. Cover public route rendering, management route rendering, id preservation, idempotent rendering, collapsed/normal/expanded projection, desktop/mobile availability, and storage migration where practical. |
| 12 | planned | Run the targeted verification set for changed JS, shell templates, index panel behavior, public read-only routes, and management routes. Record any checks skipped and why. |
| 13 | planned | Update owning docs after implementation. At minimum update this tracker, the app-shell request if the implemented shape changes the plan, the multi-panel request if any projection contract is introduced, and Docs Viewer runtime/inventory docs if `docs-viewer.js` ownership or risk materially changes. |

The closeout for this third migration should confirm:

- index panel shell ownership moved from Liquid toward JavaScript app-shell ownership
- shell templates keep only the necessary mounts/context for the moved index panel area
- `docs-viewer.js` remains a compatibility entrypoint and does not become the long-term app-shell owner
- `docs-viewer-sidebar.js` remains the tree renderer inside the index panel body
- current collapsed/normal/expanded behavior and persistence still work
- public read-only routes still render expected index controls and omit management-only UI/JS
- management tree interactions still work
- generated docs payloads were rebuilt by the watcher only if source docs changed, or intentionally not rebuilt by Codex
