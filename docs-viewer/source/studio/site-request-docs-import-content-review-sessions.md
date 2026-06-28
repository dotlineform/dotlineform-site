---
doc_id: site-request-docs-import-content-review-sessions
title: Docs Import Content Review Sessions
added_date: 2026-06-28
last_updated: 2026-06-28
parent_id: change-requests
viewable: true
---
# Docs Import Content Review Sessions

## Status

Proposed.

## Problem

Returned `document-content` packages can contain expanded or rewritten text for many Docs Viewer documents. The current live source model cannot safely treat those returned rows as replacement docs by creating new revision doc ids such as `example-r2`.

Changing `doc_id` breaks existing parent-child relationships, links, references, and any other stable identity assumptions. If a parent document moved to a new revision id, its children and inbound links would also need coordinated changes. That turns a content review workflow into a source graph migration.

The returned content also may not be canonical Docs Viewer Markdown. The current `document-content` profile exports `source_text` as plain text extracted from rendered HTML, using whitespace normalization and truncation. Links, media tokens, references, tables, details, and other Markdown semantics are not guaranteed to survive. A future prepare option can export Markdown content, but plain text and Markdown should share the same review workflow.

## Decision

Implement returned content review as temporary review sessions, not as live scope writes or permanent revision docs.

A review session is a complete staged returned file. It is not a selected-row subset. If `content.jsonl` is staged, one generated review session represents the whole valid contents of `content.jsonl`.

The session should be disposable:

- generated under `var/analytics/data-sharing/import-preview/...`
- safe to delete casually
- safe to regenerate from the staged file
- excluded from live Docs Viewer scope config
- excluded from public generated payloads
- excluded from canonical source lifecycle rules

The workflow is content review, not document import:

1. A user stages a returned `document-content` file.
2. Data Sharing creates or regenerates temporary review source Markdown for the complete file.
3. Docs Viewer creates a session from the selected review source folder.
4. Docs Viewer builds the session JSON, index, and generated payloads.
5. Docs Viewer opens the session in an explicit import-review mode.
6. The user reviews generated temporary docs.
7. The user manually copies useful text into canonical source Markdown.
8. The user deletes or regenerates the review session as needed.

No live source docs are created, overwritten, or deleted by this action.

## Content Format

Content format should be a prepare option on the `document-content` profile, not a separate profile.

Initial behavior remains:

- `content_format: "plain_text"`
- returned row content is treated as plain text
- the review draft can render that text as simple Markdown prose

Future behavior can add:

- `content_format: "markdown"`
- returned row content can be rendered as Markdown in the review session
- later apply workflows can decide whether Markdown content is safe enough for canonical source replacement

The returned package metadata should identify the content format so import/review behavior is self-describing. The import side should handle whichever supported format the package declares.

Plain text versus Markdown changes review quality, not the session workflow.

## Temporary Review Sessions

Review sessions should not be first-class Docs Viewer scopes.

They should be management-only review data sources with Docs Viewer-compatible generated payloads. A session manifest should describe:

- `session_id`
- `data_domain`
- `source_scope`
- `profile_id`
- `source_export_id`
- `staged_filename`
- `content_format`
- `created_at`
- record count
- skipped/error records
- generated payload root
- delete-safe status

The session id can be derived from staged-file identity and export metadata, but regeneration should be explicit. If a session already exists for the staged file, the UI should make replacement clear rather than mutating data silently underneath an open review.

Invalid records should be reported in the manifest or session report. They should not be silently omitted.

## Temporary Source Contract

Data Sharing owns conversion from the returned staged file into temporary review source Markdown.

The source folder should live under the session output, for example:

`var/analytics/data-sharing/import-preview/<session_id>/source/`

Each valid returned row should produce one Markdown file in that folder. The file is Docs Viewer-compatible source, but it is not canonical source.

The file shape is:

- system-generated front matter
- mapped front matter copied from the staged row
- body copied verbatim from the staged row content field

The body must be a straight copy from the staged JSON field. Do not normalize, convert, wrap, enrich, linkify, or otherwise process the returned content. If the selected content field is `source_text`, the body is exactly that `source_text` value.

Front matter should be mapping-driven rather than hard-coded. Generated/system fields are owned by the session builder. Mapped fields come from the staged row when present.

System fields include:

- `doc_id`
- `title` fallback when the row title is missing
- `added_date`
- `last_updated`
- review/session metadata fields

Mapped front matter fields can include:

- `title`
- `parent_id`
- `summary`
- `viewable`
- future exported front matter fields that are explicitly allowed by the profile/session mapping

Do not copy arbitrary staged row keys into front matter. Relationship/context fields such as `children`, `ancestors`, `parent_title`, `current_summary`, and operational metadata should remain review metadata, not source front matter, unless a future profile explicitly makes them canonical front matter fields.

The content mapping should be declared by the profile or session builder, for example:

```json
{
  "content_field": "source_text",
  "front_matter_fields": ["title", "parent_id", "summary", "viewable"]
}
```

Docs Viewer owns turning a selected temporary source folder into a review session. It builds the generated JSON and index from that source folder, serves the generated payloads through management-only session endpoints, and displays the resulting docs in review mode.

## Backend Boundary

Review session files live under `var/analytics/data-sharing/import-preview/...`.

They must not be added to:

- `docs-viewer/config/scopes/docs_scopes.json`
- public scope lists
- regular generated scope outputs
- canonical source roots

Backend support should be management-only. Possible endpoints:

- list content review sessions
- create or regenerate a session for a staged file
- read session manifest
- serve session `index-tree.json`
- serve session `by-id/<doc_id>.json`
- delete a session

The session builder can reuse Docs Viewer source/generation concepts where practical, but the output remains temporary review output rather than a configured scope.

## Frontend Boundary

The normal scope selector should not list review sessions.

Review sessions should be opened from the data-sharing/import workflow. The viewer should make the mode visible with a label such as:

`Import review - library - document-content - plain text`

Review mode should be read-only:

- no source write action
- no source delete action
- no public links
- no assumption that links, references, or the full tree are complete
- no implication that the temporary docs are canonical source docs

The route should be distinct from normal scope navigation, for example:

`/docs/?review_session=<session_id>&doc=<doc_id>`

Avoid URLs that imply the review session is a normal scope, such as `scope=library-review`.

## Gating

Because a staged returned file can contain many documents, session creation should be explicit. However, a session should include the complete staged file rather than selected rows.

The first implementation should:

- require a user action to create or regenerate the session
- show the staged filename, source export id, source scope, content format, record count, and warnings before opening
- block or report rows with missing `doc_id`, missing `title`, or missing content
- warn when content was truncated during prepare
- keep all canonical source writes out of this workflow

Filtering, searching, and reviewing smaller groups should happen inside the review UI, not by creating partial sessions.

## Future Extension

Markdown return content can be added as a `document-content` prepare formatting option.

If Markdown return content later proves reliable enough for source replacement, that should be a separate apply action with stronger review and diff tooling. It should not reuse the plain-text content review action as an implicit live-source overwrite.

Potential future capabilities:

- side-by-side live/current versus returned content comparison
- content-format-aware diffing
- Markdown source export and returned Markdown review
- controlled apply of Markdown source updates
- session cleanup tooling

## Implementation Notes

Likely ownership:

- returned file parsing stays under `docs_returned_import_*`
- content review session creation should use a new data-sharing apply/review module rather than summary or hierarchy modules
- session manifests and generated payload serving should be management-only
- UI workflow state belongs to Docs Viewer management/import UI, not normal public scope runtime

The initial implementation should prefer a narrow, disposable review session over a broad live-scope integration.
