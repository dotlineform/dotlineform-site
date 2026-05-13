---
doc_id: config-data-sharing-adapters
title: Data Sharing Adapters
added_date: "2026-05-06 11:35"
last_updated: "2026-05-13 18:15"
parent_id: config
sort_order: 60
---
# Data Sharing Adapters

Config files:

- `assets/studio/data/data_sharing_adapters.json`
- `assets/studio/data/data_sharing_adapters.schema.json`

`data_sharing_adapters.json` is the source-controlled dispatch registry for Studio Data Sharing workflows.
Requests provide a `data_domain` and canonical `operation`.
The registry maps that pair to exactly one adapter id.

## Current Mapping

The implemented adapters are `documents` and `analytics-tags`.
It maps `data_domain: "library"` to the Library Docs Viewer source and generated data paths.

The first non-document adapter is:

- `data_domain: "tags"`
- `adapter_id: "analytics-tags"`
- `module: "analytics.tags"`

The tags adapter is active for `prepare`, `list_returned`, `review`, and `apply`.
Tags `prepare` exposes source-derived package profiles for tag registry, tag aliases, tag assignments, and combined tags bundles.

## Operations

The v2 registry uses only these shared operation names:

- `prepare`
- `list_returned`
- `review`
- `apply`

Adapter-specific apply variants live under the `apply` capability's `apply_actions` list.
For the documents adapter, the current actions are `summary_apply` and `hierarchy_apply`.
For the tags adapter, the current actions are `registry_apply`, `aliases_apply`, and `assignments_apply`.
Do not add new registry-level operations such as `export`, `import_files`, `import_preview`, `summary_apply`, or `hierarchy_apply`.

## Capability Metadata

Each capability declares:

- `status`: `active`, `planned`, `stub`, or `disabled`
- `selection_model`: `documents`, `records`, `file_only`, or `none`
- supported `input_formats` and `output_formats`
- `path_contract` keys that point into the domain path block
- `activity` metadata with script purpose and record groups

The `review` capability also declares the shared review-row presentation fields.
The `apply` capability declares confirmation requirements and per-action confirmation/activity metadata.

## Path Ownership

The registry owns workflow paths that the shared Data Sharing shell needs for dispatch:

- `paths.outbound_package_root`
- `paths.returned_package_staging_root`
- `paths.review_output_root`
- `paths.source_root`
- `paths.backup_root`

The first Library mapping uses a data-domain-first workflow root:

```text
var/studio/data-sharing/library/
```

Under that root, Library currently uses:

- `exports/`
- `import-staging/`
- `import-preview/`

Future folder changes should update this config instead of adding route-level folder decisions.

The active tags prepare/review/apply workflow uses the same folder shape under `var/studio/data-sharing/tags/`.
Tags package preparation writes outbound packages under `var/studio/data-sharing/tags/exports/`.

## Related Runtime

- `scripts/studio/data_sharing_adapters.py` validates duplicate dispatch, canonical operation names, status values, and safe relative paths before resolving adapters.
- `scripts/studio/data_sharing_service.py` uses the resolved adapter before running package preparation, returned-package listing, review, or apply behavior.
- `scripts/docs/docs_management_server.py` hosts the loopback HTTP endpoints and delegates Data Sharing dispatch to `scripts/studio/data_sharing_service.py`.
- `assets/studio/js/studio-transport.js` defines the service endpoints used by the browser.
