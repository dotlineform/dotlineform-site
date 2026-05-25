---
doc_id: studio-data-sharing-technical-spec
title: Studio Data Sharing Technical Spec
added_date: "2026-05-13 18:15"
last_updated: "2026-05-13 17:17"
parent_id: data-sharing
sort_order: 2000
viewable: true
---
# Studio Data Sharing Technical Spec

Studio Data Sharing is the shared Studio shell for preparing outbound share packages, listing returned packages, reviewing returned structured data, and applying confirmed changes through domain adapters.

The module uses Data Sharing terminology for current routes, code, configuration, and UI copy.
Older import/export names remain only in archived request docs, historical change-log entries, and separate domain workflows such as Docs Import or catalogue workbook import.

## Routes

- `/studio/data-sharing/?mode=manage`
- `/studio/data-sharing/prepare/?mode=manage`
- `/studio/data-sharing/review/?mode=manage`

The page shells are Studio-owned.
They call a loopback local service, render shared lifecycle states, and use adapter metadata to decide which domains, sharing profiles, review rows, and apply actions are available.

## Local Service Contract

The Docs Viewer service hosts the HTTP process because the documents adapter depends on Docs Viewer generated-data reads, backups, and rebuild follow-through.
Neutral route constants and shared dispatch still live under `studio/app/server/studio/` behind the Docs Viewer adapter boundary.

Endpoints:

- `GET <DOCS_VIEWER_BASE_URL>/data-sharing/returned-packages`
- `POST <DOCS_VIEWER_BASE_URL>/data-sharing/prepare`
- `POST <DOCS_VIEWER_BASE_URL>/data-sharing/review`
- `POST <DOCS_VIEWER_BASE_URL>/data-sharing/apply`

The shared service layer owns:

- adapter registry loading and validation
- adapter resolution by `data_domain` and canonical `operation`
- local-service request dispatch
- common path safety checks for package roots, staging roots, review roots, source roots, and backup roots
- common dry-run and confirmation gates
- activity append timing after successful adapter operations

Domain adapters own source parsing, validation, review row semantics, write planning, backups, and writes for their data model.

## Adapter Registry

The source-controlled registry is:

- `assets/studio/data/data_sharing_adapters.json`
- `assets/studio/data/data_sharing_adapters.schema.json`

Registry operation names are limited to:

- `prepare`
- `list_returned`
- `review`
- `apply`

Adapter-specific apply variants are declared as `apply_actions` under the `apply` capability.
They are not top-level registry operations.

Capability statuses are:

- `active`
- `planned`
- `stub`
- `disabled`

Selection models are:

- `documents`
- `records`
- `file_only`
- `none`

The registry must reject duplicate domain-operation dispatch, unsafe relative paths, unknown operation names, and invalid status values before a request reaches adapter code.

## Review Row Contract

Returned-package review responses are record-oriented.
Rows must be renderable without assuming a `doc_id`.

Minimum shared row fields:

- `id`
- `type`
- `title`
- `meta`
- `record_index`
- `selectable`
- `record_groups`
- `issues`

Documents can still expose document-shaped rows.
Tags can expose tag, alias, series-assignment, warning, conflict, or file-level rows without fabricating document fields.

## Documents Adapter

Adapter id: `documents`

Module identity: `documents`

Current domain:

- `data_domain: "library"`

The documents adapter owns:

- Library sharing profile loading from `assets/studio/data/library_export_configs.json`
- generated Docs Viewer index and payload reads
- document tree selection and field mapping
- outbound package generation through `docs-viewer/services/docs_export.py`
- returned Library `.json` and `.jsonl` package listing
- staged package parsing and Markdown review generation through `docs-viewer/services/docs_import.py`
- summary and hierarchy apply planning
- `docs-viewer/source/library/` writes, docs/search rebuild follow-through, and document activity metadata

Library workflow roots:

- outbound packages: `var/studio/data-sharing/library/exports/`
- returned package staging: `var/studio/data-sharing/library/import-staging/`
- review artifacts: `var/studio/data-sharing/library/import-preview/`
- source root: `docs-viewer/source/library/`
- backup root: `var/docs/backups/`

The documents adapter is the optional companion a portable Docs Viewer install can ship when it wants Library or other Docs Viewer corpus Data Sharing behavior.
It does not own the shared Data Sharing registry or non-document adapters.

## Analytics Tags Adapter

Adapter id: `analytics-tags`

Module identity: `analytics.tags`

Current domain:

- `data_domain: "tags"`
- UI scope: `Analytics`

The user-facing scope is Analytics because tag data belongs to the Analytics Studio area.
The adapter data domain remains `tags` so future Analytics scoring or registry workflows do not inherit tag-specific dispatch behavior.

The tags adapter owns:

- outbound package preparation for tag registry, tag aliases, tag assignments, and combined tags bundles
- returned-package listing under the tags staging root
- tag registry, alias, and assignment review without writing
- confirmed apply for selected registry, alias, and applicable assignment rows
- validation against tag policy, aliases, series, and work membership
- backups and writes through existing Analytics tag transaction helpers
- activity metadata for tags, aliases, series, works, and files

Tags workflow roots:

- outbound packages: `var/studio/data-sharing/tags/exports/`
- returned package staging: `var/studio/data-sharing/tags/import-staging/`
- review output root: `var/studio/data-sharing/tags/import-preview/`
- source root: `assets/studio/data/`
- backup root: `var/studio/data-sharing/tags/backups/`

Implemented sharing profiles:

- `tag-registry`
- `tag-aliases`
- `tag-assignments`
- `tags-bundle`

Implemented apply actions:

- `registry_apply`
- `aliases_apply`
- `assignments_apply`

## Activity

Data Sharing write operations append Studio Activity rows only after successful writes or package creation.

Current page ids:

- `data-sharing-prepare`
- `data-sharing-review`

Current prepare action id:

- `prepare-share-package`

Current document apply action ids:

- `apply-returned-summaries`
- `apply-returned-hierarchy`

Current tags apply action ids:

- `apply-returned-tag-registry`
- `apply-returned-tag-aliases`
- `apply-returned-tag-assignments`

Selection changes, filter changes, review-only validations, unavailable-service states, and cancelled confirmations do not write Studio Activity rows.

## Portability Boundary

Data Sharing should remain separable from Docs Viewer core.

Portable packages can be thought of as:

- Docs Viewer core: read-only viewer, generated docs data, search, and optional local docs management
- documents data sharing adapter: document package preparation, returned-package review, and document apply behavior for Docs Viewer corpora
- Studio Data Sharing module: shared shell, adapter registry, local service dispatch, lifecycle, status, confirmation, and result presentation contracts
- Analytics tags adapter: tag registry, alias, assignment, validation, review, package, apply, backup, and activity behavior

The shared shell must not learn document parsing, tag policy, catalogue relationship validation, or source-write semantics beyond the metadata needed to route, confirm, and present adapter results.

## Verification

Focused checks for Data Sharing changes:

- `studio/tests/python/test_data_sharing_adapters.py`
- `studio/tests/python/test_data_sharing_service.py`
- `docs-viewer/tests/python/test_docs_import_service.py`
- `studio/tests/python/test_tags_data_sharing_adapter.py`
- `studio/tests/smoke/data_sharing_prepare.py`
- `studio/tests/smoke/data_sharing_review.py`

Use broader `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py` profiles only when a change touches runtime behavior, route readiness, generated docs/search contracts, or shared Studio service behavior.
