---
doc_id: studio-data-sharing
title: Studio Data Sharing
added_date: 2026-05-06
last_updated: 2026-05-26
parent_id: data-sharing
sort_order: 1000
viewable: true
---
# Studio Data Sharing

Routes:

- `/studio/data-sharing/prepare/?mode=manage`
- `/studio/data-sharing/review/?mode=manage`

Studio Data Sharing is the shared shell for preparing outbound share packages and reviewing returned packages from supported Studio data domains.
It defaults to the Library data domain and exposes Tags as a named workflow scope for package preparation, returned-package listing, review, and confirmed apply.

The durable architecture contract is recorded in [Studio Data Sharing Technical Spec](/docs/?scope=studio&doc=studio-data-sharing-technical-spec).

## Target Boundary

Studio owns the Data Sharing pages and the same-origin local API used by those pages.
The browser modules should call Studio-hosted endpoints, not `DOCS_VIEWER_BASE_URL`, for service health, adapter selectable records, package preparation, returned-package listing, review, and confirmed apply.
Docs Viewer URLs remain valid for navigation and page/document implementation links only.

The headless Data Sharing subsystem owns shared workflow code, adapter registry/config loading, schemas, package I/O, path contracts, operation dispatch, and domain adapters.
That subsystem lives under `data-sharing/` and must not host servers, UI routes, browser modules, or Studio shell behavior.
Studio calls it from local API handlers.

Domain adapters own the records a prepare workflow can select.
The prepare page asks the active adapter for selectable records instead of reading a generic generated-docs index from Studio shell code.
For Library documents, that selectable-record response can still be backed by Docs Viewer generated data and docs-domain helpers; the shared Studio shell should not hard-code that implementation detail.

Document source writes remain docs-aware.
The documents adapter calls reusable docs-domain helpers for generated reads, simplified HTML/package creation, returned JSON review, Markdown/front matter updates, backups, and docs/search rebuild follow-through.
Those helpers are callable without routing through Docs Viewer HTTP endpoints.

Runtime packages, returned-package staging, and review artifacts use:

```text
var/studio/data-sharing/<domain>/
```

Disposable packages under old `var/studio/export-import/...` roots are not part of the target compatibility contract.

## Current Scope

Library is the implemented documents data domain.
Tags are implemented for package preparation, returned-package listing, review, and confirmed apply through the Analytics tags adapter.
The page scope selector presents this as Analytics; the internal data domain remains `tags`.

The prepare page:

- loads enabled Library and Analytics tag sharing profiles from the Data Sharing config boundary
- requests adapter-owned selectable records from the Studio Data Sharing API
- renders the returned records using the active adapter's selection model
- supports JSON and JSONL target formats according to each profile
- posts the selected profile, format, and record ids to the Studio Data Sharing API
- can prepare tag registry, tag aliases, tag assignments, or a combined tags bundle
- displays the output package path, counts, warnings, and errors returned by the adapter workflow

The review page:

- lists returned `.json` and `.jsonl` package files from the active adapter staging root
- generates Markdown review artifacts for the selected package
- displays parsed records, warnings, and review rows
- can apply selected summary or hierarchy changes after confirmation
- lists returned Tags `.json` and `.jsonl` package files from the configured staging root
- validates tag registry, tag aliases, and tag assignments returned packages without writing
- reports tag assignment applicable rows, conflicts, missing series, and invalid work rows
- can apply selected tag registry, alias, or applicable assignment rows after confirmation

The target Studio API uses same-origin Data Sharing endpoints:

- `GET /studio/api/data-sharing/health`
- `GET /studio/api/data-sharing/selectable-records`
- `GET /studio/api/data-sharing/returned-packages`
- `POST /studio/api/data-sharing/prepare`
- `POST /studio/api/data-sharing/review`
- `POST /studio/api/data-sharing/apply`

## Runtime

The page shells load:

- `studio/app/frontend/js/data-sharing-prepare.js`
- `studio/app/frontend/js/data-sharing-prepare-render.js`
- `studio/app/frontend/js/data-sharing-prepare-service.js`
- `studio/app/frontend/js/data-sharing-prepare-workflow.js`
- `studio/app/frontend/js/data-sharing-review.js`
- `studio/app/frontend/js/data-sharing-adapters.js`
- `studio/app/server/studio/data_sharing_routes.py`
- `studio/app/server/studio/data_sharing_service.py`
- `data-sharing/config/adapters.json`
- `data-sharing/config/library-export-configs.json`
- `data-sharing/adapters/documents/`
- `data-sharing/adapters/tags/`

The dashboard, prepare, and review shells are hosted by the local Studio app server.
The old Jekyll route files under `studio/data-sharing/` are retired; the browser modules and CSS contracts remain Studio-owned assets.
The documents adapter owns the implemented Library config set, selectable document records, field mapping, returned-package review, summary apply, and hierarchy apply behavior through reusable docs-domain helpers.
The Analytics tags adapter owns tag registry, alias, and assignment package preparation, returned-package review, and apply behavior through existing Analytics tag planners and backup/write helpers.
The shared adapter registry uses canonical Data Sharing operation names: `prepare`, `list_returned`, `review`, and `apply`.
Document-specific apply variants such as `summary_apply` and `hierarchy_apply` are apply actions, not top-level registry operations.
The Studio app server hosts the loopback HTTP process for Data Sharing.
Docs Viewer supplies docs-domain helper behavior for document workflows, but does not own the Data Sharing HTTP endpoints.

## Activity

Successful write runs attach Studio Activity context with:

- prepare page id: `data-sharing-prepare`
- prepare action id: `prepare-share-package`
- review page id: `data-sharing-review`
- review action ids: `apply-returned-summaries` and `apply-returned-hierarchy`
- tags review action ids: `apply-returned-tag-registry`, `apply-returned-tag-aliases`, and `apply-returned-tag-assignments`

Selection changes, filter changes, review-only previews, and unavailable-service states are not written to Studio Activity.

## Verification

The retained smoke entry points are:

- `studio/tests/smoke/local_studio_app_data_sharing_routes.py`
- `studio/tests/smoke/data_sharing_prepare.py`
- `studio/tests/smoke/data_sharing_review.py`
- `studio/tests/python/test_data_sharing_service.py`
- `docs-viewer/tests/python/test_docs_import_service.py`
- `studio/tests/python/test_tags_data_sharing_adapter.py`
