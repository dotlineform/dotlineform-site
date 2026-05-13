---
doc_id: studio-data-sharing
title: Studio Data Sharing
added_date: 2026-05-06
last_updated: "2026-05-13"
parent_id: studio
sort_order: 98
---
# Studio Data Sharing

Routes:

- `/studio/data-sharing/`
- `/studio/data-sharing/prepare/`
- `/studio/data-sharing/review/`

Studio Data Sharing is the shared shell for preparing outbound share packages and reviewing returned packages from supported Studio data domains.
It defaults to the Library data domain and can expose Catalogue and Analytics as named workflow scopes when those adapters are present in `assets/studio/data/data_sharing_adapters.json`.

## Current Scope

Library is the only implemented data domain in this slice.

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

## Runtime

The page shells load:

- `assets/studio/js/data-sharing-prepare.js`
- `assets/studio/js/data-sharing-review.js`
- `assets/studio/js/data-sharing-adapters.js`
- `assets/studio/data/data_sharing_adapters.json`
- `assets/studio/data/library_export_configs.json`

The documents adapter still owns the implemented Library config set, source index, document tree selection, field mapping, review rows, and apply behavior.

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
