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

Another useful implementation input is the existing Studio page behavior after a user clicks a command button.
Many pages already display immediate status messages, result summaries, warning text, and modal details after actions such as save, delete, rebuild, export, import, or docs import.
Those messages are good evidence for what the persistent activity log should say.

The activity log should not replace on-page messages or result panels.
The page should still give immediate feedback in the workflow where the user clicked.
The log gives those same kinds of messages a persistent home so the user can review what happened later and connect related downstream script actions.

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
- include server-generated background activity that is not yet correlated to a Studio page action

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

This contract should be visible and reviewable in the repo, not buried only in service code.
It is not expected to be something the user edits often, but it should work like the JSON registry and export/import configs: a structured source of truth that makes the logic, assignments, and display labels explicit.

The user should be able to inspect the contract and answer:

- which Studio pages are covered
- which buttons or commands on each page are captured
- what user-action label appears in the report
- which downstream script purposes can be emitted for that action
- how statuses and detail summaries are displayed

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

## Activity Contract Registry

Add a structured registry or config file for the activity contract.

Candidate location:

- `assets/studio/data/activity_contract.json`

The exact filename can change during implementation, but the contract should stay in a reviewable data file rather than being scattered across page scripts and services.

Suggested top-level shape:

```json
{
  "pages": {
    "catalogue-work": {
      "label": "catalogue work editor",
      "route": "/studio/catalogue-work/",
      "actions": {
        "save-work": {
          "label": "save work",
          "control_label": "Save",
          "script_purposes": [
            "save-canonical-data",
            "rebuild-published-work-data",
            "rebuild-lookups",
            "update-search"
          ]
        }
      }
    }
  },
  "script_purposes": {
    "save-canonical-data": {
      "label": "save canonical data",
      "detail_templates": ["Saved canonical work record {work_id}"]
    },
    "update-search": {
      "label": "update search",
      "detail_templates": ["Rebuilt catalogue search"]
    }
  }
}
```

The registry should be explicit enough that reviewing it answers "what will appear in the activity report if this Studio button is clicked?".
Page scripts and services should refer to stable ids from the registry rather than hardcoding display labels independently.

The registry should not become a user-editable settings page in the first implementation.
It is an operational contract and review aid, similar to other structured configuration files that make Studio behavior visible without turning every mapping into UI.

## Page Message Review

Before implementation, review the current Studio routes and the messages they show when a user clicks a button.

Examples of useful cues:

- success and warning text shown after saving a catalogue record
- delete preview and apply summaries
- rebuild result messages
- import/export completion summaries
- docs import preview/apply result panels
- local media generation warnings and follow-up prompts

These messages should inform:

- `user_action_label`
- `script_purpose_label`
- row status
- modal `detail_items`
- warning/attention language

The activity log should reuse the user-facing meaning of these messages, but not necessarily copy the exact same text.
On-page messages are immediate workflow feedback.
Activity log messages are a persistent summary of the same action and its downstream effects.

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

Initial source coverage should exclude background server-generated activity such as docs-watcher events unless the event can be clearly correlated to a Studio page action.
That exclusion is a first-slice boundary, not a permanent design decision.
Docs-watcher is still often responding to user edits, so a later milestone should be able to include watcher-triggered activity once the initiating user action or source edit can be represented clearly.

## UI Requirements

The unified page should follow existing Studio operational UI conventions:

- compact table/list layout optimized for scanning
- sortable date-time column
- visible status marker as the modal trigger
- stable page, user-action, and script-purpose labels sourced from the activity contract registry, with general UI copy still using `assets/studio/data/studio_config.json` where practical
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

For later background-service coverage, watcher or server-triggered events should enter the same feed only after they can carry a meaningful source context.
If the best available cause is "docs source file changed", the row should say that clearly rather than pretending a Studio button click happened.

## V1 Implementation Slice

First implementation should prove the model with one narrow action:

- page: `/studio/catalogue-work/`
- route id: `catalogue-work`
- control: `#catalogueWorkSave`
- visible button label: `Save`
- user action label: `save work`
- scenario: save metadata edits to a single existing work

The v1 slice should not try to cover bulk save, new work creation, delete, publish/unpublish, docs import, export/import, or background watcher events.
Those should remain later expansions after the correlation model is working for one common catalogue action.

### V1 Expected Rows

For a published work whose metadata save also updates public output, v1 should produce rows like:

| Page | User Action | Script Purpose |
|---|---|---|
| `catalogue work editor` | `save work` | `save canonical data` |
| `catalogue work editor` | `save work` | `rebuild published work data` |
| `catalogue work editor` | `save work` | `rebuild lookups` |
| `catalogue work editor` | `save work` | `update search` |

If the work is draft/unpublished, the downstream published/search rows may be absent or marked as not applicable according to the existing save response.
If there are no changes, v1 should either write a single `no changes` row or skip writing activity, but the decision must be explicit in the registry and tests.

### V1 Tasks

1. Define the first activity contract registry entry.
   - Add the catalogue work editor page.
   - Add the `save-work` action for `#catalogueWorkSave`.
   - Add script-purpose ids for canonical save, published work rebuild, lookup rebuild, and search update.
   - Add user-facing labels and detail templates for each purpose.

2. Add registry validation.
   - Validate unique page ids, action ids, and script-purpose ids.
   - Validate every action references existing script-purpose ids.
   - Validate required display labels are present.
   - Keep validation runnable from Codex and from the normal check profile once the implementation is mature.

3. Pass activity context from the work editor to the catalogue write server.
   - Include page id, action id, route, control id, and current work id in the save request.
   - Let the service assign or normalize a correlation id.
   - Keep the request shape narrow and ignore unknown activity context fields safely.

4. Emit structured v1 activity rows in the catalogue write path.
   - Record one row for the source-record save outcome.
   - Record rows for public rebuild, lookup refresh, and search rebuild when those actions are actually attempted.
   - Use existing save response data and build results rather than scraping UI text.
   - Preserve enough record context to show the work id and changed record family in the modal.

5. Generate a capped activity feed for the new page.
   - Store raw local activity in a local-only journal.
   - Generate a Studio-readable feed with enough rows for the report.
   - Keep local-only paths, payloads, and full log lines out of the feed.

6. Build the first `/studio/activity/` route.
   - Render the required list columns.
   - Load the generated feed through a local service read.
   - Use status as the modal trigger.
   - Show detail items as a stacked vertical list.
   - Implement the shared Studio ready-state attributes.

7. Keep existing work-editor messages in place.
   - The current `Save` result messages should still appear on `/studio/catalogue-work/`.
   - The activity log should persist equivalent meaning, not move immediate feedback away from the editing page.

8. Retain old report pages during v1.
   - Do not remove `/studio/build-activity/` or `/studio/catalogue-activity/` in the first slice.
   - Add the new page alongside them until v1 reporting is trusted.
   - Defer redirect/removal decisions to a later slice.

### V1 Detail Modal Examples

For a successful published work metadata save, the modal details might include:

- Saved canonical work record `00001`
- Updated published work JSON for `00001`
- Refreshed catalogue lookup data for work `00001`
- Rebuilt catalogue search for work `00001`

For a partial failure, the modal should preserve the same structure while marking the failed or warning step clearly.

## Documentation Requirements

Implementation should update:

- the V1 implementation task list in this request
- the activity contract registry/config reference
- Studio runtime/page inventory docs
- catalogue write server docs
- scoped catalogue build docs
- docs import docs if docs activity is included in the first slice
- existing Build Activity and Catalogue Activity docs to describe their retirement or replacement
- Studio UI rules if the status-modal list pattern becomes a reusable operational pattern

## Acceptance Criteria

Codex-run checks should include:

- structured event tests for grouping multiple script rows under one user action
- registry validation tests that confirm covered pages, actions, labels, and script-purpose ids are valid and unique
- v1 tests for a single `/studio/catalogue-work/` metadata save producing the expected correlated rows
- feed-generation tests that merge catalogue write, build, import, and docs activity without duplicate rows
- checks that representative on-page action messages have corresponding activity-log row/detail coverage
- route-ready audit coverage for the new `/studio/activity/` page
- docs-data rebuild for the Studio docs scope
- docs search rebuild when the request or related docs are updated

Manual checks should include:

- click a catalogue editor `Save` action and confirm multiple downstream rows share the same user action
- save metadata edits for one work from `/studio/catalogue-work/` and confirm the report shows `catalogue work editor`, `save work`, and the expected script-purpose rows
- inspect the activity contract registry and confirm the page/button/action labels match the report
- compare representative on-page save/delete/import result messages with the persistent activity rows and modal details
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
