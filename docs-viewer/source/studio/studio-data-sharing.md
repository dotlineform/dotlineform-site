---
doc_id: studio-data-sharing
title: Analytics Data Sharing Runtime
added_date: 2026-05-06
last_updated: 2026-06-21
parent_id: data-sharing
viewable: true
---
# Analytics Data Sharing Runtime

Routes:

- `/analytics/data-sharing/prepare/`
- `/analytics/data-sharing/review/`

Analytics Data Sharing is the local shell for preparing outbound share packages and reviewing returned packages from supported local data domains.
It exposes Library document profiles and Analytics tag profiles for package preparation, returned-package listing, review, and confirmed apply.

- The durable runtime boundary is recorded here and in [Analytics Data Sharing Runtime](/docs/?scope=studio&doc=studio-data-sharing)
- The adapter implementation pattern is recorded in [Data Sharing Adapter Architecture](/docs/?scope=studio&doc=data-sharing-adapter-architecture).

## Target Boundary

The standalone Local Analytics app owns the Data Sharing pages and the same-origin local API used by those pages.
The browser modules call Analytics-hosted endpoints, not `DOCS_VIEWER_BASE_URL` or Local Studio endpoints, for service health, adapter selectable records, package preparation, returned-package listing, review, and confirmed apply.
Docs Viewer URLs remain valid for navigation and page/document implementation links only.
Local Studio does not publish Data Sharing routes, API endpoints, runtime-service config, proxies, aliases, or static shims.

The headless Data Sharing subsystem owns shared workflow code, adapter registry/config loading, schemas, package I/O, path contracts, operation dispatch, and domain adapters.
That subsystem lives under `data-sharing/` and must not host servers, UI routes, browser modules, or app-shell behavior.
The Analytics app calls it from local API handlers.

Domain adapters own the records a prepare workflow can select.
The prepare page asks the active adapter for selectable records instead of reading a generic generated-docs index from app-shell code.
For Library documents, that selectable-record response is backed by Docs Viewer source metadata and docs-domain helpers; the shared Analytics shell should not hard-code that implementation detail.

Document source writes remain docs-aware.
The documents adapter calls reusable docs-domain helpers for source-derived metadata, package creation, returned JSON review, Markdown/front matter updates, and docs/search rebuild follow-through.
Those helpers are callable without routing through Docs Viewer HTTP endpoints.

Data Sharing apply routes no longer create local backup artifacts.
Recovery for changed source records relies on Git history, host/filesystem backups, or explicit manual copies made before a risky operation.

Runtime packages, returned-package staging, and review artifacts use:

```text
var/analytics/data-sharing/
```

The adapter registry validates the shared `exports/`, `import-staging/`, and `import-preview/` roots so active adapters cannot silently fall back to older package folders.
Disposable packages under old `var/studio/export-import/...` roots are not part of the target compatibility contract.

## Current Scope

Library is the implemented documents data domain.
Tags are implemented for package preparation, returned-package listing, review, and confirmed apply through the Analytics tags adapter.
The page app selector presents Tags under Analytics; the internal data domain remains `tags`.

The prepare page:

- loads enabled Library and Analytics tag sharing profiles from the Data Sharing config boundary
- requests adapter-owned selectable records from the Analytics Data Sharing API
- renders the returned records using the active adapter's selection model
- supports JSON and JSONL target formats according to each profile
- posts the selected profile, format, and selected ids to the Analytics Data Sharing API
- uses `selection.doc_ids` for document-backed profiles and `selection.record_ids` for generic record-backed profiles such as `tag-registry`
- can prepare tag registry, tag aliases, tag assignments, or a combined tags bundle
- can prepare a tag registry package containing only the selected tag records
- displays the output package path, counts, warnings, and errors returned by the adapter workflow

The review page:

- lists returned `.json` and `.jsonl` package files from the active adapter staging root
- displays parsed records, warnings, and review rows
- writes one Markdown review document for the selected rows
- can apply selected summary or hierarchy changes after confirmation
- lists returned Tags `.json` and `.jsonl` package files from the configured staging root
- validates tag registry, tag aliases, and tag assignments returned packages without writing
- reports tag assignment applicable rows, conflicts, missing series, and invalid work rows
- can apply selected tag registry, alias, or applicable assignment rows after confirmation

The Analytics API exposes same-origin Data Sharing endpoints:

- `GET /analytics/api/data-sharing/health`
- `GET /analytics/api/data-sharing/selectable-records`
- `GET /analytics/api/data-sharing/returned-packages`
- `POST /analytics/api/data-sharing/prepare`
- `POST /analytics/api/data-sharing/review`
- `POST /analytics/api/data-sharing/apply`

These endpoints are published in Local Analytics runtime config under `app.runtime.services.data_sharing`.
Docs Viewer service endpoints are not published under `app.runtime.services.docs` for Data Sharing.

## Runtime

The page shells load:

- `analytics-app/app/frontend/js/data-sharing-prepare.js`
- `analytics-app/app/frontend/js/data-sharing-prepare-render.js`
- `analytics-app/app/frontend/js/data-sharing-prepare-service.js`
- `analytics-app/app/frontend/js/data-sharing-prepare-workflow.js`
- `analytics-app/app/frontend/js/data-sharing-review.js`
- `analytics-app/app/frontend/js/data-sharing-adapters.js`
- `analytics-app/app/server/analytics_app/data_sharing_routes.py`
- `analytics-app/app/server/analytics_app/data_sharing_service.py`
- `analytics-app/app/server/analytics_app/analytics_data_sharing_api.py`
- `data-sharing/services/dispatch.py`
- `data-sharing/workflows/prepare.py`
- `data-sharing/workflows/list_returned.py`
- `data-sharing/workflows/review.py`
- `data-sharing/workflows/apply.py`
- `data-sharing/config/adapters.json`
- `data-sharing/adapters/documents/config/prepare-profiles.json`
- `data-sharing/adapters/documents/`
- `data-sharing/adapters/tags/`

The prepare and review shells are hosted by the Local Analytics app server.
The browser modules and CSS contracts are Analytics-owned assets under `analytics-app/`.
The documents adapter lives under `data-sharing/adapters/documents/`.
Its `adapter.py` module only wires `DataSharingAdapterHandlers`.
Prepare, returned-package orchestration, shared context, and document-family behavior live in `prepare.py`, `returned.py`, `context.py`, and `families/documents.py`.
The implemented document family owns the Library config set, selectable document records, field mapping, returned-package review, summary apply, and hierarchy apply behavior through reusable docs-domain helpers.
Those helpers are split by responsibility under the `docs-viewer/services/docs_data_sharing/` package.
The Analytics tags adapter lives under `data-sharing/adapters/tags/`.
Its `adapter.py` module only wires `DataSharingAdapterHandlers`.
Prepare, returned-package orchestration, shared context, and tag-family behavior live in `prepare.py`, `returned.py`, `context.py`, and `families/`.
The tags families own tag registry, alias, assignment, and bundle package behavior, including selected tag-record export for `tag-registry`, returned-package review, and confirmed apply through Analytics tag mutation/write helpers.
The shared adapter registry uses canonical Data Sharing operation names: `prepare`, `list_returned`, `review`, and `apply`.
The headless `data-sharing/` workflow modules own shared operation dispatch; the Analytics server provides the local HTTP boundary, adapter resolver handoff, and activity timing.
Document-specific apply variants such as `summary_apply` and `hierarchy_apply` are apply actions, not top-level registry operations.
The Analytics app server hosts the loopback HTTP process for Data Sharing.
Docs Viewer supplies docs-domain helper behavior for document workflows, but does not own the Data Sharing HTTP endpoints.

## Architecture Trace

The 2026-05 split moved the durable Data Sharing boundary to:

- Analytics-owned pages and `/analytics/api/data-sharing/...` endpoints
- `data-sharing/` owned registry/config, path contracts, package I/O, workflow dispatch, and documents/tags adapters
- Docs Viewer-owned docs-domain helpers under `docs-viewer/services/docs_data_sharing/`
- runtime artifacts under `var/analytics/data-sharing/exports/`, `import-staging/`, and `import-preview/`

The stable runtime no longer publishes Data Sharing endpoints from Docs Viewer service config or Local Studio runtime config.
Generated Docs Viewer payloads are not the source of this documentation slice; source docs are updated first.
Codex did not run a manual Docs Viewer payload rebuild for this slice, but the local docs watcher may regenerate the affected Studio JSON payloads after these source docs change.

## Activity

Successful write runs attach Studio Activity context with:

- prepare page id: `data-sharing-prepare`
- prepare action id: `prepare-share-package`
- review page id: `data-sharing-review`
- review action ids: `apply-returned-summaries` and `apply-returned-hierarchy`
- tags review action ids: `apply-returned-tag-registry`, `apply-returned-tag-aliases`, and `apply-returned-tag-assignments`

Selection changes, filter changes, and unavailable-service states are not written to Studio Activity.

## Verification

The retained smoke entry points are:

- `analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py`
- `analytics-app/tests/python/test_analytics_data_sharing_api.py`
- `analytics-app/tests/python/test_tags_data_sharing_prepare.py`
- `analytics-app/tests/python/test_tags_data_sharing_returned_registry_aliases.py`
- `analytics-app/tests/python/test_tags_data_sharing_returned_assignments.py`
- `docs-viewer/tests/python/test_docs_import_service.py`

The architecture request tracker records the latest focused evidence for Analytics API dispatch, Docs Management and Local Studio non-publication of Data Sharing endpoints, route-level Data Sharing smokes, adapter path validation, and documents/tags adapter behavior.
Retired Studio routes and endpoints must remain absent rather than being restored as compatibility layers.
