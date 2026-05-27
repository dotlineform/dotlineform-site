---
doc_id: site-request-docs-viewer-app-shell-document-metadata-tasks
title: Docs Viewer App Shell Document Mount And Metadata Shell Tasks
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: done
parent_id: site-request-docs-viewer-javascript-app-shell
sort_order: 12108
viewable: true
---
# Docs Viewer App Shell Document Mount And Metadata Shell Tasks

This is the tracker for implementing the fourth app-shell migration slice from [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).

The fourth migration is the document mount and metadata shell.
It should move the document panel container, read-only document metadata shell, content mount, search/recent result mounts, and document/status visibility projection toward the JavaScript app shell without changing document payload loading, Markdown rendering, search/recent behavior, report rendering, bookmark behavior, or public route behavior.

This slice should align with [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell), but it should not implement the full document/info panel architecture unless the narrow document-shell migration requires a small enabling piece.

## Status

### just done

- Completed [Docs Viewer App Shell Management Actions Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-management-actions-tasks).
- Completed [Docs Viewer App Shell Header Controls Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-header-controls-tasks).
- Completed [Docs Viewer App Shell Index Panel Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-app-shell-index-panel-tasks).
- Established `docs-viewer/runtime/js/docs-viewer-app-shell.js` as the app-shell coordinator while keeping `docs-viewer/runtime/js/docs-viewer.js` as the compatibility entrypoint.
- Moved header controls, management action controls, and index panel chrome out of `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html`, leaving route-provided mounts/context for those areas.

### implementation closeout

- Moved the document shell markup from `_includes/docs_viewer_shell.html` and `docs-viewer/shell/docs-viewer-shell.html` into `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`, coordinated by `docs-viewer/runtime/js/docs-viewer-app-shell.js`.
- The templates now provide only `#docsViewerDocumentShellMount` for the moved area, with the existing no-JavaScript fallback text inside that mount.
- Preserved the existing refs: `docsViewerMeta`, `docsViewerPath`, `docsViewerUpdated`, `docsViewerSummary`, `docsViewerStatusPills`, `docsViewerBookmarkToggle`, `docsViewerContent`, `docsViewerResultsStatus`, `docsViewerResults`, and `docsViewerMore`.
- Kept `docs-viewer/runtime/js/docs-viewer-sidebar.js` as the breadcrumb/read-only metadata renderer and kept `docs-viewer/runtime/js/docs-viewer-document-controller.js` as the document payload, search/recent pane, generated report, missing-doc, and error controller.
- Added a narrow document-shell projection helper for current document/search/recent visibility and results-status state only; the broader info-panel/hosted-view architecture remains deferred to the multi-panel request.
- Updated `docs-viewer/runtime/js/docs-viewer.js` to read document refs from the app shell after shell rendering, then pass a document-shell projection callback into the existing document controller.

### verification closeout

- `node --check docs-viewer/runtime/js/docs-viewer.js`
- `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
- `node --check docs-viewer/runtime/js/docs-viewer-document-controller.js`
- `node --check docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `PYTHONDONTWRITEBYTECODE=1 $HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .`
- `git diff --check`

The broad `docs_viewer_routes.py --site-root .` smoke was not run because the current isolated public build shape covers `/library/` and `/analysis/`, while `/docs/` management is served by the standalone Docs Viewer service and was covered by `docs_viewer_service_manage.py`.

### steer for next task

- Implement the document mount and metadata shell as the next narrow app-shell-owned shell responsibility.
- Keep the slice focused on `.docsViewer__main`, read-only metadata chrome, `docsViewerContent`, `docsViewerResultsStatus`, `docsViewerResults`, `docsViewerMore`, and document/search/recent visibility projection.
- Preserve the current `docs-viewer/runtime/js/docs-viewer-document-controller.js` payload, report, search/recent pane, and missing/error rendering contracts unless a small, tested shell-ref handoff is clearly needed.
- Preserve `docs-viewer/runtime/js/docs-viewer-sidebar.js` ownership of breadcrumb metadata rendering unless the slice creates a focused document metadata renderer and rewires it deliberately.
- Do not move document payload fetching, Markdown rendering, generated report rendering, search/recent result rendering, bookmark storage behavior, management command behavior, metadata edit modal internals, import modal internals, or info-panel views in this pass.
- Preserve existing ids or provide a deliberate compatibility mapping for `docsViewerMeta`, `docsViewerPath`, `docsViewerUpdated`, `docsViewerSummary`, `docsViewerStatusPills`, `docsViewerBookmarkToggle`, `docsViewerContent`, `docsViewerResultsStatus`, `docsViewerResults`, and `docsViewerMore`.
- Keep public read-only behavior for `/library/` and `/analysis/` unchanged.

### baseline verification set

Run only the checks warranted by the touched files.
For this slice, the expected verification set is:

- JavaScript syntax checks:
  - `node --check docs-viewer/runtime/js/docs-viewer.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-app-shell.js`
  - `node --check docs-viewer/runtime/js/docs-viewer-document-controller.js`
  - any changed focused app-shell/document-shell modules
- Focused module smoke checks when document refs, IDs, or shell render ownership change:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`
  - add or extend a focused document-shell module smoke if existing coverage does not pin the moved refs and visibility projection
- Route/document behavior smoke checks when document mount, metadata refs, history, hash navigation, search/recent panes, or route loading changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_routes.py --site-root .`
  - focused public Library document/hash/search smoke if the broad route smoke cannot run against the current isolated build shape
- Public read-only smoke when shell markup or route boot changes:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build`
- Management service smoke when management-route document shell, status pills, bookmarks, or metadata refs are touched:
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
  - `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_modal.py --site-root .` if metadata edit modal refs or status-pill behavior are touched
- Jekyll build only when includes, route templates, CSS, or loaded assets change:
  - `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when product code is healthy.
Use `PYTHONDONTWRITEBYTECODE=1` for Python smoke checks when practical so test runs do not create watched `__pycache__` files.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the JavaScript maintenance gate for high-risk shared runtime files.
- This slice is part of the app-shell enabling work, not a broad `docs-viewer.js` refactor.
- Keep `docs-viewer.js` as orchestration only: boot/config handoff, route readiness, existing controller wiring, and calls into focused owners.
- New shell rendering should live in `docs-viewer/runtime/js/docs-viewer-app-shell.js` or focused app-shell child modules.
- Treat the document shell as a shell/layout responsibility and document payload rendering as a body renderer/controller responsibility.
- Avoid creating the full info-panel architecture in this slice; add only a narrow compatibility projection if the moved document shell requires it.
- Public routes must not load management-only controls or management-only JavaScript.
- Backend endpoints continue to enforce writes and filesystem operations; document shell migration must not add browser-side write authority.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Inventory current document panel and read-only metadata shell markup and ownership in `_includes/docs_viewer_shell.html`, `docs-viewer/shell/docs-viewer-shell.html`, `docs-viewer/runtime/js/docs-viewer.js`, `docs-viewer/runtime/js/docs-viewer-document-controller.js`, `docs-viewer/runtime/js/docs-viewer-sidebar.js`, and management modules that read status/metadata refs. Deliverable: short implementation note in this tracker or closeout summary identifying the exact shell markup and refs to move. |
| 2 | done | Define the focused app-shell surface for the document mount and metadata shell. Decide whether to extend `docs-viewer/runtime/js/docs-viewer-app-shell.js` directly or add a child renderer such as `docs-viewer-document-shell-renderer.js`. Deliverable: clear module ownership and no new broad shell responsibility added to `docs-viewer.js`. |
| 3 | done | Decide the narrow relationship to the multi-panel request. If a small document-panel projection helper is needed, keep it limited to the current document/search/recent/report mount visibility states and defer info-panel or hosted-view architecture. |
| 4 | done | Replace Liquid-owned document panel shell markup with minimal mounts/context while preserving existing document, search, recent, report, bookmark, and status-pill behavior. Deliverable: shell templates no longer own full document panel chrome composition for the moved area. |
| 5 | done | Render `.docsViewer__main`, `docsViewerMeta`, metadata row/copy/actions, `docsViewerContent`, `docsViewerResultsStatus`, `docsViewerResults`, and `docsViewerMore` from JavaScript. Preserve current ids unless a deliberate compatibility mapping is documented and tested. |
| 6 | done | Keep `docs-viewer-document-controller.js` as the document payload, missing/error, search/recent pane, and report host controller. Do not move Markdown rendering, generated report loading, payload fetching, or search/recent result rendering in this pass. |
| 7 | done | Keep current read-only metadata behavior working with minimal churn: breadcrumbs, updated date, summary, status pills, bookmark toggle, hidden/draft indicators, and selected-document projection. |
| 8 | done | If refs move behind app-shell rendering, make `docs-viewer.js` wait for or receive those refs before initializing document controller, sidebar metadata rendering, bookmark rendering, status-pill rendering, route handling, and management status behavior. |
| 9 | done | Preserve public route behavior for `/library/` and `/analysis/`: read-only boot, document payload rendering, hash navigation, metadata visibility, search/recent behavior, report rendering, bookmarks, and absence of management-only imports. |
| 10 | done | Preserve local `/docs/` management behavior: document rendering, manage-mode status pills, bookmark toggle, metadata edit flow, report rendering, browser history behavior, and management status messages. |
| 11 | done | Add or update focused module smoke coverage for the document shell renderer/projection. Cover public route rendering, management route rendering, id preservation, idempotent rendering, document/search/recent visibility projection, metadata refs, and management-only omission where practical. |
| 12 | done | Run the targeted verification set for changed JS, shell templates, document shell behavior, public read-only routes, and management routes. Record any checks skipped and why. |
| 13 | done | Update owning docs after implementation. At minimum update this tracker, the app-shell request if the implemented shape changes the plan, the multi-panel request if any projection contract is introduced, and Docs Viewer runtime/inventory docs if `docs-viewer.js` ownership or risk materially changes. |

The closeout for this fourth migration should confirm:

- document mount and read-only metadata shell ownership moved from Liquid toward JavaScript app-shell ownership
- shell templates keep only the necessary mounts/context for the moved document shell area
- `docs-viewer.js` remains a compatibility entrypoint and does not become the long-term app-shell owner
- `docs-viewer-document-controller.js` remains the document/search/recent/report body controller
- current document, metadata, search/recent, report, bookmark, and status-pill behavior still works
- public read-only routes still render expected document shell and omit management-only UI/JS
- management document and metadata interactions still work
- generated docs payloads were rebuilt by the watcher only if source docs changed, or intentionally not rebuilt by Codex
