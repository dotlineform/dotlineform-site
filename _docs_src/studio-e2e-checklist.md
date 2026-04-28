---
doc_id: new-pipeline-studio-e2e-checklist
title: "Studio E2E Checklist"
added_date: 2026-04-19
last_updated: 2026-04-19
parent_id: new-pipeline
sort_order: 60
---

# Studio End-To-End Checklist

This document is the execution surface for the first end-to-end testing pass across the Studio workflow.

It is not a results log. Record pass/fail notes and follow-up issues outside this document.

## Purpose

Use this checklist to:

- verify that the implemented Studio routes are usable as a day-to-day admin workflow
- verify that canonical source writes, scoped rebuilds, and public/runtime follow-through remain aligned
- separate browser-led checks from Codex-runnable verification so execution is predictable

## Prerequisites

Complete these before running the checklist:

- start the local Studio stack with `bin/dev-studio`
- confirm the site is available at `http://127.0.0.1:4000/`
- confirm the local catalogue write server is available on `http://127.0.0.1:8788/`
- confirm `DOTLINEFORM_PROJECTS_BASE_DIR` points to the current source tree used for prose, work media, and moments
- confirm `DOTLINEFORM_MEDIA_BASE_DIR` is set if media-generation behavior is being checked
- confirm `assets/studio/data/catalogue/` is present and current
- confirm `data/works_bulk_import.xlsx` is present if bulk import is in scope for the run
- confirm at least one representative source case exists for each required state:
  - published work
  - draft work
  - work with details
  - work with file and link records
  - series with `primary_work_id`
  - moment source markdown file
  - prose-ready work or series
  - missing-file or missing-metadata readiness case

## Execution Split

Manual browser testing:

- route shell, nav, dashboard signposting, and page-to-page flow
- form interaction, search/open flows, create/save/delete confirmations, and bulk-edit behavior
- current-record previews, readiness panels, activity/build visibility, and responsive layout
- public-site verification after source changes and rebuilds

Codex-run verification:

- local service health
- docs rebuild
- Jekyll build
- syntax checks for changed JS/Python where relevant
- direct scoped preview/apply commands where browser interaction is not required
- lightweight artifact/runtime spot checks when faster than repeating a browser action

## Recording Conventions

For each scenario, record outside this document:

- `pass`
- `fail`
- blocking error text if present
- whether the issue is reproducible
- the follow-up bucket:
  - `source/config issue`
  - `UI issue`
  - `write-service issue`
  - `generator/build issue`
  - `docs/signposting issue`

## Checklist Order

Run the scenarios in this order.

## 1. Studio Shell And Navigation

Route:

- `/studio/`

Owner:

- manual

Checks:

- open `/studio/` from the footer `studio` link
- confirm the Studio header nav shows `Catalogue`, `Library`, `Analytics`, `Search`, and `Docs`
- confirm the public header nav is not shown on Studio routes
- confirm the site title returns to the public site
- confirm `/studio/` shows only the four domain panels
- open each domain dashboard once from the landing page

Expected results:

- Studio entry and exit boundary is clear
- the four dashboards are reachable without docs
- no unexpected crossover links appear between public and Studio nav models

## 2. Docs Surface

Route:

- `/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan`

Owner:

- manual plus Codex for rebuild command if needed

Checks:

- open a Studio-scoped docs page
- confirm the Studio header nav is present on docs
- confirm the docs rebuild button appears beside the docs search input
- trigger docs rebuild once if a rebuild check is part of the run

Expected results:

- docs remain inside the Studio shell
- the rebuild action is visible and completes without leaving the docs context

## 3. Catalogue Dashboard Routing

Route:

- `/studio/catalogue/`

Owner:

- manual

Checks:

- confirm the dashboard signposts create, edit, review, maintenance, and guidance flows
- open each linked Catalogue route at least once:
  - `/studio/catalogue-new-series/`
  - `/studio/catalogue-new-work-detail/`
  - `/studio/catalogue-moment-import/`
  - `/studio/catalogue-work/`
  - `/studio/catalogue-series/`
  - `/studio/catalogue-work-detail/`
  - `/studio/catalogue-status/`
  - `/studio/catalogue-status/?view=draft-works`
  - `/studio/catalogue-activity/`
  - `/studio/build-activity/`
  - `/studio/bulk-add-work/`

Expected results:

- every current Catalogue workflow surface is reachable from the dashboard
- no route feels like a dead end or hidden tool

## 4. Work Create, Edit, Save, And Rebuild

Route:

- `/studio/catalogue-work/?mode=new`
- `/studio/catalogue-work/?work=<work_id>`

Owner:

- manual plus Codex for any direct rebuild verification if needed

Checks:

- create one draft work record
- confirm `/studio/catalogue-new-work/` redirects to `/studio/catalogue-work/?mode=new`
- open the new or selected work in `/studio/catalogue-work/`
- edit several scalar metadata fields and save source only
- confirm rebuild-needed state appears after save
- run `Save + Rebuild`
- open the public work page after rebuild

Expected results:

- source save succeeds without leaving the editor unexpectedly
- scoped rebuild completes and updates Build Activity
- the public work page reflects the expected runtime state after rebuild

## 5. Work Bulk Edit

Route:

- `/studio/catalogue-work/`

Owner:

- manual

Checks:

- enter a bulk selection using explicit ids and/or ranges
- confirm the page enters bulk mode
- change one scalar field across the selection
- run one `series_ids` replacement or `+id` / `-id` operation
- save without rebuild once
- save with rebuild once

Expected results:

- untouched fields remain unchanged per record
- touched fields update across the selected works only
- bulk mode hides the record-specific detail/file/link sections
- rebuild runs only for affected work scopes

## 6. Detail Create, Edit, Bulk Edit, And Rebuild

Route:

- `/studio/catalogue-new-work-detail/`
- `/studio/catalogue-work-detail/`

Owner:

- manual

Checks:

- create one draft detail under a known work
- confirm the new detail can be opened in the detail editor
- edit and save one detail in focused mode
- run `Save + Rebuild`
- open the parent work page and confirm the detail appears as expected
- enter detail bulk mode with a small multi-detail selection and run one bulk metadata change

Expected results:

- detail save and rebuild stay scoped to the parent work runtime
- bulk edit works only on the selected details
- parent work output updates as expected after detail rebuild

## 7. Work-Owned Files And Links

Route:

- `/studio/catalogue-work/`

Owner:

- manual

Checks:

- add one download entry from the work editor
- add one link entry from the work editor
- edit each entry from the parent work draft
- cancel one modal and confirm the parent draft does not change
- delete one entry and confirm the parent draft becomes dirty
- save from the parent work flow
- confirm the public work page metadata updates if the record is published/in scope

Expected results:

- files and links are not standalone child records
- saved file/link metadata appears in the expected parent work runtime context after rebuild

## 8. Series Create, Edit, Delete, And Rebuild

Route:

- `/studio/catalogue-new-series/`
- `/studio/catalogue-series/`

Owner:

- manual

Checks:

- create one draft series
- open and edit the series in the series editor
- confirm `primary_work_id` and membership expectations behave correctly
- run `Save + Rebuild`
- open the public series page after rebuild
- run one delete preview for a safe test series
- if the preview is clean and the series is disposable, run delete apply

Expected results:

- series save preserves source integrity with work membership
- series rebuild updates the public series surface
- delete preview exposes blockers clearly before apply

## 9. Work And Detail Delete Flows

Route:

- `/studio/catalogue-work/`
- `/studio/catalogue-work-detail/`

Owner:

- manual

Checks:

- run delete preview for one disposable work detail
- if clean, run delete apply and confirm the parent work rebuild scope is clear
- run delete preview for one disposable work
- review dependent detail/file/link impacts before apply
- apply only if the record is safe to remove in the current environment

Expected results:

- preview shows blockers and dependent impacts clearly
- apply performs one atomic source update
- follow-up rebuild scope is understandable and checkable

## 10. Bulk Import

Route:

- `/studio/bulk-add-work/`

Owner:

- manual plus Codex for workbook/schema spot checks if needed

Checks:

- run preview in `works` mode
- confirm candidate, importable, duplicate, and blocked counts are understandable
- run preview in `work_details` mode
- confirm blocked rows, if any, are actionable
- run apply only when the workbook is intentionally prepared for import

Expected results:

- import remains one-way from `data/works_bulk_import.xlsx` into canonical JSON
- duplicate rows are skipped rather than overwritten
- apply is blocked when workbook rows are invalid

## 11. Moments Import

Route:

- `/studio/catalogue-moment-import/`

Owner:

- manual

Checks:

- preview one known source markdown filename
- confirm front matter, image state, and generated/runtime state are shown clearly
- run import/apply for one valid moment
- check the public moment page afterward
- include one case where the source image is missing

Expected results:

- missing images do not block the import flow
- moment import updates activity/build reporting and public runtime as expected

## 12. Catalogue Activity And Build Activity

Route:

- `/studio/catalogue-activity/`
- `/studio/build-activity/`

Owner:

- manual

Checks:

- confirm a source save or import produces a Catalogue Activity entry
- confirm a rebuild produces a Build Activity entry
- sort by multiple headers on each page
- follow links from activity rows back into relevant editors or next-step routes
- confirm local media generation results are visible where expected

Expected results:

- source-side and build-side reporting stay distinct
- rows are sortable, legible, and operationally useful

## 13. Media And Prose Readiness

Route:

- `/studio/catalogue-work/`
- `/studio/catalogue-series/`
- `/studio/catalogue-work-detail/`

Owner:

- manual

Checks:

- inspect one work with ready prose and ready media
- inspect one work or detail with missing media file
- inspect one work or series with missing prose metadata or missing prose file
- inspect one record where local thumbnails are pending generation
- run `Import prose + rebuild` for one ready prose case

Expected results:

- readiness states are understandable without docs
- each non-ready state points to an obvious next step
- prose import updates runtime output without implying in-Studio prose editing

## 14. Public Runtime Spot Checks

Routes:

- `/works/<work_id>/`
- `/series/<series_id>/`
- `/moments/<moment_id>/`
- `/series/`

Owner:

- manual

Checks:

- after key Studio mutations, open the relevant public page
- confirm updated metadata, prose, detail rows, file/link metadata, or moment output appear where expected
- confirm no obvious regression appears in the shared catalogue entry surfaces

Expected results:

- Studio actions produce visible public/runtime consequences where appropriate
- no rebuild appears successful in Studio while leaving stale public output behind

## 15. Responsive Pass

Routes:

- `/studio/`
- `/studio/catalogue/`
- `/studio/catalogue-work/`
- `/studio/catalogue-work-detail/`
- `/studio/catalogue-series/`
- `/studio/bulk-add-work/`
- `/studio/catalogue-moment-import/`
- `/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan`

Owner:

- manual

Checks:

- run one desktop-width pass
- run one mobile-width pass
- confirm header nav, dashboard links, action buttons, form rows, current-record panels, and list/table views remain usable

Expected results:

- no major overlap, clipping, hidden actions, or broken navigation at mobile width
- key operational pages remain usable without a desktop-only assumption

## Suggested Codex Command Set

Use these as companion checks during execution:

```bash
python -m py_compile scripts/generate_work_pages.py scripts/catalogue_json_build.py scripts/studio/catalogue_write_server.py
./scripts/build_docs.rb --write
bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build
python scripts/catalogue_json_build.py --work-id <work_id>
python scripts/catalogue_json_build.py --moment-file <moment_file>.md
```

Add narrower commands only when a scenario needs them.

## Exit Condition

The first full pass is complete when:

- every checklist section above has a pass/fail outcome recorded externally
- blockers are grouped into the triage buckets above
- the remaining issues can be described as implementation fixes rather than missing test definition
