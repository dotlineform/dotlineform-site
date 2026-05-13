---
doc_id: studio-activity
title: Studio Activity
added_date: 2026-05-08
last_updated: "2026-05-13"
parent_id: studio
sort_order: 53
---
# Studio Activity

This document describes the Studio page at `/studio/activity/`.

## Purpose

The page is the v1 unified activity report for local authoring actions.
It lists script-level activity rows while preserving the page and button action that initiated them.

Current coverage includes catalogue editor save/create/delete/publication actions plus Batch C import/export/report/audit/utility actions: workbook import apply, moment import apply, project-state report generation, docs source import, Data Sharing package/apply actions, docs broken-links audit, Studio audits, series tag saves/imports, tag registry writes, and tag alias writes.
Most initiating pages live under `/studio/`; Docs source import is a Docs Viewer manage-mode activity and is recorded with `surface: "docs"` in `assets/studio/data/activity_contract.json`.
The retired split source-side and build-side report pages have been removed; this is the only active Studio activity report.

## Route Ready State

The page root `#studioActivityRoot` implements the shared Studio ready-state contract:

- `data-studio-ready="false"` during initial feed loading
- `data-studio-ready="true"` after the activity feed has loaded or reached a stable unavailable state
- `data-studio-busy="false"` because this route has no route-level commands
- `data-studio-mode="empty|list"`
- `data-studio-service="available|unavailable"`
- `data-studio-record-loaded="true|false"`

## Inputs

The page reads the unified feed through the local Catalogue Write Server:

- `GET /catalogue/read?key=activity_log`

That service-backed read returns:

- `var/studio/activity/activity_log.json`

The fuller local journal lives beside the capped feed outside published route data:

- `var/studio/activity/activity_log.jsonl`

The feed labels hydrate from:

- `assets/studio/data/activity_contract.json`

## Row Shape

Each feed row includes:

- date-time
- compact status marker
- page label
- user action label
- script purpose label
- affected record groups
- detail items for the modal

Affected record group summaries include catalogue records plus docs, files, tags, aliases, and search rows when the emitting service supplies those groups.

Clicking the status marker opens the detail modal for that row.

## V1 Boundaries

What this page is for:

- correlated Studio activity reporting
- reviewing the downstream effects of a button click
- serving as the unified replacement for the retired split activity surfaces

What it is not for:

- raw log viewing
- full field-level diffs
- terminal output
- background watcher activity without a meaningful initiating context

## Related References

- **[Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log)**
- **[Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)**
