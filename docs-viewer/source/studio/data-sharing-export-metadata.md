---
doc_id: data-sharing-export-metadata
title: Data Sharing Export Metadata
added_date: "2026-06-27"
last_updated: 2026-06-27
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
var/analytics/data-sharing/meta/
```

The filename is derived from `export_id`:

```text
var/analytics/data-sharing/meta/ds_20260627T173012Z.meta.json
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
  "record_shape": "document_rows",
  "generated_at": "2026-06-27T17:30:12Z"
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
The documents adapter treats `profile_id` as the same value as `config_id` until those concepts diverge.

## External Package Identity

External package payloads must include `export_id` and must not include internal metadata fields such as app, domain, adapter id, source scope, generated counts, source timestamps, or checksums.

JSON envelope packages use a top-level `export_id`:

```json
{
  "schema_version": "data_sharing_returned_package_v1",
  "export_id": "ds_20260627T173012Z",
  "documents": [
    {
      "doc_id": "library",
      "title": "Library"
    }
  ]
}
```

JSON document-row packages that would otherwise be a bare array also use an identity envelope:

```json
{
  "schema_version": "data_sharing_returned_package_v1",
  "export_id": "ds_20260627T173012Z",
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
{"record_type":"data_sharing_header","schema_version":"data_sharing_returned_package_v1","export_id":"ds_20260627T173012Z"}
{"doc_id":"library","title":"Library","source_text":"Document body."}
```

For JSONL, line 1 is internal routing identity and all following lines are package records.
External instructions in the package context should tell reviewers to preserve the first JSONL line unchanged.

## Review Resolution

The review page lists staged files from:

```text
var/analytics/data-sharing/import-staging/
```

It ignores context files such as `.context.json`.
When a user selects a staged file, review reads only enough of the file to extract `export_id`:

- JSON envelope: read top-level `export_id`
- JSONL: read line 1 and require `record_type: "data_sharing_header"`

If `export_id` is missing or invalid, the staged file is invalid.
If the matching metadata file is missing, the staged file cannot be reviewed.

After metadata is loaded, the app and data domain are derived from metadata and displayed as labels.
They are not user-selectable controls in the review workflow.
Review dispatch uses the derived `data_domain`, `adapter_id`, and profile metadata.

## Failure States

Review should fail closed for these cases:

- staged file has no `export_id`
- staged file has an invalid `export_id`
- JSONL first line is not a `data_sharing_header` row
- metadata file for `export_id` is missing
- metadata `export_id` does not match the staged file `export_id`
- metadata references an inactive or unknown adapter/domain/profile
- staged package format does not match metadata `target_format`

These failures should be shown before preview generation so the operator can fix staging or rerun prepare.

## Relationship To Context Files

`.context.json` remains external task guidance.
It can be sent with the package to explain the requested response shape.

`.meta.json` is internal routing metadata under `var/analytics/data-sharing/meta/`.
It must not be confused with context.

The external package should contain only the `export_id` needed to find the internal metadata after the returned file is staged.
