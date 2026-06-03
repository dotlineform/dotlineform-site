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

Prepare the Docs Viewer app shell so the Markdown editor can be implemented as a manage-only main-view hosted view.

This request uses `main view panel` for the internal architecture because the central panel can host more than rendered documents.
It is still fine for user-facing UI or docs to refer to the same region as the document panel when the active view is a rendered document.

This request is intentionally narrower than the broader [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell).
It covers only the panel, toolbar, view-state, and module-registration work needed before the source editor can be built cleanly.

## Goal

The next implementation slice should make `markdown-source` a natural main-view hosted view rather than a feature bolted onto the current document renderer or `docs-viewer.js`.

After this work, the Markdown editor request should be able to focus on:

- source read/write/rebuild backend endpoints
- source editor rendering and dirty-state behavior
- rebuild diagnostics
- return-to-rendered workflow

## Required Outcomes

### 0. Main-View Terminology Alignment

Align the new infrastructure boundary around `main view` terminology before migrating existing views.

This should be a targeted migration, not a repo-wide rename.
The goal is to keep the new host, toolbar, view-state, and hosted-view contracts generic enough for rendered documents, search results, recent results, reports, and the future source editor.

Use `mainView` naming for new or touched architecture surfaces such as:

- host/controller module names
- app-shell refs and helper APIs
- view-state and panel-layout contracts
- hosted-view registry records and context fields
- toolbar projection and panel intents
- durable docs that describe the current architecture

It is acceptable to keep `document` terminology where the code specifically owns rendered document payload behavior, such as the existing document controller or rendered-document view.
Avoid mass-renaming CSS selectors, DOM ids, or controller internals unless they are part of the new main-view boundary.
If temporary compatibility selectors or refs are needed, document their removal path in the implementation tracker.

Task reminder for tracker:

```text
Add an early terminology-alignment task before the host migration:
- introduce mainView naming for new host, toolbar, view-state, hosted-view, and context contracts
- keep document naming only where it specifically means rendered document payload behavior
- avoid broad selector/controller renames unless required by the new host boundary
- identify any temporary aliases and record removal criteria
- update durable panel/runtime docs after the code boundary changes
```

### 1. Main-View Hosted-View Host

Create a main-view host/controller that can switch explicit hosted views in the central content region.

Initial view model:

- `rendered-document`: existing generated document payload view
- `search-results`: search result view
- `recent-results`: recently added result view
- future `markdown-source`: manage-only source editor view

The host must preserve:

- selected-document state independent from main-view visibility
- existing generated document payload loading
- search, recent, and report continuity
- public read-only behavior
- graceful unavailable states for manage-only main-view hosted views

The current document/search/recent/report controllers may remain the owners of their existing rendering behavior during the host-foundation slice, but the main view panel should gain a clear hosted-view lifecycle boundary that the source editor can attach to.

After the host foundation exists, migrate `search-results` and `recent-results` onto the same main-view hosting mechanism.
That migration is part of the pre-editor stabilization path: it proves the host with existing user-facing views before `markdown-source` is added.

`report-host` does not need to move in this request.
Current report behavior works and can remain under the existing report/document payload path unless implementation reveals a direct need.
Treat report-host migration as a follow-up decision about whether reports gain enough from the main-view model to justify the extra change.

### 2. Minimal Main-View Toolbar Projection

Move existing panel controls into explicit panel toolbar ownership without changing the visual design.

Current controls already define the practical toolbar content:

- rendered-document view: breadcrumbs, updated date, status pill, bookmark/favourite controls
- index panel in tree mode: collapse/expand button
- info panel: panel name such as `Info`, active-view label where useful, and close button

The first toolbar task is to make these controls part of panel toolbar projection rather than floating at the top of each panel or view.
The visual result should remain essentially the same as the current UI.

The toolbar contract should support:

- panel-owned controls, such as index collapse/expand and info close
- active-view controls, such as rendered-document metadata controls or editor actions
- a manage-only rendered-document `Edit` control that requests the future `markdown-source` view
- routing toolbar actions through explicit panel intents
- stable accessible labels from UI text/config
- predictable focus and mobile behavior

Do not broaden this slice into a complete toolbar redesign for every panel.

### 2a. Main-View Switch Intent Contract

One hosted view should not directly call, import, or mount another replacement view.
Instead, a hosted view should emit an explicit main-view intent and let the main-view host perform the switch.

Expected editor path:

1. `rendered-document` projects breadcrumbs, updated date, status, bookmark controls, and a manage-only `Edit` control.
2. The `Edit` control emits a main-view switch intent, such as `requestMainView("markdown-source")`.
3. The main-view host validates access and availability, unmounts or hides the current view according to policy, and mounts `markdown-source`.
4. `markdown-source` projects its own toolbar controls, such as `Rebuild doc`, cancel/back, dirty state, and diagnostics.
5. After a successful rebuild, `markdown-source` emits a switch intent back to `rendered-document`.

This keeps the panel host responsible for replacing views while each active view contributes the controls it needs through a shared toolbar projection contract.

### 3. Source-View State Policy

Define the policy before implementation.

The main-view active view should live in explicit app/view state, not in the URL.
The main-view host should use explicit intents and state-domain updates to decide what is mounted.

URL state should be used only when it has real navigation, reload, or share value.
It is acceptable for current rendered-document, search, and recent route behavior to keep the URL behavior they already need for continuity, but the URL should not become the source of truth for the main-view host.

Policy:

- rendered document route state remains URL-addressable as it is today
- search and recent may preserve existing route/query behavior where that is already part of their workflow
- `markdown-source` is transient app/view state
- `markdown-source` is not linked from public docs links
- reloading a page should return to a stable rendered-document route, not reopen an unsaved source editor buffer
- unsaved source editor buffer state does not persist across reloads
- leaving a dirty source view is handled by the editor request, not this infrastructure slice
- URL projection for a main-view id may be revisited later only if a concrete user workflow or operational debugging need appears

### 4. Explicit Repo Module Registration Boundary

Define how a repo-owned main-view module will register without creating a plugin platform.

The future source editor module may live under:

```text
docs-viewer/runtime/js/modules/source-editor/
```

The pre-editor work should establish:

- explicit registration for built-in or repo-owned main-view modules
- no arbitrary route-config module string loading
- no plugin manifests, marketplaces, package protocols, or third-party loader behavior
- explicit public/manage access projection separate from backend write authority

### 5. Manage-Only Unavailable State Policy

Clarify likely failure causes and implement the simplest useful UI explanation.

Manage-only main-view views can be unavailable for several reasons:

- the current route is public/read-only and should not expose the view
- management route access is present, but backend capability or write service authority is not available
- the hosted-view module is absent or disabled in the current build
- the selected document is missing, not loadable, or no longer available
- a local service stops, a source file disappears, or a source revision becomes stale after the user entered the workflow
- the view fails to load or mount because of a runtime error

Policy:

- public/read-only routes should omit manage-only controls entirely
- unavailable manage-only controls may be hidden unless there is a direct user benefit to showing a disabled control
- if a user has already selected or requested a manage-only view and it cannot load, show a simple local panel warning with the reason available from the host or service
- do not build elaborate recovery flows for sudden local-service, source-file, or module failures in this pre-editor slice
- keep failure handling local to the main view panel and preserve the ability to return to `rendered-document`
- backend endpoints remain responsible for authoritative validation and write rejection

### 6. Hidden View Lifecycle Policy

Do not require hidden main-view hosted views to keep loaded payloads or module state in this request.

Default policy:

- switching away from a main-view hosted view may unmount or clear that view
- rendered documents should reload when re-entered or when route/document state requires it because source can be edited outside Docs Viewer
- `markdown-source` buffer persistence is not part of this pre-editor request and belongs to the editor request
- no hidden-view persistence behavior is needed to prove the pre-editor host

The architecture should not block future retained-state behavior.
If a later view needs to preserve expensive data, scroll state, canvas state, or workflow state while hidden, treat that as an explicit per-view capability and define the verification for that view.

### 7. Source-Editor Management Context Policy

The future source editor should receive management service access through an explicit main-view module context.

Do not make the main-view host know source-editor service details.
Do not make the source editor reach into the existing lazy management controller or broad management state.

Recommended context shape:

```js
{
  selectedDocument,
  scope,
  routeAccess,
  mainView: {
    requestView(id),
    projectToolbar(model),
    showWarning(message)
  },
  services: {
    sourceEditor: {
      readSource(...),
      rebuildSource(...)
    }
  }
}
```

Policy:

- the main-view host owns switching, mount/unmount, toolbar projection, and context handoff
- source-editor service methods are supplied only when route access and frontend capability projection allow the view
- public/read-only route context omits source-editor services and should not expose the `markdown-source` view
- management service methods are browser-side convenience only; backend endpoints remain the authoritative source-read, source-write, revision, allowlist, and rebuild validators
- the source editor should depend on the explicit module context, not on modal orchestration or broad management controller state

### 8. Main-View UI Text Ownership

Prefer view-owned UI text/config for hosted-view labels and toolbar controls.

This may live in JavaScript near the owning hosted-view module when that keeps the text easier to find and avoids growing large shared config files.
The important rule is ownership clarity: a developer should be able to find a view's labels, accessible names, empty states, diagnostics, and toolbar copy near the view that uses them.

Policy:

- view-specific copy belongs to the hosted view or a small view-local config module
- host-owned copy is limited to generic panel chrome and lifecycle messages, such as unavailable-view warnings, close labels, or generic return actions
- shared `ui-text.json` should stay for genuinely shared or route-wide copy, not every hosted-view label
- the main-view host should render a normalized toolbar model and should not reach into private view text config
- optional modules should be easy to include or omit without editing a large central copy file

Example view-owned toolbar model:

```js
export function createRenderedDocumentView(options) {
  return {
    id: "rendered-document",
    label: "Document",
    toolbar(context) {
      return {
        primary: [
          { id: "edit", label: "Edit", ariaLabel: "Edit Markdown source" }
        ],
        meta: [
          // breadcrumbs, updated date, status, bookmark controls
        ]
      };
    }
  };
}
```

Example future source-editor local text:

```js
const SOURCE_EDITOR_TEXT = {
  label: "Markdown source",
  rebuildButton: "Rebuild doc",
  cancelButton: "Cancel",
  dirtyLabel: "Unsaved changes"
};
```

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

- None currently. Create the implementation task tracker once this spec is locked.

## Acceptance

- A main-view host/controller exists with a documented lifecycle boundary.
- The rendered document view still behaves as it does today on public and manage routes.
- Search, recent, and report behavior is not regressed.
- Search and recent are migrated to the same main-view hosting mechanism before the Markdown editor is implemented.
- Report-host migration is recorded as a follow-up decision rather than included in this pre-editor slice.
- Manage-only main-view availability is capability-gated and graceful.
- Existing panel controls are projected through explicit panel toolbar ownership without a visual redesign.
- The main view panel supports a switch-intent contract for future `rendered-document` to `markdown-source` replacement.
- The source-view URL and persistence policy is recorded.
- The future source editor has a named module-registration path that does not imply a plugin system.
- Owning durable docs are updated where current panel-host behavior changes.

## Proposed Verification

Use focused checks when this request is implemented:

- public route boot with no management main-view actions
- manage route boot with capability-gated main-view actions
- rendered document load and selected-document update
- search and recent continuity
- report continuity, with no report-host migration expected in this slice
- desktop and mobile toolbar/layout checks when toolbar UI changes

If implementation touches Docs Viewer runtime JavaScript, also run the smallest relevant Docs Viewer check profile from [Testing](/docs/?scope=studio&doc=testing) or [Run Checks](/docs/?scope=studio&doc=scripts-run-checks).

## Next Step

Review and lock this spec, then implement it through [Docs Viewer Pre-Editor Work Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-pre-editor-work-tasks).

## Follow-Up Decisions

### Report-Host Main-View Migration

Decide after the pre-editor work whether `report-host` should become a true main-view hosted view.

Recommended starting position:

- defer report-host migration for this request
- keep current report behavior unchanged while main-view hosting is proven with `rendered-document`, `search-results`, and `recent-results`
- revisit if reports need shared toolbar projection, shared lifecycle behavior, or cleaner replacement semantics with other main-view views

Potential benefits:

- reports would use the same lifecycle as other central-panel views
- report toolbar/status controls could use the same projection contract
- future reports could switch cleanly with rendered documents, search, recent, and editor views

Risks:

- report behavior already works, so migration could add churn without helping the editor
- reports may have payload and route semantics that are closer to document loading than generic hosted views
- moving reports now could widen verification beyond the intended pre-editor stabilization slice

## Related References

- [Docs Viewer Markdown Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor)
- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)
- [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
