---
doc_id: site-request-data-sharing-import-content
title: Data Sharing Import Content
added_date: 2026-06-28
last_updated: 2026-06-29
parent_id: change-requests
viewable: true
---
# Data Sharing Import Content

Proposed.

## Problem

Returned `document-content` packages can contain expanded or rewritten text for many Docs Viewer documents. The current live source model cannot safely treat those returned rows as replacement docs by creating new revision doc ids such as `example-r2`.

Changing `doc_id` breaks existing parent-child relationships, links, references, and any other stable identity assumptions. If a parent document moved to a new revision id, its children and inbound links would also need coordinated changes. That turns a content review workflow into a source graph migration.

## Solution

Implement returned content review as temporary review source folders, not as live scope writes or permanent revision docs.

A review source folder represents a complete staged returned file. It is not a selected-row subset. If `content.jsonl` is staged, one source folder represents the whole valid contents of `content.jsonl`.

The folder should be disposable:

- generated under `var/analytics/data-sharing/import-preview/...`
- safe to delete casually
- safe to regenerate from the staged file
- excluded from live Docs Viewer scope config
- excluded from public generated payloads
- excluded from canonical source lifecycle rules

The workflow is content review, not document import:

1. A user stages a returned `document-content` file.
2. Data Sharing creates or regenerates temporary review source Markdown documents for the complete file.
3. `/docs-review/` lists the review source folder.
4. `/docs-review/` builds generated Docs JSON from the selected folder's `source/*.md`.
5. `/docs-review/` renders the generated tree and selected document.

No live source docs are created, overwritten, or deleted by this workflow.

`/docs-review/` refers to using Docs Viewer to preview the temporary Markdown files. This is a separate request [Docs Review Local App](/docs/?scope=studio&doc=site-request-docs-review-local-app) which this current request doesn't depend on.

## Temporary Review Source Folders

Review source folders should not be first-class Docs Viewer scopes.

They are temporary source inputs for `/docs-review/`. A folder manifest should describe:

- `folder_id`
- `data_domain`
- `source_scope`
- `profile_id`
- `source_export_id`
- `staged_filename`
- `content_format`
- `created_at`
- record count
- skipped/error records
- delete-safe status

The folder id can be derived from staged-file identity and export metadata, but regeneration should be explicit. If a folder already exists for the staged file, the UI should make replacement clear rather than mutating data silently underneath an open review.

Invalid records should be reported in the manifest or source-folder creation report. They should not be silently omitted.

## Temporary Source Contract

Data Sharing owns conversion from the returned staged file into temporary review source Markdown. It does not own rendered Docs payload generation.

The source folder should live under the review folder output, for example:

`var/analytics/data-sharing/import-preview/<folder_id>/source/`

Each valid returned row should produce one Markdown file in that folder. The file is Docs Viewer-compatible source, but it is not canonical source.

The file shape is:

- system-generated front matter
- mapped front matter copied from the staged row
- body copied verbatim from the staged row content field

The body must be a straight copy from the staged JSON field. Do not normalize, convert, wrap, enrich, linkify, or otherwise process the returned content. If the selected content field is `content`, the body is exactly that `content` value.

Front matter should be mapping-driven rather than hard-coded. Generated/system fields are owned by the source-folder builder. Mapped fields come from the staged row when present.

System fields include:

- `doc_id`
- `title` fallback when the row title is missing
- `added_date`
- `last_updated`
- review-folder metadata fields

Mapped front matter fields can include:

- `title`
- `parent_id`
- `summary`
- `viewable`
- future exported front matter fields that are explicitly allowed by the profile/source-folder mapping

Do not copy arbitrary staged row keys into front matter. Relationship/context fields such as `children`, `ancestors`, `parent_title`, `current_summary`, and operational metadata should remain review metadata, not source front matter, unless a future profile explicitly makes them canonical front matter fields.

The content mapping should be declared by the profile or source-folder builder, for example:

```json
{
  "content_field": "content",
  "content_format": "markdown",
  "front_matter_fields": ["title", "parent_id", "summary", "viewable"]
}
```

`/docs-review/` owns turning a selected temporary source folder into rendered review documents. It builds the generated JSON and index from that source folder, serves those generated payloads through review-folder endpoints, and displays the resulting docs in the review app.

## Backend Boundary

Review source folders live under `var/analytics/data-sharing/import-preview/...`.

They must not be added to:

- `docs-viewer/config/scopes/docs_scopes.json`
- public scope lists
- regular generated scope outputs
- canonical source roots

Review folders are temporary artifacts. The folder tree under `var/analytics/data-sharing/import-preview/...` is the source of truth for what review source folders exist. There should be no config registration, durable registry, or source-control lifecycle for these folders.

Manual deletion is valid. If a user deletes a review folder outside the UI, the system should not complain. The next list operation should simply omit that folder, and an already-open stale folder can report that the folder no longer exists.

Data Sharing backend support should be limited to source-folder creation/regeneration from returned staged packages. `/docs-review/` owns folder listing, building generated payloads, and rendering.

Data Sharing operations:

- create or regenerate a review source folder for a staged file
- write a folder manifest
- write one source Markdown file per valid returned row
- report skipped/error records

## Frontend Boundary

The normal `/docs/` app should not list or open review folders.

Review folders should be opened in `/docs-review/`. The review app should make the mode visible with a label such as:

`Import review - library - document-content - markdown`

The review app should be read-only:

- no source write action
- no source delete action
- no public links
- no assumption that links, references, or the full tree are complete
- no implication that the temporary docs are canonical source docs

The route should be distinct from normal scope navigation:

`/docs-review/?folder=<folder_id>&doc=<doc_id>`

Avoid URLs that imply the review folder is a normal scope, such as `scope=library-review`.

Initial review UI shape:

- list review folders under `var/analytics/data-sharing/import-preview/...`
- show whether the selected folder has generated payloads
- provide a Build action for the selected folder
- load generated docs from the selected built folder
- keep delete/cleanup out of the first slice unless explicitly added later

Loading a review folder must not mutate the active configured scope.

## Gating

Because a staged returned file can contain many documents, review source-folder creation should be explicit. However, a folder should include the complete staged file rather than selected rows.

The first implementation should:

- require a user action to create or regenerate the review source folder
- show the staged filename, source export id, source scope, content format, record count, and warnings before opening
- require `content_format: "markdown"` for full content-review source folders
- block or report rows with missing `doc_id`, missing `title`, or missing content
- warn when content was truncated during prepare
- keep all canonical source writes out of this workflow

Filtering, searching, and reviewing smaller groups should happen inside the review UI, not by creating partial source folders.

## Future Extension

If Markdown return content later proves reliable enough for source replacement, that could be a separate apply action with stronger review and diff tooling. It should not reuse the plain-text content review action as an implicit live-source overwrite.

Potential future capabilities:

- side-by-side live/current versus returned content comparison
- content-format-aware diffing
- controlled apply of Markdown source updates
- review folder cleanup tooling

## Implementation Architecture

Data Sharing implementation should stay narrow.

It should own only:

- validating staged returned `document-content` packages
- requiring `content_format: "markdown"`
- creating or replacing one review source folder under `var/analytics/data-sharing/import-preview/...`
- writing `manifest.json`
- writing one source Markdown file per valid returned row under `source/`
- reporting skipped/error rows

It should not:

- list review folders for the review app
- build `generated/`
- read generated `index-tree.json`
- read generated `by-id/<doc_id>.json`
- render documents
- add the folder to Docs Viewer scope config
- open `/docs-review/`
- mutate canonical source Markdown
- publish public payloads

The resulting folder contract is:

```text
var/analytics/data-sharing/import-preview/<folder_id>/
  manifest.json
  source/
    example.md
    child.md
```

The folder id should be a display-safe folder name derived from staged-file identity and export metadata. It should not be an arbitrary path.

`/docs-review/` owns everything after that point:

- list subfolders under `var/analytics/data-sharing/import-preview/...`
- validate selected folder ids
- build `generated/` from `source/*.md`
- read generated index and payload files
- render the temporary docs
- handle stale or manually deleted folders

The normal `/docs/` app remains unaware of this workflow.
