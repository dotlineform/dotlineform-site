---
doc_id: studio-data-sharing-technical-spec
title: Studio Data Sharing Technical Spec
added_date: "2026-05-13 18:15"
last_updated: 2026-05-26
parent_id: data-sharing
sort_order: 2000
viewable: true
---
# Studio Data Sharing Technical Spec

Studio Data Sharing is the shared Studio shell for preparing outbound share packages, listing returned packages, reviewing returned structured data, and applying confirmed changes through domain adapters.

The module uses Data Sharing terminology for current routes, code, configuration, and UI copy.
Older import/export names remain only in archived request docs, historical change-log entries, and separate domain workflows such as Docs Import or catalogue workbook import.

## Routes

- `/studio/data-sharing/prepare/?mode=manage`
- `/studio/data-sharing/review/?mode=manage`

The page shells are Studio-owned.
They call a same-origin Studio local API, render shared lifecycle states, and use adapter metadata to decide which domains, sharing profiles, selectable records, review rows, and apply actions are available.

## Local Service Contract

Studio owns the Data Sharing HTTP process.
The local API is same-origin with the Studio pages and delegates headless work to the Data Sharing subsystem.
Docs Viewer service endpoints are not part of the durable Data Sharing route contract.

Endpoints:

- `GET /studio/api/data-sharing/health`
- `GET /studio/api/data-sharing/selectable-records`
- `GET /studio/api/data-sharing/returned-packages`
- `POST /studio/api/data-sharing/prepare`
- `POST /studio/api/data-sharing/review`
- `POST /studio/api/data-sharing/apply`

Studio API handlers own:

- same-origin request routing and local-origin enforcement
- route readiness, unavailable-service payloads, and browser-facing status responses
- passing request payloads to the headless Data Sharing dispatcher
- activity append timing after successful package creation or confirmed writes

Current implementation:

- `studio/app/server/studio/studio_data_sharing_api.py` owns the Local Studio endpoint dispatch surface.
- Runtime config publishes endpoint URLs under `app.runtime.services.data_sharing`.
- `data-sharing/data_sharing/services/dispatch.py` owns handler selection and shared operation dispatch for `prepare`, `list_returned`, `review`, and `apply`.
- `data-sharing/data_sharing/workflows/prepare.py`, `list_returned.py`, `review.py`, and `apply.py` expose the headless workflow entry points.
- `studio/app/server/studio/data_sharing_service.py` remains as a Studio compatibility gateway that supplies the current Studio adapter resolver to the headless workflow dispatchers.
- `GET /studio/api/data-sharing/selectable-records` returns the active adapter's selection model and an adapter-owned record list; the documents adapter currently derives that list from generated Docs Viewer data without going through Docs Viewer HTTP.

The headless `data-sharing/` subsystem owns:

- adapter registry loading and validation
- adapter resolution by `data_domain` and canonical `operation`
- operation dispatch for `prepare`, `list_returned`, `review`, and `apply`
- selectable-record dispatch for prepare workflows
- package I/O and returned JSON handling
- common path safety checks for package roots, staging roots, review roots, source roots, and backup roots
- common dry-run and confirmation gates
- shared path contracts and schemas

Domain adapters own source parsing, validation, review row semantics, write planning, backups, and writes for their data model.
They may call reusable domain helpers, but the shared Studio shell and local API do not implement domain write logic directly.

## Headless Subsystem

Target tracked layout:

```text
data-sharing/
  config/
    adapters.json
    adapters.schema.json
    library-export-configs.json
    library-export-configs.schema.json
  data_sharing/
    adapters/
      documents/
      tags/
      catalogue/
    services/
      registry.py
      dispatch.py
      paths.py
      package_io.py
    workflows/
      prepare.py
      list_returned.py
      review.py
      apply.py
```

`data-sharing/` must stay headless.
It must not contain servers, route views, browser modules, Studio shell state, or page rendering.
Studio imports it from local API handlers.

## Adapter Registry

The target source-controlled registry is:

- `data-sharing/config/adapters.json`
- `data-sharing/config/adapters.schema.json`

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

## Selectable Record Contract

Prepare pages receive selectable records from the active adapter.
The Studio shell must not fetch a generic generated-docs index as its durable selection source.

Minimum shared selectable-record fields:

- `id`
- `title`
- `type`
- `meta`
- `selectable`
- `children`
- `issues`

Adapters may include domain-specific fields when their render module understands them.
The documents adapter can return a hierarchy ordered from Docs Viewer generated data.
Tags or future catalogue adapters can return flat records, grouped records, file-only choices, or no selection according to their capability metadata.

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

Implementation module:

- `data-sharing/data_sharing/adapters/documents/adapter.py`

The documents adapter owns:

- Library sharing profile loading from `data-sharing/config/library-export-configs.json`
- generated Docs Viewer index and payload reads
- selectable document records and field mapping
- outbound package generation through reusable docs-domain helpers
- returned Library `.json` and `.jsonl` package listing
- staged package parsing and Markdown review generation through reusable docs-domain helpers
- summary and hierarchy apply planning
- `docs-viewer/source/library/` writes, docs/search rebuild follow-through, and document activity metadata

Current docs-domain helper package:

- `docs-viewer/services/docs_data_sharing/package.py`: selectable document records, package generation, and returned-package listing
- `docs-viewer/services/docs_data_sharing/review.py`: staged package parsing, Markdown preview generation, and review-row shaping
- `docs-viewer/services/docs_data_sharing/apply.py`: summary and hierarchy apply planning and result payload shaping
- `docs-viewer/services/docs_data_sharing/write.py`: source writes, backups, and docs/search rebuild follow-through

Library workflow roots:

- outbound packages: `var/studio/data-sharing/library/exports/`
- returned package staging: `var/studio/data-sharing/library/import-staging/`
- review artifacts: `var/studio/data-sharing/library/import-preview/`
- source root: `docs-viewer/source/library/`
- backup root: `var/docs/backups/`

The adapter registry validates the first three roots against `var/studio/data-sharing/<data_domain>/...`; adapters should not add fallback reads for old disposable `var/studio/export-import/...` packages.

The documents adapter is Data Sharing-owned adapter code that a portable Docs Viewer install can ship when it wants Library or other Docs Viewer corpus Data Sharing behavior.
It does not own the shared Data Sharing registry or non-document adapters.
Docs-domain helpers remain under the Docs Viewer ownership boundary unless a later implementation deliberately creates a new package boundary.
They must be callable without Docs Viewer HTTP or UI/service wrapper modules.

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

The tags adapter implementation lives at `data-sharing/data_sharing/adapters/tags/adapter.py` and is resolved through the same Data Sharing registry and workflow dispatcher as the documents adapter.
It should not depend on Docs Viewer service availability.

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
- Data Sharing subsystem: headless registry, adapter config, package contracts, workflow dispatch, path contracts, package I/O, and adapters
- documents data sharing adapter: document selectable records, package preparation, returned-package review, and document apply behavior for Docs Viewer corpora through reusable docs-domain helpers
- Studio Data Sharing module: pages, browser modules, same-origin local API, lifecycle, status, confirmation, and result presentation contracts
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
