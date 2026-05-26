---
doc_id: studio-data-sharing
title: Studio Data Sharing
added_date: 2026-05-06
last_updated: "2026-05-13 17:17"
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

## Current Scope

Library is the implemented documents data domain.
Tags are implemented for package preparation, returned-package listing, review, and confirmed apply through the Analytics tags adapter.
The page scope selector presents this as Analytics; the internal data domain remains `tags`.

The prepare page:

- loads enabled Library sharing profiles from `assets/studio/data/library_export_configs.json`
- loads enabled Analytics tag sharing profiles from `assets/studio/data/data_sharing_adapters.json`
- reads the generated Library docs index through the configured Docs Viewer service
- renders a selectable hierarchical document list in Docs Viewer order
- supports JSON and JSONL target formats according to each profile
- posts the selected profile, format, and document ids to the configured Docs Viewer service
- can prepare tag registry, tag aliases, tag assignments, or a combined tags bundle
- displays the output package path, counts, warnings, and errors returned by the service

The review page:

- lists returned Library `.json` and `.jsonl` package files from the configured staging root
- generates Markdown review artifacts for the selected package
- displays parsed records, warnings, and review rows
- can apply selected summary or hierarchy changes after confirmation
- lists returned Tags `.json` and `.jsonl` package files from the configured staging root
- validates tag registry, tag aliases, and tag assignments returned packages without writing
- reports tag assignment applicable rows, conflicts, missing series, and invalid work rows
- can apply selected tag registry, alias, or applicable assignment rows after confirmation

The configured Docs Viewer service uses neutral Data Sharing endpoints:

- `GET <DOCS_VIEWER_BASE_URL>/data-sharing/returned-packages`
- `POST <DOCS_VIEWER_BASE_URL>/data-sharing/prepare`
- `POST <DOCS_VIEWER_BASE_URL>/data-sharing/review`
- `POST <DOCS_VIEWER_BASE_URL>/data-sharing/apply`

## Runtime

The page shells load:

- `assets/studio/js/data-sharing-prepare.js`
- `assets/studio/js/data-sharing-prepare-render.js`
- `assets/studio/js/data-sharing-prepare-service.js`
- `assets/studio/js/data-sharing-prepare-workflow.js`
- `assets/studio/js/data-sharing-review.js`
- `assets/studio/js/data-sharing-adapters.js`
- `assets/studio/data/data_sharing_adapters.json`
- `assets/studio/data/library_export_configs.json`
- `studio/app/server/studio/data_sharing_routes.py`
- `studio/app/server/studio/data_sharing_service.py`
- `docs-viewer/services/documents_data_sharing_adapter.py`
- `studio/services/analytics/tags_data_sharing_adapter.py`

The dashboard, prepare, and review shells are hosted by the local Studio app server.
The old Jekyll route files under `studio/data-sharing/` are retired; the browser modules and CSS contracts remain Studio-owned assets.
The documents adapter wrapper owns the implemented Library config set, source index, document tree selection, field mapping, returned-package review, summary apply, and hierarchy apply behavior.
The Analytics tags adapter owns tag registry, alias, and assignment package preparation, returned-package review, and apply behavior, using existing Analytics tag planners and backup/write helpers.
The shared adapter registry uses canonical Data Sharing operation names: `prepare`, `list_returned`, `review`, and `apply`.
Document-specific apply variants such as `summary_apply` and `hierarchy_apply` are apply actions, not top-level registry operations.
The Docs Viewer service hosts the loopback HTTP process and supplies backup, log, generated-read, and rebuild dependencies.
Shared adapter dispatch still uses the Studio Data Sharing service modules behind an explicit Docs Viewer adapter boundary.

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
