---
doc_id: site-request-docs-viewer-app-shell-header-controls-tasks
title: Docs Viewer App Shell Header Controls Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: done
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

### implementation note

Implemented 2026-05-27.
The header-control markup moved out of `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html`.
Both shells now provide `#docsViewerHeaderControlsMount` with route context for search enabled/disabled state, placeholder text, and aria label text.
`docs-viewer/runtime/js/docs-viewer-app-shell.js` delegates header rendering to `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`, then renders the management action row into the management mount only when the route allows management.

The replaced Liquid-owned area was the duplicated `.docsViewer__searchRow` composition:
scope select placement for `allow_scope_query`, the recently-added button, the search input label/placeholder/aria label, and the management action mount in the search-enabled and scope-only branches.
The renderer preserves the existing runtime IDs: `docsViewerScopeSelect`, `docsViewerRecentButton`, `docsViewerSearchInput`, and `docsViewerManageActionsMount`.
`docs-viewer.js` still reads those IDs synchronously after app-shell initialization, so config, route, search, bookmark, and management controllers did not need a broad rewrite.

### verification

- Passed: `node --check docs-viewer/runtime/js/docs-viewer.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/services/docs_viewer_service.py docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`
- Passed: `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- Passed: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- Passed: `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Passed: focused public Library header/search smoke against `/tmp/dlf-jekyll-build`
- Passed: `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- Passed: `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_scope_ui.py`
- Not used for closeout: `docs_viewer_routes.py --site-root /tmp/dlf-jekyll-build`, because this repo's public Jekyll config excludes `/docs/` from the isolated public build. The moved header-control behavior was covered by focused app-shell module checks, the public Library route/search smoke, public read-only smoke, standalone `/docs/` management smoke, and management scope UI smoke.

Codex did not run a Docs Viewer docs/search payload rebuild.
The live docs watcher regenerated the affected Studio docs payloads after source-doc edits, and those generated changes were left in place.

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
| 1 | done | Inventoried the duplicated header-control area in `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html`: both shells composed `.docsViewer__searchRow`, optional `docsViewerScopeSelect`, `docsViewerRecentButton`, `docsViewerSearchInput`, search labels/placeholders, and the management action mount across search-enabled and scope-only branches. |
| 2 | done | Added focused header ownership in `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`, coordinated by `docs-viewer/runtime/js/docs-viewer-app-shell.js`. `docs-viewer.js` remains the compatibility entrypoint and controller orchestration file. |
| 3 | done | Replaced the full Liquid header-control composition in both shell templates with `#docsViewerHeaderControlsMount` and route context data attributes for search enabled state and search copy. |
| 4 | done | Rendered the scope picker, recent button, and search input from JavaScript where route options require them, preserving `docsViewerScopeSelect`, `docsViewerRecentButton`, and `docsViewerSearchInput`. |
| 5 | done | Kept config, route, and search modules on the existing synchronous ID contract. Header controls render synchronously during app-shell initialization before `docs-viewer.js` reads refs. |
| 6 | done | Preserved search-enabled and search-disabled rendering branches. Public `/library/` and `/analysis/` remain read-only and omit management-only UI/JS. |
| 7 | done | Preserved manage-mode scope switching. The local `/docs/` management shell renders the scope picker through the app shell and the existing config controller still owns option loading and scope-change navigation. |
| 8 | done | Extended `docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py` to cover public search-enabled rendering, search-disabled scope-only rendering, management rendering, preserved IDs/order, and idempotent rendering. |
| 9 | done | Ran the targeted verification set recorded above. The broad `docs_viewer_routes.py` isolated-build check was not used for closeout because `/docs/` is excluded from the public Jekyll build. |
| 10 | done | Updated this tracker, the app-shell request, Docs Viewer overview, and Docs Viewer JavaScript inventory notes. Added a structured docs-log entry for the completed slice. |

The closeout for this second migration should confirm:

- header control ownership moved from Liquid toward JavaScript app-shell ownership
- shell templates keep only the necessary mounts/context for the moved header-control area
- `docs-viewer.js` remains a compatibility entrypoint and does not become the long-term app-shell owner
- public read-only routes still render expected controls and omit management-only UI/JS
- management scope switching still works
- generated docs payloads were rebuilt by the watcher only if source docs changed, or intentionally not rebuilt by Codex
