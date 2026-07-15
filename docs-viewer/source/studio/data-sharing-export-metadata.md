---
doc_id: data-sharing-export-metadata
title: Data Sharing Export Metadata
added_date: 2026-06-27
last_updated: 2026-07-15
parent_id: data-sharing
viewable: true
---
# Data Sharing Export Metadata

## Why It Exists

A returned filename or row shape is not trusted routing authority. Each prepare run creates one `export_id` that links the external package to internal provenance under the Data Sharing workspace.

```text
external JSON/JSONL contains export_id
  -> $DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/meta/<export_id>.meta.json
  -> app + domain + adapter + profile + source scope + format
  -> returned-package validation and dispatch
```

The ID format and parser are code-owned in `services/returned_metadata.py`.

## Three Artifacts

- **Package** (`exports/`) — records sent outside; contains only the routing ID and package contract data.
- **Context sidecar** (`*.context.json`) — external task/response guidance; safe to send with the package.
- **Metadata** (`meta/<export_id>.meta.json`) — internal routing/provenance; never required from or sent back by the external editor.

Do not merge context and metadata. Context is editable guidance; metadata is trusted local identity.

## Required Routing Identity

Internal metadata identifies:

- schema and matching `export_id`;
- owning app/data domain/adapter;
- prepare config/profile;
- target format and record shape;
- generated time;
- source scope/content format when the domain/profile requires them;
- returned-import eligibility.

It may also retain checksums, selected IDs, source freshness, and counts as provenance. Those optional fields are evidence, not dispatch alternatives.

JSON packages carry top-level `export_id`. JSONL packages require the first non-empty row to be a `data_sharing_header` containing it. External instructions should preserve that header exactly.

## Resolution Rules

Returned listing/review:

1. confines the selected filename to `import-staging/`;
2. extracts and validates `export_id` from the package contract;
3. loads the exact internal metadata filename;
4. requires matching identity and required fields;
5. checks domain/adapter/profile/format and return eligibility;
6. only then parses records through the selected adapter family.

No fallback is allowed from filename, sibling metadata, embedded profile fields, or guessed row shape. Export-only or unsupported profiles are blocked before review.

## Failure And Recovery

A package is not actionable when the ID/header is missing/invalid, metadata is missing/mismatched, the configured owner is inactive/unknown, the format/profile disagrees, or return import is disabled/unimplemented.

If a package was copied without its internal metadata, rerun prepare or restore the matching trusted metadata. Do not reconstruct routing fields from the returned content and silently accept it.

## Weak Spots

- Portability of a package currently depends on a local metadata companion that is intentionally not inside the external file.
- Timestamp-derived IDs operate at second resolution; collision handling must remain a package-writer concern.
- Optional freshness/checksum evidence exists but does not automatically establish a universal conflict policy.
- Retaining metadata indefinitely can grow stale; deleting it makes the corresponding returned package intentionally unreviewable.
