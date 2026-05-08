---
doc_id: studio-activity
title: Studio Activity
added_date: 2026-05-08
last_updated: "2026-05-08 18:20"
parent_id: studio
sort_order: 53
---
# Studio Activity

This document describes the Studio page at `/studio/activity/`.

## Purpose

The page is the v1 unified activity report for Studio actions.
It lists script-level activity rows while preserving the page and button action that initiated them.

Current coverage includes catalogue editor save/create/delete/publication actions plus the first Batch C catalogue-service actions: workbook import apply, moment import apply, and project-state report generation.
Older Build Activity and Catalogue Activity pages remain available during validation.

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

- `assets/studio/data/activity_log.json`

The fuller local journal lives outside published route data:

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

Clicking the status marker opens the detail modal for that row.

## V1 Boundaries

What this page is for:

- correlated Studio activity reporting
- reviewing the downstream effects of a button click
- replacing the old split activity surfaces after the new report is trusted

What it is not for:

- raw log viewing
- full field-level diffs
- terminal output
- background watcher activity without a meaningful initiating context

## Related References

- **[Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log)**
- **[Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory)**
- **[Catalogue Activity](/docs/?scope=studio&doc=catalogue-activity)**
- **[Build Activity](/docs/?scope=studio&doc=build-activity)**
