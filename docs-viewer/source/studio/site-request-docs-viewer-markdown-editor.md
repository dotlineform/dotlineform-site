---
doc_id: site-request-docs-viewer-markdown-editor
title: Docs Viewer Markdown Editor Request
added_date: 2026-06-02
last_updated: 2026-06-03
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Markdown Editor Request

Status:

- proposed
- prerequisite for [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)

## Summary

Add a manage-mode Markdown source editor view for the current Docs Viewer document.

The editor lets an authorized manage-mode user:

- switch from rendered document view to Markdown source view
- edit the source Markdown freely
- rebuild the selected document from the edited source
- return to rendered view after a successful rebuild

This request is about source editing and rebuild orchestration only.
It does not include semantic-reference token insertion, target pickers, or semantic-reference registry integration.
Those belong to the dependent [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor).

## Reason

Docs Viewer source documents are Markdown files.
Some management workflows need a focused way to adjust the source for the currently selected document without leaving the viewer, then immediately rebuild the generated payload.

The editor should be close to editing the source file directly.
It is not a WYSIWYG editor and it does not try to prevent every possible Markdown authoring mistake.
Its value is management-mode access control, source revision protection, source-contract validation, targeted rebuild orchestration, and visible diagnostics.

## Goals

- provide a manage-only Markdown source view for the current document
- allow normal free-form text editing in the source view
- read the current source plus a revision token
- track dirty state in the browser
- write the full edited source only when the user clicks `Rebuild doc`
- protect against overwriting external edits with a revision or mtime guard
- validate front matter/source metadata enough to preserve the Docs Viewer source contract
- run a targeted rebuild after a successful source write
- reload the generated document payload after rebuild
- switch back to rendered document view after a successful rebuild
- show write/rebuild diagnostics, warnings, and errors in the viewer
- keep the source editor implementation in focused modules rather than growing `docs-viewer.js`

## Non-Goals

- no semantic-reference token insertion in this request
- no target picker or semantic-reference registry integration in this request
- no rendered HTML editing
- no live preview requirement
- no autosave
- no application-level undo stack
- no full Markdown formatting toolbar
- no custom Markdown linting beyond front matter/source-contract validation
- no attempt to prevent all possible Markdown authoring mistakes
- no public-route authoring UI
- no broad rewrite of the Docs Viewer builder pipeline
- no portable authoring platform for arbitrary downstream installs

Native textarea or browser-level undo behavior is acceptable if provided by the browser or editor component.
Docs Viewer should not build its own operation history for this slice.

## Product Model

The Markdown editor is a manage-mode main-view hosted view.
It is acceptable for user-facing copy to say document panel when the active view is a rendered document, but the internal architecture uses main-view terminology for the central panel.

Initial main-view views:

- `rendered-document`: existing generated document payload view
- `markdown-source`: manage-only editable Markdown source view

The source view should expose:

- editable source text
- dirty-state indication
- `Rebuild doc` action
- cancel/back-to-rendered action for abandoning unsaved browser-buffer changes
- rebuild diagnostics after save/rebuild

The action should be named `Rebuild doc`, not `Save`, because the commit point writes source and regenerates the rendered payload.

## Workflow

1. User opens a document in `/docs/?mode=manage`.
2. User clicks a `Markdown source` or equivalent main-view control.
3. Viewer requests the current source Markdown and source revision token.
4. Viewer displays the source in an editable source view.
5. User edits source normally.
6. User clicks `Rebuild doc`.
7. Frontend sends the full edited source plus source revision token once.
8. Backend checks the revision token, parses and validates front matter/source metadata, writes the source, and runs a targeted rebuild.
9. Viewer reloads the generated document payload.
10. Main view switches back to rendered document view.
11. Viewer shows rebuild warnings or errors.

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
  "source": "---\ndoc_id: example-doc\n---\n# Example\n",
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
  "source": "---\ndoc_id: example-doc\n---\n# Example\n"
}
```

Backend responsibilities:

- require management mode and write capabilities
- resolve `scope` and `doc_id` through the configured Docs Viewer source allowlist
- verify the submitted revision still matches the current source
- parse front matter
- preserve required source metadata contracts, especially `doc_id`
- reject source that would break required front matter structure
- write the submitted full source once
- run targeted docs rebuild for the affected doc
- return rebuild diagnostics, warnings, and generated payload status

Frontend responsibilities:

- render the source view
- maintain the local edited buffer
- show dirty state
- warn before leaving source view with unsaved local changes
- send the source only when `Rebuild doc` is clicked
- switch back to rendered view only after successful rebuild/payload reload
- keep errors visible when write or rebuild fails

## Validation Policy

Validate:

- management capability
- source revision freshness
- source path allowlist
- front matter parseability
- required front matter fields needed by Docs Viewer
- `doc_id` consistency

Do not attempt in this request:

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

- add a management read endpoint for source Markdown
- add a management write/rebuild endpoint accepting full source plus revision token
- enforce scope/source allowlists
- validate front matter and `doc_id` consistency
- run targeted rebuild after write
- return structured diagnostics

Acceptance:

- source can be read only in manage mode
- source write is rejected when revision is stale
- source write is rejected when front matter cannot be parsed
- successful write rebuilds the selected doc

### 2. Manage-Only Markdown Source View

Tasks:

- add a `Markdown source` view/action for selected docs in manage mode
- load source and revision on entry
- show editable source text
- track dirty state
- support cancel/back to rendered view without writing
- send full source on `Rebuild doc`
- switch back to rendered view after successful rebuild

Acceptance:

- no source is written until `Rebuild doc`
- successful rebuild reloads rendered document content
- failed write or rebuild keeps the user in source view with visible diagnostics

### 3. Focused Verification And Docs Follow-Through

Tasks:

- add backend tests for source read, stale revision, invalid front matter, and successful rebuild request shaping
- add browser smoke coverage for source view, rebuild, and rendered-view return
- update owning Docs Viewer management docs after implementation

Acceptance:

- tests cover both success and failure paths
- docs explain that this is a manage-only source editor, not a general Markdown editor

## Open Questions

- Should the source editor use a plain textarea first, or a lightweight editor component with line numbers?
- Should `Rebuild doc` run only a targeted doc rebuild or also refresh related generated artifacts through existing targeted rebuild behavior?
- Should the browser warn before leaving source view with unsaved local changes?

## Risks

- users can corrupt Markdown body content
- stale source can be overwritten if revision checks are weak
- rebuild may fail after source write, leaving source changed but rendered payload stale
- source editor behavior could grow into an accidental general Markdown editor
- adding source editing directly to `docs-viewer.js` would increase runtime coupling

Mitigations:

- require revision token checks
- validate front matter before write
- keep writes behind management endpoints and source allowlists
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
- front matter validation
- source write plus targeted rebuild request
- manage-only source view access
- rebuild returning to rendered document view

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
