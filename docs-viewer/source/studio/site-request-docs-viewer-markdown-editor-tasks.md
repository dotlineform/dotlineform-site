---
doc_id: site-request-docs-viewer-markdown-editor-tasks
title: Docs Viewer Markdown Editor Tasks
added_date: 2026-06-03
last_updated: 2026-06-03
ui_status: planned
parent_id: site-request-docs-viewer-markdown-editor
viewable: true
---
# Docs Viewer Markdown Editor Tasks

This is the tracker for implementing [Docs Viewer Markdown Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor).

When the work is complete, move durable architecture notes into the owning Docs Viewer docs, then close out this task tracker and the parent request.

## Status

### just done

- Implemented and cleaned up the first source-editor slice:
  - added management-only `/docs/source` and `/docs/source/rebuild` endpoints
  - used SHA-256 source revision tokens for stale-write protection
  - preserved the existing front matter block exactly while replacing only the Markdown body
  - registered `markdown-source` as a repo-owned manage-only main hosted view
  - wired `Markdown source` through the existing management action-controller/button style rather than ad hoc document-level click handling
  - passed main-view `mount`, requested view id, and source-editor service methods through explicit main-view context
  - added a first-party native textarea editor with logical line-number gutter and dirty-state handling
  - added dirty leave confirmation with `Do you want to save changes?`, `Yes`, and `No`
  - verified `No` discards the browser buffer and reloads the rendered document view
  - confirmed no third-party editor dependency was added

- Request decisions were locked for the implementation path:
  - the editor is a manage-only `markdown-source` main-view hosted view
  - the editor is body-only and does not expose or mutate front matter
  - document metadata/front matter stays in the existing manage-mode Actions flow
  - source read/write payloads use `source_body` plus a source revision token
  - `Rebuild doc` writes the source body, preserves front matter, then runs targeted docs payload and targeted docs-search rebuilds for the selected doc
  - the editor uses a first-party lightweight native editor wrapper, not CodeMirror, Monaco, or another full editor dependency
  - line numbers are a simple logical-line gutter for source-body and token debugging
  - dirty state uses direct normalized body comparison, not a required hash
  - dirty in-app leave uses the simple UI Catalogue modal: `Do you want to save changes?` with `Yes` and `No`

### steer for next task

- Start with backend source-body read/write/rebuild contracts so the frontend has stable endpoint shapes.
- Keep source-body mutation separate from metadata/front matter mutation.
- Keep the main-view host generic; do not make it know source-editor service details.
- Replace the disabled manage-only `markdown-source` placeholder through the code-owned hosted-view registration boundary.
- Do not add arbitrary route-config module loading, plugin behavior, or third-party editor dependencies.
- Preserve current rendered document, search, recent, and report behavior while adding the editor.

### baseline verification set

Use the smallest checks that match each implementation slice.

- Docs-only tracker updates: source review, generated payload status, and `git diff --check`.
- Backend source/rebuild slices: focused pytest for source read, source-body write, stale revision, front matter preservation, targeted docs/search rebuild command shaping, and failure diagnostics.
- JavaScript module slices: `node --check` for touched Docs Viewer runtime modules and focused module smoke where practical.
- Main-view/editor slices: manage route boot, public route boot with no source action, rendered-document to `markdown-source` switch, source load, dirty state, dirty leave modal `Yes`/`No`, rebuild success return, and rebuild failure staying in source view.
- UI layout slices: desktop/mobile checks for the first-party editor wrapper, logical-line gutter, scroll sync, toolbar actions, and modal behavior.
- Broader checks should use the narrowest relevant profile from [Testing](/docs/?scope=studio&doc=testing) and [Run Checks](/docs/?scope=studio&doc=scripts-run-checks).

Codex sandbox note: local service, browser, and temporary localhost checks may need elevated permissions even when the product code is healthy.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the Docs Viewer App Architecture Gate and JavaScript Maintenance Gate.
- Keep route entry modules as orchestration shells; put source-editor behavior in focused service, state, render, modal, and workflow modules.
- Keep source editor UI text near the source-editor module unless the copy is genuinely shared route-wide.
- Frontend route access and capability projection are visibility helpers only; backend endpoints remain authoritative for source read/write, revision, allowlist, and rebuild validation.
- Do not edit front matter in this request. If metadata/front matter changes are needed, use the existing manage-mode Actions flow.
- Do not add soft-wrap line-number measurement, hidden mirrors, minimaps, folding, syntax highlighting, Markdown formatting toolbars, or a full editor dependency in this slice.
- If a compatibility path seems necessary, stop and record the exception decision before implementation.
- When behavior changes current panel-host, runtime, toolbar, or management boundaries, update durable docs such as [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts), [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Toolbar Model](/docs/?scope=studio&doc=docs-viewer-toolbar-model), and [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory).

## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action. Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Source-editor contract checkpoint: confirm endpoint names, `source_body` payload shape, revision token semantics, body/front-matter split rules, targeted docs/search rebuild behavior, and UI copy before code changes. |
| 2 | done | Backend source-body read service: add the management read endpoint for selected-doc source body and revision token; enforce manage capability, scope/doc allowlist, existing front matter parseability, and `doc_id` consistency. |
| 3 | done | Backend source-body write/rebuild service: add the management write/rebuild endpoint that accepts `source_body` plus revision token, preserves existing front matter exactly, writes the body, runs targeted docs payload and targeted docs-search rebuilds for the selected doc, and returns structured diagnostics. |
| 4 | done | Backend source/rebuild tests: cover source-body read, stale revision rejection, invalid existing front matter, front matter preservation, source-body write, targeted docs/search command shaping, rebuild diagnostics, and failure behavior. |
| 5 | done | Main-view registration: replace the disabled manage-only `markdown-source` placeholder with the real repo-owned hosted view through `createDocsViewerDefaultHostedViews()` without route-config module loading or plugin behavior. |
| 6 | done | Source-editor module context and services: pass selected document, scope, route access, `mainView` helpers, and capability-gated source-editor service methods through the explicit main-view module context; keep public contexts service-free. |
| 7 | done | Source-editor state and workflow module: load source body/revision on entry, store the normalized last-clean body, compute dirty state by direct normalized body comparison, keep revision token separate, and project toolbar/status state. |
| 8 | done | First-party native editor wrapper: render native text editing with repo-owned line-number gutter, no soft wrap, logical-line numbering, horizontal scrolling, selection/cursor helpers, and vertical scroll sync. |
| 9 | done | Dirty leave modal: use the simple UI Catalogue modal for dirty in-app leave attempts with `Do you want to save changes?`, `Yes`, and `No`; `Yes` runs `Rebuild doc`, `No` discards the local buffer, and browser reload/tab close uses native unload warning where available. |
| 10 | in progress | Rebuild and return workflow: implement `Rebuild doc` submit, pending/disabled states, diagnostics rendering, success payload reload, switch back to `rendered-document`, and failure behavior that keeps the user in `markdown-source`. |
| 11 | done | Access, unavailable, and continuity checks: hide source actions on public routes, show local unavailable warnings for unavailable manage-only source view requests, preserve selected-document state, and verify rendered/search/recent/report continuity. |
| 12 | in progress | Focused frontend verification: run module syntax checks and focused manage/public browser smokes for source action visibility, source load, line-number gutter, dirty comparison including undo-to-clean, dirty modal `Yes`/`No`, rebuild success return, rebuild failure, and desktop/mobile layout. |
| 13 | planned | Durable docs closeout: update owning Docs Viewer management, runtime boundary, panel host, toolbar, JavaScript inventory, and testing docs where behavior changed; record generated payload status and remaining risks. |
| 14 | planned | Final request closeout: update this tracker and the parent request statuses, record changed files and commands run, confirm open questions are resolved, confirm no third-party editor dependency was added, and note any deferred follow-up work. |

## Closeout Notes

When the implementation is complete:

- Update this tracker with changed files, decisions made, commands run, generated payload status, and known risks.
- Confirm durable decisions have moved to permanent Docs Viewer docs.
- Confirm source editing is body-only and metadata/front matter remains in manage-mode Actions.
- Confirm `Rebuild doc` refreshes both targeted docs payload and targeted docs search for the selected doc.
- Confirm public routes do not expose authoring UI or source-editor services.
- Confirm no third-party full editor dependency was introduced.

## Verification Log

- Passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_management_source_service.py docs-viewer/tests/python/test_docs_management_routes.py`
- Passed: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/services/docs_management_routes.py docs-viewer/services/docs_management_source_service.py docs-viewer/services/docs_management_read_service.py docs-viewer/services/docs_management_service.py docs-viewer/services/docs_management_capabilities_service.py docs-viewer/services/docs_viewer_service.py`
- Passed: `node --check docs-viewer/runtime/js/docs-viewer-app-runtime.js docs-viewer/runtime/js/docs-viewer-hosted-views.js docs-viewer/runtime/js/docs-viewer-main-view-host.js docs-viewer/runtime/js/docs-viewer-management.js docs-viewer/runtime/js/docs-viewer-management-actions.js docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js docs-viewer/runtime/js/docs-viewer-management-client.js docs-viewer/runtime/js/docs-viewer-view-context.js docs-viewer/runtime/js/modules/source-editor/source-editor.js`
- Passed focused browser smoke on temporary Docs Viewer service `http://127.0.0.1:8790/docs/`: manage `Markdown source` action visible, source editor loads, logical gutter starts `1,2,3`, dirty state appears, dirty leave `No` returns to rendered document, mobile editor visible, and public route keeps management row hidden.
- Not yet run: browser click of `Rebuild doc` against a real source file, to avoid mutating source during the cleanup pass. Backend tests cover write/rebuild command shaping and front matter preservation.
