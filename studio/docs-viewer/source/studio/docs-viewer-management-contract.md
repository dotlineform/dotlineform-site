---
doc_id: docs-viewer-management-contract
title: Docs Viewer Management Contract
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: docs-viewer-management
sort_order: 54200
---
# Docs Viewer Management Contract

## Summary

This document scopes a possible management mode for the shared Docs Viewer.

The feature would allow a local user to manage docs directly from a viewer instance rather than editing source files by hand first.

This is not only a UI change. It potentially affects:

- the shared Docs Viewer UI
- the `_docs` source tree
- docs metadata conventions
- the docs builder assumptions
- the local write-service boundary

## Goal

Implement a local-only management mode for the Docs Viewer that can expose document-management actions from within the viewer.

Candidate actions:

- drag and drop of index items to change `sort_order` and `parent_id`
- `new`
- `archive`
- `delete`

Required guardrails:

- enforce unique filenames
- enforce unique `doc_id` values
- define whether titles must also be unique
- expose management commands only when an explicit query param enables management mode

Phase 1 should end with a stable operational contract for:

- how source docs are stored on disk
- how the shared viewer enters management mode
- which localhost write surface is allowed to mutate docs
- what `new`, `archive`, and `delete` mean
- which conditions block write operations

## Why This Needs A Real Spec

This request is bigger than a normal UI enhancement because it mixes:

- viewer interaction design
- source-of-truth file writes
- metadata validation
- file-system mutation rules
- archive/delete semantics

The toolbar itself is straightforward. The hard part is defining what these actions mean on disk and in the generated docs tree.

## Scope

Included:

- a management toolbar in the shared Docs Viewer shell
- a URL query switch that enables management mode
- local-server-only write behavior
- source metadata updates needed for supported management actions
- validation for filename and `doc_id` uniqueness
- tree operations that affect `parent_id` and `sort_order`

Excluded:

- remote multi-user editing
- GitHub Pages hosted write behavior
- server-side auth and permissions
- collaborative conflict resolution
- inline markdown body editing
- publish workflow beyond local doc metadata mutations

## Primary Surfaces

- `/docs/`
- `/docs/?scope=library`
- `/docs/?scope=analysis`
- shared Docs Viewer shell and runtime
- local docs-management service, if introduced

## Assumptions

- management mode is for local admin/developer use only
- the feature is unavailable on the static hosted site
- the feature does not need to be exposed in mobile environments
- the current shared Docs Viewer model should remain shared unless management mode forces a deeper fork
- source docs remain file-backed under `_docs`
- `library` and `analysis` remain part of the same shared runtime, but public `/library/` and `/analysis/` are read-only shells

## Core Questions To Answer

These historical questions are kept as decision prompts and provenance.
Current Phase 1 answers are captured in the contract above and in the decision log below.

### Source Of Truth

- What is the canonical source of a managed doc: the markdown file path, front matter, or both together?
- Should management mutate only front matter and tree placement metadata, or also move files on disk?

### File Creation

- When creating a new doc, how is the filename chosen?
- Is filename generation automatic from the title, from the `doc_id`, or user-specified?
- Which directory does a new doc go into by default?

### Tree Changes

- If a doc is reparented in the viewer, does only `parent_id` change, or should the file also move into a different folder?
- If `sort_order` changes by drag/drop, should the system renumber sibling items automatically or preserve sparse numbering?

### Archive

- What does `archive` mean?
- Move the file into `_docs/archive/`?
- Set `published: false`?
- Change `parent_id` to `archive`?
- Some combination of the above?

### Delete

- Is delete a real file deletion or a soft-delete workflow?
- If soft-delete, where does the doc go?
- If hard-delete, what protections are required?

### Uniqueness Rules

- Filenames should be unique: yes or no?
- `doc_id` values should be unique: yes or no?
- Titles should be unique: yes or no?

### Management Mode

- What is the query string key that enables management mode?
- Should management mode be visible only when the local write server is available?
- Should the mode fail closed when the server is unavailable?

## Recommended Initial Narrowing

This document started with a narrower first pass:

- show management toolbar behind a query param
- support `new`
- support `archive`
- support `delete`
- support metadata validation
- defer drag/drop reorder/reparent until command semantics are proven

That narrower sequence has now been completed and extended with a leaf-doc drag/drop move flow.

## Phase 1 Contract

Phase 1 is now defined as a planning-and-boundary phase, not a viewer-UI implementation phase.

The required output of Phase 1 is an implementation-ready contract for:

- flat source storage
- management-mode gating
- localhost write authority
- create/archive/delete semantics
- validation and backup rules

### Flat Source Storage

The Studio docs source root is now flat before viewer management writes source docs.

Target shape:

- Studio docs: `_docs/*.md`
- Library docs: `_docs_library/*.md`

Implications:

- source folders under `_docs/` stop carrying storage meaning
- visible docs hierarchy remains metadata-driven through `doc_id`, `parent_id`, and `sort_order`
- special viewer groupings such as Archive continue to exist as docs in the tree, not as filesystem folders
- `doc_id` remains stable even if title changes later

Implemented flattening work:

- moved Studio markdown docs from nested folders into the `_docs/` root
- preserving existing `doc_id` values
- preserving tree position through front matter, not file placement
- rewriting any relative markdown links that currently depend on nested source paths
- rebuilding docs output and checking for broken internal links after the move

Important builder note:

- the docs builder currently resolves relative `.md` links from each file's `source_path`, so flattening is not just a file move; it also changes how relative markdown links are interpreted

### Management Mode Gating

Management mode uses this query contract:

- `?mode=manage`

Management controls are shown only when both conditions are true:

- the current URL includes `mode=manage`
- the local docs-management server reports support for the current scope

If `mode=manage` is present but the local server is unavailable, the viewer must:

- stay read-only
- show a clear `server unavailable` message in the viewer-level control area
- avoid rendering controls that imply writes will succeed

Mobile note:

- docs management is not intended as a mobile-admin surface
- mobile environments are not expected to have the required local server
- right-click-driven management actions do not need mobile equivalents

### Local Write Boundary

First implementation should use a dedicated docs-management localhost service rather than extending the existing tag or catalogue services.

Recommended script and ownership:

- script: `scripts/docs/docs_management_server.py`
- purpose: local-only management writes for shared Docs Viewer source docs

Recommended endpoint surface:

- `GET /health`
- `GET /capabilities`
- `POST /docs/create`
- `POST /docs/archive`
- `POST /docs/delete-preview`
- `POST /docs/delete-apply`

Recommended capabilities shape:

```json
{
  "ok": true,
  "capabilities": {
    "docs_management": true,
    "scopes": ["studio", "library"]
  }
}
```

Write allowlist:

- Studio scope may write only `_docs/*.md`
- Library scope may write only `_docs_library/*.md`
- backups may write only under `var/docs/backups/`
- operational logs may write only under `var/docs/logs/`

Security and operational rules:

- bind to loopback only
- allow loopback origins only
- reject writes outside the allowlisted roots
- create a timestamped backup bundle before every non-dry-run write batch
- log one structured summary record per successful apply request

### Validation Rules

Validation rules for all write commands:

- filename stem must be unique within the scope root
- `doc_id` must be unique within the scope root
- title does not need to be unique
- `sort_order`, when present, must be an integer
- `parent_id`, when present, must resolve to an existing doc in the same scope
- docs with children cannot be deleted until their children are moved or deleted
- `archive` is an ordinary doc id; the Archive command uses it as the conventional destination parent

Title-change rule:

- editing a title later does not mutate `doc_id` or filename

### `new` Command

Recommended request shape:

```json
{
  "scope": "studio",
  "title": "New Doc",
  "parent_id": "",
  "sort_order": null
}
```

Behavior:

- default title is `New Doc`
- default `doc_id` is a slug-friendly version of title
- default filename stem matches `doc_id`
- if the generated stem already exists, append `-2`, `-3`, and so on until both filename and `doc_id` are unique
- default target root is `_docs/` for Studio or `_docs_library/` for Library
- default `parent_id` is blank unless the user creates from a specific parent context
- default position is last sibling under the chosen parent
- initial markdown body may be a minimal heading based on title

Recommended sort-order rule for append operations:

- prefer sparse ordering
- append new docs at the end of the sibling list using the next available integer slot
- when inserting after a visible doc, prefer a simple integer increment for the new doc only
- do not renumber sibling docs automatically in v1

### `archive` Command

Recommended request shape:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Behavior:

- `parent_id` becomes `archive`
- `sort_order` becomes the last sibling order under `archive`
- file does not move on disk
- `published` stays unchanged
- archiving a doc that is already under `archive` is a no-op success
- archiving `archive` itself is a no-op because the command cannot move the Archive parent into itself

### `delete-preview` And `delete-apply`

Recommended preview request shape:

```json
{
  "scope": "studio",
  "doc_id": "docs-viewer-management"
}
```

Preview must report:

- whether the target exists
- child docs whose `parent_id` points at the target
- inbound markdown links from other docs when they can be detected
- file path that would be deleted
- whether apply would be blocked or allowed with warnings

Delete blockers:

- target doc does not exist
- one or more child docs still depend on the target as `parent_id`

Warnings but not blockers:

- inbound markdown links from other docs that will become broken

`delete-apply` behavior:

- requires explicit confirmation payload or matching preview token
- reruns validation before file deletion
- deletes the markdown file for the target doc
- writes backups before delete
- returns deleted path, warnings, and a summary record
