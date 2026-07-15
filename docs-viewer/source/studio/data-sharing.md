---
doc_id: data-sharing
title: Data Sharing
added_date: "2026-05-13 17:16"
last_updated: 2026-07-15
parent_id: ""
---
# Data Sharing

## Start Here

- [Data Sharing Overview](/docs/?scope=studio&doc=data-sharing-overview) — lifecycle, execution paths, authority, extension points, and gaps.
- [Adapter Registry](/docs/?scope=studio&doc=config-data-sharing-adapters) — dispatch, capabilities, workspace roots, and browser projection.
- [Adapter Architecture](/docs/?scope=studio&doc=data-sharing-adapter-architecture) — how generic operations meet domain-specific families.
- [Analytics Runtime](/docs/?scope=studio&doc=studio-data-sharing) — browser routes and same-origin HTTP boundary.
- [Export Metadata](/docs/?scope=studio&doc=data-sharing-export-metadata) — the provenance/routing link between an outbound and returned file.

## Implemented Domains

- [Documents Adapter](/docs/?scope=studio&doc=data-sharing-documents-adapter-structure)
  - [Documents Prepare Profiles](/docs/?scope=studio&doc=data-sharing-documents-prepare-profiles)
  - [Documents Returned Package Review](/docs/?scope=studio&doc=data-sharing-documents-returned-package-review)
- [Tags Adapter](/docs/?scope=studio&doc=data-sharing-tags-adapter-structure)

## Ownership Boundary

Data Sharing prepares portable packages, resolves trusted returned packages, produces review evidence, and runs narrow confirmed apply actions. It does not own canonical documents or tags.

For full reviewed documents, Data Sharing ends at a validated read-only Docs Review package. [Docs Import Architecture](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec) owns create/overwrite/skip decisions into a configured Docs Viewer collection. Existing summary/hierarchy apply actions remain narrow field updates, not general document import.

## Run

```bash
bin/local-analytics
```

Routes:

- `/analytics/data-sharing/prepare/`
- `/analytics/data-sharing/review/`

Artifacts live under `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/`; there is no repo-local fallback.
