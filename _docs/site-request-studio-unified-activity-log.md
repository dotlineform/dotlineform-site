---
doc_id: site-request-studio-unified-activity-log
title: Studio Unified Activity Log Request
added_date: 2026-05-08
last_updated: "2026-05-08 20:20"
ui_status: done
parent_id: change-requests
sort_order: 208
viewable: true
---
# Studio Unified Activity Log Request

Status:

- implemented
- closed

## Summary

Replaced the separate Studio activity report pages with one unified activity log that explains Studio work from the curator's point of view.

The implemented surface shows a row for each distinct script-level activity, while making clear which single Studio page button click initiated it.
For example, one `Save` click on `/studio/catalogue-work/` could produce separate rows for source save, published-data rebuild, lookup refresh, and search rebuild, all grouped by the same initiating action label such as `save work`.

## Closeout

The unified `/studio/activity/` surface is implemented, covered by the activity contract registry, and is now the only active Studio activity report.
The former split report routes, feed readers, feed writer modules, read keys, config entries, and generated feed artifacts were removed rather than redirected.

The completed coverage inventory remains in [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory).
Remaining optional expansion work has moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups).

## Current Inputs

The unified activity surface now summarizes covered Studio activity from these logs and generated feeds:

- `var/studio/catalogue/logs/catalogue_write_server.log`
- `var/studio/activity/activity_log.json`
- `var/studio/activity/activity_log.jsonl`

Current report route:

- `/studio/activity/`

The previous split source-side and build-side report pages have been removed.

Another useful implementation input is the existing Studio page behavior after a user clicks a command button.
Many pages already display immediate status messages, result summaries, warning text, and modal details after actions such as save, delete, rebuild, export, import, or docs import.
Those messages are good evidence for what the persistent activity log should say.

The activity log should not replace on-page messages or result panels.
The page should still give immediate feedback in the workflow where the user clicked.
The log gives those same kinds of messages a persistent home so the user can review what happened later and connect related downstream script actions.

The page and action coverage checklist lives in [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory).
That inventory records the closed milestone.
Future activity coverage should be tracked in [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups) and update the structured activity contract registry when implemented.

## Problem

This request addressed three practical gaps:

- it is difficult to tell what user action caused a script action
- it is difficult to see which records changed across canonical source data, published runtime data, lookup data, and search data
- it does not fully describe all Studio page activity, including export/import flows and docs import actions

From the user's perspective, the important question is not only "what script ran?".
The important question is "what happened after I clicked this button, and did each part complete?".

## Goals

Implemented a single activity log that:

- replaces the former split report pages as the primary Studio activity report surface
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

## Implemented Route

Route:

- `/studio/activity/`

Retirement behavior:

- the former split report pages were removed from active routes and Studio navigation
- no redirects were kept

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

Location:

- `assets/studio/data/activity_contract.json`

The contract should stay in a reviewable data file rather than being scattered across page scripts and services.

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

Implemented closeout coverage includes:

- catalogue work, detail, series, and moment editor saves
- catalogue creates, deletes, publish/unpublish, and save-published actions
- catalogue bulk import and export/import adapter activity
- docs import actions that write docs or staged media
- lookup rebuilds
- published runtime data rebuilds
- catalogue search rebuilds
- local media cleanup where covered delete/publication flows perform it

Bulk metadata saves, readiness prose/media refresh actions, R2 media publish/delete activity, and background-service attribution moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups).

Background server-generated activity such as docs-watcher events remains excluded unless the event can be clearly correlated to a Studio page action or source context.
That optional expansion now belongs in [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups).

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

## Implementation Decisions

No-change saves should not be reported.
For this purpose, no-change means that no data in the core JSON source was edited, added, or deleted.
If the core data did not change, no publishing activity should have taken place.

Redundant writes are different from no-change saves.
If a file is rewritten even though the data inside it did not change, that activity should be reported because it indicates redundant script work.
Forced rewrites, such as a `--force` rewrite or an explicitly forced refresh, should also be reported.

Preview-only commands should not be included when they genuinely do not persist data to a core JSON file or other durable generated report.
Implementation should still document what each preview does and whether it writes anything.
That review belongs in the implementation notes and inventory, but the activity log itself is for permanent user-initiated data changes, generated reports, and explicit forced rewrites.

Confirmation flows should attribute activity to the first user command that initiated the write/delete workflow.
Confirmation modals should confirm the action; they should not become separate user-action rows.
If any current modal confirmation button is the control that actually calls a write/delete script, implementation should review that flow and preserve the original command context through the modal confirmation.

`/studio/activity/` is now the only user-facing activity feed.
Existing log files may remain as debug inputs on a case-by-case basis.
Codex and developer debugging can inspect local `var/` logs directly when needed, but the Studio user should not have to choose between competing report pages.

The activity contract registry should allow optional script purposes.
The registry describes the possible chain of events for a user action, and the activity log surfaces the rows for the downstream script purposes that were actually attempted.

## Implementation Findings

This request may expose problems in the current Studio workflows, service boundaries, modal behavior, logging, or build orchestration.
Those findings should be logged carefully without turning every discovery into a blocker for the v1 activity log.

Use this triage rule:

| Finding type | Handling |
|---|---|
| Blocks v1 activity logging | Fix in the v1 implementation slice or explicitly narrow the v1 scope. |
| Makes the activity log misleading | Fix before shipping the affected action, or exclude that action until corrected. |
| Reveals redundant work, unclear flow, or optimisation opportunity | Log as a follow-up finding and continue with v1 unless it affects correctness. |
| Reveals a preview/confirmation flow that writes data unexpectedly | Review the flow, preserve original command context, and decide whether it is a blocker for that action only. |
| Reveals stale or competing report surfaces | Log as a retirement/follow-up task unless the old surface confuses v1 validation. |

Findings should record:

- route and control id
- user action label
- observed behavior
- expected behavior
- whether activity-log correctness is affected
- recommended follow-up owner or document
- proposed status: `blocker`, `v1-fix`, `follow-up`, or `noted`

The aim is to keep implementation discoveries visible and actionable while protecting the activity-log delivery path from unrelated cleanup and optimisation work.

## V1 Implementation Slice

First implementation should prove the model with one narrow action:

- page: `/studio/catalogue-work/`
- route id: `catalogue-work`
- control: `#catalogueWorkSave`
- visible button label: `Save`
- user action label: `save work`
- scenario: save metadata edits to a single existing work

The v1 slice did not try to cover bulk save, new work creation, delete, publish/unpublish, docs import, export/import, or background watcher events.
Create, delete, publication, import, export, report, audit, utility actions, and old-report retirement were completed in later batches; bulk save, readiness prose/media actions, and background watcher events moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups).

The full closeout inventory is tracked in [Activity Log Coverage Inventory](/docs/?scope=studio&doc=site-request-studio-unified-activity-log-inventory).

### V1 Expected Rows

For a published work whose metadata save also updates public output, v1 should produce rows like:

| Page | User Action | Script Purpose |
|---|---|---|
| `catalogue work editor` | `save work` | `save canonical data` |
| `catalogue work editor` | `save work` | `rebuild published work data` |
| `catalogue work editor` | `save work` | `rebuild lookups` |
| `catalogue work editor` | `save work` | `update search` |

If the work is draft/unpublished, the downstream published/search rows may be absent or marked as not applicable according to the existing save response.
If there are no core JSON changes, v1 should not write an activity row.
If the save path rewrites files or runs publishing work despite no core data change, v1 should report that redundant or forced activity.

### V1 Tasks

1. Define the first activity contract registry entry.
   - Add the catalogue work editor page.
   - Add the `save-work` action for `#catalogueWorkSave`.
   - Add script-purpose ids for canonical save, published work rebuild, lookup rebuild, and search update.
   - Mark downstream script purposes as optional when they depend on record status or actual attempted work.
   - Add user-facing labels and detail templates for each purpose.

2. Add registry validation.
   - Validate unique page ids, action ids, and script-purpose ids.
   - Validate every action references existing script-purpose ids.
   - Validate required display labels are present.
   - Keep validation runnable from Codex and from the normal check profile.

3. Pass activity context from the work editor to the catalogue write server.
   - Status: done for single-work metadata saves.
   - Include page id, action id, route, control id, and current work id in the save request.
   - Let the service assign or normalize a correlation id.
   - Keep the request shape narrow and ignore unknown activity context fields safely.

4. Emit structured v1 activity rows in the catalogue write path.
   - Status: done for single-work metadata saves from `/studio/catalogue-work/`.
   - Record one row for the source-record save outcome.
   - Record rows for public rebuild, lookup refresh, and search rebuild when those actions are actually attempted.
   - Skip activity for true no-change saves where no core JSON data was changed and no files or generated artifacts were rewritten.
   - Report forced rewrites and redundant rewrites even when serialized data content did not change.
   - Use existing save response data and build results rather than scraping UI text.
   - Preserve enough record context to show the work id and changed record family in the modal.

5. Generate a capped activity feed for the new page.
   - Status: done for the v1 feed source.
   - Store raw local activity in a local-only journal.
   - Generate a Studio-readable feed with enough rows for the report.
   - Keep local-only paths, payloads, and full log lines out of the feed.

6. Build the first `/studio/activity/` route.
   - Status: done for the v1 report page.
   - Render the required list columns.
   - Load the generated feed through a local service read.
   - Use status as the modal trigger.
   - Show detail items as a stacked vertical list.
   - Implement the shared Studio ready-state attributes.

7. Keep existing work-editor messages in place.
   - The current `Save` result messages should still appear on `/studio/catalogue-work/`.
   - The activity log should persist equivalent meaning, not move immediate feedback away from the editing page.

8. Retire old report pages after v1 coverage.
   - Batch D removed the old split activity report pages rather than redirecting them.
   - The unified `/studio/activity/` route is now the only active Studio activity report surface.

### V1 Detail Modal Examples

For a successful published work metadata save, the modal details might include:

- Saved canonical work record `00001`
- Updated published work JSON for `00001`
- Refreshed catalogue lookup data for work `00001`
- Rebuilt catalogue search for work `00001`

For a partial failure, the modal should preserve the same structure while marking the failed or warning step clearly.

## Batch Implementation Plan

After the first v1 proof, implementation should move in wider batches rather than repeating the same small slice for each button.
Each batch should include registry updates, page context wiring, service/feed emission, tests, docs, and a focused workflow-findings review.

Workflow findings are part of every batch, but optimization and script-flow cleanup are not automatically part of the batch scope.
Fix findings only when they affect truthful activity attribution, produce misleading rows, or block the covered action.
Otherwise, log them as follow-up findings using the Implementation Findings rules above.

### Batch A: Catalogue Editor Save Paths

Scope:

- catalogue work save
- catalogue work detail save
- catalogue series save
- catalogue moment save

Tasks:

- extend the activity contract registry for the four save actions
- share context-normalization and row-building helpers where the handlers have the same shape
- preserve current on-page save messages
- emit rows for canonical source saves, lookup refreshes, published data rebuilds, search rebuilds, and attempted media/script work where applicable
- skip true no-change saves
- add representative tests for each record family
- run one `/studio/activity/` browser smoke test for the batch
- record workflow findings for save flows, especially modal or confirmation behavior that could affect attribution

Batch A findings:

| Route/control | User action | Observed behavior | Activity-log impact | Handling |
|---|---|---|---|---|
| `/studio/catalogue-work-detail/` `#catalogueWorkDetailSave`; `/studio/catalogue-moment/` `#catalogueMomentSave` | `save work detail`; `save moment` | The first activity-context normalizer was work-id specific and used numeric work-id normalization for every record id. | Would reject valid detail and moment activity contexts before those actions could write unified rows. | `v1-fix`: the normalizer now dispatches by record id field. |
| `/studio/catalogue-moment/` `#catalogueMomentSave` | `save moment` | Moment metadata saves describe moment build invalidation, but the current durable downstream work is published moment data and catalogue search, not Studio catalogue lookup payloads. | A `rebuild lookups` row for moment save would be misleading. | `v1-fix`: the normalizer now excludes `rebuild-lookups`; the response-field naming cleanup is completed in [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups). |
| catalogue save handlers | save work/detail/series/moment | The source-save, lookup-refresh, and scoped-build orchestration is similar across handlers but still spread through separate methods. | Current rows can be correct, but later batches could duplicate mistakes if each action is hand-shaped. | `done`: Batch B0 introduced a thin action-profile layer for the shared UI-action contract and downstream build row mapping. |

### Batch B0: Activity Action Profiles

Status: implemented.

Before adding create, delete, and publication coverage, Batch B0 introduced a small server-side action-profile layer for catalogue-side Studio Activity logging.
The profile records the page id, action id, route, control id, selector, endpoint, record family, record id field, declared script-purpose ids, and published-build step mapping for each covered action.

The profile layer should remain narrow:

- it validates and normalizes activity context
- it keeps runtime action ids aligned with `assets/studio/data/activity_contract.json`
- it supplies common build-row mapping for published-data and search rows
- it does not decide whether source files are written, lookups refresh, builds run, or deletes clean artifacts

Batch B extended these profiles for create/delete/publication actions while keeping action-specific mutation logic in the existing handlers.

### Batch B: Catalogue Create, Delete, And Publication Paths

Status: implemented.

Scope:

- create work/detail/series
- delete work/detail/series/moment
- publish and unpublish work/detail/series/moment

Moment creation is intentionally excluded from this batch. The current moment workflow creates draft moments through the staged import/apply path, not through a normal Save-in-new-mode create action, so it belongs with the import coverage in Batch C.

Readiness prose/media actions also remain in Batch C because their write boundaries are closer to import, report, and utility actions than to catalogue metadata create/delete/publication.

Tasks:

- `done`: preserve initiating action context through publication and delete preview/confirmation flows
- `done`: emit rows for source writes, generated/public artifacts, cleanup, lookup refresh, search update, and local media cleanup
- `done`: extend `assets/studio/data/activity_contract.json` for create work/detail/series, delete work/detail/series/moment, and publish/unpublish work/detail/series/moment
- `done`: keep confirmation buttons as confirmation-only UI while passing the original route/control/action context to the apply endpoints
- `done`: add contract/profile tests for Batch B actions and delete row ordering
- `done`: moment import/create coverage moved to Batch C and was implemented as `import moment`
- `follow-up`: readiness prose/media actions moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups)

Batch B findings:

| Route/control | User action | Observed behavior | Activity-log impact | Handling |
|---|---|---|---|---|
| `/studio/catalogue-moment/` `#catalogueMomentNew` / `#catalogueMomentImportApply` | `create moment` | The page creates new moments from staged body-only Markdown through import preview/apply, not through normal Save-in-new-mode metadata creation. | Treating it like work/detail/series create would give the wrong action boundary and endpoint. | `done`: recorded as `import moment` with import actions in Batch C. |
| publication and delete confirmation modals | publish/unpublish/delete | The durable write happens after a modal confirmation, but the initiating route button remains the meaningful user action. | The confirm button should not become a separate page/action in the activity log. | `done`: frontend sends one activity context through preview/apply request objects; the service normalizes it at apply time. |

### Batch C: Import, Export, Report, Audit, And Utility Actions

Status: implemented.

Scope:

- bulk add import apply
- project-state report
- docs import apply
- Studio data export/import apply actions
- docs broken-links audit
- Studio audits
- tag registry, alias, and assignment write actions

Tasks:

- add action registry coverage for durable writes and generated reports
- exclude preview-only commands unless implementation proves they persist data
- emit summary rows with counts, warnings, output files, and affected record groups
- record findings for any command whose UI wording or persistence boundary is unclear
- keep service-specific result panels in place while adding persistent activity rows

Batch C progress:

- `done`: bulk add workbook import apply now records imported source-data and lookup-refresh rows for the initiating `/studio/bulk-add-work/` Import action.
- `done`: moment staged import apply now records imported source-data rows for the initiating `/studio/catalogue-moment/` Import action.
- `done`: project-state report generation now records a generated-report row for the initiating `/studio/project-state/` Run action.
- `done`: docs import apply, Studio data export/import apply, docs broken-links audit, Studio audits, and tag registry/alias/assignment write actions.

Batch C findings:

| Route/control | User action | Observed behavior | Activity-log impact | Handling |
|---|---|---|---|---|
| `/studio/catalogue-moment/` `#catalogueMomentImportApply` | `import moment` | Moment creation is a staged source import that writes body-only prose and canonical metadata, then opens the draft in the editor. | The truthful row is import-shaped, not create-shaped, and should not imply a normal metadata Save path. | `done`: Batch C records it as `import moment` with `import source data`. |
| `/studio/bulk-add-work/` `#bulkAddWorkApply` | `import workbook records` | Workbook apply can import works or work details depending on the selected mode, and preview-only commands do not persist. | The mode is the meaningful activity target; record ids belong in detail/record groups rather than separate actions. | `done`: Batch C uses one action with mode-specific record groups and duplicate/count detail. |
| `/studio/project-state/` `#projectStateRunButton` | `run project-state report` | The command writes a generated Markdown report rather than catalogue source data. | The row needs a report purpose rather than source-save/import wording. | `done`: Batch C records it as `generate report` with summary counts and the report path. |

### Batch D: Old Report Retirement And Hook Cleanup

Status: implemented.

Scope:

- old split activity report routes
- old split activity feed hooks
- old report navigation

Tasks:

- `done`: remove old pages rather than redirecting them
- `done`: remove old hooks and generated feeds now that covered actions have equivalent unified activity rows
- `done`: keep unrelated local service logs available for debugging

## Documentation Requirements

Implementation should update:

- the V1 implementation task list in this request
- the activity contract registry/config reference
- Studio runtime/page inventory docs
- catalogue write server docs
- scoped catalogue build docs
- docs import docs if docs activity is included in the first slice
- Studio Activity docs to describe the unified-only report surface
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
- confirm old split activity navigation, routes, feed readers, feed files, and emitters are gone

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
