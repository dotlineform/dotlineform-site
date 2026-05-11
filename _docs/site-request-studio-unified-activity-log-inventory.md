---
doc_id: site-request-studio-unified-activity-log-inventory
title: Activity Log Coverage Inventory
added_date: 2026-05-08
last_updated: "2026-05-09 16:00"
ui_status: done
parent_id: site-request-studio-unified-activity-log
sort_order: 10
viewable: true
---
# Activity Log Coverage Inventory

Status:

- completed closeout inventory
- v1 implementation target completed
- Batch A complete
- Batch B complete
- Batch C complete
- Batch D retirement and hook cleanup complete

## Purpose

This document is the completed implementation inventory for [Studio Unified Activity Log Request](/docs/?scope=studio&doc=site-request-studio-unified-activity-log).

Use it to review which Studio pages and user actions now produce structured activity rows, which script purposes appear in the report, and which actions are excluded or retired.
Remaining optional expansion work has moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups).

The inventory should stay close to the visible Studio UI. If a page button changes label, route, id, or behavior, update this inventory and the activity contract registry together.

## Status Values

Use these status values consistently:

| Status | Meaning |
|---|---|
| `follow-up` | Moved out of this closed request and into [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups). |
| `excluded` | Not an activity-log source because it is navigation, read-only filtering, sorting, or local-only form editing. |
| `retired` | Former report surface replaced by `/studio/activity/` and removed from active routes, config, feeds, and hooks. |
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
| Validate activity contract registry | `done` | Implemented in `scripts/checks/verify_activity_contract.py` and `tests/python/test_activity_contract.py`; wired into the quick check profile. |
| Pass activity context from Work editor to catalogue write server | `done` | Single-work saves now send page id, action id, route, control id, selector, and work id; the server validates the context, assigns or normalizes the correlation id, and ignores unknown fields. |
| Emit structured rows from `/catalogue/work/save` | `done` | Single-work saves now write unified activity rows for canonical save, lookup refresh, published work rebuild, and search rebuild when those actions are actually attempted. |
| Generate Studio-readable activity feed | `done` | Implemented `var/studio/activity/activity_log.jsonl` plus capped `var/studio/activity/activity_log.json`; labels hydrate from the activity contract registry. |
| Add `/studio/activity/` route | `done` | Implemented with required columns: date-time, status, page, user action, script purpose. |
| Add status detail modal | `done` | Status buttons open a modal with stacked detail items for the selected row. |
| Keep Work editor save messages unchanged | `done` | The activity log persists the same kind of feedback; it does not replace page feedback. |
| Remove old activity report pages after v1 coverage | `done` | Batch D removed the old split report pages, feeds, read keys, emitters, and dashboard links. |

## Batch Implementation Checklist

| Batch | Status | Scope | Notes |
|---|---|---|---|
| Batch A: catalogue editor save paths | `done` | work save; work-detail save; series save; moment save | Single-record metadata saves now emit unified activity rows. Moment save intentionally excludes lookup rows because it does not currently write Studio lookup payloads. |
| Batch B0: activity action profiles | `done` | shared profile layer for covered activity actions | Keeps runtime page/action/control/endpoint/record-family ids aligned with the structured registry before adding more action types. The profile does not own mutation behavior. |
| Batch B: catalogue create/delete/publication paths | `done` | create work/detail/series; delete work/detail/series/moment; publish/unpublish work/detail/series/moment | Preserves initiating context through preview/confirmation flows. Moment import/create and readiness prose/media writes move to Batch C because their write boundaries are import/utility-shaped rather than normal create/delete/publication metadata actions. |
| Batch C: import/export/report/audit/utility actions | `done` | bulk add apply, project-state, docs import, data export/import, audits, tag writes | Covered workbook import apply, moment import apply, project-state report generation, docs source import, data export/import apply, docs broken-links audit, Studio audits, series tag saves/imports, registry writes, and alias writes. Preview-only commands remain excluded unless they persist data. |
| Batch D: old report retirement and hook cleanup | `done` | old activity routes, feeds, hooks, navigation | Removed the old split report pages rather than redirecting them, and removed their feed files, read keys, writer modules, emitters, dashboard links, and config entries. |

## Catalogue Pages

| Page | Route | Button/control | User action label | Expected script coverage | Status | Notes |
|---|---|---|---|---|---|---|
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkSave` `Save` | `save work` | save canonical work record; rebuild published work data when applicable; rebuild catalogue lookups; update catalogue search | `done` | First implementation proves correlation for one button click and multiple downstream rows. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkSave` in new mode | `create work` | create draft canonical work record; refresh lookups | `done` | Batch B coverage. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkSave` in bulk mode | `bulk save works` | save multiple canonical work records; rebuild affected published output; refresh lookups; update search | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups); needs grouped record counts and clear modal summaries. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkPublication` `Publish` or `Unpublish` | `publish work` / `unpublish work` | publication preview; status change in canonical work record; public artifact build or cleanup; lookup refresh; search update | `done` | Batch B coverage. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkDelete` `Delete` | `delete work` | delete preview; delete canonical work record; delete dependent detail records when applicable; clean public artifacts; refresh lookups; update search; local media cleanup when applicable | `done` | Batch B coverage. |
| Catalogue work editor | `/studio/catalogue-work/` | `data-action="preview-build-impact"` `Preview update` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Catalogue work editor | `/studio/catalogue-work/` | readiness action `data-prose-import="work"` | `import work prose` | prose import preview; prose source write; backup when overwriting | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups). |
| Catalogue work editor | `/studio/catalogue-work/` | readiness action `data-media-refresh="work"` | `refresh work media` | media-only build; source media checks; local derivative refresh; public thumbnail staging | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups); should distinguish blocked media from successful derivative refresh. |
| Catalogue work editor | `/studio/catalogue-work/` | `#catalogueWorkOpen`, `#catalogueWorkNew`, file/link row buttons, series picker buttons | none | none | `excluded` | These are navigation, form-mode changes, or unsaved local form edits unless followed by Save. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailSave` `Save` | `save work detail` | save canonical detail record; rebuild parent work output when applicable; refresh lookups; update search | `done` | Mirrors work save, but public output is parent-work scoped. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailSave` in new mode | `create work detail` | create draft canonical detail record; refresh lookups | `done` | Batch B coverage. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailSave` in bulk mode | `bulk save work details` | save multiple canonical detail records; rebuild parent work output for affected published details; refresh lookups; update search | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups); needs parent-work grouping. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailPublication` | `publish work detail` / `unpublish work detail` | publication preview; status change; parent work output build or cleanup; lookup refresh; search update | `done` | Batch B coverage. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailDelete` | `delete work detail` | delete preview; delete canonical detail; clean detail artifacts; rebuild parent work output; refresh lookups; update search; local media cleanup when applicable | `done` | Batch B coverage. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | readiness action `data-media-refresh="detail"` | `refresh detail media` | media-only build; detail derivative refresh; public thumbnail staging | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups); should report blocked media distinctly. |
| Catalogue work detail editor | `/studio/catalogue-work-detail/` | `#catalogueWorkDetailOpen` | none | none | `excluded` | Record navigation only. |
| Catalogue series editor | `/studio/catalogue-series/` | `#catalogueSeriesSave` `Save` | `save series` | save canonical series record; save affected work membership records; rebuild published series/work output; refresh lookups; update search | `done` | Membership edits are local until Save. |
| Catalogue series editor | `/studio/catalogue-series/` | `#catalogueSeriesSave` in new mode | `create series` | create draft canonical series record; refresh lookups | `done` | Batch B coverage. |
| Catalogue series editor | `/studio/catalogue-series/` | `#catalogueSeriesPublication` | `publish series` / `unpublish series` | publication preview; status change; attached draft work status changes when applicable; public artifact build or cleanup; lookup refresh; search update | `done` | Batch B coverage. |
| Catalogue series editor | `/studio/catalogue-series/` | `#catalogueSeriesDelete` | `delete series` | delete preview; delete canonical series; update affected work membership; clean public series artifacts; refresh lookups; update search | `done` | Batch B coverage. |
| Catalogue series editor | `/studio/catalogue-series/` | readiness action `data-prose-import="series"` | `import series prose` | prose import preview; prose source write; backup when overwriting | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups). |
| Catalogue series editor | `/studio/catalogue-series/` | member add/remove/primary buttons | none | none | `excluded` | Local form edits until series Save. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentSave` `Save` | `save moment` | save canonical moment record; rebuild public moment when applicable; update search | `done` | Moment saves do not currently write Studio catalogue lookup payloads, so Batch A does not emit a lookup row for this action. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentNew` then `#catalogueMomentSave` | `create moment` | create canonical moment record through import/apply path | `done` | Implemented as `import moment`; current creation is staged import, not Save-in-new-mode metadata creation. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentPublication` | `publish moment` / `unpublish moment` | publication preview; status change; public moment build or cleanup; search update | `done` | Batch B coverage. Moment publication does not currently write Studio catalogue lookup payloads. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentDelete` | `delete moment` | delete preview; delete canonical moment; clean public artifacts; update search; local media cleanup when applicable | `done` | Batch B coverage. Moment delete does not currently write Studio catalogue lookup payloads. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentImportPreview` `Preview` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Catalogue moment editor | `/studio/catalogue-moment/` | `#catalogueMomentImportApply` `Import` | `import moment` | staged moment import apply; canonical moment metadata write; body-only prose source write | `done` | The compatibility route redirects here, so coverage belongs to the editor page. |
| Catalogue moment editor | `/studio/catalogue-moment/` | readiness prose/media actions | `import moment prose` / `refresh moment media` | prose source write or media-only build; backup or blocked-media detail as applicable | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups); keep separate from metadata Save. |
| Bulk add work | `/studio/bulk-add-work/` | `#bulkAddWorkPreview` `Preview` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Bulk add work | `/studio/bulk-add-work/` | `#bulkAddWorkApply` `Import` | `import workbook records` | create new canonical work or work-detail records; backup; refresh lookups | `done` | Active one-way import adapter from the configured workbook. |
| Project state | `/studio/project-state/` | `#projectStateRunButton` `Run` | `run project-state report` | scan project folders; write project-state report | `done` | Local report generation records one report row with counts and the output path. |
| Project state | `/studio/project-state/` | `#projectStateOpenButton` `Open file` | none | none | `excluded` | Opens documentation/source context; not a report-generating action. |
| Catalogue status | `/studio/catalogue-status/` | filters/sort/open links | none | none | `excluded` | Review surface only. |
| Studio works | `/studio/studio-works/` | sort/copy/filter controls | none | none | `excluded` | Review/navigation surface only. |
| Retired split activity reports | removed | report pages | none | none | `retired` | Former source-side and build-side report surfaces were removed; `/studio/activity/` is the only active activity report. |

## Docs And Library Pages

| Page | Route | Button/control | User action label | Expected script coverage | Status | Notes |
|---|---|---|---|---|---|---|
| Docs import | `/docs/?mode=manage&import=1` | `#docsHtmlImportRun` | `import docs source` | staged source conversion; validation; source doc write; backup; media source registration when applicable | `done` | Batch C coverage. Preview/replacement-required states stay excluded until the import writes source files. |
| Docs import | `/docs/?mode=manage&import=1` | `#docsHtmlImportConfirm` | none | none | `excluded` | Confirmation should preserve the original `import docs source` context rather than creating a separate action row. |
| Docs import | `/docs/?mode=manage&import=1` | result source link | none | none | `excluded` | Opening the source file is not activity-report scope for v1. |
| Studio data export | `/studio/export/` | `#dataExportRun` | `export data` | docs export generation; selected records; output file/report; warnings or skipped records | `done` | Batch C coverage for output-writing exports. |
| Studio data import | `/studio/import/` | `#dataImportPreview` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Studio data import | `/studio/import/` | `#dataImportUpdateSummary` | `update import summaries` | import apply preflight; source doc backups; summary field writes; result counts | `done` | Batch C coverage for confirmed apply writes; preflight remains excluded. |
| Studio data import | `/studio/import/` | `#dataImportApplyHierarchy` | `update import hierarchy` | import apply preflight; source doc backups; parent-id writes; result counts | `done` | Batch C coverage for confirmed apply writes; preflight remains excluded. |
| Docs broken links | `/studio/docs-broken-links/` | `#docsBrokenLinksRun` | `run broken-links audit` | broken-link scan; generated result list | `done` | Batch C report coverage. |
| Library documents | `/studio/library-documents/` | sort/filter/open controls | none | none | `excluded` | Review surface only. |

## Tag Pages

| Page | Route | Button/control | User action label | Expected script coverage | Status | Notes |
|---|---|---|---|---|---|---|
| Series tags | `/studio/analytics/series-tags/` | import modal `preview-import` | none | none | `excluded` | Preview-only commands should not be reported unless implementation finds they persist data. |
| Series tags | `/studio/analytics/series-tags/` | import modal `apply-import` | `import series tag assignments` | tag assignment import apply; tag assignment writes; backup; conflict resolution summary | `done` | Batch C coverage through the tag write service. |
| Series tags | `/studio/analytics/series-tags/` | session modal copy/download/clear | none | none | `excluded` | Browser/session-local output controls unless a later follow-up persists them by service. |
| Series tag editor | `/studio/analytics/series-tag-editor/` | `data-role="add-tag"` | none | none | `excluded` | Local assignment edit until Save. |
| Series tag editor | `/studio/analytics/series-tag-editor/` | `data-role="save"` | `save series tags` | save tag assignments; backup; generated tag assignment data update | `done` | Batch C coverage through the shared tag save flow. |
| Tag registry | `/studio/analytics/tag-registry/` | `data-role="open-import-modal"` then import action | `import tag registry` | registry import preview/apply; registry writes; backups; validation results | `done` | Batch C coverage for import apply; patch-mode output remains excluded. |
| Tag registry | `/studio/analytics/tag-registry/` | `data-role="open-new-tag"` / row edit actions | `create tag` / `edit tag` | mutate tag preview/apply; registry writes; backups; validation results | `done` | Batch C coverage; affected tag ids are carried in activity details/groups. |
| Tag registry | `/studio/analytics/tag-registry/` | demote/delete-like actions | `demote tag` / `delete tag` | demote/delete apply; registry updates; assignment or alias consequences | `done` | Batch C coverage for confirmed write actions. |
| Tag aliases | `/studio/analytics/tag-aliases/` | `data-role="open-import-modal"` then import action | `import tag aliases` | alias import preview/apply; alias writes; backups; validation results | `done` | Batch C coverage through the tag write service. |
| Tag aliases | `/studio/analytics/tag-aliases/` | `data-role="open-new-alias"` / row edit actions | `create tag alias` / `edit tag alias` | alias mutation; alias writes; backups | `done` | Batch C coverage; affected alias keys are carried in activity details/groups. |
| Tag aliases | `/studio/analytics/tag-aliases/` | promote/demote/delete actions | `promote tag alias` / `delete tag alias` / `demote tag` | preview/apply where applicable; alias registry writes; tag registry effects when promoting or demoting | `done` | Batch C coverage for confirmed write actions. |
| Tag groups | `/studio/analytics/tag-groups/` | filters/sort/open controls | none | none | `excluded` | Review surface; future writable behavior belongs in [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups). |

## Audit And Utility Pages

| Page | Route | Button/control | User action label | Expected script coverage | Status | Notes |
|---|---|---|---|---|---|---|
| Studio audits | `/studio/audits/` | `data-run-audit="<audit_id>"` | `run studio audit` | audit service run; pass/warn/fail result; report path or summary | `done` | Batch C coverage; details include audit label, status, error/warning counts, and duration. |
| Catalogue field registry | `/studio/catalogue-field-registry/` | review controls | none | none | `excluded` | Review/config surface; future writable behavior belongs in [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups). |
| Studio dashboards | `/studio/`, `/studio/catalogue/`, `/studio/library/`, `/studio/analytics/` | dashboard links and hydration | none | none | `excluded` | Navigation and read-only metric hydration should not appear in the activity log. |
| Docs Viewer | `/docs/` | view/search/navigation controls | none | none | `excluded` | Not a Studio write/build action. |

## Background And Future Sources

| Source | Trigger | Expected script coverage | Status | Notes |
|---|---|---|---|---|
| Docs live rebuild watcher | source file changes after user editing | docs rebuild; docs search rebuild; generated payload changes | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups); only useful with meaningful source context. |
| Jekyll/site serve watchers | local filesystem changes | site rebuild | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups); only useful if correlated to a Studio action or explicit user command. |
| Manual terminal scripts | direct shell command | script-specific report rows | `follow-up` | Moved to [Studio Activity Follow-Ups](/docs/?scope=studio&doc=site-request-studio-activity-follow-ups); would need explicit run context and sanitization. |

## Verification Matrix

| Scope | Codex-run checks | Manual checks |
|---|---|---|
| V1 catalogue editor saves | registry validation; structured event unit tests; save endpoint tests producing correlated rows; activity feed generation test | Save metadata edits for one existing work, detail, series, and moment; confirm `/studio/activity/` shows the expected page/action labels and downstream script-purpose rows. |
| Activity report UI | route-ready audit; modal rendering smoke test; feed read error-state check | Open `/studio/activity/`, click status markers, and confirm stacked details are readable. |
| Inventory completeness | scan Studio route files and service endpoints for unclassified buttons before each implementation slice | Compare the inventory against visible Studio pages during a light manual pass. |
| Old report transition | route/link/feed scan after cleanup | Confirm no retired split activity routes, read keys, feed files, emitters, or dashboard links remain. |
| Implementation findings | findings logged with route, control id, observed behavior, expected behavior, activity-log impact, and status | Confirm non-blocking issues are captured as follow-ups rather than folded into the v1 implementation by default. |
