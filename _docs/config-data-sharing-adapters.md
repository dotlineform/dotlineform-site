---
doc_id: config-data-sharing-adapters
title: Data Sharing Adapters
added_date: "2026-05-06 11:35"
last_updated: "2026-05-13"
parent_id: config
sort_order: 60
---
# Data Sharing Adapters

Config files:

- `assets/studio/data/data_sharing_adapters.json`
- `assets/studio/data/data_sharing_adapters.schema.json`

`data_sharing_adapters.json` is the source-controlled dispatch registry for Studio Data Sharing workflows.
Requests provide a `data_domain` and `operation`.
The registry maps that pair to exactly one adapter id.

## Current Mapping

The implemented adapter is `documents`.
It maps `data_domain: "library"` to the Library Docs Viewer source and generated data paths.

Configured operations remain behavior-compatible with the existing Library documents adapter for this terminology slice.
The registry also names future `catalogue` and `analytics` adapter extension points.
Those adapters are marked `status: "stub"` and their capabilities are marked `planned`.

## Path Ownership

The registry owns workflow paths that the shared Data Sharing shell needs for dispatch:

- `paths.export_root`
- `paths.staging_root`
- `paths.preview_root`
- `paths.source_root`

The first Library mapping uses a data-domain-first workflow root:

```text
var/studio/data-sharing/library/
```

Under that root, Library currently uses:

- `exports/`
- `import-staging/`
- `import-preview/`

Future folder changes should update this config instead of adding route-level folder decisions.

Catalogue and Analytics stubs already reserve the same folder shape:

- `var/studio/data-sharing/catalogue/`
- `var/studio/data-sharing/analytics/`

## Related Runtime

- `scripts/studio/data_sharing_adapters.py` loads and resolves this registry for the docs-management service.
- `scripts/docs/docs_management_server.py` uses the resolved adapter before running package preparation, returned-package listing, review, or apply behavior.
- `assets/studio/js/studio-transport.js` defines the service endpoints used by the browser.
