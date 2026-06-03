---
doc_id: site-request-docs-viewer-pre-editor-work-tasks
title: Docs Viewer Pre-Editor Work Tasks
added_date: 2026-06-03
last_updated: 2026-06-03
ui_status: planned
parent_id: site-request-docs-viewer-markdown-editor
viewable: true
---
# Docs Viewer Pre-Editor Work Tasks

This is the tracker for implementing [Docs Viewer Pre-Editor Work Request](/docs/?scope=studio&doc=site-request-docs-viewer-pre-editor-work).

When the work is complete, move durable architecture notes into the owning Docs Viewer docs, then delete this task tracker and the temporary request spec.

## Status

### just done

- Task tracker created from the locked pre-editor request shape.

### steer for next task

- Start with terminology alignment at the new main-view ownership boundary.
- Keep the migration targeted: use `mainView` for new host, toolbar, view-state, hosted-view, and context contracts; keep `document` where it specifically means rendered document payload behavior.
- Avoid broad CSS, DOM id, or controller renames unless they are part of the new main-view boundary.
- Record any temporary aliases and their removal criteria.

### baseline verification set

Use the smallest checks that match each implementation slice.

- Source/docs-only updates: source review and `git diff --check`.
- JavaScript architecture slices: focused module syntax/import checks where practical.
- Main-view host and toolbar slices: public route boot, manage route boot, rendered document load, selected-document update, search continuity, recent continuity, and desktop/mobile toolbar layout checks.
- Report behavior should be smoke checked for continuity if touched, but report-host migration is not expected in this implementation.
- Broader Docs Viewer checks should use the narrowest relevant profile from [Testing](/docs/?scope=studio&doc=testing) and [Run Checks](/docs/?scope=studio&doc=scripts-run-checks).

Codex sandbox note: local service, browser, and temporary localhost checks may need elevated permissions even when the product code is healthy.

### general steer

- Follow [Development Workflow](/docs/?scope=studio&doc=development-workflow), especially the Docs Viewer App Architecture Gate and JavaScript Maintenance Gate.
- Keep the main-view host generic: switching, mount/unmount, toolbar projection, context handoff, unavailable-state handling, and lifecycle coordination.
- Do not make the host know source-editor service details.
- Do not couple the future source editor to the existing lazy management controller or broad management state.
- Do not create plugin manifests, package protocols, marketplaces, third-party loaders, or arbitrary route-config module string loading.
- Keep view-specific UI text near the hosted view or a view-local config module; keep shared `ui-text.json` for genuinely shared route-wide copy.
- Keep backend authority separate from frontend availability. Frontend route access and capability projection are visibility helpers only.
- When implementation changes current panel-host behavior, update durable docs such as [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts), [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer Toolbar Model](/docs/?scope=studio&doc=docs-viewer-toolbar-model), and [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory).

## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action. Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Main-view terminology alignment: introduce `mainView` naming for new host, toolbar, view-state, hosted-view, and context contracts; keep `document` naming only where it specifically means rendered document payload behavior; avoid broad selector/controller renames unless required by the new host boundary; identify temporary aliases and removal criteria. |
| 2 | planned | Main-view host foundation: create the host/controller lifecycle boundary for the central content region; support explicit hosted-view records for `rendered-document`, `search-results`, `recent-results`, and future `markdown-source`; preserve selected-document state independent from main-view visibility. |
| 3 | planned | Main-view toolbar projection: move current rendered-document breadcrumbs, updated date, status pill, bookmark/favourite controls, index tree collapse/expand, and info title/close controls into explicit panel toolbar ownership without a visual redesign. |
| 4 | planned | Main-view switch intents: define the hosted-view intent contract so views request replacement views through the host, such as future `rendered-document` `Edit` requesting `markdown-source`; keep direct view-to-view imports/calls out of the contract. |
| 5 | planned | State, unavailable, and lifecycle policies in code: make app/view state the host source of truth; avoid URL as host state; hide manage-only controls on public routes; show simple local warnings for requested views that cannot load; default to unmount/clear hidden views without blocking future per-view retained-state capabilities. |
| 6 | planned | Source-editor module context preparation: define the explicit main-view module context shape with selected document, scope, route access, `mainView` intent/toolbar/warning helpers, and optional source-editor service slots; ensure public contexts omit source-editor services. |
| 7 | planned | Migrate search and recent: move `search-results` and `recent-results` onto the same main-view hosting mechanism to prove the host with existing user-facing views before implementing `markdown-source`; preserve current search/recent route continuity and behavior. |
| 8 | planned | Main-view module registration boundary: establish explicit registration for built-in or repo-owned main-view modules without arbitrary route-config module loading or plugin-system behavior. |
| 9 | planned | Focused verification: run the agreed checks for public/manage boot, rendered document load, selected-document updates, search/recent continuity, toolbar layout, and any touched JavaScript syntax/import checks; record results in this tracker. |
| 10 | planned | Durable docs closeout: move durable architecture notes into owning Docs Viewer docs, update inventory rows where needed, record the report-host migration follow-up decision, and remove this temporary task tracker plus the pre-editor request when no longer needed. |
| 11 | deferred | Report-host main-view migration: defer unless implementation reveals a direct need. Current report behavior works; revisit after pre-editor work if reports need shared toolbar projection, shared lifecycle behavior, or cleaner replacement semantics. |

## Closeout Notes

When the implementation is complete:

- Update this tracker with changed files, decisions made, commands run, and known risks.
- Confirm durable decisions have moved to permanent Docs Viewer docs.
- Confirm the Markdown editor request can proceed with a stable main-view host environment.
- Delete this tracker and the pre-editor request once their temporary planning purpose is complete.
