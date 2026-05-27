---
doc_id: site-request-docs-viewer-semantic-reference-editor
title: Docs Viewer Semantic Reference Editor Request
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: draft
parent_id: change-requests
sort_order: 12160
viewable: true
---
# Docs Viewer Semantic Reference Editor Request

Status:

- proposed

## Summary

Add a manage-mode Markdown source view that helps authors create Docs Viewer semantic-reference tokens.

The v1 workflow is intentionally narrow:

- the document panel can switch from rendered view to editable Markdown source view
- the user edits the source text normally
- the user can select text and use semantic-reference controls to wrap that text in a supported token
- the user saves once by clicking `Rebuild doc`
- the backend writes the full source, runs a targeted rebuild, and the viewer switches back to rendered view

This is not intended to become a full Markdown editor.
The special authoring UI should focus on semantic-reference insertion.

## Reason

Docs semantic references are currently authored by typing tokens such as:

```md
[[ref:work:00638|3 symbols]]
```

That syntax is compact and useful, but it is error-prone when authors have to type target kinds, ids, labels, and punctuation manually.

The Docs Viewer already knows the selected document, management mode, and supported generated/catalogue data.
It can provide a safer local authoring workflow:

- load the current Markdown source
- let the author select the intended label text
- choose a supported reference target through constrained controls
- insert the valid token around the selected text
- rebuild the document through the existing local management/rebuild boundary

The goal is to reduce token authoring errors without hiding the underlying Markdown source model.

## Goals

- provide a manage-only Markdown source view for the current document
- allow normal text editing in the source view
- add semantic-reference insertion helpers for selected text
- keep token insertion local in the editor buffer until the user clicks `Rebuild doc`
- save the full edited source once and rebuild automatically
- switch back to rendered document view after a successful rebuild
- show rebuild diagnostics, warnings, and errors in the viewer
- protect against overwriting external edits with a revision or mtime guard
- validate front matter/source metadata enough to preserve the Docs Viewer source contract
- rely on the existing builder for semantic-reference parsing, rendering, and warning behavior

## Non-Goals

- no rendered HTML editing
- no live preview requirement
- no autosave
- no application-level undo stack
- no full Markdown formatting toolbar
- no custom Markdown linting beyond front matter/source-contract validation
- no attempt to prevent all possible Markdown authoring mistakes
- no public-route authoring UI
- no broad rewrite of the existing semantic-reference builder pipeline

Native textarea or browser-level undo behavior is acceptable if provided by the browser or editor component.
The Docs Viewer should not build its own operation history for v1.

## Product Model

The v1 editor is a manage-mode authoring view.
It is closer to editing the source file directly than to using a WYSIWYG editor.

The user accepts the normal risks of source editing, including the possibility of malformed Markdown.
The value added by Docs Viewer is focused semantic-reference insertion, rebuild orchestration, and source-contract validation.

Initial document panel views:

- `rendered`: existing generated document payload view
- `markdown-source`: manage-only editable Markdown source view

The source view should expose:

- editable source text
- dirty-state indication
- `Rebuild doc` action
- cancel/back-to-rendered action for abandoning unsaved browser-buffer changes
- semantic-reference insertion controls
- target picker/search for supported reference kinds
- rebuild diagnostics after save/rebuild

The action should be named `Rebuild doc`, not `Save`, because the commit point writes source and regenerates the rendered payload.

## V1 Workflow

1. User opens a document in `/docs/?mode=manage`.
2. User clicks a `Markdown source` or equivalent document-panel view control.
3. Viewer requests the current source Markdown and source revision token.
4. Viewer displays the source in an editable source view.
5. User edits source normally.
6. User selects text in the source view.
7. User chooses a semantic-reference kind and target.
8. Viewer wraps selected text in the matching token in the local editor buffer.
9. User repeats edits or token insertions as needed.
10. User clicks `Rebuild doc`.
11. Frontend sends the full edited source plus source revision token once.
12. Backend checks the revision token, parses and validates front matter/source metadata, writes the source, and runs a targeted rebuild.
13. Viewer reloads the generated document payload.
14. Document panel switches back to rendered view.
15. Viewer shows rebuild warnings or errors.

## Token Insertion Behavior

For selected text:

```text
3 symbols
```

and target:

```text
kind: work
id: 00638
```

the editor inserts:

```md
[[ref:work:00638|3 symbols]]
```

Supported v1 target kinds should follow the current semantic-reference builder contract:

- `work`
- `series`
- `moment`

The insertion UI should leave room for future target kinds, such as `tag`, without changing the source-view model.

The helper should avoid inserting tokens when:

- no text is selected
- the target kind is unsupported
- no target id is selected
- the selected text spans an unsupported region if the source editor can detect that reliably

The backend does not need to validate every body token before writing.
The targeted rebuild should surface builder warnings or errors after the write/rebuild step.

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
- insert semantic-reference tokens into selected text
- show dirty state
- read semantic target registries, UI text, modal/options config, and other public-safe support data through modular client-side helpers where practical
- send the source only when `Rebuild doc` is clicked
- switch back to rendered view only after successful rebuild/payload reload
- keep errors visible when save or rebuild fails

Read-oriented support behavior should stay in browser modules wherever it can safely consume generated JSON or browser config.
Examples include semantic target lookup, target picker option shaping, modal/view copy, view registration, and supported token-kind metadata.
The backend should not become a general read orchestrator for UI state when the same data can be supplied through generated artifacts or Docs Viewer config.

## Validation Policy

V1 validation should stay intentionally small.

Validate:

- management capability
- source revision freshness
- source path allowlist
- front matter parseability
- required front matter fields needed by Docs Viewer
- `doc_id` consistency

Do not attempt in v1:

- full Markdown validation
- body token validation before write
- semantic-reference target validation outside the existing builder pipeline
- automated Markdown repair
- custom undo/redo recovery

This accepts the practical risk that a manage-mode user can corrupt Markdown body content.
That risk is comparable to editing the source file directly.

## Relationship To Panel And App-Shell Work

This request can be implemented as a manage-only document panel view.

It should align with:

- [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell)
- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)
- [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references)

The source editor does not require the full multi-panel model to exist first.
If implemented earlier, it should still use focused modules so it can later become a document-panel view without being rewired from scratch.

Candidate modules:

- `docs-viewer/runtime/js/docs-viewer-source-editor.js` for source-view orchestration
- `docs-viewer/runtime/js/docs-viewer-semantic-token-editor.js` for token insertion helpers
- `docs-viewer/runtime/js/docs-viewer-semantic-target-picker.js` for target selection
- `docs-viewer/runtime/js/docs-viewer-semantic-targets.js` for client-side target registry reads and option normalization
- management service modules for source read/write/rebuild endpoints

`docs-viewer/runtime/js/docs-viewer.js` should remain orchestration only.
It should initialize the source editor and hand off selected document, scope, rendered-payload reload, and status callbacks.

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

### 3. Semantic Reference Insertion Helper

Tasks:

- add controls for supported semantic-reference target kinds
- provide a constrained target picker/search
- load target picker data through client-side generated-data/config helpers where practical
- wrap selected source text in the selected token
- keep all token insertion local until rebuild

Acceptance:

- selected text can be wrapped as a `work`, `series`, or `moment` reference
- no token insertion happens without selected text and selected target
- inserted syntax matches the current builder grammar
- target lookup and option rendering are owned by focused browser modules, not route-controller inline logic

### 4. Focused Verification And Docs Follow-Through

Tasks:

- add backend tests for source read, stale revision, invalid front matter, and successful rebuild request shaping
- add browser smoke coverage for source view, token insertion, rebuild, and rendered-view return
- update owning Docs Viewer management and semantic-reference docs after implementation

Acceptance:

- tests cover both success and failure paths
- docs explain that this is a manage-only source editor with semantic-reference tools, not a general Markdown editor

## Open Questions

- Should the source editor use a plain textarea first, or a lightweight editor component with line numbers?
- Where should the target picker read supported work/series/moment options from?
- Should unsupported selected ranges be blocked in v1, or should token insertion operate only on textarea selection offsets?
- Should `Rebuild doc` run only a targeted doc rebuild or also refresh related reference buckets as part of the existing targeted rebuild behavior?
- How should warnings be displayed when rebuild succeeds but semantic references are unresolved?
- Should the browser warn before leaving source view with unsaved local changes?

## Risks

- users can corrupt Markdown body content
- stale source can be overwritten if revision checks are weak
- frontend token insertion can produce invalid syntax if escaping rules are incomplete
- rebuild may fail after source write, leaving source changed but rendered payload stale
- source editor behavior could grow into an accidental general Markdown editor
- adding source editing directly to `docs-viewer.js` would increase runtime coupling
- target lookup, modal copy, and config reads could drift into backend orchestration or inline route-controller logic

Mitigations:

- require revision token checks
- validate front matter before write
- keep writes behind management endpoints and source allowlists
- keep token insertion helpers small and tested
- keep semantic registry reads, target option shaping, modal/view config, and picker behavior in focused client-side modules where practical
- rely on builder diagnostics for semantic-reference warnings
- avoid adding general Markdown formatting tools in v1
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
- token insertion helper behavior
- manage-only source view access
- rebuild returning to rendered document view

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references)
- [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references)
- [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell)
- [Docs Viewer Multi-Panel App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-multi-panel-app-shell)
