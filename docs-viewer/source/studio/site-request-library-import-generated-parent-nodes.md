---
doc_id: site-request-library-import-generated-parent-nodes
title: Library Import Generated Parent Nodes Request
added_date: 2026-05-04
last_updated: "2026-05-04 23:26"
ui_status: draft
parent_id: change-requests
viewable: true
---
# Library Import Generated Parent Nodes Request

Status:

- proposed

## Summary

Library hierarchy import should eventually be able to create new parent/group docs while applying an externally organized parent-child mapping.

The current hierarchy apply contract allows unknown `parent_id` values and renders them as root-level relationships in generated Library docs data.
That is useful as a safe interim behavior, but it is not enough for the intended external-organization workflow: an external service may create a better hierarchy by introducing new parent nodes that do not exist in `docs-viewer/source/library/` yet.

## Context

The external service is expected to be ChatGPT or a similar model.
Because the service is promptable, the import format should not rely on guessing which unknown `parent_id` values should become new docs.
The prompt and staged JSON contract should require new parent nodes to be declared explicitly.

## Goal

Allow a staged hierarchy import to create missing parent docs on the fly, then apply selected child `parent_id` changes against those newly created docs in one confirmed operation.

The desired outcome:

- new parent/group nodes are explicitly declared in the import JSON
- apply preflight shows which source docs will be created and which existing docs will be reparented
- apply creates backup(s) before writing
- new docs are source-controlled Library docs under `docs-viewer/source/library/`
- generated Library docs data no longer needs to treat those parent ids as unresolved after apply

## Proposed Staged JSON Contract

The import JSON should include a distinct section for new hierarchy nodes.

Example shape:

```json
{
  "records": [
    {
      "doc_id": "existing-child",
      "title": "Existing Child",
      "parent_id": "new-theme-node"
    }
  ],
  "new_parent_nodes": [
    {
      "doc_id": "new-theme-node",
      "title": "New Theme Node",
      "summary": "Optional short explanation of why these documents belong together.",
      "parent_id": "",
      "node_kind": "generated_parent"
    }
  ]
}
```

Contract notes:

- `new_parent_nodes` is explicit; unknown `parent_id` values in document rows are not enough to create source docs
- every generated parent node must include `doc_id` and `title`
- generated parent nodes may themselves have `parent_id` values, allowing multi-level generated groupings
- `summary` is optional but useful for human review
- `node_kind` or an equivalent marker should make generated structural docs easy to audit later
- future `sort_order` can remain out of scope until staged files include a stable ordering field

## Prompting Requirement

ChatGPT-facing instructions should require the model to:

- reuse existing `doc_id` values for existing Library docs
- create a `new_parent_nodes` entry for every new grouping parent it invents
- never invent an undeclared `parent_id`
- keep generated `doc_id` values lowercase, stable, slug-like, and unique within the staged file
- include concise titles for generated parent nodes
- include summaries only when they explain the grouping better than the title alone
- avoid using broad catch-all parents when a flatter hierarchy is clearer

## Apply Behavior

Preflight should report:

- selected existing docs that will be reparented
- declared parent nodes that will be created
- declared parent nodes that already exist and will be reused
- unknown parent ids that are not declared in `new_parent_nodes`
- duplicate generated node ids
- generated node ids that collide with selected child ids
- skipped rows, unchanged rows, warnings, and blocking errors

Apply should:

- require OK/Cancel confirmation
- create timestamped backups before source writes
- create new Library source docs for declared missing parent nodes
- write selected existing docs with new `parent_id` values
- preserve existing selected-doc `sort_order`
- assign conservative `sort_order` values to newly created parent docs only if required by the current source model
- rebuild Library docs payloads and Library docs search after writing

## Open Questions

- Should generated parent docs default to `viewable: false` for review, or inherit public visibility from the selected child set?
- Should generated parent docs have an empty body, a generated summary body, or a short review-only placeholder body?
- Should generated parent node creation be selectable independently from child reparenting, or should selected children implicitly include the parent nodes needed by their mapping?
- Should generated parent nodes be marked with `ui_status`, `node_kind`, or another front-matter field for later auditing?
