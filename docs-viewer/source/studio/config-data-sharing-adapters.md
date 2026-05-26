---
doc_id: config-data-sharing-adapters
title: Data Sharing Adapters
added_date: "2026-05-06 11:35"
last_updated: 2026-05-26
parent_id: data-sharing
sort_order: 3000
viewable: true
---
# Data Sharing Adapters

Config files:

- `data-sharing/config/adapters.json`
- `data-sharing/config/adapters.schema.json`
- `data-sharing/config/library-export-configs.json`

`adapters.json` is the source-controlled dispatch registry for Data Sharing workflows.
Requests provide a `data_domain` and canonical `operation`.
The registry maps that pair to exactly one adapter id.
The registry is owned by the headless `data-sharing/` subsystem, not by Studio route code or Docs Viewer service code.

Studio reads this config through its same-origin Data Sharing API.
Browser modules must not infer endpoint ownership or selectable-record behavior from the config file path.

## Current Mapping

The implemented adapters are `documents` and `analytics-tags`.
It maps `data_domain: "library"` to the Library Docs Viewer source and generated data paths.

The first non-document adapter is:

- `data_domain: "tags"`
- UI scope: `Analytics`
- `adapter_id: "analytics-tags"`
- `module: "analytics.tags"`

The data domain stays `tags` so future Analytics workflows do not inherit tag-specific assumptions.
The Studio Data Sharing scope selector presents that domain as Analytics because the user-facing Studio scope is Analytics, while the sharing profile selector names the tag-specific package families.

The tags adapter is active for `prepare`, `list_returned`, `review`, and `apply`.
Tags `prepare` exposes source-derived package profiles for tag registry, tag aliases, tag assignments, and combined tags bundles.

Adapters are Data Sharing-owned modules under the target `data-sharing/adapters/` boundary.
They can call domain helpers for reads, validation, backups, writes, and rebuild follow-through.
The documents adapter calls docs-domain helpers; the tags adapter calls Analytics tag helpers.
Neither adapter should require Data Sharing browser modules to know those helper boundaries.

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

The `prepare` capability also declares the adapter selectable-record model.
Selectable records are returned by the active adapter through the Studio Data Sharing API.
The Studio shell must not treat the Library generated-docs index as the shared contract for all domains.

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

Old disposable package roots under `var/studio/export-import/...` are outside the target compatibility contract.
Do not add registry paths or adapter fallback reads that preserve those roots.

## Related Runtime

- `data-sharing/services/registry.py` validates duplicate dispatch, canonical operation names, status values, and safe relative paths before resolving adapters.
- `data-sharing/services/dispatch.py` uses the resolved adapter before running selectable-record, package preparation, returned-package listing, review, or apply behavior.
- `studio/app/server/studio/` owns the same-origin `/studio/api/data-sharing/...` endpoints and local-origin enforcement.
- `studio/app/frontend/js/studio-transport.js` should use Studio-owned same-origin Data Sharing endpoints.
- Docs Viewer service modules may expose Docs Viewer-owned import or management behavior, but they do not own the Data Sharing API boundary.
