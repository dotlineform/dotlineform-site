---
doc_id: studio-data-sharing-technical-spec
title: Analytics Data Sharing Technical Spec
added_date: "2026-05-13 18:15"
last_updated: 2026-06-05
parent_id: data-sharing
viewable: true
---
# Analytics Data Sharing Technical Spec

Analytics Data Sharing is the shared Local Analytics shell for preparing outbound share packages, listing returned packages, reviewing returned structured data, and applying confirmed changes through domain adapters.

The module uses Data Sharing terminology for current routes, code, configuration, and UI copy.

Older import/export names remain only in historical change-log entries, and separate domain workflows such as Docs Import or catalogue workbook import.

## Routes

- `/analytics/data-sharing/prepare/?mode=manage`
- `/analytics/data-sharing/review/?mode=manage`

The page shells are Analytics-owned.
They call a same-origin Analytics local API, render shared lifecycle states, and use adapter metadata to decide which domains, sharing profiles, selectable records, review rows, and apply actions are available.
Retired Local Studio Data Sharing routes are intentionally not redirected, proxied, or shimmed.

## Local Service Contract

The standalone Local Analytics app owns the Data Sharing HTTP process.
The local API is same-origin with the Analytics pages and delegates headless work to the Data Sharing subsystem.
Local Studio and Docs Viewer service endpoints are not part of the durable Data Sharing route contract.

Endpoints:

- `GET /analytics/api/data-sharing/health`
- `GET /analytics/api/data-sharing/selectable-records`
- `GET /analytics/api/data-sharing/returned-packages`
- `POST /analytics/api/data-sharing/prepare`
- `POST /analytics/api/data-sharing/review`
- `POST /analytics/api/data-sharing/apply`

Analytics API handlers own:

- same-origin request routing and local-origin enforcement
- route readiness, unavailable-service payloads, and browser-facing status responses
- passing request payloads to the headless Data Sharing dispatcher
- activity append timing after successful package creation or confirmed writes

Current implementation:

- `analytics-app/app/server/analytics_app/analytics_data_sharing_api.py` owns the Local Analytics endpoint dispatch surface.
- Runtime config publishes endpoint URLs under `app.runtime.services.data_sharing`.
- `data-sharing/data_sharing/services/dispatch.py` owns handler selection and shared operation dispatch for `prepare`, `list_returned`, `review`, and `apply`.
- `data-sharing/data_sharing/workflows/prepare.py`, `list_returned.py`, `review.py`, and `apply.py` expose the headless workflow entry points.
- `analytics-app/app/server/analytics_app/data_sharing_service.py` supplies the Analytics adapter resolver to the headless workflow dispatchers.
- `GET /analytics/api/data-sharing/selectable-records` returns the active adapter's selection model and an adapter-owned record list; the documents adapter derives that list from Docs Viewer source metadata without going through Docs Viewer HTTP.

The headless `data-sharing/` subsystem owns:

- adapter registry loading and validation
- adapter resolution by `data_domain` and canonical `operation`
- operation dispatch for `prepare`, `list_returned`, `review`, and `apply`
- selectable-record dispatch for prepare workflows
- package I/O and returned JSON handling
- common path safety checks for package roots, staging roots, review roots, and source roots
- common dry-run and confirmation gates
- shared path contracts and schemas

Domain adapters own source parsing, validation, review row semantics, write planning, and writes for their data model.
They may call reusable domain helpers, but the shared Analytics shell and local API do not implement domain write logic directly.

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
It must not contain servers, route views, browser modules, app-shell state, or page rendering.
The Analytics app imports it from local API handlers.

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
The Analytics shell must not fetch a generic generated-docs index as its durable selection source.

Minimum shared selectable-record fields:

- `id`
- `title`
- `type`
- `meta`
- `selectable`
- `children`
- `issues`

Adapters may include domain-specific fields when their render module understands them.
The documents adapter returns document records from Docs Viewer source metadata derived from scope config and source Markdown.
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
- source-derived Docs Viewer document metadata reads
- selectable document records and field mapping
- outbound package generation through reusable docs-domain helpers
- returned Library `.json` and `.jsonl` package listing
- staged package parsing and Markdown review generation through reusable docs-domain helpers
- summary and hierarchy apply planning
- `docs-viewer/source/library/` writes, docs/search rebuild follow-through, and document activity metadata

Current docs-domain helper package:

- `docs-viewer/services/docs_data_sharing/source_metadata.py`: source metadata records, source rendering, content text, and headings for Data Sharing document workflows
- `docs-viewer/services/docs_data_sharing/package.py`: selectable document records, package generation, and returned-package listing
- `docs-viewer/services/docs_data_sharing/review.py`: staged package parsing, Markdown preview generation, and review-row shaping
- `docs-viewer/services/docs_data_sharing/apply.py`: summary and hierarchy apply planning and result payload shaping
- `docs-viewer/services/docs_data_sharing/write.py`: source writes and docs/search rebuild follow-through

Document metadata source contract:

- The source of truth is the configured Docs Viewer scope plus source Markdown front matter and body content.
- The read helper is Docs Viewer-owned and consumed in-process by the documents adapter.
- Generated publication artifacts are not metadata inputs for selectable records, export rows, source-text extraction, or returned-package current-context checks.
- Public flat docs indexes, public tree/search/recently-added payloads, generated by-id payloads, manage/local generated indexes, and generated metadata JSON must not be used as compatibility fallbacks.

Library workflow roots:

- outbound packages: `var/analytics/data-sharing/library/exports/`
- returned package staging: `var/analytics/data-sharing/library/import-staging/`
- review artifacts: `var/analytics/data-sharing/library/import-preview/`
- source root: `docs-viewer/source/library/`
The adapter registry validates the first three roots against `var/analytics/data-sharing/<data_domain>/...`; adapters should not add fallback reads for old disposable `var/studio/data-sharing/...` or `var/studio/export-import/...` packages.

The documents adapter is Data Sharing-owned adapter code that a portable Docs Viewer install can ship when it wants Library or other Docs Viewer corpus Data Sharing behavior.
It does not own the shared Data Sharing registry or non-document adapters.
Docs-domain helpers remain under the Docs Viewer ownership boundary unless a later implementation deliberately creates a new package boundary.
They must be callable without Docs Viewer HTTP or UI/service wrapper modules.

Document Data Sharing uses narrow in-process dependencies:

- `docs_data_sharing.package` owns selectable document reads, package generation, and returned-package listing.
- `docs_data_sharing.review` owns staged document package parsing and review-row shaping.
- `docs_data_sharing.apply` owns summary and hierarchy apply planning.
- `docs_data_sharing.write` delegates source-write rebuild follow-through through an injected callable.
- `docs_data_sharing.activity` owns document Data Sharing Studio Activity attachment for package creation and apply operations.

The Analytics Data Sharing API injects these helpers into the documents adapter.
It must not import `docs_management_context`, call Docs Viewer service HTTP endpoints, or route document Data Sharing work through broad Docs Viewer management-service handles.

## Analytics Tags Adapter

Adapter id: `analytics-tags`

Module identity: `analytics.tags`

Current domain:

- `data_domain: "tags"`
- UI scope: `Analytics`

The user-facing scope is Analytics because tag data belongs to the Analytics app boundary.
The adapter data domain remains `tags` so future Analytics scoring or registry workflows do not inherit tag-specific dispatch behavior.

The tags adapter owns:

- outbound package preparation for tag registry, tag aliases, tag assignments, and combined tags bundles
- returned-package listing under the tags staging root
- tag registry, alias, and assignment review without writing
- confirmed apply for selected registry, alias, and applicable assignment rows
- validation against tag policy, aliases, series, and work membership
- atomic writes through existing Analytics tag transaction helpers
- activity metadata for tags, aliases, series, works, and files

Tags workflow roots:

- outbound packages: `var/analytics/data-sharing/tags/exports/`
- returned package staging: `var/analytics/data-sharing/tags/import-staging/`
- review output root: `var/analytics/data-sharing/tags/import-preview/`
- source root: `analytics-app/data/canonical/`
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

## Moved Modules

The implemented architecture moved Data Sharing-owned code and config out of Studio and Docs Viewer service wrappers:

- adapter registry, schemas, path contracts, package I/O, and dispatch now live under `data-sharing/`
- documents adapter code lives at `data-sharing/data_sharing/adapters/documents/adapter.py`
- Analytics tags adapter code lives at `data-sharing/data_sharing/adapters/tags/adapter.py`
- shared operation dispatch lives at `data-sharing/data_sharing/services/dispatch.py`
- workflow entry points live under `data-sharing/data_sharing/workflows/`
- documents-domain helper responsibilities live under `docs-viewer/services/docs_data_sharing/`
- Analytics local HTTP endpoints live under `analytics-app/app/server/analytics_app/analytics_data_sharing_api.py`

Do not reintroduce Data Sharing HTTP endpoints into Docs Viewer service modules.
Do not reintroduce Analytics Data Sharing imports from `docs_management_context`, `docs_management_service`, or Docs Viewer management routes.
Do not reintroduce Data Sharing HTTP endpoints, route shells, proxies, or static shims into Local Studio.
Do not add browser, server, or route shell code under `data-sharing/`.

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
- Analytics Data Sharing module: pages, browser modules, same-origin local API, lifecycle, status, confirmation, and result presentation contracts
- Analytics tags adapter: tag registry, alias, assignment, validation, review, package, apply, and activity behavior

The shared shell must not learn document parsing, tag policy, catalogue relationship validation, or source-write semantics beyond the metadata needed to route, confirm, and present adapter results.

## Verification

Focused checks for Data Sharing changes:

- `analytics-app/tests/python/test_analytics_data_sharing_api.py`
- `docs-viewer/tests/python/test_docs_import_service.py`
- `analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py`
- `analytics-app/tests/smoke/data_sharing_prepare.py`
- `analytics-app/tests/smoke/data_sharing_review.py`

Use broader `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py` profiles only when a change touches runtime behavior, route readiness, generated docs/search contracts, or shared service behavior.

The 2026-05 split records focused API tests and mock/block/route smokes against the Analytics-owned `/analytics/api/data-sharing/...` boundary.
Codex did not run a manual Docs Viewer generated payload rebuild during SDSA-015; local docs-watcher output, when present, is normal follow-through from the edited source docs.
The full prepare/review browser smoke entrypoints default to the Local Analytics app host because Data Sharing route shells are no longer static Jekyll route files and no longer belong to Local Studio.
