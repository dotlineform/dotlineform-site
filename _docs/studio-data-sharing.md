---
doc_id: studio-data-sharing
title: Studio Data Sharing
added_date: 2026-05-06
last_updated: "2026-05-13 16:13"
parent_id: studio
sort_order: 98
---
# Studio Data Sharing

Routes:

- `/studio/data-sharing/`
- `/studio/data-sharing/prepare/`
- `/studio/data-sharing/review/`

Studio Data Sharing is the shared shell for preparing outbound share packages and reviewing returned packages from supported Studio data domains.
It defaults to the Library data domain and can expose Tags as a named workflow scope when the planned Analytics tags adapter is present in `assets/studio/data/data_sharing_adapters.json`.

## Current Scope

Library is the only implemented data domain in this slice.
Tags are visible as a planned/stub data domain for the adapter contract, but tag package preparation, review, and apply behavior remain unavailable until later slices.

The prepare page:

- loads enabled Library sharing profiles from `assets/studio/data/library_export_configs.json`
- reads the generated Library docs index through the docs-management local service
- renders a selectable hierarchical document list in Docs Viewer order
- supports JSON and JSONL target formats according to each profile
- posts the selected profile, format, and document ids to the local docs-management service
- displays the output package path, counts, warnings, and errors returned by the service

The review page:

- lists returned Library `.json` and `.jsonl` package files from the configured staging root
- generates Markdown review artifacts for the selected package
- displays parsed records, warnings, and review rows
- can apply selected summary or hierarchy changes after confirmation

The local service gateway uses neutral Data Sharing endpoints:

- `GET /data-sharing/returned-packages`
- `POST /data-sharing/prepare`
- `POST /data-sharing/review`
- `POST /data-sharing/apply`

## Runtime

The page shells load:

- `assets/studio/js/data-sharing-prepare.js`
- `assets/studio/js/data-sharing-review.js`
- `assets/studio/js/data-sharing-adapters.js`
- `assets/studio/data/data_sharing_adapters.json`
- `assets/studio/data/library_export_configs.json`
- `scripts/studio/data_sharing_routes.py`
- `scripts/studio/data_sharing_service.py`
- `scripts/docs/documents_data_sharing_adapter.py`

The documents adapter wrapper owns the implemented Library config set, source index, document tree selection, field mapping, returned-package review, summary apply, and hierarchy apply behavior.
The shared adapter registry uses canonical Data Sharing operation names: `prepare`, `list_returned`, `review`, and `apply`.
Document-specific apply variants such as `summary_apply` and `hierarchy_apply` are apply actions, not top-level registry operations.
The docs-management server hosts the loopback HTTP process and supplies backup, log, and rebuild dependencies, but Data Sharing route ownership and shared adapter dispatch live under `scripts/studio/`.

## Activity

Successful write runs attach Studio Activity context with:

- prepare page id: `data-sharing-prepare`
- prepare action id: `prepare-share-package`
- review page id: `data-sharing-review`
- review action ids: `apply-returned-summaries` and `apply-returned-hierarchy`

Selection changes, filter changes, review-only previews, and unavailable-service states are not written to Studio Activity.

## Verification

The retained smoke entry points are:

- `tests/smoke/data_sharing_prepare.py`
- `tests/smoke/data_sharing_review.py`
- `tests/python/test_data_sharing_service.py`
- `tests/python/test_docs_import_service.py`
