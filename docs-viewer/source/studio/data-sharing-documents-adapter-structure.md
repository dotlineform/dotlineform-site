---
doc_id: data-sharing-documents-adapter-structure
title: Documents Data Sharing Adapter Structure
added_date: "2026-06-21 00:00"
last_updated: 2026-06-21
parent_id: data-sharing
viewable: true
---
# Documents Data Sharing Adapter Structure

The documents adapter implements Data Sharing for Docs Viewer-backed document records.
It follows the shared [Data Sharing Adapter Architecture](/docs/?scope=studio&doc=data-sharing-adapter-architecture) and delegates document-specific behavior to the current `library` family.

## Layout

```text
data-sharing/adapters/documents/
  adapter.py
  context.py
  prepare.py
  returned.py

  families/
    library.py
```

`adapter.py` only wires `DataSharingAdapterHandlers` for module `documents`.

`context.py` owns documents adapter support:

- adapter validation for module `documents`
- `DocumentsDataSharingDependencies`
- Docs Viewer write dependency bridging
- adapter context attachment
- selection model lookup
- Docs Viewer scope normalization
- adapter-domain scope fallback through `domain.scope` or `domain.docs_scope`
- request selection validation

`prepare.py` delegates prepare operations to the current document family.

`returned.py` delegates returned-package list, review, and apply operations to the current document family.

`families/library.py` owns the active document implementation.
It calls Docs Viewer data-sharing helpers for selectable records, package preparation, returned package listing, returned package review, and source apply actions.

## Scope And Selectable Records

Document selection is scoped by `selection.docs_scope`.
When a request omits that value, the adapter can fall back to the configured adapter domain scope.
If neither request nor domain config supplies a scope for a required operation, scope validation fails.

Selectable records come from Docs Viewer source metadata, not generated publication payloads.
The documents adapter calls `selectable_document_records(...)`, which returns generic selectable records for the prepare UI.
Records must include the shared `id` and `name` fields; document-specific fields such as `doc_id` and `title` are implementation details.

Generated Docs Viewer tree, by-id, search, recently-added, report, and generated metadata payloads are not fallback metadata inputs for Data Sharing.

## Prepare

The documents prepare flow uses export configs from:

```text
data-sharing/config/library-export-configs.json
```

Those configs are documented in [Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs).

`families/library.py` passes the selected docs, target format, missing-summary option, output root, and config path to Docs Viewer package helpers.
The adapter adds Data Sharing context and summary text, and logs a `docs-export` event through dependencies.

## Returned Packages

Returned packages are staged under the shared Data Sharing import-staging root.
The documents adapter delegates parsing and preview generation to Docs Viewer returned-package helpers.

Review produces document-oriented review rows and optional Markdown preview files under the shared review-output root.

Current apply actions are:

- `summary_apply`
- `hierarchy_apply`

Apply requires `DocumentsDataSharingDependencies` because source writes must run through Docs Viewer write/rebuild dependencies.
Successful applies can update source Markdown and trigger Docs/search rebuild follow-through through Docs Viewer helpers.

## Current Family Boundary

The only current documents family is `library`.
That family covers the existing Library export configs and document returned-package review/apply behavior.

Add a new documents family when a document-backed profile needs a different source record shape, package contract, returned-package parser, review row model, apply action, or validation model.
Do not add those branches to `adapter.py`.

## Verification

Run these focused checks after documents adapter changes:

```bash
$HOME/miniconda3/bin/python3 -m py_compile data-sharing/adapters/documents/*.py data-sharing/adapters/documents/families/*.py
$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_docs_import_service.py docs-viewer/tests/python/test_docs_management_service.py docs-viewer/tests/python/test_docs_data_sharing_source_metadata.py -q
$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_data_sharing_adapters.py analytics-app/tests/python/test_data_sharing_service.py analytics-app/tests/python/test_analytics_data_sharing_api.py -q
```

Run the local route smoke when handler wiring or browser-visible behavior changes:

```bash
$HOME/miniconda3/bin/python3 analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py
```
