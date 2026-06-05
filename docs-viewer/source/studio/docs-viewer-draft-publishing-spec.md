---
doc_id: docs-viewer-draft-publishing-spec
title: Viewability Workflow Spec
added_date: 2026-04-24
last_updated: "2026-05-13 20:20"
parent_id: docs-viewer
---
# Viewability Workflow Spec

## Purpose

This spec defines a generated-but-non-viewable workflow for docs scopes in the shared Docs Viewer.

The immediate use case is Library growth.
Many Library docs may be imported before their final parent-child structure is known.
If every imported doc is immediately viewable, the public `/library/` viewer can become a long, unsorted root-level list.

The desired workflow is:

- import or create Library docs as generated but not publicly viewable
- keep non-viewable docs out of the public/default viewer
- allow manage mode to show non-viewable docs when requested
- make selected docs viewable when they are ready
- avoid creating a parallel manage-only docs index if the existing index can carry the needed state

The first implementation is now in place for the shared Docs Viewer, docs builder, docs search builder, and Docs Viewer service management endpoints.

## Current Model

Docs source files support a binary front-matter field:

```yaml
viewable: false
```

Docs Viewer source no longer uses a separate `published` front-matter field.
Every Markdown source doc in a configured scope is included in generated docs payloads.
Use `viewable: false` when a generated doc should be reviewable in manage mode but excluded from public/default discovery.

There is no docs `status` field.
The docs builder and management flow support `viewable`.

## Decision: Use `viewable`

The current visibility workflow uses `viewable: true | false` as the source field.

Direction:

- `viewable: true` means visible in the public/default viewer
- `viewable: false` means generated and reviewable in manage mode, but excluded from public/default discovery
- absence of `viewable` should default to `true` for existing docs
- no `status` field should be added yet

Reasons:

- the immediate problem is public/default visibility for generated docs
- removing the older `published` source field avoids two overlapping visibility concepts
- `viewable` names the user-facing behavior more directly than `published`
- a separate `status` field creates precedence questions before there is a concrete need
- richer states such as `deprecated` should wait until there is display, search, and workflow behavior for them

Avoided ambiguity:

- `status: draft` plus `viewable: true`
- `deprecated` but still visible in search
- warning banners or lifecycle badges before the product behavior is clear

Recommended working states:

```yaml
# Normal public/default doc.
```

```yaml
# Generated and manageable, but excluded from public/default discovery.
viewable: false
```

## Generated Route Artifacts

The preferred public-route design is compact generated docs payloads per scope.

Direction:

- keep `assets/data/docs/scopes/<scope>/index-tree.json` as the public navigation payload
- keep `assets/data/docs/scopes/<scope>/recently-added.json` as the public recently-added payload
- keep `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json` as selected-document payloads
- omit `viewable` on viewable index rows and include `viewable: false` only for non-viewable rows
- do not create a separate manage-only non-viewable-doc index
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

- generate `assets/data/docs/scopes/<scope>/by-id/<doc_id>.json` for every source doc
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
- a `show non-viewable` toggle can include non-viewable generated docs in the tree
- direct manage-mode links to a non-viewable doc should auto-enable the draft tree state
- non-viewable rows should be visually marked
- when non-viewable docs are shown, tree ancestors needed to reach selected non-viewable docs should also be visible
- selected non-viewable docs should be openable and reviewable

Possible display labels:

- non-viewable badge on tree rows
- non-viewable marker in metadata row
- `Make viewable` or `Show on site` button in the manage action row when the selected doc has `viewable: false`

The UI may use `draft` as the user-facing label for `viewable: false`.
This is acceptable because `draft` describes the user's workflow state, while `viewable` remains the source schema and runtime filtering term.

## Manage Mode Viewability UI

Manage mode should provide a small viewability-management surface in the existing Docs Viewer controls.

Initial controls:

- show/hide drafts toggle that adds non-viewable docs to the tree
- make selected doc viewable button when the selected doc has `viewable: false`

Viewable docs should always remain displayed in manage mode.
Showing drafts/non-viewable docs is an additive context-preserving view, not a replacement filter.

Future controls:

- make selected doc non-viewable
- make selected subtree viewable
- non-viewable count
- manage-mode search/filter over non-viewable docs

Make-viewable action:

- requires manage mode
- requires Docs Viewer service availability
- writes `viewable: true` to the selected source doc
- rebuilds the same docs scope
- rebuilds docs search if search remains viewable-only and the doc should now appear
- reloads the current viewer index and keeps the doc selected

Initial non-goal:

- do not implement a full lifecycle manager
- do not add bulk viewability changes until single-doc behavior is understood

## Builder Requirements

The docs builder should include every configured Markdown source doc and carry `viewable` metadata into generated docs.

Required behavior:

- parse `viewable` from source front matter
- default missing `viewable` to `true`
- omit default `viewable: true` in generated docs JSON and include `viewable: false` only for non-viewable docs
- generate per-doc payloads for every source doc
- validate `parent_id` references across the generated source set
- preserve deterministic sorting

Open behavior to decide:

- whether viewable docs under non-viewable parents are allowed
- whether non-viewable ancestors required by viewable children should be forced into public/default tree as structural-only rows

Recommended first rule:

- do as little builder enforcement as possible

Reason:

- viewable children under non-viewable parents are conceptually confusing, but this should usually be a user/content-management responsibility
- the builder should prevent hard failures and invalid payloads, not become a strict workflow policy engine

## Search Requirements

Docs search should remain viewable-only initially.

Direction:

- search builder should read Docs Viewer source front matter and filter to `viewable !== false`
- search artifacts should not include non-viewable records
- search results should not expose non-viewable docs unless a later manage-mode search path is intentionally added

Reasons:

- search is a public/default discovery surface
- the immediate need is non-viewable-doc review in manage mode, not non-viewable-doc search
- keeping search viewable-only reduces accidental public exposure

## Import And Create Defaults

Library import and create flows should probably default new docs to generated but non-viewable once this workflow exists.

Recommended defaults:

- Library imports: `viewable: false`
- Library new docs in manage mode: `viewable: false`
- Studio new docs: omit `viewable`, which defaults them to viewable

Reasons:

- Library has the immediate bulk-import/structure-review problem
- Studio docs are usually implementation notes and may still benefit from immediate visibility
- defaults should be scope-aware rather than globally surprising

Open decision:

- whether import UI should expose a `make viewable immediately` option later; the first implementation defaults Library imports to non-viewable without adding another import-page choice

## Data Model Notes

The old `published` source field is retired; generated inclusion now follows configured source membership.
`viewable` should be added as a boolean source-field for public/default viewer visibility.

Generated docs index row should include:

```json
{
  "doc_id": "...",
  "title": "...",
  "viewable": false
}
```

The generated index omits `viewable` for default viewable rows and includes `viewable: false` only for non-viewable rows.

No `status` field should be introduced until there is a concrete need for more than pipeline inclusion and public/default visibility gating.

## Suggested Phases

### Phase 1. Schema and builder contract

- parse `viewable`
- include `viewable: false` in docs index rows only for non-viewable docs
- generate per-doc payloads for all source docs
- update docs data-model docs
- update docs builder docs
- keep viewer filtering viewable-only by default

Status: implemented.

### Phase 2. Viewer filtering

- filter public/default tree to viewable docs
- hide non-viewable docs from search/recently-added
- handle direct non-viewable URLs outside manage mode using the existing missing-doc behavior: fall back to the scope default doc

Status: implemented.

### Phase 3. Manage-mode visibility toggle

- add show/hide drafts toggle in manage mode
- mark non-viewable rows
- allow non-viewable docs to be selected and reviewed

Status: implemented.

### Phase 4. Make-viewable action

- add make-selected-doc-viewable button
- remove `viewable` through the Docs Viewer service so the source returns to the default viewable state
- rebuild docs and search
- reload viewer state

Status: implemented through the bulk docs-management endpoint.
The viewer keeps one selected-doc button, prompts for required ancestor and optional descendant expansion, and uses the same-scope docs/search rebuild path rather than incremental search.

### Phase 5. Import/create defaults

- make Library import/create default to `viewable: false`
- consider UI option for immediate viewability
- document scope-specific defaults

Status: implemented for defaults.
The immediate-viewability option remains deferred.

## Risks

- non-viewable metadata and payloads exist in generated assets even if excluded from public UI
- public filtering must be reliable because non-viewable rows are in the single index
- consumers other than the Docs Viewer may accidentally expose non-viewable docs if they ignore `viewable`
- viewable children under non-viewable parents can make the public tree ambiguous
- visibility toggles can clutter manage mode if the UI is not restrained
- the extra source field adds schema and validation surface area
- single-doc viewability changes currently rebuild same-scope docs search; bulk viewability should batch writes and run one rebuild, or wait for a dedicated incremental search design

## Resolved Decisions

- Library docs created through import/create should default to `viewable: false`.
- Studio docs should omit `viewable` by default.
- Public/default direct URLs to non-viewable docs should behave like missing docs and fall back to the scope default doc.
- Manage mode should always show viewable docs; the draft toggle should add non-viewable docs rather than replacing the tree.
- `draft` is acceptable UI language for `viewable: false`, but the schema and generated data should use `viewable`.
- Draft/non-viewable styling should be configurable, especially font weight and color, so accessibility can be tuned without code changes.
- The builder should avoid strict workflow enforcement for viewable docs under non-viewable parents, beyond preventing hard failures and invalid payloads.
- Non-viewable per-doc payload generation is acceptable for all docs scopes. There is no current private/sensitive docs requirement that needs a separate preview strategy.
