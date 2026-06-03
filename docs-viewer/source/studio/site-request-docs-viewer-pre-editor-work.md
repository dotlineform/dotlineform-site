---
doc_id: site-request-docs-viewer-pre-editor-work
title: Docs Viewer Pre-Editor Work Request
added_date: 2026-06-03
last_updated: 2026-06-03
ui_status: in-progress
parent_id: site-request-docs-viewer-markdown-editor
viewable: true
---
# Docs Viewer Pre-Editor Work Request

Status:

- proposed
- child request of [Docs Viewer Markdown Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor)

## Summary

Prepare the Docs Viewer app shell so the Markdown editor can be implemented as a manage-only document-panel hosted view.

This request is intentionally narrower than the broader [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell).
It covers only the panel, toolbar, view-state, and module-registration work needed before the source editor can be built cleanly.

## Goal

The next implementation slice should make `markdown-source` a natural document-panel view rather than a feature bolted onto the current document renderer or `docs-viewer.js`.

After this work, the Markdown editor request should be able to focus on:

- source read/write/rebuild backend endpoints
- source editor rendering and dirty-state behavior
- rebuild diagnostics
- return-to-rendered workflow

## Required Outcomes

### 1. Document-Panel Hosted-View Host

Create a document-panel host/controller that can switch explicit document-panel views.

Initial view model:

- `rendered`: existing generated document payload view
- future `markdown-source`: manage-only source editor view

The host must preserve:

- selected-document state independent from document-panel visibility
- existing generated document payload loading
- search, recent, and report continuity
- public read-only behavior
- graceful unavailable states for manage-only document-panel views

The current document/search/recent/report controllers may remain the owners of their existing rendering behavior during this slice, but the document panel should gain a clear hosted-view lifecycle boundary that the source editor can attach to.

### 2. Minimal Document-Panel Toolbar Projection

Add only the document-panel toolbar model needed for the editor path.

The toolbar should support:

- selecting the rendered document view
- exposing a manage-only Markdown source action or view option when available
- routing toolbar actions through explicit panel intents
- stable accessible labels from UI text/config
- predictable focus and mobile behavior

Do not broaden this slice into a complete toolbar redesign for every panel.

### 3. Source-View State Policy

Define the policy before implementation.

Recommended starting policy:

- rendered document route state remains URL-addressable as it is today
- `markdown-source` is transient browser state
- `markdown-source` is not linked from public docs links
- unsaved source editor buffer state does not persist across reloads
- leaving a dirty source view is handled by the editor request, not this infrastructure slice

### 4. Explicit Repo Module Registration Boundary

Define how a repo-owned document-panel module will register without creating a plugin platform.

The future source editor module may live under:

```text
docs-viewer/runtime/js/modules/source-editor/
```

The pre-editor work should establish:

- explicit registration for built-in or repo-owned document-panel modules
- no arbitrary route-config module string loading
- no plugin manifests, marketplaces, package protocols, or third-party loader behavior
- explicit public/manage access projection separate from backend write authority

## Out Of Scope

- Markdown source read/write/rebuild endpoints
- source editor textarea or editor-component UI
- dirty-buffer prompts
- semantic-reference token insertion
- semantic-reference registry integration
- new info-panel views
- visualization modules
- broad panel-state persistence changes
- generic plugin architecture

## Open Questions

- Should `search-results`, `recent-results`, and `report-host` remain document-panel view ids in the hosted-view registry, or should this slice limit hosted switching to `rendered` and future editor views while preserving existing search/recent/report controllers?
- Should `report-host` become a true document-panel hosted view now, or remain a document payload/report mode until a later report-specific slice?
- What is the smallest toolbar projection that gives the editor a clean entry point without redesigning existing document controls?
- Should the document-panel active view ever be reflected in the URL, or is transient browser state the right policy for all manage-only source views?
- When a manage-only document view is unavailable, should the UI hide it entirely, show it disabled with a reason, or expose an unavailable panel state only after direct selection?
- Should hidden document-panel views keep any loaded payload or module state, or should switching away always unmount them?
- Where should the future source editor receive management service context: directly from the document-panel host, through a document-panel module context, or through the existing lazy management boundary?
- Which UI text/config file should own document-panel view labels and toolbar accessible names?

## Acceptance

- A document-panel host/controller exists with a documented lifecycle boundary.
- The rendered document view still behaves as it does today on public and manage routes.
- Search, recent, and report behavior is not regressed.
- Manage-only document-panel view availability is capability-gated and graceful.
- The document panel has enough toolbar projection for a future `Markdown source` view/action.
- The source-view URL and persistence policy is recorded.
- The future source editor has a named module-registration path that does not imply a plugin system.
- Owning durable docs are updated where current panel-host behavior changes.

## Proposed Verification

Use focused checks when this request is implemented:

- public route boot with no management document-panel actions
- manage route boot with capability-gated document-panel actions
- rendered document load and selected-document update
- search and recent continuity
- report continuity if report routing is touched
- desktop and mobile toolbar/layout checks when toolbar UI changes

If implementation touches Docs Viewer runtime JavaScript, also run the smallest relevant Docs Viewer check profile from [Testing](/docs/?scope=studio&doc=testing) or [Run Checks](/docs/?scope=studio&doc=scripts-run-checks).

## Next Step

Resolve the open questions that affect scope, then create an implementation task tracker as a child of this request using [Tasks Template](/docs/?scope=studio&doc=tasks-template).

## Related References

- [Docs Viewer Markdown Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor)
- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)
- [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
