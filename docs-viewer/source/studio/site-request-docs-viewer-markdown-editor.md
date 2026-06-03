---
doc_id: site-request-docs-viewer-markdown-editor
title: Docs Viewer Markdown Editor Request
added_date: 2026-06-02
last_updated: 2026-06-03
ui_status: done
parent_id: change-requests
viewable: true
---
# Docs Viewer Markdown Editor Request

Status:

- done
- prerequisite for [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
- implementation tracker: [Docs Viewer Markdown Editor Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor-tasks)

## Summary

Add a manage-mode Markdown source editor view for the current Docs Viewer document.

The editor lets an authorized manage-mode user:

- switch from rendered document view to Markdown source view
- edit the source Markdown body freely
- rebuild the selected document from the edited source
- return to rendered view after a successful rebuild

This request is about source editing and rebuild orchestration only.
It does not expose or edit front matter; document metadata/front matter remains owned by the existing manage-mode Actions flow.
It does not include semantic-reference token insertion, target pickers, or semantic-reference registry integration.
Those belong to the dependent [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor).

## Reason

Docs Viewer source documents are Markdown files.
Some management workflows need a focused way to adjust the source for the currently selected document without leaving the viewer, then immediately rebuild the generated payload.

The editor should be close to editing the Markdown body directly.
It is not a WYSIWYG editor and it does not try to prevent every possible Markdown authoring mistake.
Its value is management-mode access control, source revision protection, body-only source writes, targeted rebuild orchestration, and visible diagnostics.

## Goals

- provide a manage-only Markdown source view for the current document
- allow normal free-form Markdown body editing in the source view
- read the current source body plus a revision token
- track dirty state in the browser
- write the edited source body only when the user clicks `Rebuild doc`
- protect against overwriting external edits with a revision or mtime guard
- preserve existing front matter and source metadata; front matter edits stay in the existing manage-mode Actions flow
- run targeted docs payload and targeted docs-search rebuilds for the selected doc after a successful source write
- reload the generated document payload after rebuild
- switch back to rendered document view after a successful rebuild
- show write/rebuild diagnostics, warnings, and errors in the viewer
- keep the source editor implementation in focused modules rather than growing `docs-viewer.js`

## Non-Goals

- no semantic-reference token insertion in this request
- no target picker or semantic-reference registry integration in this request
- no front matter or metadata editing in this request
- no rendered HTML editing
- no live preview requirement
- no autosave
- no application-level undo stack
- no full Markdown formatting toolbar
- no third-party full editor dependency such as CodeMirror or Monaco in this slice
- no custom Markdown linting beyond existing front matter/source-contract validation
- no attempt to prevent all possible Markdown authoring mistakes
- no public-route authoring UI
- no broad rewrite of the Docs Viewer builder pipeline
- no portable authoring platform for arbitrary downstream installs

Browser-level undo behavior is acceptable if provided by the native editing surface.
Docs Viewer should not build its own operation history for this slice.

## Product Model

The Markdown editor is a manage-mode main-view hosted view.
It is acceptable for user-facing copy to say document panel when the active view is a rendered document, but the internal architecture uses main-view terminology for the central panel.

Initial main-view views:

- `rendered-document`: existing generated document payload view
- `markdown-source`: manage-only editable Markdown source view

Implementation steer:

- Register the source editor through the code-owned hosted-view registration boundary, replacing the current disabled manage-only `markdown-source` placeholder when the module is ready.
- Use the explicit main-view module context for selected document, scope, route access, `mainView.requestView(...)`, toolbar projection, warnings, and capability-gated source-editor services.
- Do not load arbitrary route-config `module` strings, reach into the lazy management controller for source-editor services, or make `markdown-source` URL state.
- Keep report behavior unchanged unless the source editor creates a concrete need to migrate reports into the main-view lifecycle.

The source view should expose:

- editable Markdown body text
- first-party lightweight editor wrapper with native text editing and line numbers
- dirty-state indication
- `Rebuild doc` action
- cancel/back-to-rendered action for abandoning unsaved browser-buffer changes
- unsaved-change confirmation before leaving the source view
- rebuild diagnostics after save/rebuild

The action should be named `Rebuild doc`, not `Save`, because the commit point writes source and regenerates the rendered payload.

Rebuild scope decision:

- `Rebuild doc` runs the existing targeted same-scope follow-through: targeted docs payload rebuild plus targeted docs-search update.
- For this body-only editor, the affected doc set is the selected doc. Child docs are not affected because this endpoint does not change front matter fields such as `title`, `parent_id`, `viewable`, or `ui_status`.
- If a later editor path exposes metadata/front matter changes, that path should use the existing manage-mode Actions behavior or define separate affected-doc rules.

Editor wrapper decision:

- Build a first-party lightweight editor wrapper rather than adopting a third-party full editor.
- Use native text editing as the editing surface, with repo-owned line-number chrome, dirty-state handling, toolbar hooks, and selection helpers.
- Keep selection and cursor access simple enough for future enhancements such as converting selected text to custom semantic-reference tokens.
- Do not introduce CodeMirror, Monaco, or similar editor dependencies unless a later request needs capabilities the native wrapper cannot reasonably provide.
- Keep this request limited to source-body editing, dirty state, rebuild, diagnostics, and line-numbered editing. Token insertion and target-picking remain in the dependent semantic-reference editor request.

Line-number implementation decision:

- Line numbers exist primarily to help debug source-body and future custom-token issues.
- Implement line numbers as a simple first-party gutter beside the native editing surface.
- Count logical source lines after normalizing line endings to `\n`.
- Keep the gutter `aria-hidden`, non-focusable, and non-selectable.
- Match the gutter font, line-height, and vertical padding to the editor body, and sync vertical scroll with the editing surface.
- Use no soft wrap for the first slice so logical source lines align predictably with gutter numbers; horizontal scrolling is acceptable.
- Do not build hidden mirror measurement, wrapped visual-line numbering, minimaps, folding, or syntax-highlighting machinery for this slice.

Dirty-state and leave-confirmation decision:

- Detect local changes by comparing the current editor body against the last clean body loaded from the backend or accepted after a successful rebuild.
- Normalize line endings to `\n` before comparison, but do not trim leading/trailing whitespace because Markdown whitespace can be meaningful.
- Store the normalized last-clean body and compare it directly to the normalized current editor body. Do not require a hash for dirty-state detection.
- A hash may be added later as an internal optimization only if direct comparison becomes measurably expensive; the behavioral contract remains normalized body comparison.
- Do not treat "editor has received input" as dirty by itself; if the user edits and undoes back to the clean body, dirty state should clear.
- Keep the source revision token separately for stale-write protection. The revision token is not the dirty-state signal.
- Before an in-app action leaves `markdown-source` while dirty, show the simple UI Catalogue modal with `Do you want to save changes?`, `Yes`, and `No`.
- `Yes` runs the same `Rebuild doc` flow before leaving. `No` discards the local body buffer and continues to the requested view/route.
- For browser reload/tab close, use the browser's native unload warning when available; custom modal behavior is only required for in-app navigation and main-view switches.

## Workflow

1. User opens a document in `/docs/?mode=manage`.
2. User clicks a `Markdown source` or equivalent main-view control.
3. Viewer requests the current source Markdown body and source revision token.
4. Viewer displays the body in an editable source view.
5. User edits source normally.
6. User clicks `Rebuild doc`.
7. Frontend sends the edited source body plus source revision token once.
8. Backend checks the revision token, preserves existing front matter, writes the source body, and runs targeted docs payload plus targeted docs-search rebuilds for the selected doc.
9. Viewer reloads the generated document payload.
10. Main view switches back to rendered document view.
11. Viewer shows rebuild warnings or errors.

If the user tries to leave `markdown-source` with dirty local changes, the viewer asks whether to save changes first. Choosing `Yes` runs the same rebuild flow; choosing `No` abandons the local buffer.

## Source And Backend Boundary

The frontend should not write source files directly.
It should call named management endpoints.

Candidate read endpoint:

```text
GET /docs/source?scope=<scope>&doc=<doc_id>
```

Candidate response:

```json
{
  "scope": "studio",
  "doc_id": "example-doc",
  "source_body": "# Example\n",
  "source_revision": "mtime-or-content-hash"
}
```

Candidate rebuild endpoint:

```text
POST /docs/source/rebuild
```

Candidate payload:

```json
{
  "scope": "studio",
  "doc_id": "example-doc",
  "source_revision": "mtime-or-content-hash",
  "source_body": "# Example\n"
}
```

Backend responsibilities:

- require management mode and write capabilities
- resolve `scope` and `doc_id` through the configured Docs Viewer source allowlist
- verify the submitted revision still matches the current source
- parse the existing front matter enough to verify the source contract and locate the Markdown body
- preserve the existing front matter exactly for this endpoint
- write the submitted body back under the preserved front matter
- run targeted docs payload and targeted docs-search rebuilds for the selected doc
- return rebuild diagnostics, warnings, and generated payload status

Frontend responsibilities:

- render the source view
- maintain the local edited buffer
- show dirty state
- compare the current normalized body with the last clean normalized body to detect unsaved changes
- warn before leaving source view with unsaved local changes using the simple UI Catalogue modal
- send the source body only when `Rebuild doc` is clicked
- switch back to rendered view only after successful rebuild/payload reload
- keep errors visible when write or rebuild fails

## Validation Policy

Validate:

- management capability
- source revision freshness
- source path allowlist
- existing front matter parseability
- existing required front matter fields needed by Docs Viewer
- existing `doc_id` consistency

Do not attempt in this request:

- front matter mutation
- full Markdown validation
- body token validation before write
- semantic-reference target validation
- automated Markdown repair
- custom undo/redo recovery

This accepts the practical risk that a manage-mode user can corrupt Markdown body content.
That risk is comparable to editing the source file directly.

## Relationship To Panel And App-Shell Work

This request can be implemented as a manage-only main-view hosted view.

It should align with:

- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)

The source editor should be grouped as an optional, clearly identifiable module so it can be included in this repo and left out of portable installs.
If the module is absent or disabled, Docs Viewer core should omit the Markdown source view.

Candidate module folder:

- `docs-viewer/runtime/js/modules/source-editor/`

Candidate files inside that folder:

- `source-editor.js` for source-view orchestration
- source editor state/render modules as needed
- management service modules for source read/write/rebuild endpoints

`docs-viewer/runtime/js/docs-viewer.js` should remain orchestration only.
It should initialize or register the source-editor module when available and hand off selected document, scope, rendered-payload reload, and status callbacks.

## Proposed Implementation Steps

### 1. Backend Source Read And Rebuild Endpoint

Tasks:

- add a management read endpoint for source Markdown body
- add a management write/rebuild endpoint accepting source body plus revision token
- enforce scope/source allowlists
- preserve front matter and validate existing `doc_id` consistency
- run targeted docs payload plus targeted docs-search rebuilds for the selected doc after write
- return structured diagnostics

Acceptance:

- source can be read only in manage mode
- source write is rejected when revision is stale
- source write is rejected when existing front matter cannot be parsed
- successful write rebuilds the selected doc payload and same-scope docs-search entry

### 2. Manage-Only Markdown Source View

Tasks:

- add a `Markdown source` view/action for selected docs in manage mode
- load source and revision on entry
- show editable Markdown body text in a first-party lightweight editor wrapper with line numbers
- keep line numbers aligned to logical source lines without soft wrap
- track dirty state
- support cancel/back to rendered view with a `Do you want to save changes?` Yes/No modal when dirty
- send source body on `Rebuild doc`
- switch back to rendered view after successful rebuild

Acceptance:

- no source is written until `Rebuild doc`
- dirty state clears if the current editor body matches the last clean body again
- dirty leave confirmation uses the simple UI Catalogue modal; `Yes` rebuilds before leaving and `No` discards the local buffer
- successful rebuild reloads rendered document content
- failed write or rebuild keeps the user in source view with visible diagnostics

### 3. Focused Verification And Docs Follow-Through

Tasks:

- add backend tests for source-body read, stale revision, invalid existing front matter, front matter preservation, and successful rebuild request shaping
- add browser smoke coverage for source view, rebuild, and rendered-view return
- update owning Docs Viewer management docs after implementation

Acceptance:

- tests cover both success and failure paths
- docs explain that this is a manage-only source editor, not a general Markdown editor

## Open Questions

- None currently.

## Risks

- users can corrupt Markdown body content
- stale source can be overwritten if revision checks are weak
- rebuild may fail after source write, leaving source changed but rendered payload stale
- source editor behavior could grow into an accidental general Markdown editor
- a third-party editor dependency could expand scope into a full editor platform before token-editing needs justify it
- line-number behavior could drift into full-editor layout work if soft-wrap or mirror measurement is added too early
- body-only writes could accidentally disturb front matter if source splitting is weak
- dirty-state comparison could be noisy if line endings are not normalized consistently
- hash-based dirty state could hide the simple body-comparison contract if introduced prematurely
- adding source editing directly to `docs-viewer.js` would increase runtime coupling

Mitigations:

- require revision token checks
- validate and preserve existing front matter before write
- keep writes behind management endpoints and source allowlists
- accept only body text from the editor endpoint
- normalize line endings before dirty-state comparisons without trimming Markdown whitespace
- use direct normalized body comparison first; only add hash comparison later as an implementation optimization if profiling justifies it
- keep the editor wrapper first-party and native unless later token-editing work proves a richer editor dependency is necessary
- keep line numbers as a simple logical-line gutter; defer soft-wrap alignment and rich editor layout features
- avoid adding general Markdown formatting tools in this slice
- keep source editor code in focused modules

## Verification

Suggested implementation checks:

```bash
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_management_routes.py
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_management_mutations.py
```

Add focused tests or smoke checks for:

- source read endpoint
- stale revision rejection
- existing front matter validation and preservation
- source-body write plus targeted docs payload/search rebuild request
- manage-only source view access
- logical-line gutter rendering and scroll sync
- dirty-state comparison, undo-to-clean behavior, and dirty leave confirmation Yes/No paths
- rebuild returning to rendered document view

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Markdown Editor Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor-tasks)
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
