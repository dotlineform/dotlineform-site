---
doc_id: config-export-import-adapters
title: "Export Import Adapters"
added_date: "2026-05-06 11:35"
last_updated: "2026-05-06 11:35"
parent_id: config
sort_order: 38
---

# Export Import Adapters

Config files:

- `assets/studio/data/export_import_adapters.json`
- `assets/studio/data/export_import_adapters.schema.json`

`export_import_adapters.json` is the source-controlled dispatch registry for Studio export/import workflows.
Requests provide a `data_domain` and `operation`.
The registry maps that pair to exactly one adapter id.

## Current Mapping

The first configured adapter is `documents`.
It maps `data_domain: "library"` to the Library Docs Viewer source and generated data paths.

Configured operations:

- `export`
- `import_files`
- `import_preview`
- `summary_apply`
- `hierarchy_apply`

The docs-management server fails closed when a request has no matching dispatch entry or more than one matching dispatch entry.
It does not infer that a data domain should use document parsing unless the registry says so.

## Path Ownership

The registry owns workflow paths that the shared export/import shell needs for dispatch:

- `paths.export_root`
- `paths.staging_root`
- `paths.preview_root`
- `paths.source_root`

The first Library mapping still points at the current Library folders.
Future folder normalization should update this config instead of adding route-level folder decisions.

## Related Runtime

- `scripts/docs/export_import_adapters.py` loads and resolves this registry for the docs-management service.
- `scripts/docs/docs_management_server.py` uses the resolved adapter before running export, staged-file listing, preview, or apply behavior.
- `assets/studio/js/studio-transport.js` defines the neutral service endpoints used by the browser.
