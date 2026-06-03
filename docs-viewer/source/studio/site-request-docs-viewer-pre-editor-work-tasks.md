---
doc_id: site-request-docs-viewer-pre-editor-work-tasks
title: Docs Viewer Pre-Editor Work Tasks
added_date: 2026-06-03
last_updated: 2026-06-03
ui_status: in-progress
parent_id: site-request-docs-viewer-markdown-editor
viewable: true
---
# Docs Viewer Pre-Editor Work Tasks

This is the tracker for implementing [Docs Viewer Pre-Editor Work Request](/docs/?scope=studio&doc=site-request-docs-viewer-pre-editor-work).

When the work is complete, move durable architecture notes into the owning Docs Viewer docs, then delete this task tracker and the temporary request spec.

## Status

### just done

- An initial compatibility-shaped code patch was backed out before verification because it mapped old `document` panel ids to new `main` ids instead of first doing the remedial ownership cleanup.
- Completed the first direct cleanup slice without compatibility aliases:
  - route config now uses `panels.main.default_view: rendered-document`
  - hosted-view records now use the `main` panel with `rendered-document`, `search-results`, and `recent-results`
  - `document-host` and `panels.document` were retired rather than mapped
  - the shell mount is now `data-docs-viewer-main-view-mount`
  - app-shell refs now expose `mainView`
  - `docs-viewer-main-view-renderer.js` owns the central shell renderer
  - `docs-viewer-main-view-host.js` owns main-view switch validation and active-view state projection
- Search and recent now request `search-results` and `recent-results` through the main-view host while existing controllers still render their current panes.
- Durable docs were updated for the main-view boundary and report-host deferral.
- Completed the focused toolbar projection and source-editor context preparation slice:
  - rendered-document breadcrumbs, updated date, status pills, and bookmark/favourite control now sit inside the explicit `docsViewerMainViewToolbar` surface
  - the main-view renderer exposes `mainView.toolbar` refs and supports `toolbarHidden` projection
  - the document controller projects toolbar visibility for rendered-document, search-results, recent-results, loading, missing, and error states
  - the main-view host exposes generic toolbar projection and module-context helpers without source-editor service details
  - `docs-viewer-view-context.js` defines `createDocsViewerMainViewModuleContext(...)` with selected document, scope, route access, `mainView` intent/toolbar/warning helpers, and management-gated `sourceEditorServices`
  - public main-view contexts omit source-editor services even if a caller supplies them
  - durable toolbar, panel-host, runtime-boundary, and JavaScript inventory docs were updated

### steer for next task

- Continue with main-view module registration boundary.
- Define explicit built-in/repo-owned registration for future main-view modules without route-config arbitrary module loading or plugin-system behavior.
- `mainView` is the policy for the central panel architecture boundary: host, toolbar, view-state, hosted-view registry, route-config panel ids, context contracts, and durable docs.
- `document` remains only where the code specifically means rendered document payload behavior.
- Do not add dual-read fields, old-id mappings, compatibility aliases, fallback route-config names, or temporary selector aliases unless the tracker records the justification before implementation and the user confirms that exception.
- A compatibility exception must include exact need, affected files, expected lifespan, removal criteria, and verification required before removal.
- Low implementation risk means smaller remediated slices with evidence, not preserving the old infrastructure behind new names.
- The remaining `projectDocumentShell` naming is inside `docs-viewer-document-controller.js` and its controller context, where it still describes the current rendered-document/search/recent projection handoff. Do not expand that name back into app-shell, route-config, or hosted-view contracts.

### baseline verification set

Use the smallest checks that match each implementation slice.

- Source/docs-only updates: source review and `git diff --check`.
- JavaScript architecture slices: focused module syntax/import checks where practical.
- Main-view host and toolbar slices: public route boot, manage route boot, rendered document load, selected-document update, search continuity, recent continuity, and desktop/mobile toolbar layout checks.
- Report behavior should be smoke checked for continuity if touched, but report-host migration is not expected in this implementation.
- Broader Docs Viewer checks should use the narrowest relevant profile from [Testing](/docs/?scope=studio&doc=testing) and [Run Checks](/docs/?scope=studio&doc=scripts-run-checks).

Codex sandbox note: local service, browser, and temporary localhost checks may need elevated permissions even when the product code is healthy.

Closeout note: do not treat `docs-viewer/tests/smoke/public_docs_viewer_readonly.py` as required local verification for this pre-editor work. Public desktop/mobile deploy validation is expected to move to GitHub Actions soon, making this local public-site smoke redundant. Until that deploy smoke exists, use focused module smoke plus targeted runtime checks for pre-editor slices unless the change specifically touches public route generation or deploy behavior.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the Docs Viewer App Architecture Gate and JavaScript Maintenance Gate.
- Treat terminology and ownership cleanup as required remedial work, not optional polish.
- Keep the main-view host generic: switching, mount/unmount, toolbar projection, context handoff, unavailable-state handling, and lifecycle coordination.
- Do not make the host know source-editor service details.
- Do not couple the future source editor to the existing lazy management controller or broad management state.
- Do not create plugin manifests, package protocols, marketplaces, third-party loaders, or arbitrary route-config module string loading.
- Do not add compatibility paths to avoid current-code cleanup. If a compatibility path appears necessary, stop before implementation and record the exception decision in this tracker.
- Keep view-specific UI text near the hosted view or a view-local config module; keep shared `ui-text.json` for genuinely shared route-wide copy.
- Keep backend authority separate from frontend availability. Frontend route access and capability projection are visibility helpers only.
- When implementation changes current panel-host behavior, update durable docs such as [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts), [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Toolbar Model](/docs/?scope=studio&doc=docs-viewer-toolbar-model), and [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory).

### compatibility exception gate

Compatibility behavior is prohibited by default for this work.

This includes:

- accepting both `panels.document` and `panels.main` as equivalent current route-config fields
- mapping `document-host` to `rendered-document`
- mapping hosted-view panel `document` to `main`
- returning duplicate `document` and `main` view-state projections for the same panel
- adding CSS selector aliases or duplicate DOM refs to avoid updating the current owner boundary

Before any exception is implemented, record:

- why direct remedial cleanup is not practical in this slice
- which active user workflow or route would break without the exception
- exact files and fields affected
- how long the exception is expected to live
- removal criteria
- verification required before and after removal

If that justification is not written before the code change, do the remedial cleanup instead.

## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action. Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Main-view terminology audit: list current `document` uses in route config, hosted-view records, view state, panel layout, app shell refs, document shell renderer, CSS selectors, document controller, search/recent flow, toolbar docs, and durable docs; classify each as true rendered-document behavior or legacy central-panel terminology. |
| 2 | done | Remedial cleanup decision checkpoint: from the audit, define the direct cleanup slice and confirm that no compatibility exception is needed. If an exception is proposed, record the full compatibility exception gate details before code changes and ask for confirmation. |
| 3 | done | Main-view route/config/state cleanup: update current route config, hosted-view panel ids, view-state domain, and panel-layout contracts to use `mainView`/`main` directly for the central panel. Do not dual-read old and new fields unless task 2 explicitly approved an exception. |
| 4 | done | Main-view shell/ref cleanup: rename or reshape app-shell and panel refs at the ownership boundary so new host and toolbar code consumes `mainView` refs. Keep existing rendered-document DOM/CSS names only where they specifically own rendered document payload or visual styling that is not part of the host contract. |
| 5 | done | Main-view host foundation: create the host/controller lifecycle boundary for the central content region; support explicit hosted-view records for `rendered-document`, `search-results`, `recent-results`, and future `markdown-source`; preserve selected-document state independent from main-view visibility. |
| 6 | done | Main-view toolbar projection: move current rendered-document breadcrumbs, updated date, status pill, bookmark/favourite controls, index tree collapse/expand, and info title/close controls into explicit panel toolbar ownership without a visual redesign. |
| 7 | done | Main-view switch intents: define the hosted-view intent contract so views request replacement views through the host, such as future `rendered-document` `Edit` requesting `markdown-source`; keep direct view-to-view imports/calls out of the contract. |
| 8 | done | State, unavailable, and lifecycle policies in code: make app/view state the host source of truth; avoid URL as host state; hide manage-only controls on public routes; show simple local warnings for requested views that cannot load; default to unmount/clear hidden views without blocking future per-view retained-state capabilities. |
| 9 | done | Source-editor module context preparation: define the explicit main-view module context shape with selected document, scope, route access, `mainView` intent/toolbar/warning helpers, and optional source-editor service slots; ensure public contexts omit source-editor services. |
| 10 | done | Migrate search and recent: move `search-results` and `recent-results` onto the same main-view hosting mechanism to prove the host with existing user-facing views before implementing `markdown-source`; preserve current search/recent route continuity and behavior. |
| 11 | planned | Main-view module registration boundary: establish explicit registration for built-in or repo-owned main-view modules without arbitrary route-config module loading or plugin-system behavior. |
| 12 | in progress | Focused verification: run the agreed checks for public/manage boot, rendered document load, selected-document updates, search/recent continuity, toolbar layout, and any touched JavaScript syntax/import checks; record results in this tracker. |
| 13 | in progress | Durable docs closeout: move durable architecture notes into owning Docs Viewer docs, update inventory rows where needed, record the report-host migration follow-up decision, and remove this temporary task tracker plus the pre-editor request when no longer needed. |
| 14 | deferred | Report-host main-view migration: defer unless implementation reveals a direct need. Current report behavior works; revisit after pre-editor work if reports need shared toolbar projection, shared lifecycle behavior, or cleaner replacement semantics. |

## Closeout Notes

When the implementation is complete:

- Update this tracker with changed files, decisions made, commands run, and known risks.
- Confirm durable decisions have moved to permanent Docs Viewer docs.
- Confirm the Markdown editor request can proceed with a stable main-view host environment.
- Confirm public desktop/mobile route coverage has either moved to GitHub Actions deploy validation or the old local `public_docs_viewer_readonly.py` smoke has been explicitly retired from the required local closeout set.
- Delete this tracker and the pre-editor request once their temporary planning purpose is complete.

## Verification Log

- Passed: `node --check` for touched Docs Viewer runtime modules.
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py docs-viewer/tests/smoke/docs_viewer_service_manage.py docs-viewer/tests/smoke/public_docs_viewer_readonly.py`.
- Passed: `git diff --check`.
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-main-view-renderer.js`.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-document-controller.js`.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-main-view-host.js`.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-view-context.js`.
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js`.
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py`.
- Passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_app_shell_modules.py --site-root .`.
- Passed: `git diff --check`.
- Blocked: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root .` timed out waiting for `#docsViewerRoot:not([hidden])`; the smoke expects a built public-site root, not the repo root.
- Blocked: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root _site` reached the route root, then timed out waiting for the expected public document heading; the current `_site` output is not a reliable fresh target for this smoke.
- Partial: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py` reaches the report section, then fails an existing report-status expectation because the UI reports `27 broken links` rather than including the selected scope. This is outside the main-view migration and report-host migration remains deferred.
