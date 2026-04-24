---
doc_id: docs-viewer-draft-publishing-spec
title: "Viewability Workflow Spec"
added_date: 2026-04-24
last_updated: 2026-04-24
parent_id: docs-viewer
sort_order: 35
---

# Viewability Workflow Spec

## Purpose

This spec defines a generated-but-hidden workflow for docs scopes in the shared Docs Viewer.

The immediate use case is Library growth.
Many Library docs may be imported before their final parent-child structure is known.
If every imported doc is immediately viewable, the public `/library/` viewer can become a long, unsorted root-level list.

The terminology matters because `published` already has a pipeline meaning in the docs system.
It means the source Markdown is included in the generated docs-viewer artifacts.
It should not also mean public/default visibility.

The desired workflow is:

- import or create Library docs as generated but not publicly viewable
- keep non-viewable docs hidden from the public/default viewer
- allow manage mode to show non-viewable docs when requested
- make selected docs viewable when they are ready
- avoid creating a parallel manage-only docs index if the existing index can carry the needed state

This is a planning spec, not the current implementation.

## Current Model

Docs source files already support a binary front-matter field:

```yaml
published: false
```

Current behavior treats unpublished docs as excluded from generated docs/search outputs.
Some Studio docs already use this field for local audit outputs that should not appear in the viewer.

This means `published: false` is a pipeline inclusion flag today.
It is not suitable as the public visibility flag for generated-but-hidden Library docs.

There is no docs `status` field and no docs `viewable` field yet.

The docs-management flow already has an `_archive` structural section, but `_archive` is not a publication state.
It is a tree/navigation location for archived docs.

## Decision: Keep `published`, Add `viewable`

The first visibility workflow should preserve the existing `published: true | false` source field and add a separate `viewable: true | false` source field.

Direction:

- `published: true` means the source doc is included in generated docs-viewer JSON artifacts
- `published: false` means the source doc is excluded from generated docs-viewer JSON artifacts
- `viewable: true` means visible in the public/default viewer
- `viewable: false` means generated and reviewable in manage mode, but hidden from public/default discovery
- absence of `published` should continue to default to `true` for existing docs
- absence of `viewable` should default to `true` for existing docs
- `_archive` remains a structural parent, not a status value
- no `status` field should be added yet

Reasons:

- the immediate problem is public/default visibility for generated docs, not pipeline inclusion
- `published` already has clear builder semantics and should not be overloaded
- `viewable` names the user-facing behavior more directly than `published`
- a separate `status` field creates precedence questions before there is a concrete need
- richer states such as `deprecated` should wait until there is display, search, and workflow behavior for them

Avoided ambiguity:

- `published: false` but expected to open in manage mode
- `published: true` but expected to be hidden from public navigation
- `status: draft` plus `viewable: true`
- `status: archived` versus parent `_archive`
- `deprecated` but still visible in search
- warning banners or lifecycle badges before the product behavior is clear

Recommended working states:

```yaml
# Normal public/default doc.
published: true
viewable: true
```

```yaml
# Generated and manageable, but hidden from public/default discovery.
published: true
viewable: false
```

```yaml
# Source-only working note, excluded from generated docs artifacts.
published: false
```

## One Index Artifact

The preferred design is one generated docs index per scope.

Direction:

- keep `assets/data/docs/scopes/<scope>/index.json` as the single docs index artifact
- include `published: true` and `viewable: true | false` on each index row
- do not create a separate manage-only hidden-doc index
- let the Docs Viewer filter rows based on route/mode state

Reasons:

- avoids a second artifact that can drift from the primary docs index
- keeps the generated data contract easier to reason about
- lets public/default and manage-mode views share sorting, hierarchy, and metadata logic
- keeps viewability as a viewer/runtime decision rather than a separate data path

Consequence:

- the index will contain metadata for generated but non-viewable docs
- every runtime consumer of the docs index must understand the `viewable` field or default to viewable-only behavior
- public visibility filtering becomes a required viewer responsibility

## Per-Doc Payloads

Non-viewable docs should have generated per-doc payloads if manage mode can open and review them.

Direction:

- generate `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json` for every `published: true` doc
- keep non-viewable payloads reachable only through manage-mode viewer behavior
- do not expose non-viewable docs through public/default search initially

Reasons:

- visibility decisions require reviewing generated content
- opening a non-viewable doc in manage mode should not require a separate server-only render path
- one build path is easier to validate than a public build plus a private preview path

Risk:

- non-viewable content exists in generated assets even if hidden from normal navigation
- this is acceptable for a local/personal project but should be revisited if private drafts become sensitive

## Viewer Visibility Rules

The shared Docs Viewer should filter the one index differently depending on mode.

Default/public mode:

- show only `viewable !== false`
- route requests for non-viewable docs should fail gracefully or redirect to the default doc
- inline docs search remains viewable-only
- recently-added remains viewable-only

Manage mode:

- default view can still show viewable docs only, to avoid clutter
- a `show non-viewable` toggle can include hidden generated docs in the tree
- non-viewable rows should be visually marked
- when non-viewable docs are shown, tree ancestors needed to reach selected non-viewable docs should also be visible
- selected non-viewable docs should be openable and reviewable

Possible display labels:

- hidden badge on tree rows
- non-viewable marker in metadata row
- `Make viewable` or `Show on site` button in the manage action row when the selected doc has `viewable: false`

## Manage Mode Viewability UI

Manage mode should provide a small viewability-management surface in the existing Docs Viewer controls.

Initial controls:

- show/hide non-viewable toggle
- make selected doc viewable button when the selected doc has `viewable: false`

Future controls:

- make selected doc non-viewable
- show only non-viewable docs
- make selected subtree viewable
- non-viewable count
- manage-mode search/filter over non-viewable docs

Make-viewable action:

- requires manage mode
- requires docs-management server availability
- writes `viewable: true` to the selected source doc
- rebuilds the same docs scope
- rebuilds docs search if search remains viewable-only and the doc should now appear
- reloads the current viewer index and keeps the doc selected

Initial non-goal:

- do not implement a full lifecycle manager
- do not add bulk viewability changes until single-doc behavior is understood

## Builder Requirements

The docs builder should keep excluding `published: false` docs, but include `viewable` metadata for generated docs.

Required behavior:

- parse `published` from source front matter
- parse `viewable` from source front matter
- default missing `published` to `true`
- default missing `viewable` to `true`
- skip `published: false` docs before generated artifact creation, as today
- include `published: true` and `viewable: true | false` in generated index rows for generated docs
- generate per-doc payloads for every `published: true` doc
- validate `parent_id` references across the generated source set
- preserve deterministic sorting

Open behavior to decide:

- whether viewable docs under non-viewable parents are allowed
- whether non-viewable ancestors required by viewable children should be forced into public/default tree as structural-only rows

Recommended first rule:

- avoid viewable docs under non-viewable parents unless there is a clear use case

Reason:

- public tree rendering becomes confusing if a viewable child depends on a hidden generated ancestor

## Search Requirements

Docs search should remain viewable-only initially.

Direction:

- search builder should read the generated docs index but filter to `viewable !== false`
- search artifacts should not include non-viewable records
- search results should not expose non-viewable docs unless a later manage-mode search path is intentionally added

Reasons:

- search is a public/default discovery surface
- the immediate need is hidden-doc review in manage mode, not hidden-doc search
- keeping search viewable-only reduces accidental public exposure

## Import And Create Defaults

Library import and create flows should probably default new docs to generated but non-viewable once this workflow exists.

Recommended defaults:

- Library imports: `published: true`, `viewable: false`
- Library new docs in manage mode: `published: true`, `viewable: false`
- Studio docs new docs: decide separately, likely published by default unless created through a draft-oriented workflow

Reasons:

- Library has the immediate bulk-import/structure-review problem
- Studio docs are usually implementation notes and may still benefit from immediate visibility
- defaults should be scope-aware rather than globally surprising

Open decision:

- whether import UI should expose a `make viewable immediately` option

## Data Model Notes

`published` should remain a boolean source-field for pipeline inclusion.
`viewable` should be added as a boolean source-field for public/default viewer visibility.

Generated docs index row should include:

```json
{
  "doc_id": "...",
  "title": "...",
  "published": true,
  "viewable": false
}
```

Both fields should be included for every generated row so consumers do not need to infer absence.

No `status` field should be introduced until there is a concrete need for more than pipeline inclusion and public/default visibility gating.

## Relationship To Archive

Archive and viewability are separate concerns.

Non-viewable:

- generated but not publicly visible
- not in public/default search
- can be made viewable later

Archive:

- structural location under `_archive`
- may still be viewable if the archive section is visible
- used for docs that should remain available but are no longer active

The system should not treat `_archive` as equivalent to `viewable: false`.

## Suggested Phases

### Phase 1. Schema and builder contract

- parse and emit `viewable`
- include `published` and `viewable` in docs index rows
- generate per-doc payloads for all `published: true` docs
- update docs data-model docs
- update docs builder docs
- keep viewer filtering viewable-only by default

### Phase 2. Viewer filtering

- filter public/default tree to viewable docs
- hide non-viewable docs from search/recently-added
- handle direct non-viewable URLs gracefully outside manage mode

### Phase 3. Manage-mode visibility toggle

- add show/hide non-viewable toggle in manage mode
- mark non-viewable rows
- allow non-viewable docs to be selected and reviewed

### Phase 4. Make-viewable action

- add make-selected-doc-viewable button
- write `viewable: true` through docs-management server
- rebuild docs and search
- reload viewer state

### Phase 5. Import/create defaults

- make Library import/create default to `published: true`, `viewable: false`
- consider UI option for immediate viewability
- document scope-specific defaults

## Risks

- non-viewable metadata and payloads exist in generated assets even if hidden from public UI
- public filtering must be reliable because non-viewable rows are in the single index
- consumers other than the Docs Viewer may accidentally expose hidden docs if they ignore `viewable`
- viewable children under non-viewable parents can make the public tree ambiguous
- visibility toggles can clutter manage mode if the UI is not restrained
- the extra source field adds schema and validation surface area

## Open Questions

- Should Library import/create default to non-viewable immediately when this workflow lands?
- Should Studio docs use the same default or remain published by default?
- Should public direct URLs to non-viewable docs show a not-found state or redirect to the scope default doc?
- Should manage mode support `show only non-viewable` in the first implementation?
- Should viewable docs under non-viewable parents be rejected by the builder?
- Should non-viewable per-doc payload generation be acceptable for all scopes, or should private-sensitive docs require a different preview strategy later?
