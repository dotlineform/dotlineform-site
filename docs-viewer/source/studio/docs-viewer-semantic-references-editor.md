---
doc_id: docs-viewer-semantic-references-editor
title: Semantic References Editor
added_date: 2026-06-23
last_updated: 2026-06-23
parent_id: docs-viewer
viewable: true
---
# Semantic References Editor

The Semantic References Editor is the manage-mode source-editor integration for inserting `[[ref:...]]` tokens into Docs Viewer Markdown.

It is an authoring helper, not a separate editor, route, validation service, or write path.
It helps an author search supported semantic targets and insert syntactically valid tokens into the current local Markdown buffer.
The existing Markdown source editor still owns source loading, dirty state, write/rebuild, and return to rendered document view.

Registry, lookup, builder, and generated artifact internals are documented in [Semantic References Implementation](/docs/?scope=studio&doc=docs-viewer-semantic-references-implementation).
Future editor enhancements are tracked in [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor).

## Product Shape

The editor integration is hosted inside the existing manage-mode Markdown source editor.

Current behavior:

- source editing happens in the Markdown source textarea
- semantic target search is shown in the info panel as `semantic-token-picker`
- selected source text seeds the picker search while a range is selected
- manual picker search is also supported
- choosing a target inserts a semantic-reference token into the source buffer
- inserted changes remain local until `Rebuild doc`

The picker is intentionally narrow.
It does not write source, rebuild docs, validate every token in the document, or prove target existence.

## Info Panel Integration

The semantic picker is a hosted view in the existing info panel:

- panel: `info`
- hosted view id: `semantic-token-picker`
- access: manage-only
- availability: only while Markdown source mode has an active source-editor adapter

Default info-panel view follows document mode:

- rendered document mode uses `metadata-info`
- Markdown source mode uses `semantic-token-picker`

The info panel does not contain its own view-switching toolbar.
Outside document/source context selects the active hosted view.
This model is documented in [Info Panel](/docs/?scope=studio&doc=docs-viewer-info-panel).

## Source Editor Adapter

`docs-viewer/runtime/js/management/source-editor/source-editor.js` owns the textarea and exposes a narrow active adapter while source mode is mounted.

The adapter supports:

- reading current selection text and offsets
- subscribing to selection changes
- replacing the selected range or caret insertion point
- returning focus to the textarea
- projecting insertion status through the source-editor surface

The adapter does not expose:

- source read endpoint ownership
- source write/rebuild endpoint ownership
- dirty-state truth
- rendered document reload
- document display-mode switching
- broad route or app state

This keeps semantic insertion as a child feature of the Markdown source editor rather than a second source-editing owner.

## Search Behavior

The picker reads:

- `docs-viewer/config/semantic-references/registry.json`
- `docs-viewer/generated/semantic-references/target-lookup.json`

The registry supplies supported kinds and the target lookup URL.
The lookup supplies compact target rows with `kind`, `id`, `title`, and optional `meta`.

When source text is selected:

1. the picker reads the selected text through the adapter
2. the selected text is normalized into the search input
3. browser-side matching ranks title-oriented target matches
4. results render as selectable rows

When the selected text is deleted or the editor selection becomes empty, a search that was seeded from the selection is cleared.
Manual searches typed into the picker are not cleared just because the source editor has no selected text.

Search is title-weighted.
For example, selecting or typing `symbols` can surface both a `series` target and a `work` target titled `3 symbols`.
Ids and metadata can help display and tie-break rows, but they should not dominate title search.

## Result Rows

Target rows are rendered by:

```text
docs-viewer/runtime/js/management/source-editor/semantic-target-picker.js
```

Rows use the target lookup shape:

- title
- kind
- id
- optional compact metadata

The list owns:

- row rendering
- delegated mouse selection
- active row state
- ArrowUp and ArrowDown navigation
- Enter selection
- Escape focus return through the picker view

It does not own token construction, source buffer changes, registry loading, or rebuild behavior.
The component is local to the source-editor feature for now.
If another Docs Viewer management feature needs the same selectable-list behavior, the generic core can be extracted later.

## Token Insertion

Choosing a target builds a token with:

- target kind
- target id
- target title as the label

The target title is always used as the inserted link label.
Selected source text is only a search seed and replacement range; it is not reused as the label because it may be abbreviated or misspelled.

Example selected text:

```text
3 symblos
```

Chosen target:

```text
kind: work
id: 00638
title: 3 symbols
```

Inserted token:

```md
[[ref:work:00638|3 symbols]]
```

If the editor has only a caret and no selected range, choosing a target inserts the same labeled token at the caret.

Token construction lives in:

```text
docs-viewer/runtime/js/management/source-editor/semantic-token-editor.js
```

The helper refuses to build a token without a kind, id, or usable target title.

## Commit Point

Semantic insertion changes only the local source textarea buffer.

The existing source editor remains the commit owner:

- `Rebuild doc` writes the source
- `Rebuild doc` rebuilds the generated document payload
- rendered document reload happens through the source-editor workflow
- unsaved changes remain part of the source editor dirty-state model

The semantic picker must not write source directly and must not trigger a rebuild.

## Current Files

Source-editor integration:

- `docs-viewer/runtime/js/management/source-editor/source-editor.js`
- `docs-viewer/runtime/js/management/source-editor/semantic-token-picker-view.js`
- `docs-viewer/runtime/js/management/source-editor/semantic-target-picker.js`
- `docs-viewer/runtime/js/management/source-editor/semantic-targets.js`
- `docs-viewer/runtime/js/management/source-editor/semantic-token-editor.js`
- `docs-viewer/runtime/js/management/source-editor/semantic-reference-registry.js`

Management registration and default view mapping:

- `docs-viewer/runtime/js/management/docs-viewer-management-hosted-views.js`
- `docs-viewer/runtime/js/management/docs-viewer-manage.js`

Shared generic panel/context plumbing:

- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-host.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-info-panel-renderer.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-view-context.js`
- `site/docs-viewer/runtime/js/shared/docs-viewer-app-runtime.js`

Styling:

- `docs-viewer/static/css/docs-viewer-manage.css`

Semantic picker CSS belongs in the management stylesheet.
It should not be added to the public/shared Docs Viewer stylesheet.

## Boundaries

The semantic references editor should not:

- create a new panel or sidebar
- add public route UI
- introduce a target lookup service endpoint
- validate target existence as source-write authority
- own source read/write/rebuild lifecycle
- duplicate registry supported-kind lists
- depend on Studio catalogue picker code

The builder remains the parse/render authority during rebuild.
The picker is editor assistance.
The report is the right place for future stale-target or suspicious-token audits.
