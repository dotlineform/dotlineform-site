---
doc_id: data-sharing-documents-returned-package-review
title: Documents Returned Package Review
added_date: "2026-06-27"
last_updated: 2026-06-29
parent_id: data-sharing
viewable: true
---
# Documents Returned Package Review

This page describes what the documents Data Sharing review workflow does after an external package has been returned and staged.

Related config:

- `data-sharing/config/adapters.json`
- `docs-viewer/services/docs_import.py`
- `docs-viewer/services/docs_data_sharing/review.py`
- `docs-viewer/services/docs_data_sharing/review_sources.py`
- `docs-viewer/services/docs_data_sharing/apply.py`

The prepare/export side is covered by [Documents Prepare Profiles](/docs/?scope=studio&doc=data-sharing-documents-prepare-profiles).

## Returned Package Contract

Returned packages are staged under:

```text
var/analytics/data-sharing/import-staging/
```

The parser requires a staged-file `export_id` and canonical import metadata.
There is no fallback detection from row shape or filename.

Metadata comes from:

- an internal metadata file under `var/analytics/data-sharing/meta/<export_id>.meta.json`, referenced by the staged file's `export_id`

JSONL staged files must put the `export_id` in the first non-empty row as a `data_sharing_header`.
JSON staged files must include the `export_id` on the top-level object.
Sibling `<stem>.meta.json` files and embedded `profile_id` or `config_id` fields are not accepted as metadata fallbacks.

The profile id determines the returned-package family.
Rows are parsed after that family is known.
Fields such as `ancestors`, `children`, or `content` do not decide what the file means.

If the staged file lacks a valid `export_id`, the metadata file is missing or mismatched, or the metadata names an unsupported profile, review fails closed with an import metadata error.

## Sparse Returns

Exports may be context-rich.
Returns should be sparse.

For example, the `document-content` export can send `content`, headings, current summary, parent context, ancestors, and children so an external service can make a good decision.
The returned file does not need to echo that context.

A returned summary proposal can be as small as:

```json
{"doc_id": "alpha", "title": "Alpha", "summary": "Proposed summary."}
```

The review/apply layer treats returned fields as candidate changes.
Only fields used by the selected write action are considered write candidates.
Unchanged context fields are not required.

## Returned Records Operation

The review page loads records from the selected staged file through:

```text
POST /analytics/api/data-sharing/returned-records
```

For documents, this operation:

- validates the staged file path
- parses the returned JSON or JSONL file
- loads required package metadata
- normalizes returned records into document rows
- loads current Docs Viewer source context for the selected scope
- annotates each returned row with current-source existence and renderability
- returns `review_rows` for the Analytics review page selectable list

It does not write Markdown artifacts or source files.

## Review Operation

The Review button is exposed through:

```text
POST /analytics/api/data-sharing/review
```

For documents, it dispatches to `review_returned_document_package`.
The operation requires selected `record_indices` and writes one Markdown review document for only those selected records:

```text
var/analytics/data-sharing/import-preview/{timestamp}-{data_domain}-{profile_id}.md
```

The Markdown document front matter includes:

- `source_file`
- `profile_id`
- `scope`

The body is a table with one row per selected document:

- `doc_id`
- `title`
- `summary`
- `parent_id`

Review does not mutate source Markdown.
It is a selected-record review artifact step.

## Review Source Folder Action

The Analytics review page also exposes a documents-only `Create review folder` action through the same endpoint:

```text
POST /analytics/api/data-sharing/review
```

The request uses:

```json
{
  "operation": "review",
  "review_action": "source_folder"
}
```

For `document-content` packages, this action creates or regenerates one temporary source folder for the complete staged returned file:

```text
var/analytics/data-sharing/import-preview/<folder_id>/
  manifest.json
  source/
    <doc_id>.md
```

The folder id is derived only from the staged file's `export_id` and matching internal metadata:

```text
<metadata generated_at as YYYYMMDD-HHMMSS>-<metadata data_domain>-<metadata profile_id>
```

There is no fallback to staged filename, returned filename, row shape, or embedded profile fields. Missing or mismatched metadata fails closed.

The source-folder action:

- validates `doc_id`, `title`, and string `content` for each returned row
- writes one Markdown file per valid row
- records invalid rows in the manifest and response
- copies only allowed front matter fields from returned rows: `title`, `parent_id`, `summary`, and `viewable`
- writes the returned `content` field as the Markdown body without content normalization or conversion
- treats `content_format` as manifest metadata only
- replaces an existing folder with the same metadata-derived id when the user explicitly runs the action

It does not build generated review payloads, register the folder as a Docs Viewer scope, open `/docs-review/`, or mutate canonical source Markdown.

## Review Rows

`review_rows` are UI-facing records for the returned package list.
Each row includes:

- `id`
- `type`
- `title`
- `meta`
- `record_index`
- `selectable`
- `record_groups`
- `issues`
- `depth`

The row title comes from the returned record title.
The row metadata includes the returned `doc_id`, duplicate status, and whether the document exists in the current source context.

The selectable row index is the apply input.
Apply actions receive selected `record_indices`, not file paths.

The canonical apply input is still:

- staged returned package filename
- selected record indices
- selected apply action
- confirmation flag

## Write Actions

The documents adapter currently exposes these apply actions:

- `summary_apply`
- `hierarchy_apply`

Both actions require explicit confirmation before writing.
Both parse the staged returned package again at apply time.
Both operate only on selected record indices.
Both write through Docs Viewer source helpers and run targeted rebuild work after successful writes.

## Summary Apply

Action id:

```text
summary_apply
```

Purpose:

- update source Markdown front matter `summary`

Returned field used:

- `summary`

Behavior:

- selected records without `doc_id` are skipped
- duplicate selected `doc_id` values are skipped after the first planned update
- records with no returned `summary` are skipped
- empty normalized summaries are skipped
- records whose proposed summary matches current source summary are skipped
- records whose target doc does not exist produce an error
- confirmed non-dry-run updates rewrite the target source Markdown `summary`

Summary text is normalized before comparison and writing.
The action does not write `current_summary`, `content`, headings, relationships, or unknown fields.

## Hierarchy Apply

Action id:

```text
hierarchy_apply
```

Purpose:

- update source Markdown front matter `parent_id`

Returned field used:

- `parent_id`

Behavior:

- selected records without `doc_id` are skipped
- duplicate selected `doc_id` values are skipped after the first planned update
- `parent_id` equal to the record's own `doc_id` is skipped
- unknown non-empty parent ids produce a warning, because unresolved parents can render at root level depending on scope rules
- records whose proposed parent matches current source parent are unchanged
- records whose target doc does not exist produce an error
- confirmed non-dry-run updates rewrite the target source Markdown `parent_id`

The action does not write summaries, source text, headings, ancestor lists, child lists, or unknown fields.

## Rebuild And Backups

Confirmed writes call the shared Docs Viewer write path.
The write path:

- rewrites selected source Markdown files
- records write metadata including staged filename, selected record indices, and updated doc ids
- runs targeted docs/search rebuild work for the changed doc ids

The apply payload reports:

- selected records
- updates
- skipped rows
- warnings
- errors
- rebuild result
- whether a write actually occurred

## Non-Goals

Returned-package review is not an LLM output validator.
It checks package shape, metadata, current-source context, and write-action preconditions.

It does not infer file meaning from row fields.
It does not apply unrecognized fields.
It does not treat review Markdown as canonical apply input.
It does not automatically create missing documents or parent documents.
