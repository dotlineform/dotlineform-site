---
doc_id: config-export-import-adapters
title: Export Import Adapters
added_date: "2026-05-06 11:35"
last_updated: "2026-05-06 21:14"
parent_id: import-export
sort_order: 60
---
# Export Import Adapters

Config files:

- `assets/studio/data/export_import_adapters.json`
- `assets/studio/data/export_import_adapters.schema.json`

`export_import_adapters.json` is the source-controlled dispatch registry for Studio export/import workflows.
Requests provide a `data_domain` and `operation`.
The registry maps that pair to exactly one adapter id.

## Current Mapping

The implemented adapter is `documents`.
It maps `data_domain: "library"` to the Library Docs Viewer source and generated data paths.

Configured operations:

- `export`
- `import_files`
- `import_preview`
- `summary_apply`
- `hierarchy_apply`

The registry also names future `catalogue` and `analytics` adapter extension points.
Those adapters are marked `status: "stub"` and their capabilities are marked `planned`.
They declare data-domain-first workflow roots under `var/studio/export-import/<data-domain>/`, but they do not dispatch to implemented domain behavior yet.

The docs-management server fails closed when a request has no matching dispatch entry or more than one matching dispatch entry.
It does not infer that a data domain should use document parsing unless the registry says so.
Stub adapters and non-active capabilities fail closed before document-specific code runs.

## Path Ownership

The registry owns workflow paths that the shared export/import shell needs for dispatch:

- `paths.export_root`
- `paths.staging_root`
- `paths.preview_root`
- `paths.source_root`

The first Library mapping uses a data-domain-first workflow root:

```text
var/studio/export-import/library/
```

Under that root, Library uses:

- `exports/`
- `import-staging/`
- `import-preview/`

Future folder changes should update this config instead of adding route-level folder decisions.

Catalogue and Analytics stubs already reserve the same folder shape:

- `var/studio/export-import/catalogue/`
- `var/studio/export-import/analytics/`

Those folders are placeholders only until their adapters define parser, preview, validation, and apply contracts.

## Capability Status

Capabilities may be written as explicit records:

```json
{
  "operation": "export",
  "status": "planned",
  "message": "Catalogue export is not implemented yet."
}
```

Supported status values:

- `active`: implemented and eligible for service dispatch
- `planned`: visible extension point, not runnable
- `unsupported`: intentionally unavailable for that adapter

The browser shell can use these records to show unavailable future domains without guessing.
The service resolver accepts only `active` adapters, data domains, and capabilities.

## Related Runtime

- `scripts/docs/export_import_adapters.py` loads and resolves this registry for the docs-management service.
- `scripts/docs/docs_management_server.py` uses the resolved adapter before running export, staged-file listing, preview, or apply behavior.
- `assets/studio/js/studio-transport.js` defines the neutral service endpoints used by the browser.
