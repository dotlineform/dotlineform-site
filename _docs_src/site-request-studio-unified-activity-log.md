---
doc_id: site-request-studio-unified-activity-log
title: Studio Unified Activity Log Request
added_date: 2026-05-08
last_updated: "2026-05-08"
ui_status: proposed
parent_id: change-requests
sort_order: 208
---
# Studio Unified Activity Log Request

Status:

- proposed

## Summary

Replace the separate Studio activity report pages with one unified activity log that explains Studio work from the curator's point of view.

The new surface should show a row for each distinct script-level activity, while making clear which single Studio page button click initiated it.
For example, one `Save` click on `/studio/catalogue-work/` could produce separate rows for source save, published-data rebuild, lookup refresh, and search rebuild, all grouped by the same initiating action label such as `save work`.

## Current Inputs

The current activity surfaces summarize overlapping parts of these logs and generated feeds:

- `var/studio/catalogue/logs/catalogue_write_server.log`
- `assets/studio/data/catalogue_activity.json`
- `assets/studio/data/build_activity.json`
- `var/build_activity/build_catalogue.jsonl`

Current report routes:

- `/studio/build-activity/`
- `/studio/catalogue-activity/`

Those pages are useful, but they separate source-side activity from build activity in a way that makes causality harder to understand.

## Problem

The current activity reporting has three practical gaps:

- it is difficult to tell what user action caused a script action
- it is difficult to see which records changed across canonical source data, published runtime data, lookup data, and search data
- it does not fully describe all Studio page activity, including export/import flows and docs import actions

From the user's perspective, the important question is not only "what script ran?".
The important question is "what happened after I clicked this button, and did each part complete?".

## Goals

Build a single activity log that:

- replaces `/studio/build-activity/` and `/studio/catalogue-activity/` as the primary Studio activity report surface
- includes activity from catalogue editors, catalogue import/export flows, docs import, and other Studio pages that perform writes or build actions
- records the initiating Studio page and user action for every row
- records one row for each distinct downstream action, such as saving canonical data, saving published data, rebuilding lookups, updating search, deleting media, or importing docs
- lets multiple rows share one initiating action so the user can see the full consequence chain of a button click
- reports affected record groups across canonical, published, lookup, search, local media, and remote media boundaries
- provides a detail modal with concise, stacked descriptions of what happened

## Non-Goals

The first implementation should not:

- expose raw log files directly in the browser
- become a terminal-output viewer
- record full field-level diffs by default
- replace script-specific JSON reports where those reports are still useful for debugging
- publish local-only operational activity to the public site
- expose secrets, credentials, local absolute paths, or full payload dumps

## Proposed Route

Preferred route:

- `/studio/activity/`

Retirement behavior:

- `/studio/build-activity/` and `/studio/catalogue-activity/` should no longer be the primary report pages
- they may redirect to `/studio/activity/`, show a deprecation notice, or be removed from Studio navigation after the unified page is stable

## Activity Row Model

Each list row represents one distinct script-level activity initiated by a Studio action.

Required columns:

| Column | Purpose |
|---|---|
| `date-time` | when the script-level activity completed or reached a terminal state |
| `status` | compact status marker, using `✅` for completed and `❗️` for warning/attention |
| `page` | human label for the Studio page, such as `catalogue work editor` or `docs import` |
| `user action` | the initiating button/action label, such as `save work`, `delete`, `import docs`, or `publish series` |
| `script purpose` | the downstream purpose, such as `save canonical data`, `rebuild lookups`, `update search`, or `delete local media` |

Rows from one button click should share a stable correlation value even when they come from different scripts or generated feeds.
The row does not need to display the raw correlation id by default, but the detail modal may show it for troubleshooting.

## Example Row Expansion

A single user click:

- page: `catalogue work editor`
- user action: `save work`

Could produce rows:

| Status | Script Purpose |
|---|---|
| `✅` | save canonical data |
| `✅` | rebuild published work data |
| `✅` | rebuild lookups |
| `✅` | update search |
| `❗️` | publish remote media |

The list should make it obvious that those rows belong to one initiating action without collapsing them into an unreadable single row.

## Detail Modal

Clicking the status marker for a row should open a modal with a stacked vertical list of detailed descriptions for that activity.

Example detail items:

- Deleted series `xxx`
- Deleted dependent source records `xxxxx`
- Deleted local media `xxx`
- Updated `assets/data/series_index.json`
- Rebuilt catalogue search

Detail items should be concise and user-readable.
They should not require the user to understand low-level implementation details, but they should be specific enough to support follow-up decisions.

## Structured Event Contract

The implementation should introduce or normalize a structured event shape that every participating Studio action can emit.

Suggested fields:

| Field | Purpose |
|---|---|
| `activity_id` | unique id for the row |
| `correlation_id` | shared id for all rows caused by one user action |
| `timestamp` | completion timestamp |
| `status` | `completed`, `warning`, or later `failed` if needed |
| `page_id` | stable Studio page id |
| `page_label` | display label for the Studio page |
| `user_action_id` | stable initiating action id |
| `user_action_label` | display label such as `save work` |
| `script_purpose_id` | stable downstream action id |
| `script_purpose_label` | display label such as `rebuild search` |
| `record_groups` | affected works, details, series, moments, docs, files, and search records |
| `detail_items` | ordered descriptions shown in the modal |
| `source_refs` | optional log/feed references for troubleshooting |

The user-action fields should be assigned at the point where a Studio page invokes the local service.
Downstream scripts should preserve that context rather than inventing their own user-facing cause.

## Source Coverage

The unified log should cover at least:

- catalogue work, detail, series, and moment editor saves
- catalogue creates, deletes, publish/unpublish, and save-published actions
- catalogue bulk import and export/import adapter activity
- docs import preview/apply actions that write docs or staged media
- lookup rebuilds
- published runtime data rebuilds
- catalogue search rebuilds
- local media generation and cleanup
- R2 media publish/delete activity when triggered through Studio or attached to a Studio workflow

## UI Requirements

The unified page should follow existing Studio operational UI conventions:

- compact table/list layout optimized for scanning
- sortable date-time column
- visible status marker as the modal trigger
- stable page and user-action labels, stored in `assets/studio/data/studio_config.json` where practical
- no card-heavy overview or marketing-style explanation
- no raw JSON dump in the default view
- empty, loading, unavailable, and warning states

The route should implement the shared Studio ready-state contract:

- `data-studio-ready`
- `data-studio-busy`
- `data-studio-mode`
- `data-studio-service`

## Data Flow

Preferred direction:

1. Studio page sends a write/build/import request with page and user-action context.
2. Local service attaches a correlation id to that request.
3. Each downstream script or service step appends structured activity rows.
4. A generated activity feed provides the capped list used by `/studio/activity/`.
5. The raw journals remain local-only and are not served as public assets.

This should reduce coupling between the UI and raw log formats.
The browser should read a curated activity feed, not parse `*.log` or `*.jsonl` files directly.

## Documentation Requirements

Implementation should update:

- Studio runtime/page inventory docs
- catalogue write server docs
- scoped catalogue build docs
- docs import docs if docs activity is included in the first slice
- existing Build Activity and Catalogue Activity docs to describe their retirement or replacement
- Studio UI rules if the status-modal list pattern becomes a reusable operational pattern

## Acceptance Criteria

Codex-run checks should include:

- structured event tests for grouping multiple script rows under one user action
- feed-generation tests that merge catalogue write, build, import, and docs activity without duplicate rows
- route-ready audit coverage for the new `/studio/activity/` page
- docs-data rebuild for the Studio docs scope
- docs search rebuild when the request or related docs are updated

Manual checks should include:

- click a catalogue editor `Save` action and confirm multiple downstream rows share the same user action
- click a delete action and confirm the detail modal lists deleted source records, generated artifacts, local media, and search/index updates
- perform a docs import apply and confirm it appears with page `docs import`
- confirm old Build Activity and Catalogue Activity navigation no longer leads users to competing report surfaces

## Benefits

- gives the user a cause-and-effect view of Studio actions
- makes multi-step saves and deletes easier to audit without reading raw logs
- creates one place for catalogue, docs, import/export, build, lookup, search, and media activity
- keeps detailed descriptions available without overloading the main list

## Risks

- event correlation must be introduced carefully or the unified list may imply false causality
- merging existing logs can duplicate or lose activity unless each source has a clear event identity
- adding every script detail to the main row would make the list noisy, so detail belongs in the modal
- route retirement needs clear navigation changes so users do not keep relying on the old split pages
