---
doc_id: site-request-studio-unified-activity-log-inventory
title: Activity Log Coverage Inventory
added_date: 2026-05-08
last_updated: "2026-05-08 18:20"
ui_status: in-progress
parent_id: site-request-studio-unified-activity-log
sort_order: 10
viewable: true
---
# Activity Log Coverage Inventory

Status:

- initial v1 planning inventory
- v1 implementation target selected
- Batch C catalogue-service slice in progress
- broader docs/tag/audit surface area not yet implemented

## Purpose

This document is the implementation inventory for [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log).

Use it to track which Studio pages and user actions should eventually produce structured activity rows, which script purposes should appear in the report, and which actions have been implemented.

The inventory should stay close to the visible Studio UI. If a page button changes label, route, id, or behavior, update this inventory and the activity contract registry together.

## Status Values

Use these status values consistently:

| Status | Meaning |
|---|---|
| `v1-target` | In scope for the first implementation slice. |
| `in-progress` | Partially implemented across the current batch. |
| `planned` | Should be covered after v1 proves the contract. |
| `future` | Worth supporting later, but not needed for the initial catalogue activity report. |
| `excluded` | Not an activity-log source because it is navigation, read-only filtering, sorting, or local-only form editing. |
| `retire` | Existing report surface that should be replaced by `/studio/activity/` after the unified page is trusted. |
| `done` | Implemented for the current slice. |

## Coverage Rules

Record actions that initiate a script, local service call, file write, build, import, export, audit, or generated report.
Preview-only commands are excluded when they do not persist data.
Confirmation controls are not separate activity actions; they should preserve the original command context.

Do not record routine UI-only actions:

- opening a record for editing
- filtering, sorting, expanding, or selecting list rows
- adding/removing unsaved form rows before a save
- opening result modals without running a new action
- copying or downloading browser-local session data unless it represents a persisted Studio operation

Each covered action should map to one user-action label and one or more script-purpose labels.
The user-action label describes the button click from the page perspective.
The script-purpose label describes each downstream operation recorded as its own row.

## V1 Implementation Checklist

| Item | Status | Notes |
|---|---|---|
| Define `catalogue-work` page entry in the activity contract registry | `done` | Implemented in `assets/studio/data/activity_contract.json`; page label: `catalogue work editor`; route: `/studio/catalogue-work/`. |
| Define `save-work` action for `#catalogueWorkSave` | `done` | Implemented in `assets/studio/data/activity_contract.json`; user action label: `save work`; scenario: metadata edits to one existing work. |
| Define script purposes for the v1 save path | `done` | Implemented script purposes: `save canonical data`, `rebuild published work data`, `rebuild lookups`, `update search`. |
| Validate activity contract registry | `done` | Implemented in `scripts/verify_activity_contract.py` and `tests/python/test_activity_contract.py`; wired into the quick check profile. |
| Pass activity context from Work editor to catalogue write server | `done` | Single-work saves now send page id, action id, route, control id, selector, and work id; the server validates the context, assigns or normalizes the correlation id, and ignores unknown fields. |
| Emit structured rows from `/catalogue/work/save` | `done` | Single-work saves now write unified activity rows for canonical save, lookup refresh, published work rebuild, and search rebuild when those actions are actually attempted. |
| Generate Studio-readable activity feed | `done` | Implemented `var/studio/activity/activity_log.jsonl` plus capped `assets/studio/data/activity_log.json`; labels hydrate from the activity contract registry. |
| Add `/studio/activity/` route | `done` | Implemented with required columns: date-time, status, page, user action, script purpose. |
| Add status detail modal | `done` | Status buttons open a modal with stacked detail items for the selected row. |
| Keep Work editor save messages unchanged | `v1-target` | The activity log persists the same kind of feedback; it does not replace page feedback. |
| Keep old activity report pages during v1 | `v1-target` | Defer redirect/removal until the new report is trusted. |

## Batch Implementation Checklist

| Batch | Status | Scope | Notes |
|---|---|---|---|
| Batch A: catalogue editor save paths | `done` | work save; work-detail save; series save; moment save | Single-record metadata saves now emit unified activity rows. Bulk/create/delete/publication paths stay in later batches. Moment save intentionally excludes lookup rows because it does not currently write Studio lookup payloads. |
| Batch B0: activity action profiles | `done` | shared profile layer for covered activity actions | Keeps runtime page/action/control/endpoint/record-family ids aligned with the structured registry before adding more action types. The profile does not own mutation behavior. |
| Batch B: catalogue create/delete/publication paths | `done` | create work/detail/series; delete work/detail/series/moment; publish/unpublish work/detail/series/moment | Preserves initiating context through preview/confirmation flows. Moment import/create and readiness prose/media writes move to Batch C because their write boundaries are import/utility-shaped rather than normal create/delete/publication metadata actions. |
| Batch C: import/export/report/audit/utility actions | `in-progress` | bulk add apply, project-state, docs import, data export/import, audits, tag writes | First catalogue-service slice covers workbook import apply, moment import apply, and project-state report generation. Keep preview-only commands excluded unless they persist data. |
| Batch D: old report retirement and hook cleanup | `planned` | old activity routes, feeds, hooks, navigation | Keep old pages visible while old hooks remain live; remove or redirect only after unified rows cover equivalent activity. |

## Catalogue Pages

| Page | Route | Button/control | User action label | Expected script coverage | Status | Notes |
|---|---|---|---|---|---|---|
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkSave` `Save` | `save work` | save canonical work record; rebuild published work data when applicable; rebuild catalogue lookups; update catalogue search | `done` | First implementation proves correlation for one button click and multiple downstream rows. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkSave` in new mode | `create work` | create draft canonical work record; refresh lookups | `done` | Batch B coverage. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkSave` in bulk mode | `bulk save works` | save multiple canonical work records; rebuild affected published output; refresh lookups; update search | `planned` | Needs grouped record counts and clear modal summaries. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkPublication` `Publish` or `Unpublish` | `publish work` / `unpublish work` | publication preview; status change in canonical work record; public artifact build or cleanup; lookup refresh; search update | `done` | Batch B coverage. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkDelete` `Delete` | `delete work` | delete preview; delete canonical work record; delete dependent detail records when applicable; clean public artifacts; refresh lookups; update search; local media cleanup when applicable | `done` | Batch B coverage. |
| Catalogue work editor | `/studio/catalogue-work/` | `data-action="preview-build-impact"` `Preview update` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Catalogue work editor | `/studio/catalogue-work/` | readiness action `data-prose-import="work"` | `import work prose` | prose import preview; prose source write; backup when overwriting | `planned` | Existing on-page result gives strong detail text for the modal. |
| Catalogue work editor | `/studio/catalogue-work/` | readiness action `data-media-refresh="work"` | `refresh work media` | media-only build; source media checks; local derivative refresh; public thumbnail staging | `planned` | Should distinguish blocked media from successful derivative refresh. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkOpen`, `#catalogueWorkNew`, file/link row buttons, series picker buttons | none | none | `excluded` | These are navigation, form-mode changes, or unsaved local form edits unless followed by Save. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailSave` `Save` | `save work detail` | save canonical detail record; rebuild parent work output when applicable; refresh lookups; update search | `done` | Mirrors work save, but public output is parent-work scoped. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailSave` in new mode | `create work detail` | create draft canonical detail record; refresh lookups | `done` | Batch B coverage. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailSave` in bulk mode | `bulk save work details` | save multiple canonical detail records; rebuild parent work output for affected published details; refresh lookups; update search | `planned` | Needs parent-work grouping. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailPublication` | `publish work detail` / `unpublish work detail` | publication preview; status change; parent work output build or cleanup; lookup refresh; search update | `done` | Batch B coverage. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailDelete` | `delete work detail` | delete preview; delete canonical detail; clean detail artifacts; rebuild parent work output; refresh lookups; update search; local media cleanup when applicable | `done` | Batch B coverage. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | readiness action `data-media-refresh="detail"` | `refresh detail media` | media-only build; detail derivative refresh; public thumbnail staging | `planned` | Should report blocked media distinctly. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailOpen` | none | none | `excluded` | Record navigation only. |
| Catalogue series editor | `/studio/catalogue-series/` | `#catalogueSeriesSave` `Save` | `save series` | save canonical series record; save affected work membership records; rebuild published series/work output; refresh lookups; update search | `done` | Membership edits are local until Save. |
| Catalogue series editor | `/studio/catalogue-series/` | `#catalogueSeriesSave` in new mode | `create series` | create draft canonical series record; refresh lookups | `done` | Batch B coverage. |
| Catalogue series editor | `/studio/catalogue-series/` | `#catalogueSeriesPublication` | `publish series` / `unpublish series` | publication preview; status change; attached draft work status changes when applicable; public artifact build or cleanup; lookup refresh; search update | `done` | Batch B coverage. |
| Catalogue series editor | `/studio/catalogue-series/` | `#catalogueSeriesDelete` | `delete series` | delete preview; delete canonical series; update affected work membership; clean public series artifacts; refresh lookups; update search | `done` | Batch B coverage. |
| Catalogue series editor | `/studio/catalogue-series/` | readiness action `data-prose-import="series"` | `import series prose` | prose import preview; prose source write; backup when overwriting | `planned` | Similar to work prose import. |
| Catalogue series editor | `/studio/catalogue-series/` | member add/remove/primary buttons | none | none | `excluded` | Local form edits until series Save. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentSave` `Save` | `save moment` | save canonical moment record; rebuild public moment when applicable; update search | `done` | Moment saves do not currently write Studio catalogue lookup payloads, so Batch A does not emit a lookup row for this action. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentNew` then `#catalogueMomentSave` | `create moment` | create canonical moment record through import/apply path | `done` | Implemented as `import moment`; current creation is staged import, not Save-in-new-mode metadata creation. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentPublication` | `publish moment` / `unpublish moment` | publication preview; status change; public moment build or cleanup; search update | `done` | Batch B coverage. Moment publication does not currently write Studio catalogue lookup payloads. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentDelete` | `delete moment` | delete preview; delete canonical moment; clean public artifacts; update search; local media cleanup when applicable | `done` | Batch B coverage. Moment delete does not currently write Studio catalogue lookup payloads. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentImportPreview` `Preview` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentImportApply` `Import` | `import moment` | staged moment import apply; canonical moment metadata write; body-only prose source write | `done` | The compatibility route redirects here, so coverage belongs to the editor page. |
| Catalogue moment editor | `/studio/catalogue-moment/` | readiness prose/media actions | `import moment prose` / `refresh moment media` | prose source write or media-only build; backup or blocked-media detail as applicable | `planned` | Keep separate from metadata Save. |
| Bulk add work | `/studio/bulk-add-work/` | `#bulkAddWorkPreview` `Preview` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Bulk add work | `/studio/bulk-add-work/` | `#bulkAddWorkApply` `Import` | `import workbook records` | create new canonical work or work-detail records; backup; refresh lookups | `done` | Active one-way import adapter from the configured workbook. |
| Project state | `/studio/project-state/` | `#projectStateRunButton` `Run` | `run project-state report` | scan project folders; write project-state report | `done` | Local report generation records one report row with counts and the output path. |
| Project state | `/studio/project-state/` | `#projectStateOpenButton` `Open file` | none | none | `excluded` | Opens documentation/source context; not a report-generating action. |
| Catalogue status | `/studio/catalogue-status/` | filters/sort/open links | none | none | `excluded` | Review surface only. |
| Studio works | `/studio/studio-works/` | sort/copy/filter controls | none | none | `excluded` | Review/navigation surface only. |
| Catalogue activity | `/studio/catalogue-activity/` | report page | none | none | `retire` | Replaced as a primary report surface by `/studio/activity/`. |
| Build activity | `/studio/build-activity/` | report page | none | none | `retire` | Replaced as a primary report surface by `/studio/activity/`. |

## Docs And Library Pages

| Page | Route | Button/control | User action label | Expected script coverage | Status | Notes |
|---|---|---|---|---|---|---|
| Docs import | `/studio/docs-import/` | `#docsHtmlImportRun` | `import docs source` | staged source conversion; validation; source doc write; backup; media source registration when applicable | `planned` | Current result panel is a strong source for activity detail text. |
| Docs import | `/studio/docs-import/` | `#docsHtmlImportConfirm` | none | none | `excluded` | Confirmation should preserve the original `import docs source` context rather than creating a separate action row. |
| Docs import | `/studio/docs-import/` | result source link | none | none | `excluded` | Opening the source file is not activity-report scope for v1. |
| Studio data export | `/studio/export/` | `#dataExportRun` | `export data` | docs export generation; selected records; output file/report; warnings or skipped records | `planned` | Covers library, analytics, and other configured export scopes. |
| Studio data import | `/studio/import/` | `#dataImportPreview` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Studio data import | `/studio/import/` | `#dataImportUpdateSummary` | `update import summaries` | import apply preflight; source doc backups; summary field writes; result counts | `planned` | Confirmation modal activity should share this original command context. |
| Studio data import | `/studio/import/` | `#dataImportApplyHierarchy` | `update import hierarchy` | import apply preflight; source doc backups; parent-id writes; result counts | `planned` | Confirmation modal activity should share this original command context. |
| Docs broken links | `/studio/docs-broken-links/` | `#docsBrokenLinksRun` | `run broken-links audit` | broken-link scan; generated result list | `planned` | Audit/report action, not a source write. |
| Library documents | `/studio/library-documents/` | sort/filter/open controls | none | none | `excluded` | Review surface only. |

## Tag Pages

| Page | Route | Button/control | User action label | Expected script coverage | Status | Notes |
|---|---|---|---|---|---|---|
| Series tags | `/studio/series-tags/` | import modal `preview-import` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Series tags | `/studio/series-tags/` | import modal `apply-import` | `import series tag assignments` | tag assignment import apply; tag assignment writes; backup; conflict resolution summary | `planned` | Uses tag write service. |
| Series tags | `/studio/series-tags/` | session modal copy/download/clear | none | none | `excluded` | Browser/session-local output controls unless later persisted by service. |
| Series tag editor | `/studio/series-tag-editor/` | `data-role="add-tag"` | none | none | `excluded` | Local assignment edit until Save. |
| Series tag editor | `/studio/series-tag-editor/` | `data-role="save"` | `save series tags` | save tag assignments; backup; generated tag assignment data update | `planned` | Uses shared tag save flow. |
| Tag registry | `/studio/tag-registry/` | `data-role="open-import-modal"` then import action | `import tag registry` | registry import preview/apply; registry writes; backups; validation results | `planned` | Split preview/apply in implementation if the UI exposes both as distinct commands. |
| Tag registry | `/studio/tag-registry/` | `data-role="open-new-tag"` / row edit actions | `create tag` / `edit tag` | mutate tag preview/apply; registry writes; backups; validation results | `planned` | Registry mutation should report affected tag ids. |
| Tag registry | `/studio/tag-registry/` | demote/delete-like actions | `demote tag` | demote preview/apply; registry updates; assignment or alias consequences | `planned` | Label should match current UI text once captured in registry. |
| Tag aliases | `/studio/tag-aliases/` | `data-role="open-import-modal"` then import action | `import tag aliases` | alias import preview/apply; alias writes; backups; validation results | `planned` | Uses tag write service. |
| Tag aliases | `/studio/tag-aliases/` | `data-role="open-new-alias"` / row edit actions | `create tag alias` / `edit tag alias` | alias mutation; alias writes; backups | `planned` | Report alias key and target tag. |
| Tag aliases | `/studio/tag-aliases/` | promote/demote/delete actions | `promote tag alias` / `delete tag alias` | preview/apply where applicable; alias registry writes; tag registry effects when promoting | `planned` | Preserve current confirmation/result wording in modal details. |
| Tag groups | `/studio/tag-groups/` | filters/sort/open controls | none | none | `excluded` | Review surface unless future group editing is added. |

## Audit And Utility Pages

| Page | Route | Button/control | User action label | Expected script coverage | Status | Notes |
|---|---|---|---|---|---|---|
| Studio audits | `/studio/audits/` | `data-run-audit="<audit_id>"` | `run studio audit` | audit service run; pass/warn/fail result; report path or summary | `planned` | The row should include the specific audit label in details. |
| Catalogue field registry | `/studio/catalogue-field-registry/` | review controls | none | none | `excluded` | Review/config surface unless a future write action is added. |
| Studio dashboards | `/studio/`, `/studio/catalogue/`, `/studio/library/`, `/studio/analytics/`, `/studio/search/` | dashboard links and hydration | none | none | `excluded` | Navigation and read-only metric hydration should not appear in the activity log. |
| Docs Viewer | `/docs/` | view/search/navigation controls | none | none | `excluded` | Not a Studio write/build action. |

## Background And Future Sources

| Source | Trigger | Expected script coverage | Status | Notes |
|---|---|---|---|---|
| Docs live rebuild watcher | source file changes after user editing | docs rebuild; docs search rebuild; generated payload changes | `future` | Excluded from the initial report unless it can carry meaningful source context. It is still responding to user actions, so it should be considered later. |
| Jekyll/site serve watchers | local filesystem changes | site rebuild | `future` | Only useful if correlated to a Studio action or explicit user command. |
| Manual terminal scripts | direct shell command | script-specific report rows | `future` | Could be supported later with explicit run context, but v1 is page-button initiated. |

## Verification Matrix

| Scope | Codex-run checks | Manual checks |
|---|---|---|
| V1 catalogue editor saves | registry validation; structured event unit tests; save endpoint tests producing correlated rows; activity feed generation test | Save metadata edits for one existing work, detail, series, and moment; confirm `/studio/activity/` shows the expected page/action labels and downstream script-purpose rows. |
| Activity report UI | route-ready audit; modal rendering smoke test; feed read error-state check | Open `/studio/activity/`, click status markers, and confirm stacked details are readable. |
| Inventory completeness | scan Studio route files and service endpoints for unclassified buttons before each implementation slice | Compare the inventory against visible Studio pages during a light manual pass. |
| Old report transition | link/navigation check once the new route is stable | Confirm old Build Activity and Catalogue Activity routes no longer compete with the unified report. |
| Implementation findings | findings logged with route, control id, observed behavior, expected behavior, activity-log impact, and status | Confirm non-blocking issues are captured as follow-ups rather than folded into the v1 implementation by default. |
