---
doc_id: data-sharing-export-metadata
title: Data Sharing Export Metadata
added_date: "2026-06-27"
last_updated: 2026-06-29
parent_id: data-sharing
viewable: true
---
# Data Sharing Export Metadata

Data Sharing prepare runs create external package files for review outside Studio and internal metadata for routing returned packages back into the correct review flow.
The two concerns must stay separate.

## Purpose

Returned-package review must not depend on staged filenames.
Files can be renamed after export, copied between systems, or returned with operator-edited names.

Every prepared package therefore gets an `export_id`.
The external package carries only that id as routing identity.
The internal metadata file stores the profile, domain, source scope, and other Studio-owned context needed by review.

## Export Id

`export_id` is a per-prepare-run id.
It identifies one exported package and the internal metadata created with it.

Use this format:

```text
ds_YYYYMMDDTHHMMSSZ
```

Example:

```text
ds_20260627T173012Z
```

Validation pattern:

```text
^ds_[0-9]{8}T[0-9]{6}Z$
```

The timestamp is UTC.
Manual exports make same-second collisions operationally negligible.
If a collision ever occurs, the prepare operation should fail rather than silently overwrite an existing metadata file.

`export_id` is not a profile id.
Profile identity belongs in the internal metadata file.

## Internal Metadata Location

Internal metadata files live under:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta/
```

The internal metadata filename is derived from `export_id`:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta/ds_20260627T173012Z.meta.json
```

This file is local Studio metadata.
It is not part of the external review package and should not be sent out for external editing.

## Metadata Shape

The metadata file should be a JSON object with stable routing fields:

```json
{
  "schema_version": "data_sharing_export_meta_v1",
  "export_id": "ds_20260627T173012Z",
  "app": "docs-viewer",
  "data_domain": "documents",
  "adapter_id": "documents",
  "config_id": "document-content",
  "profile_id": "document-content",
  "scope": "library",
  "target_format": "jsonl",
  "content_format": "markdown",
  "record_shape": "document_rows",
  "generated_at": "2026-06-27T17:30:12Z",
  "supports_return_import": true
}
```

Required fields:

- `schema_version`
- `export_id`
- `app`
- `data_domain`
- `adapter_id`
- `config_id`
- `profile_id`
- `target_format`
- `record_shape`
- `generated_at`

Documents packages also require `scope`.
Document-content packages also require `content_format`.
The documents adapter treats `profile_id` as the same value as `config_id` until those concepts diverge.

| Field | Purpose | Values / Corresponds To |
| --- | --- | --- |
| `schema_version` | Identifies the metadata contract so review can validate the file before using it. | Currently `data_sharing_export_meta_v1`. |
| `export_id` | Stable routing id shared by the external package and this internal metadata file. | `ds_YYYYMMDDTHHMMSSZ`, derived from the UTC prepare run time. Must match the staged package `export_id` and the internal metadata filename. It must not be used in external package filenames. |
| `app` | Browser/app surface that owns the data domain. | Current documents value is `docs-viewer`. Tags use `analytics`. Future domains should use the app key from the adapter registry. |
| `data_domain` | Dispatch domain used by review and apply. | Current documents value is `documents`. Must match an active `data_domain` in `data-sharing/config/adapters.json`. |
| `adapter_id` | Exact adapter registry id that prepared the package. | Current documents value is `documents`. Must match the adapter id configured for the metadata `data_domain`. |
| `config_id` | Prepare profile/config that generated the package. | For documents, one of the ids from `data-sharing/adapters/documents/config/prepare-profiles.json`, such as `document-content`. |
| `profile_id` | Workflow profile identity for review UI and future profile-specific behavior. | For documents, currently the same value as `config_id`. If config and UI profile concepts diverge later, this records the user-facing profile id. |
| `scope` | Source Docs Viewer scope used during prepare. | Required for documents, for example `library`. Corresponds to `selection.docs_scope` and a configured scope in `docs-viewer/config/scopes/docs_scopes.json`. |
| `target_format` | File format written by prepare and expected by review. | `json` or `jsonl`. Must match the selected profile's supported target format and the staged file extension. |
| `content_format` | String format supplied in exported document `content` fields. | `markdown` or `plain_text` for `document-content`. This is distinct from the JSON/JSONL package container format. |
| `record_shape` | Structural shape of the external records inside the package. | `document_rows` for JSONL rows or JSON `records` arrays; `document_tree` for JSON `docs` trees. |
| `generated_at` | UTC timestamp for the prepare run. | `YYYY-MM-DDTHH:MM:SSZ`. This is the source of `export_id` and should not be edited. |
| `supports_return_import` | Whether this exported package is eligible for returned-package review/apply. | Defaults to true for older metadata. Export-only profiles write false. Valid metadata with false is still provenance, but the staged file is not actionable. |
| `config_checksum` | Optional integrity/provenance value for the prepare profile used at export time. | Present when included by the profile metadata settings. Hashes the profile config so later review can detect profile drift if needed. |
| `selected_doc_ids` | Optional provenance list of documents selected for export. | Ordered normalized document ids after selection resolution. Useful for audit, not for routing. |
| `source_last_updated` | Optional freshness map for selected source docs. | Object keyed by `doc_id`, with source `last_updated` values from prepare time. Apply can use this later for freshness checks. |
| `counts` | Optional prepare run counts. | Object with counts such as `selected`, `exported`, `skipped`, `failed`, and `truncated`. Used for operator audit, not for dispatch. |

## External Package Identity

External package payloads must include `export_id` and must not include internal metadata fields such as app, domain, adapter id, source scope, generated counts, source timestamps, or checksums.

JSON document-row packages use a top-level `export_id`:

```json
{
  "schema_version": "data_sharing_returned_package_v1",
  "export_id": "ds_20260627T173012Z",
  "content_format": "markdown",
  "records": [
    {
      "doc_id": "library",
      "title": "Library"
    }
  ]
}
```

JSONL packages use a required first-line header row:

```jsonl
{"record_type":"data_sharing_header","schema_version":"data_sharing_returned_package_v1","export_id":"ds_20260627T173012Z","profile_id":"document-content","content_format":"markdown"}
{"doc_id":"library","title":"Library","content":"Document body."}
```

For JSONL, line 1 is internal routing identity and all following lines are package records.
External instructions in the package context should tell reviewers to preserve the first JSONL line unchanged.

Export-only document-tree packages use a top-level `export_id` beside a nested `docs` tree:

```json
{
  "schema": "docs_data_sharing_document_tree_v1",
  "export_id": "ds_20260627T173012Z",
  "docs": [
    {
      "doc_id": "library",
      "title": "Library",
      "children": [
        {
          "doc_id": "child-doc",
          "title": "Child Doc"
        }
      ]
    }
  ]
}
```

## Review Resolution

The review page lists staged files from:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
```

It ignores context files such as `.context.json`.
When a user selects a staged file, review reads only enough of the file to extract `export_id`:

- JSON: read top-level `export_id`
- JSONL: read line 1 and require `record_type: "data_sharing_header"`

If `export_id` is missing or invalid, the staged file is invalid.
If the matching metadata file is missing, the staged file cannot be reviewed.

After metadata is loaded, the app and data domain are derived from metadata and displayed as labels.
They are not user-selectable controls in the review workflow.
Review dispatch uses the derived `data_domain`, `adapter_id`, and profile metadata.

Valid metadata does not by itself make a staged file reviewable.
The profile must both declare returned-package import support and have a corresponding server-side import type/action.
Export-only files should be kept out of the primary actionable returned-package list and reported as blocked with `blocked_reason: "export_only_profile"` when diagnostic data is shown.

## Failure States

Review should fail closed for these cases:

- staged file has no `export_id`
- staged file has an invalid `export_id`
- JSONL first line is not a `data_sharing_header` row
- metadata file for `export_id` is missing
- metadata `export_id` does not match the staged file `export_id`
- metadata references an inactive or unknown adapter/domain/profile
- metadata marks the profile as export-only
- metadata references a profile with no supported import action
- staged package format does not match metadata `target_format`

These failures should be shown before preview generation so the operator can fix staging or rerun prepare.

## Relationship To Context Files

`.context.json` remains external task guidance.
It can be sent with the package to explain the requested response shape.

`.meta.json` is internal routing metadata under `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta/`.
It must not be confused with context.

The external package should contain only the `export_id` needed to find the internal metadata after the returned file is staged.
