---
doc_id: site-change-log
title: "Site Change Log"
added_date: 2026-04-24
last_updated: 2026-04-29
parent_id: ""
sort_order: 270
---
# Site Change Log

## [2026-04-29] Converted work-detail editor to explicit Publish and Unpublish commands

**Status:** implemented

**Area:** Studio / catalogue work details / publication workflow

**Summary:**
Updated the Work Detail editor so detail publication is controlled by `Publish` / `Unpublish` instead of save-time public update controls.

**Reason:**
Work details still exposed `Update site now` as a save-time checkbox and follow-up command after the Work and Series editors moved to separate `Save`, `Publish`, and `Unpublish` intentions. Details need the same publication model, with published saves updating the parent work output internally.

**Effect:**
The detail status field is now a non-input Readonly Display surface in single, bulk, and new modes. Single-detail `Save` never changes publication status, draft saves stay source-only, and published saves request the internal parent-work public update without showing an update command. Saved draft details expose `Publish`; published details expose `Unpublish`, which ignores unsaved form edits after confirmation and uses the shared publication preview/apply endpoints to clean public output. Bulk detail saves update public output only for changed published detail records.

**Affected files/docs:**

- `studio/catalogue-work-detail/index.md`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-work-detail-fields.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Publication Workflow Request](/docs/?scope=studio&doc=site-request-catalogue-publication-workflow)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-04-29] Rendered Work and Series status as Readonly Display

**Status:** implemented

**Area:** Studio / catalogue publication workflow

**Summary:**
Changed the Work and Series editor `status` controls from disabled dropdowns to non-input Readonly Display surfaces.

**Reason:**
Once publication state changes moved to explicit `Publish` / `Unpublish` commands, a disabled dropdown made the status field look like an unavailable edit control rather than current state.

**Effect:**
Work and Series status now reads as display state through span-based `tagStudio__input--readonlyDisplay` surfaces while preserving the existing draft/save validation flow. The input primitive demo also shows Readonly Display with normal text color. `Publish` and `Unpublish` remain the only visible commands that change publication status.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-fields.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-series-fields.js`
- `assets/studio/js/catalogue-series-editor.js`
- `_includes/studio_ui_catalogue_input_demo.html`
- `studio/ui-catalogue/input/index.md`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-04-29] Converted work editor to explicit Publish and Unpublish commands

**Status:** implemented for works

**Area:** Studio / catalogue works / publication workflow

**Summary:**
Updated the Work editor so single-work publication is controlled by `Publish` / `Unpublish` instead of save-time public update controls.

**Reason:**
The publication workflow request defines `Save`, `Publish`, and `Unpublish` as separate user intentions. Works needed the same command model as Series, with the added wrinkle that bulk saves should update public output only for changed records that are already published.

**Effect:**
The work status field is now read-only in single, bulk, and new modes. Single-work `Save` never changes publication status, draft saves stay source-only, and published saves request the internal public catalogue update without showing a rebuild/update command. Saved draft works expose `Publish`; published works expose `Unpublish`, which ignores unsaved form edits after confirmation and uses the shared publication preview/apply endpoints to clean public output. Bulk work saves no longer expose an update checkbox and only run public-update targets for changed published records.

**Affected files/docs:**

- `studio/catalogue-work/index.md`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/data/studio_config.json`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Publication Workflow Request](/docs/?scope=studio&doc=site-request-catalogue-publication-workflow)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-04-29] Converted series editor to explicit Publish and Unpublish commands

**Status:** implemented

**Area:** Studio / catalogue series / publication workflow

**Summary:**
Updated the Series editor so publication is controlled by a single `Publish` / `Unpublish` command instead of save-time public update controls.

**Reason:**
The publication workflow request defines `Save`, `Publish`, and `Unpublish` as separate user intentions. The Series editor was the first target because it exposed the confusing `Update site now` checkbox problem.

**Effect:**
The series status field is now read-only, `Save` never changes publication status, draft saves stay source-only, and published saves request the internal public catalogue update without showing a rebuild/update command. Draft series expose `Publish` when the saved form is clean and valid; published series expose `Unpublish`, which ignores unsaved form edits after confirmation and uses the shared publication preview/apply endpoints to clean public output.

**Affected files/docs:**

- `studio/catalogue-series/index.md`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Catalogue Publication Workflow Request](/docs/?scope=studio&doc=site-request-catalogue-publication-workflow)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-04-29] Added shared catalogue publication preview/apply server shape

**Status:** implemented

**Area:** Studio / catalogue workflow

**Summary:**
Added shared `POST /catalogue/publication-preview` and `POST /catalogue/publication-apply` endpoints for catalogue record publication flows.

**Reason:**
The series editor conversion needs a server contract that separates metadata saves, publish, and unpublish before the UI removes save-time public update controls.

**Effect:**
The catalogue write server can now preview and apply `publish`, `unpublish`, and `save_published` actions for works, work details, series, and moments. Preview reports blockers, changed source fields, affected ids, and public update or cleanup impact. Apply re-runs preview, honors stale-write hashes, writes id-scoped source changes, records backups for existing generated/public-update files, refreshes Studio lookup data, and can return `public_update_failed` when a source save succeeds but the internal public update fails.

**Affected files/docs:**

- `scripts/studio/catalogue_write_server.py`
- [Catalogue Publication Workflow Request](/docs/?scope=studio&doc=site-request-catalogue-publication-workflow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-04-29] Refined catalogue publication workflow request

**Status:** specified

**Area:** Studio / catalogue workflow

**Summary:**
Updated the catalogue publication workflow request around a simpler user-facing model: records are `draft` or `published`, `Save` saves metadata, and one publication button switches between `Publish` and `Unpublish`.

**Reason:**
The user does not need to reason about canonical source data, generated public data, or rebuild mechanics. Published-record saves should update the public site internally, while publication state changes should happen only through explicit Publish/Unpublish commands.

**Effect:**
The request now removes `Rebuild` and `Update site now` from the editor UI model, makes status read-only, defines save-on-published behavior, specifies Publish and Unpublish enablement, and requires unpublish to remove generated route files so draft records are no longer publicly routable.

**Affected files/docs:**

- [Catalogue Publication Workflow Request](/docs/?scope=studio&doc=site-request-catalogue-publication-workflow)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-04-29] Opened Catalogue Status editor links in new tabs

**Status:** implemented

**Area:** Studio / catalogue status

**Summary:**
Changed Catalogue Status row links so opening a work, work detail, or series editor preserves the report in the current tab.

**Reason:**
Catalogue Status is used as a review queue. Replacing the report when opening a draft work or series interrupted the review workflow.

**Effect:**
Row id links still route to the focused editor for the record family, but now open in a new browser tab with `rel="noopener"`.

**Affected files/docs:**

- `assets/studio/js/catalogue-status.js`
- [Catalogue Status](/docs/?scope=studio&doc=catalogue-status)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-29] Fixed per-series JSON member filtering

**Status:** implemented

**Area:** catalogue generation / generated series data

**Summary:**
Fixed the generator path that populates published member works in `assets/series/index/<series_id>.json`.

**Reason:**
The generator filtered per-series membership through `work_meta_by_id.status`, but that metadata map intentionally does not include work publication status. As a result, regenerated per-series payloads could emit `series.works: []` for published series even when the aggregate `assets/data/series_index.json` still had the correct visible grid membership.

**Effect:**
Per-series JSON generation now uses an internal `work_status_by_id` lookup sourced directly from canonical work status data. The public payload contract is unchanged: published series payloads can include published member works, while the public series grid continues to render from the aggregate series and works indexes.

**Affected files/docs:**

- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## [2026-04-29] Added catalogue unified editor cleanup request

**Status:** proposed

**Area:** Studio / catalogue editors / generated catalogue data

**Summary:**
Added an umbrella change request for cleanup work that should follow the work, work-detail, and series editor unification work.

**Reason:**
The unified editor changes intentionally kept some legacy route artifacts and compatibility concerns separate from behavior fixes. The current series JSON investigation also surfaced a generated per-series membership field that is part of the payload contract but not consumed by the public series grid.

**Effect:**
The cleanup backlog now has one request covering retired `catalogue-new-*` routes/controllers/docs, final shared-helper review, old URL compatibility policy, and the future decision to keep or remove `series.works` from per-series runtime JSON.

**Affected files/docs:**

- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [Catalogue Unified Editor Cleanup Request](/docs/?scope=studio&doc=site-request-catalogue-unified-editor-cleanup)

## [2026-04-29] Blocked draft works from public updates

**Status:** implemented

**Area:** Studio / catalogue work / public build pipeline

**Summary:**
Aligned work saves and scoped work builds around a published-only public update boundary.

**Reason:**
Changing work `00375` from blank status to `draft` still allowed the checked `Update site now` path to run. The runtime build path treated that draft work as buildable and rewrote it to `published`, removing it from the draft status report until it was manually changed back.

**Effect:**
Draft work saves are source-only. The work editor disables and unchecks save-time public update controls while the form status is `draft`, the write server skips save-time build requests for draft works, and JSON-source work builds reject non-published works.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `scripts/studio/catalogue_write_server.py`
- `scripts/catalogue_json_build.py`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Build Catalogue JSON](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-29] Required year metadata for series saves

**Status:** implemented

**Area:** Studio / catalogue series

**Summary:**
Edit-mode series saves now require `year` and `year_display`, matching the required metadata already enforced by new-mode series creation.

**Reason:**
The unified series editor could create a valid draft with year metadata, then later allow those same fields to be cleared on `Save`. The save path needed the same user-facing field errors plus a write-server guard for direct endpoint calls.

**Effect:**
`/studio/catalogue-series/` now blocks `Save` when `year` or `year_display` is blank, and `POST /catalogue/series/save` rejects direct payloads missing either field. Historical records that already lack those fields must be filled before they can be saved through the editor.

**Affected files/docs:**

- `assets/studio/js/catalogue-series-fields.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Series Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-series-unified-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-29] Added draft-series recovery view

**Status:** implemented

**Area:** Studio / catalogue status / series editor

**Summary:**
Extended Catalogue Status with a focused draft-series view and added a Catalogue dashboard link for reopening draft series records.

**Reason:**
After the series editor gained unified draft creation, draft series needed the same recovery path that draft works already have. The all-status page listed non-published series, but a focused `?view=draft-series` route makes newly created source-only series easier to find after the create session ends.

**Effect:**
`/studio/catalogue-status/?view=draft-series` now filters to draft series, shows the primary work reference when present, and links each row to `/studio/catalogue-series/?series=<series_id>`. The Catalogue dashboard now includes `Review Draft Series` beside `Review Draft Works`.

**Affected files/docs:**

- `studio/catalogue/index.md`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Catalogue Status](/docs/?scope=studio&doc=catalogue-status)
- [Studio E2E Checklist](/docs/?scope=studio&doc=new-pipeline-studio-e2e-checklist)
- [Catalogue Series Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-series-unified-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-29] Added catalogue publication workflow request

**Status:** specified

**Area:** Studio / catalogue workflow

**Summary:**
Added a catalogue-wide change request for replacing save-time publication checkboxes with explicit `Publish`, `Unpublish`, and `Rebuild` commands.

**Reason:**
The series draft/publication issue showed that a checkbox is the wrong interaction model for changing public visibility. The same distinction between source save, public visibility, and runtime rebuild needs to be consistent across works, work details, series, and moments.

**Effect:**
The new request defines the shared command vocabulary, record-family rules, implementation tasks, benefits, risks, and open questions for a future catalogue-wide publication workflow pass.

**Affected files/docs:**

- [Catalogue Publication Workflow Request](/docs/?scope=studio&doc=site-request-catalogue-publication-workflow)
- [Change Requests](/docs/?scope=studio&doc=change-requests)

## [2026-04-29] Blocked draft series from public updates

**Status:** implemented

**Area:** Studio / catalogue series / public build pipeline

**Summary:**
Aligned the series editor, write server, scoped JSON build helper, and generator around a published-only public update boundary for series.

**Reason:**
A draft save with `Update site now` still checked could run the public update path, creating public series artifacts for a draft series. The same path also exposed an older data issue where series `002` pointed at work `00640`, whose status is blank.

**Effect:**
Draft series saves are source-only. The editor disables and unchecks save-time public update controls while the form status is `draft`, the write server skips save-time build requests for draft series, scoped series builds require a published series with a published primary work, and generated public series payloads only include published member works. Series `002` is restored to `draft` with no `published_date` in canonical source.

The stale public aggregate artifacts were also regenerated so series `002` is removed from the public series index, recent index, and catalogue search. Its existing collection stub is marked `published: false` so Jekyll stops emitting the direct `/series/002/` page while the source record is draft. The validation pass aligned the retired `copy_draft_media_files.py` entrypoint with the deprecated-script contract so a bare run exits cleanly with guidance.

**Affected files/docs:**

- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/data/catalogue/series.json`
- `scripts/studio/catalogue_write_server.py`
- `scripts/catalogue_json_build.py`
- `scripts/generate_work_pages.py`
- `scripts/copy_draft_media_files.py`
- `assets/data/series_index.json`
- `assets/data/recent_index.json`
- `assets/data/search/catalogue/index.json`
- `_series/002.md`
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Build Catalogue JSON](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Copy Draft Media](/docs/?scope=studio&doc=scripts-copy-draft-media)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-29] Kept series form state fresh after save

**Status:** implemented

**Area:** Studio / catalogue series

**Summary:**
Changed the series editor save flow so the current form baseline is reset from the write response record instead of immediately reloading generated lookup JSON.

**Reason:**
After saving a series status change, generated lookup data could still be stale in the browser briefly. Rehydrating from that lookup made the status field appear unchanged until a browser refresh even though the source save succeeded.

**Effect:**
Saving a series status change, including changing series `002` to `draft`, keeps the saved status visible immediately after save. Generated lookup JSON is still used when opening series records and for preview context.

**Affected files/docs:**

- `assets/studio/js/catalogue-series-editor.js`
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-29] Migrated series creation to the unified route

**Status:** implemented

**Area:** Studio / catalogue series

**Summary:**
Moved active series creation navigation to `/studio/catalogue-series/?mode=new` through the main series editor, converted `/studio/catalogue-new-series/` into a compatibility redirect, and removed the legacy new-series route and UI text from active Studio config.

**Reason:**
After new mode landed on the main series editor, keeping the standalone create page active would split testing and keep the Catalogue dashboard presenting series creation and editing as separate workflows.

**Effect:**
The Catalogue dashboard now exposes one `Series Editor` entry. Old `/studio/catalogue-new-series/` links redirect to the unified new-mode route, while docs and E2E guidance now point active create/edit work at `/studio/catalogue-series/`.

**Affected files/docs:**

- `studio/catalogue/index.md`
- `studio/catalogue-new-series/index.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [New Catalogue Series](/docs/?scope=studio&doc=catalogue-new-series-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Studio E2E Checklist](/docs/?scope=studio&doc=new-pipeline-studio-e2e-checklist)
- [Catalogue Series Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-series-unified-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

## [2026-04-29] Added new mode to the catalogue series editor

**Status:** implemented

**Area:** Studio / catalogue series

**Summary:**
Added `?mode=new` support to `/studio/catalogue-series/`, including a `New` command, draft-only create behavior, required create fields, and a config-backed `series_type` select.

**Reason:**
The series unified editor request needs create and edit behavior on one route before the legacy new-series route can be retired.

**Effect:**
The series editor can now create draft series source records through `POST /catalogue/series/create`. Create mode defaults `series_type` to `primary`, requires `title`, `series_type`, `year`, and `year_display`, disables member/prose/build/delete actions until the source record exists, and opens the created series in normal edit mode.

**Affected files/docs:**

- `studio/catalogue-series/index.md`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-series-fields.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Catalogue Series Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-series-unified-editor)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)

## [2026-04-29] Factored shared catalogue series editor helpers

**Status:** implemented

**Area:** Studio / catalogue series

**Summary:**
Added a shared series source helper module and moved the current new-series and edit-series controllers onto shared field definitions, id normalization, draft shaping, validation helpers, next-id suggestion, and create/save payload helpers.

**Reason:**
The series unified editor work needs one source-field contract before adding `?mode=new` to the main series editor route.

**Effect:**
The current `/studio/catalogue-series/` and `/studio/catalogue-new-series/` route behavior remains unchanged, but both paths now depend on the same series helper surface.

**Affected files/docs:**

- `assets/studio/js/catalogue-series-fields.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/catalogue-new-series-editor.js`
- [Catalogue Series Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-series-unified-editor)

## [2026-04-29] Added series unified editor request spec

**Status:** specified

**Area:** Studio / catalogue series

**Summary:**
Added a change-request spec and task list for unifying new-series and edit-series workflows around `/studio/catalogue-series/?mode=new` and `/studio/catalogue-series/?series=<series_id>`.

**Reason:**
Work and work-detail route unification established the shared create/edit direction. Series is the next parent-record editor to align before a later catalogue-wide cleanup pass.

**Effect:**
The series implementation now has a locked Task 1 route/mode contract, documented new-mode behavior, draft-series visibility plan, risks, non-goals, and six implementation tasks. New-mode create is specified with `series_type` defaulting to `primary`, `series_type` rendered as a config-backed Studio select initially offering `primary` and `holding`, and `title`, `series_type`, `year`, and `year_display` required.

**Affected files/docs:**

- [Catalogue Series Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-series-unified-editor)

## [2026-04-29] Kept work-detail form state fresh after save-and-update

**Status:** implemented

**Area:** Studio / catalogue work details

**Summary:**
Changed the work-detail editor save flow so the current form baseline is reset from the write response record instead of immediately reloading generated lookup JSON.

**Reason:**
After saving with `Update site`, generated lookup data can still be stale in the browser for a moment. Rehydrating from that lookup made edited fields such as `title` appear to revert even though the source save succeeded.

**Effect:**
Saving a detail title now keeps the edited title visible after `Save` or `Save + Update site`; generated lookup JSON is still used when opening records.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-detail-editor.js`
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-29] Migrated work-detail create navigation to the unified route

**Status:** implemented

**Area:** Studio / catalogue work details

**Summary:**
Moved active work-detail create navigation to `/studio/catalogue-work-detail/?work=<work_id>&mode=new`, converted `/studio/catalogue-new-work-detail/` into a compatibility redirect, and removed the standalone detail-create route from active Studio config.

**Reason:**
After parent-scoped new mode landed on the main work-detail editor, keeping active links and dashboard copy pointed at the legacy create page would split testing and keep presenting details as standalone records.

**Effect:**
The work page now opens detail creation directly on the unified editor route. Old links with `?work=<work_id>` redirect to the same unified route, while missing-parent legacy links redirect to the work editor. The Catalogue dashboard no longer promotes `Create New Detail` as a primary workflow.

**Affected files/docs:**

- `studio/catalogue-work/index.md`
- `studio/catalogue-new-work-detail/index.md`
- `studio/catalogue/index.md`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [New Catalogue Work Detail](/docs/?scope=studio&doc=catalogue-new-work-detail-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio E2E Checklist](/docs/?scope=studio&doc=studio-e2e-checklist)
- [Catalogue Work Detail Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-detail-unified-editor)

## [2026-04-29] Added parent-scoped new mode to the work-detail editor

**Status:** implemented

**Area:** Studio / catalogue work details

**Summary:**
Added `?work=<work_id>&mode=new` support to `/studio/catalogue-work-detail/` so the main detail editor can create a draft detail under a locked parent work.

**Reason:**
The unified work-detail editor needs create and edit behavior on one route while preserving the product rule that work details are normally created from their parent work.

**Effect:**
New mode shows the parent work as read-only context, pre-fills the suggested next `detail_id`, keeps `status` visible and draft-only, disables build/delete/update actions until create succeeds, writes only through `POST /catalogue/work-detail/create`, and then opens the created detail in normal edit mode.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/data/studio_config.json`
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Work Detail Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-detail-unified-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-29] Factored shared work-detail editor helpers

**Status:** implemented

**Area:** Studio / catalogue work details

**Summary:**
Added a shared work-detail source helper module and moved existing new-detail and edit-detail controllers onto the same field definitions, id normalization, draft shaping, validation, and payload helpers.

**Reason:**
The work-detail unified editor request needs one source-field contract before the parent-scoped new mode can be added to the main detail editor.

**Effect:**
The current `/studio/catalogue-work-detail/` and `/studio/catalogue-new-work-detail/` route behavior remains unchanged, but both paths now depend on the same work-detail helper surface.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-detail-fields.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-new-work-detail-editor.js`
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [New Catalogue Work Detail](/docs/?scope=studio&doc=catalogue-new-work-detail-editor)
- [Catalogue Work Detail Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-detail-unified-editor)

## [2026-04-28] Added Change Requests docs root

**Status:** implemented

**Area:** Studio docs

**Summary:**
Added a dedicated Change Requests root and moved site request docs plus UI Requests under it.

**Reason:**
Request docs were split between Site Docs and the top-level UI Requests section, which made active planning material harder to scan as one group.

**Effect:**
The docs viewer now has one top-level Change Requests section for proposed and in-progress request docs. UI Requests remains a subgroup, while site request docs now sit directly under Change Requests.

**Affected files/docs:**

- [Change Requests](/docs/?scope=studio&doc=change-requests)
- [UI Requests](/docs/?scope=studio&doc=ui-requests)
- [Site Docs](/docs/?scope=studio&doc=site-docs)

## [2026-04-28] Added work-detail unified editor request

**Status:** planned

**Area:** Studio / catalogue work details

**Summary:**
Added a separate request for unifying work-detail create/edit implementation while keeping work-detail navigation parent-work-context-driven.

**Reason:**
Work details differ from works and series because users normally find and create them from the parent work page, not as isolated dashboard records.

**Effect:**
The new request documents a parent-scoped route contract, migration plan, implementation tasks, benefits, and risks for eventually retiring the standalone new-work-detail implementation without changing the intended user workflow.

**Affected files/docs:**

- [Catalogue Work Detail Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-detail-unified-editor)
- [Catalogue Work Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-unified-editor)

## [2026-04-28] Added title-search series selection to the work editor

**Status:** implemented

**Area:** Studio / catalogue work editor

**Summary:**
Replaced raw user-facing `series_ids` entry with a title-search series picker for single-work edit and new mode.

**Reason:**
Series ids are not normally visible in the works UI, so requiring raw ids made a required create/edit field depend on hidden knowledge.

**Effect:**
The work editor now searches series by title, displays selected series as title-first chips with ids as secondary context, and still saves canonical `series_ids` to work source records. Bulk mode keeps the existing raw id/diff input until bulk add/remove picker semantics are designed.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-fields.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-unified-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-28] Retired the standalone new-work route in favor of work-editor new mode

**Status:** implemented

**Area:** Studio / catalogue work editor

**Summary:**
Migrated the Catalogue dashboard and Studio config to the unified work editor, made `/studio/catalogue-new-work/` redirect to `/studio/catalogue-work/?mode=new`, and added a draft-work view to Catalogue Status.

**Reason:**
After new mode landed in the work editor, keeping a separate create route active would split testing and let field structure drift again.

**Effect:**
Work creation and editing now share one active route. Draft works created without publishing can be found from `Review Draft Works`, which opens `/studio/catalogue-status/?view=draft-works` and links rows back into the work editor.

**Affected files/docs:**

- `studio/catalogue-new-work/index.md`
- `studio/catalogue/index.md`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [New Catalogue Work](/docs/?scope=studio&doc=catalogue-new-work-editor)
- [Catalogue Status](/docs/?scope=studio&doc=catalogue-status)
- [Catalogue Work Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-unified-editor)

## [2026-04-28] Added new-work mode to the catalogue work editor

**Status:** implemented

**Area:** Studio / catalogue work editor

**Summary:**
Added `new` mode to `/studio/catalogue-work/`, including a `New` command beside `Open`, route support for `?mode=new`, draft-only create behavior, and post-create loading into normal edit mode.

**Reason:**
Creating and editing works should converge on one surface so field structure, validation, and workflow stay consistent.

**Effect:**
The work editor can now create draft work source records through the existing `POST /catalogue/work/create` endpoint. Create mode uses the same metadata form, keeps `status` fixed to `draft`, disables edit-only surfaces until the source record exists, and does not update the public site during create.

**Affected files/docs:**

- `studio/catalogue-work/index.md`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-unified-editor)

## [2026-04-28] Factored shared catalogue work-editor field helpers

**Status:** implemented

**Area:** Studio / catalogue work editor

**Summary:**
Added a shared work-editor field/model helper module and updated the existing work create/edit scripts to consume it.

**Reason:**
The planned unified work editor needs common field metadata, id normalization, series parsing, draft shaping, and source-record payload construction before `new` mode is folded into `/studio/catalogue-work/`.

**Effect:**
`assets/studio/js/catalogue-work-fields.js` now owns the shared work field definitions and core work-record helpers. The current `/studio/catalogue-work/` and `/studio/catalogue-new-work/` scripts use those helpers without adding unified new mode yet.

**Affected files/docs:**

- `assets/studio/js/catalogue-work-fields.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-new-work-editor.js`
- [Catalogue Work Unified Editor Request](/docs/?scope=studio&doc=site-request-catalogue-work-unified-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)

## [2026-04-27] Added project-state reporting for source imports

**Status:** implemented

**Area:** Studio / catalogue source review

**Summary:**
Added a project-state report that compares source project folders and primary image files against `assets/studio/data/catalogue/works.json`.

**Reason:**
After `data/works.xlsx` stopped being the canonical catalogue source, there was no direct way to identify source project folders or top-level primary-image candidates that still needed representation in `works.json`.

**Effect:**
`./scripts/project_state_report.py --write` now writes `_docs_src/project-state.md` with `published: false`. `/studio/project-state/` runs the same report through the local Catalogue Write Server and shows summary counts plus a local file-open command. The page has a default-off `include sub-folders` checkbox that includes `/projects/<project_folder>/<sub-folder>` entries when needed. Work details remain out of scope, and detail folders are skipped.

**Affected files/docs:**

- `scripts/project_state_report.py`
- `scripts/studio/catalogue_write_server.py`
- `studio/project-state/index.md`
- `studio/catalogue/index.md`
- `assets/studio/js/project-state.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- `_docs_src/project-state.md`
- [Project State Page](/docs/?scope=studio&doc=project-state-page)
- [Project State Report](/docs/?scope=studio&doc=scripts-project-state-report)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-27] Removed retired work file and link Studio routes

**Status:** implemented

**Area:** Studio / catalogue cleanup

**Summary:**
Removed the retired standalone work-file and work-link Studio pages, route scripts, old source JSON files, focused file/link lookup payloads, and generator artifact switches.

**Reason:**
Files and links are now work-owned `downloads` and `links` metadata in `works.json`. Keeping the old source files, focused lookup records, and Studio pages made the retired child-record pattern look partially supported.

**Effect:**
Normal file/link editing now lives only on `/studio/catalogue-work/`. The lookup builder no longer emits `catalogue_lookup/work_files/` or `catalogue_lookup/work_links/` payloads, `studio_config.json` no longer advertises the retired routes or data files, and `generate_work_pages.py` no longer accepts `work-files` or `work-links` as independent artifacts. External referenced files are untouched.

**Affected files/docs:**

- `studio/catalogue-work-file/index.md`
- `studio/catalogue-new-work-file/index.md`
- `studio/catalogue-work-link/index.md`
- `studio/catalogue-new-work-link/index.md`
- `assets/studio/js/catalogue-work-file-editor.js`
- `assets/studio/js/catalogue-new-work-file-editor.js`
- `assets/studio/js/catalogue-work-link-editor.js`
- `assets/studio/js/catalogue-new-work-link-editor.js`
- `assets/studio/data/catalogue/work_files.json`
- `assets/studio/data/catalogue/work_links.json`
- `scripts/generate_work_pages.py`
- `scripts/build_catalogue.py`
- `scripts/catalogue_source.py`
- `scripts/catalogue_lookup.py`
- `assets/studio/data/studio_config.json`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Source Model](/docs/?scope=studio&doc=new-pipeline-source-model)
- [Work-Owned Files And Links Request](/docs/?scope=studio&doc=site-request-work-owned-files-links)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)

## [2026-04-27] Added work-editor modals for files and links

**Status:** implemented

**Area:** Studio / catalogue work editor

**Summary:**
Added inline add/edit/delete interactions for work-owned `downloads` and `links` metadata on `/studio/catalogue-work/`.

**Reason:**
After files and links moved into `works.json`, the separate file/link pages no longer matched the source model. Editing should happen on the owning work record and save through the parent work draft.

**Effect:**
The work editor now renders downloads and links as editable list sections. Add/edit actions open shared Studio modal forms, delete uses the shared confirm modal, and changes are saved through `POST /catalogue/work/save` as `Works.downloads` and `Works.links`. Removing the final entry is now detected as a source change and normalized back to an omitted empty array.

**Affected files/docs:**

- `studio/catalogue-work/index.md`
- `studio/catalogue/index.md`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/css/studio.css`
- `assets/studio/data/studio_config.json`
- `scripts/studio/catalogue_write_server.py`
- [Work-Owned Files And Links Request](/docs/?scope=studio&doc=site-request-work-owned-files-links)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-27] Added field-aware catalogue build scoping request

**Status:** planned

**Area:** Studio / catalogue build planning

**Summary:**
Documented the follow-up request to make catalogue scoped builds depend on changed fields rather than always selecting the conservative work-plus-series artifact set.

**Reason:**
Work-owned files and links exposed that some work metadata changes do not affect related series output. The current scope is safe, but broader than the true dependency graph for local metadata such as `downloads` and `links`.

**Effect:**
No runtime behavior changed. The request defines the planned dependency registry, planner integration, dry-run explanations, verification cases, benefits, and risks for a later implementation pass.

**Affected files/docs:**

- [Field-Aware Catalogue Build Scoping Request](/docs/?scope=studio&doc=site-request-field-aware-build-scoping)

## [2026-04-27] Made catalogue files and links work-owned metadata

**Status:** implemented

**Area:** Studio / catalogue source model

**Summary:**
Moved work file/link metadata into `assets/studio/data/catalogue/works.json` as work-owned `downloads` and `links` arrays. Empty arrays are omitted from source records.

**Reason:**
Files and links no longer need independent draft/published workflows, published dates, or standalone editor routes. Keeping separate source files made small work metadata look like first-class catalogue records.

**Effect:**
Catalogue source loading now treats `Works.downloads` and `Works.links` as canonical while deriving compatibility rows for existing generator and lookup surfaces. The public `work.downloads` and `work.links` output shape is preserved. The work editor now shows files and links as read-only work-owned summaries pending the modal editing pass, Catalogue Status no longer lists file/link families, and the old standalone work-file/work-link write endpoints return a retired-endpoint response instead of writing `work_files.json` or `work_links.json`.

**Affected files/docs:**

- `assets/studio/data/catalogue/works.json`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-status.js`
- `scripts/catalogue_source.py`
- `scripts/generate_work_pages.py`
- `scripts/studio/catalogue_write_server.py`
- [Work-Owned Files And Links Request](/docs/?scope=studio&doc=site-request-work-owned-files-links)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

## [2026-04-27] Added media-only image refresh in Studio editors

**Status:** implemented

**Area:** Studio / catalogue media

**Summary:**
Added a `Refresh media` action to work, work-detail, and moment media readiness panels. The action regenerates local thumbnails and staged primary image variants from the displayed source image path without saving metadata.

**Reason:**
The legacy script workflow allowed replacing a source image and regenerating srcset outputs with scoped flags. Studio showed the resolved source media path but did not provide a metadata-neutral way to refresh derivatives from that path.

**Effect:**
`POST /catalogue/build-apply` now supports `media_only: true`. Studio sends `media_only: true` with `force: true` from the media readiness panel, so derivative generation runs even when existing outputs appear current. The media-only path stops after local image staging and derivative generation; it does not regenerate page/json/search outputs and it does not upload primary images to R2.

**Affected files/docs:**

- `scripts/catalogue_json_build.py`
- `scripts/studio/catalogue_write_server.py`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/data/studio_config.json`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

## [2026-04-27] Implemented catalogue delete cleanup for works, details, and series

**Status:** implemented

**Area:** Studio / catalogue

**Summary:**
Extended `POST /catalogue/delete-apply` so work, work-detail, and series deletes now remove repo-owned generated artifacts, local media outputs, public index references, and search references where applicable.

**Reason:**
Moment delete had been upgraded to mean "delete the repo-owned public surface for this item", but the older delete paths still primarily removed source records and refreshed Studio lookup payloads.

**Effect:**
Work delete now removes generated work artifacts, dependent generated detail artifacts, published thumbnails, repo-local staged media, stale public index/search records, per-work tag overrides, and work-storage index entries. Work-detail delete now removes generated detail artifacts/media and updates the parent work runtime JSON. Series delete now removes generated series artifacts, removes the series from affected work runtime/index records, removes the series tag-assignment row, updates recent/public indexes, and rebuilds catalogue search. Canonical prose, canonical source images, remote media, and deprecated external media staging paths remain untouched.

**Affected files/docs:**

- `scripts/studio/catalogue_write_server.py`
- [Catalogue Delete Cleanup Request](/docs/?scope=studio&doc=site-request-catalogue-delete-cleanup)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)

## [2026-04-27] Added change request for catalogue delete cleanup

**Status:** proposed

**Area:** Studio / catalogue

**Summary:**
Added a scoped request for making work, work-detail, and series deletes remove repo-owned public artifacts, media, indexes, and search references with the same semantics now used by moment delete.

**Reason:**
Moment delete now removes the generated/site surface for a deleted moment, but the older work, detail, and series delete paths still primarily remove source records and refresh Studio lookup payloads.

**Effect:**
The request captures the expected cleanup scope, non-goals, safety model, acceptance checks, benefits, and risks for a future implementation. No runtime delete behavior changed in this documentation-only step.

**Affected files/docs:**

- [Catalogue Delete Cleanup Request](/docs/?scope=studio&doc=site-request-catalogue-delete-cleanup)

## [2026-04-27] Added Moment Delete To The Catalogue Moment Editor

**Status:** implemented

**Area:** Studio / catalogue

**Summary:**
Added source-record delete support for `/studio/catalogue-moment/`.

**Reason:**
The new moment editor could reopen, save, rebuild, and import prose for existing moments, but it still lacked the delete action already present in the work, detail, and series editors.

**Effect:**
The moment editor now exposes `Delete`, previews impact through `POST /catalogue/delete-preview`, confirms in the browser, and applies through `POST /catalogue/delete-apply` with record-hash conflict protection. The operation removes the canonical moment metadata record, generated moment page/json artifacts, published thumbnails, repo-local staged media, the moments-index entry, and the catalogue search record. Canonical prose, canonical source images, and remote uploaded media remain untouched.

**Affected files/docs:**

- `studio/catalogue-moment/index.md`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/data/studio_config.json`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-27] Added the Catalogue Moment Editor

**Status:** implemented

**Area:** Studio / catalogue

**Summary:**
Added `/studio/catalogue-moment/` as the first normal editor for existing moment records.

**Reason:**
Moment metadata now lives in canonical catalogue JSON, but existing moments still needed a purpose-built Studio maintenance surface separate from the file-driven import page.

**Effect:**
The Catalogue dashboard now links to `Edit Moment`. The page opens one existing moment, edits metadata in `assets/studio/data/catalogue/moments.json`, protects saves with record hashes, can optionally run the scoped moment rebuild, shows prose/media readiness, and imports staged body-only moment prose through the shared prose import endpoints.

**Affected files/docs:**

- `studio/catalogue-moment/index.md`
- `studio/catalogue/index.md`
- `assets/studio/js/catalogue-moment-editor.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/data/studio_config.json`
- `scripts/studio/catalogue_write_server.py`
- `scripts/catalogue_json_build.py`
- [Catalogue Moment Editor](/docs/?scope=studio&doc=catalogue-moment-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)

## [2026-04-27] Added change request for a Catalogue Moment Editor

**Status:** proposed

**Area:** Studio / catalogue

**Summary:**
Added a scoped implementation request for a first-class `/studio/catalogue-moment/` editor.

**Reason:**
Moments now have repo-local metadata, prose, and media generation sources, but there is still no normal Studio edit surface for reopening an existing moment and maintaining its metadata, prose readiness, media readiness, and scoped rebuild state.

**Effect:**
The request defines the target route, source contracts, editable fields, staged prose import behavior, scoped build/media behavior, non-goals, risks, and task-level acceptance checks. No editor route was implemented in this change.

**Affected files/docs:**

- [Catalogue Moment Editor Request](/docs/?scope=studio&doc=site-request-catalogue-moment-editor)

## [2026-04-27] Extended repo-local image srcset staging to moments

**Status:** implemented

**Area:** Catalogue pipeline / Studio

**Summary:**
Moment imports now use the same repo-local image staging and thumbnail promotion workflow as work and work-detail scoped builds.

**Reason:**
Moments were the remaining catalogue image path still excluded from the new local media workflow. Their source metadata now lives in canonical catalogue JSON, so the build can resolve `source_image_file`, stage the renamed source image, create srcset derivatives, and publish thumbnails consistently.

**Effect:**
`/studio/catalogue-moment-import/` preview/apply now reports and runs local moment media generation. Source images are staged under `var/catalogue/media/moments/make_srcset_images/`, primary and thumbnail derivatives are generated under `var/catalogue/media/moments/srcset_images/`, generated thumbnails are copied into `assets/moments/img/`, and generated primary derivatives remain staged for remote publishing. Missing moment images block only the media step, not prose/metadata import.

**Affected files/docs:**

- `scripts/catalogue_json_build.py`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

## [2026-04-27] Staged work image srcsets under repo-local var output

**Status:** implemented

**Area:** Catalogue pipeline / Studio

**Summary:**
Scoped work and work-detail rebuilds now copy source images into `var/catalogue/media/`, generate primary and thumbnail srcset derivatives there, and automatically copy generated thumbnails into the repo-owned `assets/` image folders.

**Reason:**
The legacy workflow already copied and renamed source images before srcset generation, but its staging area lived outside the repo and thumbnail promotion into `assets/` was manual. The Studio-driven workflow needs the same operational shape with local staging that is easy to inspect and with thumbnail publication handled by the build action.

**Effect:**
`Save + Rebuild` and explicit scoped build actions for works/details now prepare renamed source images, create local primary and thumbnail derivatives, and publish thumbnails to `assets/works/img/` or `assets/work_details/img/`. Primary derivatives remain staged in `var/catalogue/media/` for the existing remote media/R2 handoff; no remote upload is performed.

**Affected files/docs:**

- `scripts/catalogue_json_build.py`
- `.gitignore`
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Srcset Builder](/docs/?scope=studio&doc=scripts-srcset-builder)

## [2026-04-27] Moved moment prose and metadata to repo-local catalogue sources

**Status:** implemented

**Area:** Catalogue pipeline / Studio

**Summary:**
Moment metadata now lives in `assets/studio/data/catalogue/moments.json`, and moment prose now lives as body-only Markdown under `_docs_src_catalogue/moments/`.

**Reason:**
Moments needed the same durable repo-local prose handling as work and series prose, but their previous source files also owned front matter metadata. Splitting metadata from prose keeps generated runtime JSON non-canonical and makes the source model easier to review.

**Effect:**
The moment import page now collects metadata fields, previews staged body-only prose from `var/docs/catalogue/import-staging/moments/`, writes metadata to canonical catalogue JSON, and writes prose to `_docs_src_catalogue/moments/`. The generator reads those canonical sources for moment payloads and no longer writes moment source front matter. Media image import/edit/srcset generation remains deferred to a future shared work/moment mechanism.

**Affected files/docs:**

- `assets/studio/data/catalogue/moments.json`
- `_docs_src_catalogue/moments/`
- `scripts/moment_sources.py`
- `scripts/catalogue_json_build.py`
- `scripts/generate_work_pages.py`
- `scripts/studio/catalogue_write_server.py`
- `assets/studio/js/catalogue-moment-import.js`
- `assets/studio/data/studio_config.json`
- `studio/catalogue-moment-import/index.md`
- [Moments Prose Source Model Request](/docs/?scope=studio&doc=site-request-moments-prose-source-model)
- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

## [2026-04-27] Reduced forced scoped catalogue build noise

**Status:** implemented

**Area:** Catalogue pipeline

**Summary:**
Added a narrow published-record refresh mode for scoped catalogue builds and kept broad force behavior reserved for intentional rewrites.

**Reason:**
Work, series, and moment scoped updates need to recompute selected published payloads, especially prose payloads, without rewriting unchanged aggregate JSON or catalogue search output solely because `generated_at_utc` changed.

**Effect:**
Normal scoped catalogue builds now pass `--refresh-published` to the internal generator instead of broad `--force`. Unchanged payloads still skip by content version, catalogue search is only forced when an explicit force run is requested, and already-published records keep their existing `published_date` unless they transition from `draft` to `published`. The scoped helper also now supports direct `--series-id` preview/write runs.

**Affected files/docs:**

- `scripts/generate_work_pages.py`
- `scripts/catalogue_json_build.py`
- `scripts/studio/catalogue_write_server.py`
- [Work And Series Prose Source Model Request](/docs/?scope=studio&doc=site-request-work-series-prose-source-model)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

## [2026-04-26] Moved catalogue editor usage docs under User Guide

**Status:** implemented

**Area:** Documentation

**Summary:**
Reparented the catalogue work, series, detail, file, and link editor docs from `Studio` to `User Guide`.

**Reason:**
Those documents primarily explain how to use Studio UI pages. Technical contracts, generated payload behavior, and implementation details should stay in Studio and data/script docs, while practical page workflows belong under User Guide.

**Effect:**
The User Guide now lists the catalogue editor docs alongside other task-focused guides. `Studio` remains the technical admin overview and points readers to User Guide for practical page-use docs.

**Affected files/docs:**

- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Studio](/docs/?scope=studio&doc=studio)
- [Work And Series Prose Source Model Request](/docs/?scope=studio&doc=site-request-work-series-prose-source-model)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)

## [2026-04-26] Removed legacy prose filename fields from catalogue editors

**Status:** implemented

**Area:** Studio / catalogue

**Summary:**
Removed `work_prose_file` and `series_prose_file` from the new/edit work and series Studio forms.

**Reason:**
Work and series prose publication now uses ID-derived Markdown under `_docs_src_catalogue/`, so the legacy filename fields should not remain editable publication controls.

**Effect:**
New work, work editor, new series, and series editor forms no longer render or submit the legacy prose filename fields. Existing source records are preserved, and prose import continues through the staged Markdown readiness/action flow.

**Affected files/docs:**

- `assets/studio/js/catalogue-new-work-editor.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-new-series-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- [Work And Series Prose Source Model Request](/docs/?scope=studio&doc=site-request-work-series-prose-source-model)
- [New Catalogue Work](/docs/?scope=studio&doc=catalogue-new-work-editor)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [New Catalogue Series](/docs/?scope=studio&doc=catalogue-new-series-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)

## [2026-04-26] Switched work and series prose generation to repo-local sources

**Status:** implemented

**Area:** Catalogue pipeline

**Summary:**
Work and series prose rendering now uses ID-derived Markdown files under `_docs_src_catalogue/` while preserving the public JSON payload shape.

**Reason:**
The staged import flow writes permanent repo-local prose sources, so publication needs to read those files instead of legacy external prose filename fields.

**Effect:**
`generate_work_pages.py` reads `_docs_src_catalogue/works/<work_id>.md` and `_docs_src_catalogue/series/<series_id>.md` when rendering `content_html`. Missing prose stays optional. Planner prose fingerprinting now watches those same repo-local files, and `work_prose_file` / `series_prose_file` no longer control public prose rendering.

**Affected files/docs:**

- `scripts/generate_work_pages.py`
- `scripts/build_catalogue.py`
- [Work And Series Prose Source Model Request](/docs/?scope=studio&doc=site-request-work-series-prose-source-model)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)

## [2026-04-26] Added staged catalogue prose import

**Status:** implemented

**Area:** Studio / catalogue

**Summary:**
Added a work/series prose import step that reads ID-based staged Markdown from `var/docs/catalogue/import-staging/`, validates it, and writes permanent repo-local prose source under `_docs_src_catalogue/`.

**Reason:**
Work and series prose source is moving out of externally resolved project folders and into a repo-managed Markdown source tree while keeping public work and series payloads stable.

**Effect:**
The work and series editors now expose `Import staged prose` when the matching staged Markdown file exists. The catalogue write server previews staged prose, rejects front matter, requires overwrite confirmation for different existing permanent prose, and writes without backup for this explicit prose flow. Generator lookup now reads the new permanent source roots.

**Affected files/docs:**

- `scripts/studio/catalogue_write_server.py`
- `scripts/catalogue_json_build.py`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- [Work And Series Prose Source Model Request](/docs/?scope=studio&doc=site-request-work-series-prose-source-model)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)

## [2026-04-26] Renamed Docs Import Route and Cleaned Dashboard Panels

**Status:** implemented

**Area:** Studio / dashboards

**Summary:**
Renamed the shared docs HTML import page from `/studio/library-import/` to `/studio/docs-import/`, then updated Analytics and Library dashboard panels to enter that page with scope-specific defaults.

**Reason:**
The import workflow now supports Library, Analysis, and Studio docs, so the route should not imply that it belongs only to Library. The Analytics dashboard also had too many equal-weight tag panels for one related maintenance cluster.

**Effect:**
Analytics now has an import panel that opens `/studio/docs-import/?scope=analysis`, a single Tag tools panel with plain links to the four tag pages, and the existing Analytics plan panel. Library now opens `/studio/docs-import/?scope=library`, and its Import copy no longer mentions Studio scope selection. The old `/studio/library-import/` route is removed.

**Affected files/docs:**

- `studio/docs-import/index.md`
- `studio/analytics/index.md`
- `studio/library/index.md`
- `assets/studio/js/studio-config.js`
- `assets/studio/data/studio_config.json`
- [Docs HTML Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio](/docs/?scope=studio&doc=studio)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-26] Added Analysis to Docs HTML Import

**Status:** implemented

**Area:** Studio / Docs Viewer

**Summary:**
Extended `/studio/docs-import/` so staged HTML imports can target the `analysis` docs scope as well as `library` and `studio`.

**Reason:**
The public `/analysis/` viewer already has generated docs and search artifacts, but the Studio import page still filtered valid `analysis` selections out of the workflow.

**Effect:**
The import page now preserves `?scope=analysis`, posts `analysis` to the docs-management server, and links import results to `/analysis/?doc=<doc_id>&mode=manage`. New Analysis imports use the same review-first visibility default as Library imports.

**Affected files/docs:**

- `assets/studio/js/docs-html-import.js`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_html_import.py`
- `scripts/docs/docs_management_server.py`
- [Docs HTML Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-26] Added the public Analysis docs viewer

**Status:** implemented

**Area:** Docs Viewer / Analysis

**Summary:**
Added a public `/analysis/` docs viewer backed by a new `analysis` docs scope, generated Analysis docs payloads, and an inline Analysis search artifact.

**Reason:**
Analysis needs a concrete public-facing document surface for portfolio interpretation, series/work analysis, tags, dimensions, and LLM-assisted review output without mixing that material into Library or Studio docs.

**Effect:**
The public nav now orders the main content surfaces as `works`, `analysis`, and `library`. Analysis source docs live under `_docs_src_analysis/`, with nested `series/` and `works/` folders reserved for future ID-addressable content such as `series-001` and `work-00008`. Viewer organisation still comes from `doc_id`, `parent_id`, and `sort_order`.

**Affected files/docs:**

- `analysis/index.md`
- `_docs_src_analysis/`
- `scripts/build_docs.rb`
- `scripts/build_search.rb`
- `scripts/search/build_config.json`
- `scripts/docs/docs_management_server.py`
- `scripts/docs/docs_live_rebuild_watcher.py`
- `_layouts/default.html`
- [Analysis Docs Viewer Request](/docs/?scope=studio&doc=site-request-analysis-doc-viewer)
- [Analysis Scope](/docs/?scope=studio&doc=data-models-analysis)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)

## [2026-04-26] Added the Studio list primitive catalogue page

**Status:** implemented

**Area:** Studio UI / design system

**Summary:**
Added a published list primitive page to the Studio UI catalogue covering simple, sortable, and thumbnail list versions, then tightened the contract for width, column sizing, row alignment, links, and primitive text scale.

**Reason:**
Studio already had shared `tagStudioList__*` shell classes, but the reusable list contract was not visible as a live primitive. Defining the versions first gives future list mapping and cleanup work a clearer baseline.

**Effect:**
The UI catalogue now links to `/studio/ui-catalogue/list/`, the shared list documentation names common cell, link, row-alignment, sort-indicator, width-wrapper, and thumbnail pieces, and the docs viewer explains when to use simple, sortable, or thumbnail list variants.

**Affected files/docs:**

- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- `studio/ui-catalogue/list/index.md`
- `_includes/studio_ui_catalogue_list_demo.html`
- `_includes/ui_catalogue_notes/list.md`
- `assets/studio/css/studio.css`

## [2026-04-25] Hid Library document updated dates through docs scope options

**Status:** implemented

**Area:** Docs Viewer / Library

**Summary:**
Added a generated docs-viewer scope option for document-view updated-date display, and disabled that row for Library while keeping it visible for Studio Docs.

**Reason:**
Library reading pages should stay cleaner and less operational than Studio Docs. The existing scope-option model already handles Library-specific viewer behavior without hard-coding scope checks in the shared runtime.

**Effect:**
`scripts/build_docs.rb` now emits `viewer_options.show_updated_date`. Studio sets it to `true`; Library sets it to `false`. The shared viewer hides only the document metadata-row `Updated ...` text when the option is false. Recently-added still uses `added_date`, and docs search still uses `last_updated`.

**Affected files/docs:**

- `scripts/build_docs.rb`
- `assets/js/docs-viewer.js`
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Shared Patterns](/docs/?scope=studio&doc=data-models-shared)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)

## [2026-04-25] Made Library Archive manage-only through docs scope options

**Status:** implemented

**Area:** Docs Viewer / docs scopes

**Summary:**
Added generated docs-viewer scope options so structural docs branches can be non-loadable or manage-only without hard-coding scope checks in the shared viewer.

**Reason:**
Studio Archive and Library Archive have different product intent. Studio Archive is useful public reference material for completed planning docs, deprecated guidance, and decision history. Library Archive has minimal public-facing use and should be available mainly for local management.

**Effect:**
`scripts/build_docs.rb` now emits `viewer_options` in each docs index. Studio marks `_archive` as non-loadable but keeps it visible. Library marks `_archive` as both non-loadable and manage-only, so `/library/` hides Archive and descendants unless `mode=manage` is active. The shared viewer consumes the generated options generically, and docs search applies the same manage-only tree filtering.

**Affected files/docs:**

- `scripts/build_docs.rb`
- `assets/js/docs-viewer.js`
- `scripts/build_search.rb`
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Shared Patterns](/docs/?scope=studio&doc=data-models-shared)
- [Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)

## [2026-04-25] Autolinked plain-text URLs during docs HTML import

**Status:** implemented

**Area:** Studio / docs viewer / docs HTML import

**Summary:**
Updated the docs HTML importer so plain-text `http://` and `https://` URLs in imported prose become Markdown autolinks.

**Reason:**
Some imported reference sections contain bare source URLs rather than `<a href>` elements. Keeping those as plain text made the resulting Library docs less useful even though the URLs were valid external references.

**Effect:**
Future HTML imports convert bare prose URLs to clickable Markdown autolinks while preserving existing anchor conversion and leaving code/preformatted text alone.

**Affected files/docs:**

- `scripts/docs/docs_html_import.py`
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs HTML Import](/docs/?scope=studio&doc=user-guide-docs-html-import)

## [2026-04-25] Improved no-context work-page back links

**Status:** implemented

**Area:** work pages / navigation

**Summary:**
Changed work pages opened without URL return context to prefer the work's primary series for the back link.

**Reason:**
Search result links now open works in a new tab. In that no-context entry case, the previous fallback back link went to the general works index, which was less useful than moving into the work's related series.

**Effect:**
Explicit return contexts still win: `?series=...`, recently added, public work index, and Studio work index return links keep their existing behavior. When no return context is present and the work has a resolvable primary series, the back link becomes `← <series title>` and points to that series page. If metadata or series lookup fails, the link keeps the existing `← works` fallback.

**Affected files/docs:**

- `assets/js/work.js`
- [Data Flow](/docs/?scope=studio&doc=data-flow)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Search UI Behaviour](/docs/?scope=studio&doc=search-ui-behaviour)

## [2026-04-25] Suppressed benign WEBrick client-reset noise in dev Studio

**Status:** implemented

**Area:** local development workflow / `bin/dev-studio`

**Summary:**
Filtered expected `Errno::ECONNRESET` messages from the Jekyll WEBrick server when it is launched by `bin/dev-studio`.

**Reason:**
During local rebuilds, refreshes, or cancelled asset loads, browsers can close a socket while WEBrick is still reading it. WEBrick logs that as an error-level stack trace, which made normal docs-watch and Jekyll regeneration cycles noisy even when the viewer was functioning correctly.

**Effect:**
`bin/dev-studio` now starts Jekyll with a narrow Ruby preload that suppresses only WEBrick `Errno::ECONNRESET` logger calls. Other WEBrick errors, Jekyll build warnings, and docs watcher output remain visible. Plain `bundle exec jekyll serve` is unchanged.

**Affected files/docs:**

- `bin/dev-studio`
- `scripts/jekyll_webrick_client_reset_filter.rb`
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)

## [2026-04-25] Normalized Docs Viewer drag reorder sort orders

**Status:** implemented

**Area:** Docs Viewer / docs management

**Summary:**
Made drag/drop reorder normalize destination sibling sort orders and made move Undo restore every touched placement record.

**Reason:**
Duplicate sibling `sort_order` values could make a drag/drop reorder appear to fail: the write succeeded, but the generated tree still had no unique ordering basis for the requested placement.

**Effect:**
After a successful drag/drop move, the docs-management server rewrites the destination sibling set to sparse unique `sort_order` values. The move response returns all prior placements touched by that normalization, and the index Undo action restores those records through a bulk restore endpoint. Search updates remain targeted because sibling sort-order normalization does not require a full search rebuild.

**Affected files/docs:**

- `assets/js/docs-viewer.js`
- `scripts/docs/docs_management_server.py`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-25] Refined Docs Viewer drag placement and manage startup probing

**Status:** implemented

**Area:** Docs Viewer / docs management

**Summary:**
Made manage-mode drag/drop placement easier to read and made server capability detection tolerate dev-server startup timing.

**Reason:**
The previous "move after" zone was a narrow lower-edge target with only a subtle row shadow, which made accidental child moves too easy. The viewer also checked docs-management capabilities only once, so loading manage mode before the local server was ready could leave drag/drop unavailable until refresh.

**Effect:**
The upper half of a docs-tree row now means "move inside"; the lower half means "move after" and renders a visible insert line after the target row. Drop handling uses the last highlighted target as a fallback when the final drop event cannot resolve a row cleanly. Manage-mode capability probing retries briefly before failing closed, and stale retry attempts cannot overwrite a newer successful capability check.

**Affected files/docs:**

- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-25] Added Docs Viewer move Undo and empty-node drops

**Status:** implemented

**Area:** Docs Viewer / docs management

**Summary:**
Refined manage-mode docs-tree drag/drop so any node can receive children and added a one-step Undo for the latest successful move.

**Reason:**
The previous drag/drop rule only allowed "drop inside" for collapsed nodes with existing children. Empty grouping nodes, including Archive, therefore could not receive their first child from the viewer.

**Effect:**
In manage mode, the upper/main part of a docs-tree row moves the dragged leaf doc inside that node, while the lower edge moves it after the node. There is no `folder` source or generated schema field; parent capability remains a viewer interaction concept. A new icon-only Undo control in the index toolbar restores the previous `parent_id` and `sort_order` for the most recent successful move in the current viewer session. Metadata-modal parent changes now append the doc under the new parent when the `sort_order` field is left unchanged.

**Affected files/docs:**

- `_includes/docs_viewer_shell.html`
- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`
- `scripts/docs/docs_management_server.py`
- [Docs Viewer Index Drag Undo Task](/docs/?scope=studio&doc=ui-request-docs-viewer-index-drag-undo-task)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)

## [2026-04-24] Added Docs Viewer viewability workflow

**Status:** implemented

**Area:** Docs Viewer / docs management

**Summary:**
Added a separate `viewable` docs flag so generated docs can be hidden from the public/default Docs Viewer while remaining reviewable in manage mode.

**Reason:**
Bulk Library imports need to enter the generated docs system without immediately appearing as a long unstructured public root list. The existing `published` flag already means pipeline inclusion, so public visibility needed a separate field.

**Effect:**
Generated docs indexes and per-doc payloads now include `published` and `viewable`. Public/default Docs Viewer trees, recently-added lists, and direct doc routing use viewable docs only. Manage mode has a `drafts` checkbox that adds non-viewable docs to the tree while retaining visible docs for context, plus a bulk-backed `Make viewable` action for a selected draft. That action prompts before making required non-viewable ancestors or optional descendants viewable, then writes the affected docs and runs one same-scope docs/search rebuild. Library create/import defaults to `published: true`, `viewable: false`; Studio create/import defaults to `published: true`, `viewable: true`.

**Affected files/docs:**

- `scripts/build_docs.rb`
- `scripts/docs/docs_management_server.py`
- `_includes/docs_viewer_shell.html`
- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`
- [Viewability Workflow Spec](/docs/?scope=studio&doc=docs-viewer-draft-publishing-spec)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Data Models: Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Data Models: Library Scope](/docs/?scope=studio&doc=data-models-library)

## [2026-04-24] Added desktop Docs Viewer index collapse

**Status:** implemented

**Area:** Docs Viewer

**Summary:**
Added a shared desktop/tablet collapse control for the Docs Viewer index panel.

**Reason:**
Longer Library docs needed more available reading width while keeping the index panel discoverable and easy to restore.

**Effect:**
The shared Docs Viewer now shows a small index-panel toggle on non-mobile layouts. Collapsing the panel shrinks the left column to a narrow rail, hides the tree, widens the capped Docs Viewer reading measure, and leaves the control visible for expansion. The document metadata path now shows ancestor docs only instead of repeating the current title above the H1. The collapsed state is stored per viewer scope. Mobile keeps the existing stacked layout and does not show the control.

**Affected files/docs:**

- `_includes/docs_viewer_shell.html`
- `assets/css/main.css`
- `assets/js/docs-viewer.js`
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)

## [2026-04-24] Added generated `added_date` metadata for docs scopes

**Status:** implemented

**Area:** Docs Viewer / docs data model

**Summary:**
Added `added_date` as generated docs metadata for all docs scopes and backfilled existing published docs from their current `last_updated` values.

**Reason:**
The recently-added list needed a stable date field that reflects when a doc entered the corpus. Reusing `last_updated` would make ordinary metadata/content edits reorder older docs as if they had just been added.

**Effect:**
Generated docs indexes and per-doc payloads now include `added_date`. New docs and new HTML imports write both `added_date` and `last_updated`, while overwrite, metadata, move, and archive flows preserve `added_date`. The recently-added list now sorts and displays from `added_date`; doc view metadata and docs search continue to use `last_updated`.

**Affected files/docs:**

- `scripts/build_docs.rb`
- `scripts/docs/docs_management_server.py`
- `assets/js/docs-viewer.js`
- `_docs_src/*.md`
- `_docs_library_src/*.md`
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Data Models: Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Data Models: Library Scope](/docs/?scope=studio&doc=data-models-library)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

## [2026-04-24] Added shared Docs Viewer recently-added results

**Status:** implemented

**Area:** Docs Viewer / Library / Studio docs

**Summary:**
Added a shared recently-added control to the Docs Viewer search row and aligned Docs Viewer result metadata across `/docs/` and `/library/`.

**Reason:**
The Library viewer needed a quick way to show the most recently updated Library docs, and its search results were showing `doc_id` where the Studio docs viewer already used the more useful `date • parent` pattern.

**Effect:**
The shared Docs Viewer now shows a `recently added` button beside inline search on both `/docs/` and `/library/`. The list is capped by `docs_viewer.recently_added_limit` in `studio_config.json`, sorted by `last_updated` descending then title ascending, and renders title plus `date` or `date • parent`. Search results use the same visible metadata pattern and no longer show `doc_id` as a separate line.

**Notes:**
The recently-added list currently uses `last_updated`; a future schema task should add a true added/published date.

**Affected files/docs:**

- `_includes/docs_viewer_shell.html`
- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)

## [2026-04-24] Opened Studio-originated Library viewer links in manage mode

**Status:** implemented

**Area:** Studio / Library / docs viewer management

**Summary:**
Changed Studio-originated Library viewer links so they open `/library/` with `mode=manage`.

**Reason:**
Links from the Library dashboard and from Docs HTML Import completion are admin workflow links, not public navigation. Opening the read-only Library viewer forced an extra manual URL edit before source-management controls were available.

**Effect:**
The Studio Library dashboard now opens the Library viewer at `/library/?mode=manage`, and Library-scope import results now open the imported doc at `/library/?doc=<doc_id>&mode=manage`. Public Library links outside Studio remain unchanged.

**Affected files/docs:**

- `studio/library/index.md`
- `scripts/docs/docs_management_server.py`
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-24] Escaped source-text pipes during docs HTML import

**Status:** implemented

**Area:** Studio / docs viewer / docs HTML import

**Summary:**
Updated the docs HTML importer so literal pipe characters from source text are escaped in generated Markdown.

**Reason:**
Kramdown can interpret ordinary lines containing `|` as Markdown tables, including blockquotes and list items. Imported mathematical expressions such as `I(X;Y|Z)` and `I(... | access)` were therefore rendering as accidental one-row tables instead of inline notation.

**Effect:**
Future HTML imports preserve source-text pipe characters as visible text while keeping importer-generated Markdown table delimiters for actual source `<table>` elements. This protects formulas and other technical notation from accidental table parsing.

**Affected files/docs:**

- `scripts/docs/docs_html_import.py`
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs HTML Import](/docs/?scope=studio&doc=user-guide-docs-html-import)

## [2026-04-24] Excluded local docs runtime state from Jekyll watch input

**Status:** implemented

**Area:** Studio / docs viewer / local runtime

**Summary:**
Excluded `var/` from Jekyll so local docs-management runtime files no longer trigger `jekyll serve` regeneration events.

**Reason:**
Docs-management writes create short-lived watcher-suppression markers under `var/docs/watch-suppressions/`. During local imports, the docs live watcher can remove a completed marker before Jekyll's own file watcher stats it, causing a noisy `No such file or directory @ rb_file_s_stat` message even though the docs write and same-scope rebuild succeeded.

**Effect:**
Local backups, staged imports, logs, and watcher-suppression markers under `var/docs/` remain available to Studio tooling but are no longer treated as Jekyll site input. This keeps `jekyll serve` focused on publishable source files and avoids transient file-watch races from local operational state.

**Affected files/docs:**

- `_config.yml`
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)

## [2026-04-23] Suppressed duplicate docs watcher rebuilds after localhost docs-management writes

**Status:** implemented

**Area:** Studio / docs viewer / local runtime

**Summary:**
Added short-lived watcher-suppression coordination between the localhost Docs Management Server and the Docs Live Rebuild Watcher so successful source writes no longer trigger an immediate redundant second same-scope rebuild while `bin/dev-studio` is running.

**Reason:**
Docs-management writes already rebuild same-scope docs payloads and docs search directly. With the live watcher running under `bin/dev-studio`, the same `_docs_src/*.md` or `_docs_library_src/*.md` source change was then detected again and rebuilt a second time, which made one import or manage-mode write feel much slower than the actual write itself.

**Effect:**
Successful docs-management source writes now leave a short-lived suppression marker under `var/docs/watch-suppressions/` before and after the server rebuild. The watcher recognizes those markers, waits while the server-owned rebuild is pending, and skips its own duplicate pass once the server marks the write complete. This keeps immediate write-time rebuild correctness in the server path while removing the redundant watcher rebuild for the same file change.

**Affected files/docs:**

- `scripts/docs/docs_watch_suppression.py`
- `scripts/docs/docs_management_server.py`
- `scripts/docs/docs_live_rebuild_watcher.py`
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)

## [2026-04-23] Added a Library-facing Studio HTML import page and user guide

**Status:** implemented

**Area:** Studio / docs viewer

**Summary:**
Added `/studio/docs-import/` as the user-facing Studio page for staged docs HTML import, linked it from the Library dashboard, removed the stale broken Library docs dashboard panel, and added a matching User Guide page for the workflow.

**Reason:**
The server-side import contract was in place, but the workflow still had no actual Studio surface. The Library dashboard was also carrying a dead `Library docs` panel after docs reorganization, and its middle panel still pointed to an older planning stub instead of the new import tool.

**Effect:**
The Library dashboard now links directly to `Import`, the broken `Library docs` panel is gone, and `/studio/docs-import/` lets the user choose a staged HTML file, pick a docs scope, decide whether to keep prompt/meta blocks, and complete create-or-warned-overwrite imports through the localhost docs-management service. The page uses config-backed copy, reports result metadata and warnings, and links back to the imported viewer doc. The `i` link on the new page points to a practical User Guide doc rather than the lower-level implementation spec.

**Affected files/docs:**
- `studio/library/index.md`
- `studio/docs-import/index.md`
- `assets/studio/js/docs-html-import.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/css/studio.css`
- `scripts/docs/docs_management_server.py`
- `scripts/docs/docs_html_import.py`
- [Studio](/docs/?scope=studio&doc=studio)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [User Guide](/docs/?scope=studio&doc=user-guide)
- [Docs HTML Import](/docs/?scope=studio&doc=user-guide-docs-html-import)

## [2026-04-23] Extended docs HTML import from preview-only into create and warned-overwrite writes

**Status:** implemented

**Area:** docs viewer / local docs-management

**Summary:**
Extended `POST /docs/import-html` on the localhost Docs Management Server so staged HTML import now supports real create writes plus explicit warned overwrite of an existing source doc, while validating generated Markdown through the repo's Jekyll renderer before success.

**Reason:**
The preview-only import path was enough to settle the parser and conversion contract, but it was not enough to begin real iterative use. The import flow needed an actual write path so repeated staged-file tests can create new docs, overwrite an existing target by `doc_id`, and keep backups/rebuilds inside the established docs-management boundary.

**Effect:**
`POST /docs/import-html` now creates a new source Markdown doc immediately when the generated import target is free, and returns a clear overwrite-required response when that target already exists. Overwrite now requires `overwrite_doc_id` plus `confirm_overwrite: true`, preserves the existing doc's identity and placement, writes a light-touch same-day backup under `var/docs/backups/`, and rebuilds the same-scope docs payloads plus docs search after a successful write. Generated import Markdown is also validated through the repo's Jekyll renderer helper before any write succeeds.

**Affected files/docs:**
- `scripts/docs/docs_html_import.py`
- `scripts/docs/docs_management_server.py`
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs HTML Import Task](/docs/?scope=studio&doc=ui-request-docs-html-import-task)

## [2026-04-23] Added a Studio docs broken-links audit page and shared read-only docs audit endpoint

**Status:** implemented

**Area:** docs viewer / Studio

**Summary:**
Added `/studio/docs-broken-links/`, a reusable Python docs-links audit, and a new read-only docs-management endpoint so Studio can run a strict docs broken-links check for either the `studio` or `library` docs scope.

**Reason:**
Docs maintenance needed a practical Studio surface for two concrete failure cases: links to docs that no longer exist and links whose visible text no longer matches the current target doc title. The repo also needed that logic outside the browser so the same check can be reused from the terminal.

**Effect:**
Studio now has a dedicated docs broken-links page with scope selection and a results list linking directly to the target and source pages. The audit reports `not found` and strict `wrong title` issues, including intentionally shortened labels that no longer match the target doc title exactly. The same logic now lives in `./scripts/docs/docs_broken_links.py` and is exposed through `POST /docs/broken-links` on the localhost docs-management service. Same-doc fragment links are ignored because they do not affect page-level docs structure, and archived deprecated docs no longer carry `Deprecated: ` in front-matter titles.

**Affected files/docs:**
- `studio/docs-broken-links/index.md`
- `assets/studio/js/docs-broken-links.js`
- `assets/studio/js/studio-transport.js`
- `assets/studio/js/studio-config.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/css/studio.css`
- `scripts/docs/docs_broken_links.py`
- `scripts/docs/docs_management_server.py`
- [Docs Broken Links](/docs/?scope=studio&doc=docs-broken-links)
- [Docs Broken Links Audit](/docs/?scope=studio&doc=scripts-docs-broken-links)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

## [2026-04-23] Added a User Guide section and moved docs image usage guidance into a practical how-to doc

**Status:** implemented

**Area:** docs viewer / docs authoring

**Summary:**
Added a top-level `User Guide` section for practical task-focused documentation and introduced a dedicated docs-images guide that explains the three supported docs image paths with concrete copy-paste examples.

**Reason:**
Some existing docs mixed user-facing author guidance with technical implementation reference. The docs image flow exposed that problem clearly because the real <code>&#91;&#91;media:...&#93;&#93;</code> authoring syntax was only documented inside a builder reference page.

**Effect:**
Docs now have a clearer split between practical usage guidance and technical contracts. The new guide tells authors where to save repo-local docs images, when to use <code>&#91;&#91;media:...&#93;&#93;</code>, and when inline HTML/CSS/SVG is the better fit, while the builder doc stays focused on implementation behavior.

**Affected files/docs:**
- `_docs_src/user-guide.md`
- `_docs_src/user-guide-docs-images.md`
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)

## [2026-04-22] Closed the catalogue lookup invalidation request with an in-code registry decision

**Status:** implemented

**Area:** catalogue write server / catalogue lookup

**Summary:**
Closed the catalogue lookup invalidation request by explicitly keeping the invalidation registry in write-server code rather than moving it into JSON/config.

**Reason:**
The registry currently has one real consumer, and the remaining fallback rules are still operational rather than purely declarative. Externalizing now would add config schema and indirection without a clear payoff.

**Effect:**
The in-code registry is now the explicit canonical contract for catalogue lookup invalidation. JSON/config externalization is deferred unless a second consumer appears, such as a validation tool, reporting surface, or shared runtime outside the write server.

**Affected files/docs:**
- `_docs_src/site-request-catalogue-lookup-invalidation.md`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

## [2026-04-22] Extended targeted lookup refresh to detail, file, link, and series saves

**Status:** implemented

**Area:** catalogue write server / catalogue lookup

**Summary:**
Extended the incremental lookup-refresh rollout beyond work saves so detail, file, link, and series save handlers now use focused targeted refresh paths where their dependency sets are explicit.

**Reason:**
These record families turned out to be simpler than the initial work dependency graph. Detail, file, and link saves only affect their own lookup payload plus a small parent-work surface, and series saves have no parent chain, so the next extension pass was low-risk and high-yield.

**Effect:**
`POST /catalogue/work-detail/save`, `POST /catalogue/work-file/save`, `POST /catalogue/work-link/save`, and `POST /catalogue/series/save` now return `lookup_refresh` metadata and avoid full lookup refresh for the straightforward targeted cases. Parent/id move-style cases such as `work_file.work_id` changes still fall back to `full`.

**Affected files/docs:**
- `scripts/catalogue_lookup.py`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Lookup Invalidation Request](/docs/?scope=studio&doc=site-request-catalogue-lookup-invalidation)

## [2026-04-22] Expanded the live work-save lookup refresh path to targeted multi-record updates

**Status:** implemented

**Area:** catalogue write server / catalogue lookup

**Summary:**
Extended the first live incremental lookup-refresh rollout so `POST /catalogue/work/save` now handles both locked `single-record` work fields and mapped `targeted-multi-record` work fields without dropping back to a full lookup rewrite.

**Reason:**
The first narrow rollout for simple work-only fields was stable. The next useful step was to use the already-mapped dependency registry to update the focused search, series, detail, and file lookup payloads needed for broader work edits such as `title` and `series_ids`.

**Effect:**
Work `title`, `year_display`, `status`, and `series_ids` changes now use targeted lookup writes instead of a full refresh. The lookup layer can now write focused work-search, series, detail, file, and link payloads, and work-save logs/responses now expose the chosen mode and targeted artifact set more clearly.

**Affected files/docs:**
- `scripts/catalogue_lookup.py`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Lookup Invalidation Request](/docs/?scope=studio&doc=site-request-catalogue-lookup-invalidation)

## [2026-04-22] Landed the first live incremental catalogue lookup refresh path

**Status:** implemented

**Area:** catalogue write server / catalogue lookup

**Summary:**
Implemented the first live incremental lookup-refresh path so `POST /catalogue/work/save` now rewrites only the focused `works/<work_id>.json` lookup payload when the changed work fields stay inside the locked first-pass `single-record` set.

**Reason:**
The registry, dependency mapping, and first-phase scope were already locked. The next pragmatic step was to ship the narrowest trustworthy runtime behavior instead of leaving the whole feature in planning state.

**Effect:**
Simple work-source edits such as `notes`, dimensions, storage, and related work-only metadata no longer trigger a full lookup rewrite. Broader work changes and all other save kinds still fall back to full lookup refresh. The work-save response and logs now also expose the chosen lookup refresh mode.

**Affected files/docs:**
- `scripts/catalogue_lookup.py`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Lookup Invalidation Request](/docs/?scope=studio&doc=site-request-catalogue-lookup-invalidation)

## [2026-04-22] Locked the first live incremental scope for catalogue lookup invalidation

**Status:** implemented

**Area:** catalogue write server / lookup invalidation planning

**Summary:**
Locked the first live incremental invalidation slice so the initial runtime rollout will target only `POST /catalogue/work/save` and only work fields already classified as `single-record`.

**Reason:**
The registry and dependency mapping are now broad enough to support many future paths, but the first runtime rollout needs to stay narrow enough to trust. The safest first slice is the obvious local work-field edits that do not currently require search, series, or embedded child-summary updates.

**Effect:**
The request/docs now treat Task 3 as implemented and fix the first runtime scope to simple work-save fields such as `notes`, dimensions, storage, and related work-only metadata. Broader work fields plus detail/file/link/series/moment writes remain explicit later tasks rather than implicit part of the first live rollout.

**Affected files/docs:**
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Lookup Invalidation Request](/docs/?scope=studio&doc=site-request-catalogue-lookup-invalidation)

## [2026-04-22] Completed Task 2 dependency mapping for catalogue invalidation registries

**Status:** implemented

**Area:** catalogue write server / lookup invalidation planning

**Summary:**
Completed the current dependency-mapping pass for the invalidation registries by adding explicit detail, work-file, work-link, and series field mappings, and by tightening the earlier work and moment mappings to reflect the actual derived payloads they feed.

**Reason:**
Task 2 needed to move beyond the initial work/moment foundation and capture the current payload dependencies for every saveable catalogue record family. Without that, later incremental routing would still be based partly on intuition rather than the actual lookup/search builder outputs.

**Effect:**
The write server now contains explicit field-to-artifact mappings for work, detail, work-file, work-link, series, and moment records. Unknown fields still collapse to `full`, and runtime refresh behavior is still unchanged for now. The next task can route actual writes through this now-complete registry set instead of having to discover the dependency surface at the same time.

**Affected files/docs:**
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Lookup Invalidation Request](/docs/?scope=studio&doc=site-request-catalogue-lookup-invalidation)

## [2026-04-22] Expanded catalogue invalidation mapping to include moments

**Status:** implemented

**Area:** catalogue write server / lookup invalidation planning

**Summary:**
Extended the new invalidation-registry foundation so Task 2 now explicitly includes moment-derived catalogue artifacts as part of the dependency model, rather than treating moments as outside scope because they do not live under Studio catalogue lookup JSON.

**Reason:**
Moments are part of the public catalogue and already participate in catalogue search. They are also much simpler than works and series because they currently have no cross-record dependency graph, which makes them a good early fit for the explicit registry approach.

**Effect:**
The write server now contains an initial moment-field invalidation registry, and the request/docs now record that current moment dependencies are the focused moment JSON, `assets/data/moments_index.json`, and catalogue search entries built from that index. Runtime refresh behavior is still unchanged for now; this only extends the explicit dependency contract.

**Affected files/docs:**
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Lookup Invalidation Request](/docs/?scope=studio&doc=site-request-catalogue-lookup-invalidation)

## [2026-04-22] Added the first catalogue lookup invalidation registry foundation

**Status:** implemented

**Area:** catalogue write server / lookup invalidation planning

**Summary:**
Added the first explicit work-field invalidation registry to the catalogue write server and recorded the follow-on request/task structure for moving from full lookup refresh toward scoped invalidation.

**Reason:**
The current write server still refreshes the full lookup corpus after every successful save, which is safe but leaves obvious incremental wins unused. Before changing runtime behavior, the dependency contract needed one canonical registry in code rather than living only in prose notes.

**Effect:**
The write server now contains the first work-save invalidation registry plus an initial full-refresh fallback operation set. Runtime refresh behavior is unchanged for now: successful writes still use full lookup refresh until later tasks route work-save invalidation through the registry. The follow-on request now also records that any future move from code to JSON/config should happen only after the dependency model stabilizes.

**Affected files/docs:**
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Lookup Invalidation Request](/docs/?scope=studio&doc=site-request-catalogue-lookup-invalidation)

## [2026-04-22] Fixed the work editor so source-only fields reload from canonical work source

**Status:** implemented

**Area:** Studio catalogue work editor

**Summary:**
Updated `/studio/catalogue-work/` so editable work fields now reload from canonical `assets/studio/data/catalogue/works.json` records instead of being rehydrated only from the focused lookup payload under `assets/studio/data/catalogue_lookup/works/<work_id>.json`.

**Reason:**
The first Save plus Update rollout exposed a mismatch between source-editing state and generated lookup state. Source-only fields such as `notes` and `provenance` could disappear after save because the page was rebuilding its editable baseline from lookup JSON that exists to support preview and related-runtime context, not full source editing.

**Effect:**
The work editor now keeps a canonical source-record map in memory for single-record and bulk-edit baselines, computes stale-write hashes from the full source record, and still reloads the focused lookup payload only for detail/file/link lists, preview, and readiness context. End-to-end smoke testing confirmed both `Save` with deferred publication and fresh-page `Save` plus `Update site now` against the current catalogue write server implementation.

**Affected files/docs:**
- `assets/studio/js/catalogue-work-editor.js`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-22] Replaced top-level `Rebuild` actions in catalogue editors with `Save` plus optional `Update site now`

**Status:** implemented

**Area:** Studio catalogue editors / catalogue write server

**Summary:**
Updated the catalogue work, detail, file, link, and series editors so `Save` is now the single primary action, publication is controlled by an adjacent `Update site now` choice, and any deferred publication is surfaced as a smaller follow-up action near the runtime status.

**Reason:**
The meaningful product distinction was not “save vs rebuild”; it was “save source only vs save and publish now”. The older `Rebuild` label exposed internal mechanism in the main editor UI and made deferred draft workflows harder to explain.

**Effect:**
The catalogue save endpoints now accept optional `apply_build: true` and return nested build status rather than forcing the client to treat save and publication as unrelated requests. Single-record editors default `Update site now` on, while the bulk editors default it off. If publication fails after a successful save, the page now reports that partial outcome explicitly and leaves a follow-up `Update site now` action available.

**Affected files/docs:**
- `scripts/studio/catalogue_write_server.py`
- `studio/catalogue-work/index.md`
- `studio/catalogue-work-detail/index.md`
- `studio/catalogue-work-file/index.md`
- `studio/catalogue-work-link/index.md`
- `studio/catalogue-series/index.md`
- `assets/studio/css/studio.css`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-work-file-editor.js`
- `assets/studio/js/catalogue-work-link-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Catalogue Work File Editor](/docs/?scope=studio&doc=catalogue-work-file-editor)
- [Catalogue Work Link Editor](/docs/?scope=studio&doc=catalogue-work-link-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-22] Made `dev-studio` startup docs rebuilds opt-in and added startup port preflight

**Status:** implemented

**Area:** local development workflow / `bin/dev-studio`

**Summary:**
Updated `bin/dev-studio` so startup docs/docs-search rebuilds are now opt-in by scope, and so the runner checks its required local ports before doing rebuild work or starting long-running services.

**Reason:**
The docs watcher is now the normal live-sync path while the runner is active, so unconditional startup docs rebuilds are no longer the right default for either docs scope. The runner also needed clearer operational failure behavior when an older local server was still holding one of the required ports.

**Effect:**
`bin/dev-studio` now accepts `DOCS_STARTUP_REBUILD_SCOPES` with `studio`, `library`, or `studio,library` when an explicit startup docs/docs-search refresh is wanted, and otherwise skips startup docs/docs-search rebuilds. It also checks the Jekyll, Tag Write Server, Catalogue Write Server, and Docs Management Server ports before rebuilds run, then exits early with a clear override hint if any of those ports are unavailable.

**Affected files/docs:**
- `bin/dev-studio`
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Build Incremental Request](/docs/?scope=studio&doc=site-request-docs-build-incremental)

## [2026-04-22] Made the reserved `_archive` docs node structural and non-loadable

**Status:** implemented

**Area:** docs viewer / docs build pipeline

**Summary:**
Updated the docs viewer so the reserved `_archive` node now behaves as a structural section only. Direct navigation to `_archive` now opens the first archived child doc instead of trying to load `_archive.json`.

**Reason:**
The docs-management contract already treats `_archive` as a protected reserved `doc_id`, but the generated payload path for that id becomes `_archive.json`. Jekyll does not reliably publish that leading-underscore asset under `_site`, which caused a viewer 404 when the Archive node itself was opened.

**Effect:**
The Archive row still exists in the tree and still owns archived children, but it is no longer treated as a normal loadable document target. Docs search also stops exposing `_archive` as a result because it is a structural node rather than a viewable content page. Empty Archive buckets now fall back to the scope's default doc instead of trying to load `_archive.json` through rendered viewer links.

**Rejected options:**
- renaming `_archive` to `archive`, because that would widen the change into the docs-management contract, archive API semantics, and existing source docs
- escaping the generated payload filename for `_archive`, because that would spread a one-off storage rule into the builder output contract instead of fixing the runtime meaning directly

**Affected files/docs:**
- `assets/js/docs-viewer.js`
- `scripts/build_search.rb`
- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)

## [2026-04-23] Added source-root docs watching to `bin/dev-studio`

**Status:** implemented

**Area:** docs build pipeline / local development workflow

**Summary:**
Updated `bin/dev-studio` so it now performs a startup `studio` docs-search rebuild and starts a local docs watcher that rebuilds same-scope docs payloads plus same-scope docs search while the dev runner is active.

**Reason:**
The preferred Task 7 direction was to treat `dev-studio` as the normal integrated local workflow, watch docs source roots rather than generated outputs, and keep docs-viewer data plus docs search aligned without depending on manual follow-up commands during ordinary editing.

**Effect:**
`bin/dev-studio` now starts with `studio` docs, `studio` docs search, and catalogue lookup fresh, then watches `_docs_src/*.md` as `studio` and `_docs_library_src/*.md` as `library`. Source changes are debounced, rebuild one scope at a time, and trigger one more pass if more source edits arrive during a rebuild. The watcher ignores generated outputs, so it does not loop on its own writes.

**Affected files/docs:**
- `bin/dev-studio`
- `scripts/docs/docs_live_rebuild_watcher.py`
- [Dev Studio Runner](/docs/?scope=studio&doc=scripts-dev-studio)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Build Incremental Request](/docs/?scope=studio&doc=site-request-docs-build-incremental)

## [2026-04-22] Aligned live docs-management writes with docs-search follow-through and deprecated legacy `/build-docs`

**Status:** implemented

**Area:** docs build pipeline / local development workflow

**Summary:**
Updated the local docs-management flow so successful docs-management writes now rebuild same-scope docs search consistently, and deprecated the older Studio tag-server `POST /build-docs` endpoint from the live docs workflow.

**Reason:**
After the docs payload builder became incremental and the main rebuild entrypoints became scope-explicit, the remaining inconsistency was search follow-through. Some live docs-management actions could still leave docs search stale, and the legacy tag-server rebuild path kept the workflow boundary ambiguous.

**Effect:**
Docs create, move, archive, delete, metadata edit, and explicit docs rebuild actions now keep the current scope's docs payloads and docs-search artifact aligned through the docs-management service. The legacy `POST /build-docs` path now returns a deprecation error instead of acting as a parallel live rebuild path.

**Affected files/docs:**
- `scripts/docs/docs_management_server.py`
- `scripts/studio/tag_write_server.py`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)
- [Docs Build Incremental Request](/docs/?scope=studio&doc=site-request-docs-build-incremental)

## [2026-04-21] Aligned local docs rebuild entrypoints to explicit scope behavior

**Status:** implemented

**Area:** docs build pipeline / local development workflow

**Summary:**
Updated the local docs rebuild entrypoints so Studio-local actions now rebuild `studio` explicitly instead of defaulting to hidden all-scope docs rebuilds.

**Reason:**
After separating the docs corpora conceptually and making payload writes incremental, the remaining all-scope local entrypoints were still obscuring which docs scope was actually being rebuilt. That made the workflow harder to reason about and undercut the goal of reducing rebuild churn.

**Effect:**
`bin/dev-studio` now rebuilds Studio docs only on startup, the legacy Studio `/build-docs` endpoint defaults to `scope: studio` and accepts an explicit scope, and docs-viewer manage-mode rebuilds now rebuild the current viewer scope plus that scope's docs search.

**Affected files/docs:**
- `bin/dev-studio`
- `scripts/studio/tag_write_server.py`
- `scripts/docs/docs_management_server.py`
- `assets/js/docs-viewer.js`
- `assets/studio/js/studio-transport.js`
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Docs Build Incremental Request](/docs/?scope=studio&doc=site-request-docs-build-incremental)

## [2026-04-21] Made docs payload writes incremental within each rebuilt scope

**Status:** implemented

**Area:** docs build pipeline / local development workflow

**Summary:**
Updated `scripts/build_docs.rb` so it now writes generated docs payloads incrementally within the rebuilt scope instead of deleting and recreating the full scope output tree on every write.

**Reason:**
The previous docs builder rewrote every generated docs JSON file for the selected scope, which made local Jekyll behave as if the whole docs corpus had changed even when only a small number of source docs were edited. That also made no-op rebuilds noisy and harder to interpret.

**Effect:**
Unchanged docs payloads are now skipped, changed payloads are rewritten, and stale per-doc payloads are removed when they no longer belong to the rebuilt scope. This reduces local watcher churn while preserving correct generated output for the docs viewer.

**Affected files/docs:**
- `scripts/build_docs.rb`
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)

## [2026-04-21] Added remediation and open-decision sections to Studio UI audits

**Status:** implemented

**Area:** Studio UI docs / audit workflow

**Summary:**
Updated the Studio UI conformance process so audit docs now explicitly carry `Remediation Status` and `Open Decisions` sections, and updated the first real audit doc to use that structure.

**Reason:**
The audit process could record findings and cleanup, but it did not yet make clear where post-audit remediation and unresolved decisions should live. Without that, important follow-up work could be buried or drift into the site change log.

**Effect:**
Studio audit docs are now explicitly living records until a page is settled. Post-audit remediation stays in the audit doc, the site change log remains reserved for implemented outcomes, and only genuinely shared design/spec questions should move into [UI Requests](/docs/?scope=studio&doc=ui-requests).

**Affected files/docs:**
- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [UI Audits](/docs/?scope=studio&doc=ui-audits)
- [UI Audit: Catalogue Moment Import (2026-04-21)](/docs/?scope=studio&doc=ui-audit-catalogue-moment-import-20260421)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-21] Lightened Studio default-text treatment for inputs

**Status:** implemented

**Area:** Studio UI / shared input contract

**Summary:**
Adjusted the shared Studio input styling so placeholder text, default-value displays, and disabled values now use a lighter dedicated default-text tone instead of the same muted color used for ordinary labels and helper text.

**Reason:**
Default text was too close in tone to entered content, especially on pages such as `/studio/catalogue-work/` where the work search placeholder sat beside native empty date fields whose browser-supplied date parts already appeared lighter.

**Effect:**
Search placeholders, file placeholders, disabled field values, and other default-value surfaces now read more clearly as unentered or unavailable state without washing out the normal muted label/meta layer.

**Affected files/docs:**
- `assets/studio/css/studio.css`
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-21] Clarified audit-outcome precedence for Studio UI conformance reviews

**Status:** implemented

**Area:** Studio UI docs / audit workflow

**Summary:**
Updated [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance) so `non-conforming` explicitly overrides `blocked by coverage gaps` whenever a page has a real covered-area standards failure.

**Reason:**
The conformance spec listed the available audit outcomes, but it did not explicitly define which outcome should win when a page had both real non-conformance and additional standards gaps. That ambiguity would have allowed inconsistent reporting.

**Effect:**
Studio page audits now have a clear outcome-precedence rule: report real covered-area failures as `non-conforming`, and report coverage gaps alongside them rather than using gaps to replace the result. `blocked by coverage gaps` is now reserved for coverage-only cases.

**Affected files/docs:**
- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-21] Added a root UI Audits section for conformance outputs

**Status:** implemented

**Area:** Studio UI docs / audit records

**Summary:**
Added a new root [UI Audits](/docs/?scope=studio&doc=ui-audits) section and a standard `ui-audit-<page-key>-<yyyymmdd>` naming convention for saved page-level UI conformance reviews.

**Reason:**
The new Studio UI conformance spec defined how page audits should be judged, but it did not yet define where those audit outputs should live. That would have left review results scattered or implicit.

**Effect:**
Formal Studio UI audit outputs now have a stable docs-viewer home, separate from [Site Change Log](/docs/?scope=studio&doc=site-change-log) implementation history and the shared standards docs. The main Design and Studio entry points now signpost both how to run an audit and where to save it.

**Affected files/docs:**
- [UI Audits](/docs/?scope=studio&doc=ui-audits)
- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [Design](/docs/?scope=studio&doc=design)
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Site Docs](/docs/?scope=studio&doc=site-docs)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-21] Added a Studio UI conformance spec

**Status:** implemented

**Area:** Studio UI docs / audit workflow

**Summary:**
Added [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance) so Studio page reviews now have an explicit audit contract covering authoritative sources, coverage states, finding categories, fixability, and cleanup reporting.

**Reason:**
The existing Studio UI docs were strong enough to guide implementation, but they did not yet make “check page X against full Studio design standards” a valid, repeatable audit. The missing piece was a conformance contract that distinguishes true non-conformance from coverage gaps and requires cleanup follow-up rather than stopping at the first visible fix.

**Effect:**
Studio UI work now has a dedicated page-level audit spec, and the main Design/Studio UI entry docs point to it directly. Reviewers can now report whether a page fully conforms, conforms only within covered scope, or is blocked by missing shared coverage, while also recording redundant code/CSS cleanup required after fixes.

**Affected files/docs:**
- [Studio UI Conformance Spec](/docs/?scope=studio&doc=studio-ui-conformance)
- [Design](/docs/?scope=studio&doc=design)
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)

## [2026-04-21] Standardized current-record panels on Readonly Display

**Status:** implemented

**Area:** Studio UI / catalogue editor family

**Summary:**
Updated the catalogue editor family so the info-only current-record panels now use the Readonly Display treatment instead of the older muted readonly surface, and applied the same treatment to the workbook path and preview-summary values on `/studio/bulk-add-work/`.

**Reason:**
Those panels are display-only by design, so the older `tagStudioForm__readonly` styling was no longer the right semantic or visual treatment. Keeping it in place also left avoidable styling and font-size drift between work/detail/file/link/series editors and the newer input primitive contract.

**Effect:**
The current-record sections on the work, work-detail, work-file, work-link, and series editors now present one consistent information-display style: bordered shells with transparent backgrounds and normal text color, while still preserving links and structured readiness content inside the same surfaces. The bulk import page now uses that same treatment for its workbook path and preview-summary values.

**Affected files/docs:**
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-work-detail-editor.js`
- `assets/studio/js/catalogue-work-file-editor.js`
- `assets/studio/js/catalogue-work-link-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
 - `assets/studio/js/bulk-add-work.js`
 - `studio/bulk-add-work/index.md`

## [2026-04-21] Clarified numeric field and label-alignment rules for Studio forms

**Status:** implemented

**Area:** Studio UI / shared form fields

**Summary:**
Updated the shared Studio form contract so numeric metadata fields now default to plain input boxes rather than native number widgets, and replaced the create/editor-family label-padding offset with an explicit centered-vs-top-aligned field-row rule.

**Reason:**
The earlier behavior was still letting storage type imply UI behavior. That was weak product guidance for Studio pages where numeric values are often just edited as plain text-box fields. The field-row label alignment also depended on local padding, which was visually fragile and did not state the real design rule clearly enough.

**Effect:**
The work/series editor family now keeps numeric fields visually plain unless a page explicitly needs step controls, and catalogue-style two-column form rows now center labels against single-line controls while leaving multiline rows top-aligned. The input primitive page now describes increment controls as opt-in rather than default numeric behavior.

**Affected files/docs:**
- [Input primitive page](/studio/ui-catalogue/input/)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `assets/studio/css/studio.css`
- `assets/studio/js/catalogue-new-work-editor.js`
- `assets/studio/js/catalogue-new-series-editor.js`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/js/catalogue-series-editor.js`
- `_includes/studio_ui_catalogue_input_demo.html`
- `_includes/ui_catalogue_notes/input.md`

## [2026-04-21] Added the Studio input primitive page

**Status:** implemented

**Area:** Studio UI / shared input primitive

**Summary:**
Published [Input primitive page](/studio/ui-catalogue/input/), added a shared `tagStudioField` composition layer for width and label layout, and documented both the disabled-vs-readonly-display split and the muted default-value treatment for field values.

**Reason:**
The UI catalogue already named `input` as a first-pass primitive, but there was no published reference page or shared field-composition contract. That left recurring decisions such as default width, fill behavior, label placement, dropdown reuse, stepped numeric adjustment, and always-readonly display at risk of drifting into route-local patterns.

**Effect:**
`/studio/ui-catalogue/input/` now gives the project one implementation reference for text fields, dropdowns, stepped numeric value assignment, readonly field display, and muted default-value states. The base `.tagStudio__input` class stays focused on the shared shell, while `tagStudioField` owns width, label, and add-on composition.

**Affected files/docs:**
- [Input primitive page](/studio/ui-catalogue/input/)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `assets/studio/css/studio.css`
- `studio/ui-catalogue/index.md`
- `_includes/studio_ui_catalogue_input_demo.html`
- `_includes/ui_catalogue_notes/input.md`

## [2026-04-20] Added a Studio UI preflight entry doc

**Status:** implemented

**Area:** Studio UI docs / implementation workflow

**Summary:**
Added [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start) as a short Studio UI landing/preflight doc, then updated the longer framework docs and `AGENTS.md` to point to it as the first stop for Studio UI work.

**Reason:**
Recent Studio UI work exposed that the longer framework docs are useful as reference but weak as an operational entry point. Important implementation checks such as primitive reuse, config-backed copy, local-vs-systemic triage, and close-out steps were present in the docs set but not prominent enough at the moment of implementation.

**Effect:**
Studio UI work now has a short checklist-style entry doc that can be given to Codex directly, while the longer framework docs remain detailed reference material rather than the first place a task has to start.

**Affected files/docs:**
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Design](/docs/?scope=studio&doc=design)
- [Studio](/docs/?scope=studio&doc=studio)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- `AGENTS.md`

## [2026-04-20] Config-backed the bulk import action buttons

**Status:** implemented

**Area:** Studio / bulk import / command buttons

**Summary:**
Added the missing `ui_text.bulk_add_work` block so the bulk import page now sources its visible runtime copy from config, and shortened the action buttons to `Preview` and `Import` with the shared default width.

**Reason:**
The page runtime was already using `getStudioText` for `bulk_add_work.*`, but there was no matching config block, so the visible copy was still coming from fallback strings. The buttons also lagged behind the current width contract.

**Effect:**
`/studio/bulk-add-work/` now renders its visible runtime copy from config, and the `Preview` / `Import` buttons use the standard width.

**Affected files/docs:**
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/bulk-add-work/index.md`
- `assets/studio/js/bulk-add-work.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`

## [2026-04-20] Standardized the Studio create-page buttons

**Status:** implemented

**Area:** Studio / create editors / command buttons

**Summary:**
Standardized the five Studio create pages so their primary action now reads `Create`, uses the shared default width, and resolves from config rather than from older runtime fallback text.

**Reason:**
The create-page family had drifted into a mix of `Create Draft …` labels, and the new work-file/new work-link pages were still missing the `ui_text` config blocks that their runtimes already expected.

**Effect:**
`/studio/catalogue-new-work/`, `/studio/catalogue-new-work-detail/`, `/studio/catalogue-new-work-file/`, `/studio/catalogue-new-work-link/`, and `/studio/catalogue-new-series/` now all show a standard-width `Create` button, with config-backed label support across the whole set.

**Affected files/docs:**
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/catalogue-new-work/index.md`
- `studio/catalogue-new-work-detail/index.md`
- `studio/catalogue-new-work-file/index.md`
- `studio/catalogue-new-work-link/index.md`
- `studio/catalogue-new-series/index.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/js/catalogue-new-work-editor.js`
- `assets/studio/js/catalogue-new-work-detail-editor.js`
- `assets/studio/js/catalogue-new-work-file-editor.js`
- `assets/studio/js/catalogue-new-work-link-editor.js`
- `assets/studio/js/catalogue-new-series-editor.js`

## [2026-04-20] Simplified the series member-work section

**Status:** implemented

**Area:** Studio / series editor / member works

**Summary:**
Removed the redundant `Open work` action from member rows, shortened `Add Work` to `Add`, moved the member search below the section heading, and only show that search when the capped member list is actually truncated.

**Reason:**
The section was duplicating both its heading and its navigation affordance, and it was showing a search field even when the on-page list was already complete. The membership controls also needed to align more closely with the current small-button/default-width rule.

**Effect:**
`/studio/catalogue-series/` now uses a single `member works` heading, the `work_id` link is the only navigation affordance to the work editor, `Add` and `Remove` use the shared default width, and the member search only appears when the list exceeds the visible cap.

**Affected files/docs:**
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/catalogue-series/index.md`
- `assets/studio/js/catalogue-series-editor.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/css/studio.css`

## [2026-04-20] Standardized the remaining catalogue editor action rows

**Status:** implemented

**Area:** Studio editor family / command buttons

**Summary:**
Applied the same `Open` / `Save` / `Rebuild` / `Delete` label and width cleanup to the work-file, work-link, and series editors, and updated their docs so the shorter labels still describe the current save/rebuild behavior clearly.

**Reason:**
Those editors share the same partial-page action-row pattern as the work and work-detail editors. Leaving the older first-pass labels in place would keep obvious drift inside one editor family even after the button contract had been clarified elsewhere.

**Effect:**
`/studio/catalogue-work-file/`, `/studio/catalogue-work-link/`, and `/studio/catalogue-series/` now use small standard-width buttons with the shorter labels, `Enter` in each search field still acts as an alternative to clicking `Open`, and the supporting docs now distinguish `Save` from `Rebuild` explicitly.

**Affected files/docs:**
- [Catalogue Work File Editor](/docs/?scope=studio&doc=catalogue-work-file-editor)
- [Catalogue Work Link Editor](/docs/?scope=studio&doc=catalogue-work-link-editor)
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/catalogue-work-file/index.md`
- `studio/catalogue-work-link/index.md`
- `studio/catalogue-series/index.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/js/catalogue-work-file-editor.js`
- `assets/studio/js/catalogue-work-link-editor.js`
- `assets/studio/js/catalogue-series-editor.js`

**Notes:**
This grouped pass is intentionally limited to the shared main action rows. The series page’s member-work controls remain separate and should be reviewed on their own terms later.

## [2026-04-20] Shortened and standardized the catalogue work-detail editor action buttons

**Status:** implemented

**Area:** Studio work-detail editor / command buttons

**Summary:**
Shortened the main action labels on `/studio/catalogue-work-detail/` to `Save`, `Rebuild`, and `Delete`, applied the standard default width to those actions plus `Open`, and clarified the save/rebuild behavior in the work-detail editor doc.

**Reason:**
The work-detail editor follows the same panel-level command pattern as the work editor, so its first-pass labels were unnecessarily long for the shared button contract. The shorter `Rebuild` label also needed explicit doc wording so its save-then-rebuild behavior stayed clear.

**Effect:**
The work-detail editor now uses the same small standard-width action row as the work editor, and the supporting doc distinguishes `Save` from `Rebuild` while noting that `Enter` in the search field is an alternative to clicking `Open`.

**Affected files/docs:**
- [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/catalogue-work-detail/index.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/js/catalogue-work-detail-editor.js`

**Notes:**
This keeps the work-detail editor aligned with the work editor button contract without assuming every other catalogue editor should be changed in the same way yet.

## [2026-04-20] Redesigned the catalogue work detail/file/link navigation headers

**Status:** implemented

**Area:** Studio work editor / navigation surfaces

**Summary:**
Moved the work-detail search below the `work details` heading and made it conditional on hidden rows, while changing the section entry actions to links: `new work detail →`, `new file →`, and `new link →`.

**Reason:**
These section actions are navigation, not commands, so button styling was misleading. The detail search box also added clutter when every detail row was already visible on the page.

**Effect:**
The `work details` header is cleaner, the search appears only when at least one grouped section exceeds the visible row limit, and the three `new` entry points now read as links rather than buttons. The related config keys were renamed from `*_button` to `*_link` to match that role change.

**Affected files/docs:**
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/catalogue-work/index.md`
- `assets/studio/js/catalogue-work-editor.js`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/css/studio.css`

**Notes:**
This is still a route-local navigation-link treatment. A later shared link primitive may absorb it, but the button-to-link boundary is now explicit on this page.

## [2026-04-20] Shortened and standardized the catalogue work editor action buttons

**Status:** implemented

**Area:** Studio work editor / command buttons

**Summary:**
Shortened the main action labels on `/studio/catalogue-work/` to `Save`, `Rebuild`, and `Delete`, applied the standard default width to those actions plus `Open`, and clarified the save/rebuild behavior in the work editor doc.

**Reason:**
The first-pass labels were functionally descriptive but too long for the new button contract. Once shortened, the doc also needed to say explicitly that `Rebuild` still saves current edits before running the scoped rebuild flow.

**Effect:**
The work editor’s main panel now uses small standard-width buttons consistently, and the supporting doc distinguishes `Save` from `Rebuild` more clearly. `Enter` in the search field still opens the current work selection, while `Open` remains an explicit button affordance.

**Affected files/docs:**
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/catalogue-work/index.md`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/js/catalogue-work-editor.js`

**Notes:**
This is a targeted cleanup for the work editor only. Similar label/width cleanup on other catalogue editors should be reviewed separately rather than assumed automatically.

## [2026-04-20] Moved button feedback to the local command area

**Status:** implemented

**Area:** design system / Studio command buttons

**Summary:**
Moved the series tag editor’s command feedback out of its distant shared message block and into a dedicated row directly below the `Add` / `Save` controls, then updated the button primitive page to make that placement rule explicit.

**Reason:**
Status and warning text for a button should read as part of the same command area. The earlier layout made the feedback feel detached from the related field and buttons, even though the bordered editor panel had room to expand and absorb the message naturally.

**Effect:**
`/studio/series-tag-editor/` now keeps `status`, `save warning`, and `save result` directly below the command row inside the editor panel, while the higher message section keeps only the broader context hint. The button primitive page now shows local feedback placement as part of the baseline command-button pattern.

**Affected files/docs:**
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/series-tag-editor/index.md`
- `assets/studio/css/studio.css`
- `studio/ui-catalogue/button/index.md`
- `_includes/studio_ui_catalogue_button_demo.html`
- `_includes/ui_catalogue_notes/button.md`

**Notes:**
This keeps the generic page context hint separate from local command feedback. Modal feedback should be reviewed later against the same adjacency rule.

## [2026-04-20] Applied the first live small-button field-row pattern

**Status:** implemented

**Area:** design system / Studio command buttons

**Summary:**
Updated the series tag editor so its input-adjacent `Add` and `Save` buttons adopt the small command-button pattern with shared default width, and revised the button primitive page so that same field-row pattern is shown explicitly.

**Reason:**
Buttons next to a field are the clearest real use case for the small button size. The primitive page needed that pattern made explicit, and the live page label `Save Tags` was longer than necessary for the shared width guidance.

**Effect:**
`/studio/series-tag-editor/` now uses `Add` and `Save` with the standard small/default-width button treatment, and the first button primitive example now shows the field-row use case rather than a standalone button.

**Affected files/docs:**
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/series-tag-editor/index.md`
- `studio/ui-catalogue/button/index.md`
- `_includes/studio_ui_catalogue_button_demo.html`
- `_includes/ui_catalogue_notes/button.md`

**Notes:**
This is the first live-page adoption of the new button contract. The wider button cleanup sweep can now use this field-row case as a reference.

## [2026-04-20] Refined the button primitive to a minimal command-only contract

**Status:** implemented

**Area:** design system / UI catalogue

**Summary:**
Refined the first button primitive page so it treats buttons as commands only, removes navigation-style and toolbar-forward examples, and introduces the initial two-size and standard-width contract without forcing a full live-page sweep yet.

**Reason:**
The initial draft was still too broad. The clearer design direction is to keep buttons minimal, separate them from links and pills, and postpone toolbar decisions until that primitive is defined explicitly.

**Effect:**
The button primitive page now focuses on small and medium command buttons, default-width behavior, modal default-action emphasis, destructive commands without special styling, and the explicit warning not to use panels as button-group boundaries.

**Affected files/docs:**
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/ui-catalogue/button/index.md`
- `_includes/studio_ui_catalogue_button_demo.html`
- `_includes/ui_catalogue_notes/button.md`
- `assets/studio/css/studio.css`

**Notes:**
This still leaves a later consistency sweep for existing pages that use anchor-styled command buttons or longer labels such as `Save Tags`.

## [2026-04-20] Added the first shared button primitive page

**Status:** implemented

**Area:** design system / UI catalogue

**Summary:**
Added `/studio/ui-catalogue/button/` as the first published reference page for shared command buttons, using the same page template approach as the panel primitive while keeping the scope focused on command actions rather than pills.

**Reason:**
Current Studio pages already share one baseline button class, but the product still mixes together command buttons, toolbar subsets, modal actions, and pill-like controls conceptually. The first pass needed to establish the role boundary before visual refinement.

**Effect:**
The new button primitive page established the first command-button scope and created a base page to refine further. The UI catalogue index now links to both the button and panel primitive pages.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/ui-catalogue/button/index.md`
- `_includes/studio_ui_catalogue_button_demo.html`
- `_includes/ui_catalogue_notes/button.md`
- `studio/ui-catalogue/index.md`

**Notes:**
This first draft was intentionally broad enough to expose drift. The later refinement on the same day narrowed it to a stricter command-only contract.

## [2026-04-20] Applied config-backed panel background images to the Studio landing page

**Status:** implemented

**Area:** design system / Studio landing page

**Summary:**
Assigned the new `01007` to `01010` image assets to the four `/studio/` landing panels and moved the chosen source-width decision into shared Jekyll data instead of embedding width-specific filenames directly in the page markup.

**Reason:**
The panel primitive owns image-fit behavior, but the chosen source image and width remain a design-time composition decision. That route-level choice needs to stay visible and adjustable rather than turning `800` into a hidden primitive default.

**Effect:**
`/studio/` now uses the image-fill panel-link variation for all four landing panels, and the selected background-image width is configured through `_data/studio_panel_images.json`.

**Affected files/docs:**
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- `_data/studio_panel_images.json`
- `studio/index.md`

**Notes:**
The chosen width is route data, not a primitive default. The data shape supports a route-wide default plus per-panel overrides, and the expected filename pattern is `{asset_id}-{variant}-{width}.{format}`.

## [2026-04-20] Split the image panel-link baseline from its contrast override

**Status:** implemented

**Area:** design system / primitive guidance

**Summary:**
Adjusted the shared image panel-link variation so it keeps the standard dark text by default, added an explicit contrast override for darker images, and created a dedicated Studio asset folder for design-time panel background images.

**Reason:**
The first image-panel demo had implicitly made white text look like the primitive default. That was inconsistent with the rest of the site and hid an important distinction between the base image-fill behavior and a common contrast override.

**Effect:**
`tagStudio__panelLink--image` now remains a neutral image-fill variation with centered `cover` behavior, `tagStudio__panelLink--imageContrast` is the explicit white-text override for darker images, the panel primitive page shows both code samples, and Studio background images now have a dedicated asset folder at `assets/studio/img/panel-backgrounds/`.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `assets/studio/css/studio.css`
- `assets/studio/img/panel-backgrounds/.gitkeep`
- `studio/ui-catalogue/panel/index.md`
- `_includes/studio_ui_catalogue_panel_demo.html`
- `_includes/ui_catalogue_notes/panel.md`

**Notes:**
Add real design-time image assets under `assets/studio/img/panel-backgrounds/` before adopting the image-panel variation on live Studio pages.

## [2026-04-20] Added design guidance to the panel primitive reference and refined the Studio landing composition

**Status:** implemented

**Area:** design system / primitive guidance

**Summary:**
Extended the panel primitive reference so it records design guidance as well as technical behavior, removed the hidden text-width cap from the shared panel-link copy, and narrowed the `/studio/` landing-page card grid so the short-copy entry panels sit in centered columns.

**Reason:**
The panel-link variation is a working design reference, not just a technical spec. The old text measure made the copy look like it was wrapping inside an invisible container, and the full-width equal-fill landing-page grid made short-copy cards feel too stretched.

**Effect:**
Panel-link copy now wraps to the panel width itself, the `/studio/` entry cards use a narrower centered composition, and the primitive docs now explicitly include design guidance where sizing and composition choices affect correct reuse.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `assets/studio/css/studio.css`
- `assets/css/main.css`

**Notes:**
This keeps the other dashboard routes on the shared fixed-height panel-link variation without redesigning their grid width.

## [2026-04-20] Unified Studio landing/dashboard cards as a shared panel-link variation

**Status:** implemented

**Area:** design system / Studio dashboard UI

**Summary:**
Moved the clickable Studio landing page and analytics/library/search dashboard card styling out of the site-wide stylesheet and into the shared Studio primitive layer as a fixed-height panel-link variation with optional image fill.

**Reason:**
The same panel design had split into two duplicated route-local patterns, and the analytics/library/search version was auto-sizing to content instead of behaving like a deliberate design-time panel.

**Effect:**
`/studio/`, `/studio/analytics/`, `/studio/library/`, and `/studio/search/` now use the same shared panel-link primitive. The panel height is fixed, hover/focus behavior still applies to the whole card, and the panel primitive reference now defines the image-fill option and short-copy requirement.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `assets/studio/css/studio.css`
- `assets/css/main.css`
- `studio/index.md`
- `studio/analytics/index.md`
- `studio/library/index.md`
- `studio/search/index.md`

**Notes:**
This intentionally favors future design consistency over preserving the old content-fit dashboard card behavior.

## [2026-04-20] Added explicit nested-panel support and strengthened the primitive-catalogue method

**Status:** implemented

**Area:** design system / primitive governance

**Summary:**
Extended the panel primitive reference with a deliberate nested-panel variation and updated the catalogue docs so primitive pages are treated as shared-system pressure tests rather than protective demos.

**Reason:**
Container primitives can validly compose with themselves. If the catalogue hides that case or explains it away as surrounding-environment noise, live pages can keep accumulating one-off compensation that masks shared primitive defects.

**Effect:**
Nested panels are now documented as a supported panel composition, direct child panels inherit a subordinate inner-surface treatment from the shared primitive, and the UI catalogue docs now state that shared defects should be fixed at source even when that exposes legacy drift.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/ui-catalogue/panel/index.md`
- `_includes/studio_ui_catalogue_panel_demo.html`
- `_includes/ui_catalogue_notes/panel.md`
- `assets/studio/css/studio.css`

**Notes:**
This is an intentional shared-source change. A future cleanup pass should look for live pages that still compensate locally for panel composition.

## [2026-04-20] Corrected the panel primitive reference template to use a neutral demo surface

**Status:** implemented

**Area:** design system / Studio UI catalogue

**Summary:**
Updated the first UI primitive reference so shared panels are shown without enclosing section panels and with vertically stacked variants.

**Reason:**
The original page nested the live panel examples inside outer panel shells, which made the editor variant look like it overlapped its container and blurred the line between a primitive defect and a page-composition problem.

**Effect:**
The panel catalogue page now shows the primitive on a neutral surface, implementation notes focus on concrete code-level warnings, and the Studio UI docs now define neutral-surface rendering as the default pattern for future primitive pages.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- `studio/ui-catalogue/panel/index.md`
- `_includes/studio_ui_catalogue_panel_demo.html`
- `_includes/ui_catalogue_notes/panel.md`
- `assets/studio/css/studio.css`

**Notes:**
This change improves the primitive-reference contract rather than changing the shared panel shell itself.

## [2026-04-19] Added the first UI catalogue and screenshot asset folders

**Status:** implemented

**Area:** design system / docs structure

**Summary:**
Added a dedicated UI catalogue parent doc with first-pass primitive child docs and matching versioned asset folders for screenshots and visual references.

**Reason:**
Shared primitives were becoming hard to keep visible inside larger framework docs, and visual component guidance needs a stable home for screenshots as the catalogue grows.

**Effect:**
[UI Catalogue](/docs/?scope=studio&doc=ui-catalogue) now sits under [Design](/docs/?scope=studio&doc=design), the first primitive docs cover `panel`, `button`, `input`, `list shell`, `toolbar`, and `modal shell`, and screenshot assets now have dedicated repo paths under `assets/docs/ui-catalogue/`.

**Affected files/docs:**
- [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue)
- [Design](/docs/?scope=studio&doc=design)
- `assets/docs/ui-catalogue/`

**Notes:**
This establishes the structure for future per-primitive and more complex component docs.

## [2026-04-19] Revisited the CSS refactor strategy and restored it to the active design docs

**Status:** implemented

**Area:** design system / CSS governance

**Summary:**
Updated the CSS refactor guidance so it reflects the current UI-system direction rather than an older point-in-time cleanup note.

**Reason:**
The original refactor doc had drifted out of view during newer work and its `last_updated` date no longer reflected the fact that it had been revisited conceptually.

**Effect:**
[CSS Refactor](/docs/?scope=studio&doc=css-refactor) now records the current strategy: formalize tokens, primitives, compositions, and behavior boundaries first; avoid defaulting passive visual shells to JS web components; and keep the document visible from [Design](/docs/?scope=studio&doc=design).

**Affected files/docs:**
- [CSS Refactor](/docs/?scope=studio&doc=css-refactor)
- [Design](/docs/?scope=studio&doc=design)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)

**Notes:**
This is documentation and governance work, not a runtime UI change.

## [2026-04-19] Flattened the Studio docs source tree for Docs Viewer management

**Status:** implemented

**Area:** Docs Viewer / docs infrastructure

**Summary:**
Flattened Studio docs into `_docs_src/*.md` and aligned the builder and management planning with that flat-source model.

**Reason:**
Viewer-side docs management depends on front-matter-driven hierarchy rather than filesystem folders. Keeping Studio docs nested on disk would make tree edits more confusing and harder to validate.

**Effect:**
Studio docs now live directly under `_docs_src/`, the shared docs-builder contract rejects nested Markdown docs, and Docs Viewer management can treat the visible tree as metadata-only.

**Affected files/docs:**
- `_docs_src/*.md`
- `scripts/build_docs.rb`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Viewer Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)

**Notes:**
This was the enabling storage change for local Docs Viewer management.

## [2026-04-19] Consolidated Studio UI triage into rules and UI requests docs

**Status:** implemented

**Area:** Studio UI workflow

**Summary:**
Replaced the temporary UI polish punch-list workflow with a permanent Studio UI rules log and a dedicated UI requests section.

**Reason:**
IAB-driven UI work needs a durable way to distinguish one-off fixes from permanent rules, and the older punch-list format overlapped with that goal.

**Effect:**
[Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules) now captures issue triage and systemic rules, while [UI Requests](/docs/?scope=studio&doc=ui-requests) holds UI feature specs and task docs such as the Docs Viewer favourites request.

**Affected files/docs:**
- [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules)
- [UI Requests](/docs/?scope=studio&doc=ui-requests)
- [Site Docs](/docs/?scope=studio&doc=site-docs)

**Notes:**
This establishes the standing local-Codex UI workflow in place of PR-based tracking.

## [2026-04-19] Added shared Docs Viewer favourites for docs and library

**Status:** implemented

**Area:** Docs Viewer

**Summary:**
Added browser-style document favourites shared by `/docs/` and `/library/`.

**Reason:**
Frequently used docs needed a quicker return path than the tree alone, especially once the shared viewer started carrying search and management controls.

**Effect:**
The shared Docs Viewer now supports IndexedDB-backed favourites, star-based add/remove, compact editable bookmark pills, and a full-width viewer-level controls band above the index and content panels.

**Affected files/docs:**
- `_includes/docs_viewer_shell.html`
- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- [Docs Viewer Favourites Spec](/docs/?scope=studio&doc=docs-viewer-favourites-spec)
- [Docs Viewer Favourites Task](/docs/?scope=studio&doc=docs-viewer-favourites-task)

**Notes:**
Private browsing still limits persistence, so this remains a browser-local feature rather than a hosted user-account feature.

## [2026-04-19] Implemented local Docs Viewer management mode

**Status:** implemented

**Area:** Docs Viewer / local server

**Summary:**
Added the first local-only management mode for the shared Docs Viewer.

**Reason:**
Managing docs directly from the viewer is faster than editing source files by hand, but it needs an explicit local write boundary and a clear opt-in mode.

**Effect:**
`/docs/` and `/library/` now expose manage mode behind `?mode=manage`, backed by `scripts/docs/docs_management_server.py` for create, archive, delete-preview, and delete-apply on flat source docs.

**Affected files/docs:**
- `scripts/docs/docs_management_server.py`
- `_includes/docs_viewer_shell.html`
- `assets/js/docs-viewer.js`
- `bin/dev-studio`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Notes:**
The feature is local-only and fails closed when the docs-management server is unavailable.

## [2026-04-19] Hardened Docs Viewer management reloads and move behavior

**Status:** implemented

**Area:** Docs Viewer / local server

**Summary:**
Refined Docs Viewer management so local development writes refresh reliably and drag/drop moves stay low-noise.

**Reason:**
The Jekyll dev server could continue serving stale docs assets after local writes, and early move behavior created too much sort-order and backup noise.

**Effect:**
Post-write reloads now fetch fresh docs/search payloads from the localhost docs-management server, create inserts after the currently selected doc, delete clears its completion banner when applied, backups are operation-scoped, drag/drop supports leaf-doc-only front-matter moves, sibling sort orders are left unchanged, and move skips search-index rebuilds.

**Affected files/docs:**
- `scripts/docs/docs_management_server.py`
- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)

**Notes:**
Only leaf docs are draggable; folders and docs with children remain fixed.

## [2026-04-19] Added Studio execution-prep coverage for the implemented routes

**Status:** implemented

**Area:** Studio testing workflow

**Summary:**
Added a dedicated Studio execution-prep checklist for the implemented Studio routes.

**Reason:**
The Studio surface had grown large enough that ad hoc testing no longer gave a reliable view of route coverage or failure triage.

**Effect:**
The execution-prep docs now spell out prerequisites, manual versus Codex execution, route coverage, public-runtime follow-through checks, responsive checks, and a failure-triage model.

**Affected files/docs:**
- [Studio End-To-End Checklist](/docs/?scope=studio&doc=new-pipeline-studio-end-to-end-checklist)
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
This is planning and operational guidance rather than a runtime feature.

## [2026-04-19] Completed internal generator cleanup for the JSON-led workflow

**Status:** implemented

**Area:** catalogue pipeline

**Summary:**
Removed the remaining workbook-oriented runtime path from the internal generator flow and aligned the bulk-import workbook configuration.

**Reason:**
The live catalogue workflow is now JSON-led, so the residual workbook branch and workbook-specific defaults were creating unnecessary complexity and stale assumptions.

**Effect:**
`generate_work_pages.py` now runs only the internal JSON-source path, moment-scoped rebuilds share that same internal boundary, `_data/pipeline.json` now points bulk import at `data/works_bulk_import.xlsx`, and the importer no longer assumes `data/works.xlsx`.

**Affected files/docs:**
- `scripts/generate_work_pages.py`
- `_data/pipeline.json`
- `/studio/bulk-add-work/`
- `AGENTS.md`
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
This closes out the workbook-oriented runtime assumptions without changing the hosted public site model.

## [2026-04-18] Implemented Studio shell foundations for the admin surface

**Status:** implemented

**Area:** Studio shell

**Summary:**
Added the first dedicated Studio shell and dashboard structure.

**Reason:**
Studio needed its own navigation and landing surface so internal tools could grow without distorting the public site navigation.

**Effect:**
The public nav stays user-facing, Studio now has its own admin nav, `/studio/` is a four-panel landing page, and domain dashboards now live under `/studio/catalogue/`, `/studio/library/`, `/studio/analytics/`, and `/studio/search/`.

**Affected files/docs:**
- `/studio/`
- `/studio/catalogue/`
- `/studio/library/`
- `/studio/analytics/`
- `/studio/search/`
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
Studio docs also gained a local `Rebuild docs` control alongside the shared docs viewer search field.

## [2026-04-18] Added the Studio moment import flow

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the dedicated moment import workflow at `/studio/catalogue-moment-import/`.

**Reason:**
Moments needed a scoped import path that could preview and apply source-file changes without running a broader catalogue maintenance flow.

**Effect:**
The moment import UI now supports explicit source-file preview/apply, targeted moment rebuilds, catalogue-search rebuild, and first-pass activity/build reporting without folder scanning or srcset generation.

**Affected files/docs:**
- `/studio/catalogue-moment-import/`
- [Catalogue Moment Import](/docs/?scope=studio&doc=catalogue-moment-import)

**Notes:**
This was Phase 2 of the Studio implementation sequence.

## [2026-04-18] Added work-file and work-link editing to the Studio catalogue

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Extended the catalogue editor flow with work-file and work-link editing surfaces.

**Reason:**
Work files and work links needed the same source-backed local editing model as works and details.

**Effect:**
`/studio/catalogue-work/` now links into focused create/edit surfaces for work files and work links, canonical `work_files.json` and `work_links.json` now have local write endpoints, and the derived catalogue lookup layer can open those editors without loading the full source set.

**Affected files/docs:**
- `/studio/catalogue-work/`
- `work_files.json`
- `work_links.json`
- [Work Files](/docs/?scope=studio&doc=catalogue-work-files)
- [Work Links](/docs/?scope=studio&doc=catalogue-work-links)

**Notes:**
The surrounding Studio runtime/docs routing and local save-flow docs were updated to match these new surfaces.

## [2026-04-18] Added workbook-backed bulk work import for new works and details

**Status:** implemented

**Area:** Studio import workflow

**Summary:**
Added the bulk work import flow at `/studio/bulk-add-work/`.

**Reason:**
Even in the JSON-led catalogue workflow, a bounded import path is still useful for bringing in batches of new works and work details from workbook data.

**Effect:**
The bulk import UI now supports one-way preview/apply import from the configured workbook source into canonical JSON for new works and new work details.

**Affected files/docs:**
- `/studio/bulk-add-work/`
- `_data/pipeline.json`
- [Bulk Add Work](/docs/?scope=studio&doc=bulk-add-work)

**Notes:**
Later follow-up work moved the workbook path to `data/works_bulk_import.xlsx`.

## [2026-04-18] Completed Studio catalogue UI consistency and operational reporting refinements

**Status:** implemented

**Area:** Studio catalogue UI

**Summary:**
Refined the catalogue admin UI with more consistent navigation, layout, and reporting surfaces.

**Reason:**
As more Studio routes were added, the catalogue domain needed a clearer internal navigation model and better operational visibility.

**Effect:**
The Catalogue dashboard now uses grouped directional links, catalogue-domain pages share a cross-linked page nav, metadata editors use the left-label single-column layout, Catalogue Status sorts by header, work-file and work-link editors can be opened from dashboard search, `Catalogue Activity` remains source-side, `Build Activity` now records rebuild outcomes, and both pages use sortable operational lists with explicit scope/result columns and links back into the relevant workflow routes.

**Affected files/docs:**
- `/studio/catalogue/`
- `/studio/catalogue-status/`
- `/studio/catalogue-activity/`
- `/studio/build-activity/`
- [Catalogue Status](/docs/?scope=studio&doc=catalogue-status)
- [Catalogue Activity](/docs/?scope=studio&doc=catalogue-activity)
- [Build Activity](/docs/?scope=studio&doc=build-activity)

**Notes:**
This covers the Phase 3 and Phase 4 UI/reporting refinements in the Studio plan.

## [2026-04-18] Completed source-readiness, preview-media, and local-media generation refinements

**Status:** implemented

**Area:** Studio media workflow

**Summary:**
Extended Studio to report source readiness, show focused preview media, and surface local derivative generation state.

**Reason:**
Editing metadata alone was not enough once Studio started coordinating source prose, source media, generated previews, and local derivative generation.

**Effect:**
Work, series, and detail editors now surface source readiness in the summary rail, work and series offer narrow `Import prose + rebuild` actions, detail preview resolves its own source media path, work and detail editors show compact current-record previews, work-detail rows on the work editor use thumbnail-led navigation, scoped rebuilds run a bounded local thumbnail-generation step for works, work details, and moments, and Build Activity records generated local media alongside rebuild outcomes.

**Affected files/docs:**
- `/studio/catalogue-work/`
- `/studio/catalogue-work-detail/`
- `/studio/catalogue-series/`
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)
- [Build Activity](/docs/?scope=studio&doc=build-activity)

**Notes:**
This entry covers the later media/readiness refinements that followed the first editor surfaces.

## [2026-04-18] Completed internal generator refactor for live JSON rebuilds

**Status:** implemented

**Area:** catalogue generator

**Summary:**
Refactored the internal generator so live JSON rebuilds no longer materialize `works.xlsx`.

**Reason:**
The live rebuild path needed to align with canonical JSON source records instead of continuing to depend on an intermediate workbook materialization step.

**Effect:**
`generate_work_pages.py` now rebuilds from canonical source records with an explicit in-memory compatibility projection, and JSON-source write runs now persist mutable source updates back into canonical catalogue JSON rather than round-tripping through a workbook file.

**Affected files/docs:**
- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
`AGENTS.md` was updated to reflect the live JSON-led workflow and retire the older workbook-led entrypoint assumptions.

## [2026-04-17] Added derived catalogue lookup payloads for lightweight Studio editors

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the derived lookup payload layer used by the Studio editors.

**Reason:**
Loading the full catalogue source set in the browser was too heavy for focused editor routes that only need lightweight search data plus a current record.

**Effect:**
Studio editors now use lightweight search indexes plus focused per-record lookup JSON rather than loading the full source browser payload.

**Affected files/docs:**
- derived catalogue lookup JSON under `assets/studio/data/`
- [Catalogue Search](/docs/?scope=studio&doc=search)
- [Studio Implementation Plan](/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan)

**Notes:**
Later editor surfaces built on this lookup layer rather than on full-source browser loads.

## [2026-04-17] Added the Studio series editor and series-scoped rebuild flow

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the first series editor route for the JSON-led catalogue workflow.

**Reason:**
Series-level metadata and membership needed the same local editing and scoped rebuild model as individual works.

**Effect:**
`/studio/catalogue-series/` now supports canonical `series.json` save flow, atomic membership writes into `works.json`, and series-scoped rebuilds for the current series, affected works, aggregate indexes, and catalogue search.

**Affected files/docs:**
- `/studio/catalogue-series/`
- `series.json`
- `works.json`
- [Catalogue Series](/docs/?scope=studio&doc=catalogue-series)

**Notes:**
This was the first series-specific editing surface in Studio.

## [2026-04-17] Added the work detail editor and grouped work-detail navigation

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the work detail editor and integrated grouped detail navigation into the work editor.

**Reason:**
Work details needed their own source-backed edit surface while still being easy to reach from the parent work context.

**Effect:**
`/studio/catalogue-work-detail/` now supports canonical `work_details.json` save flow and parent-work scoped rebuilds, while `/studio/catalogue-work/` shows grouped work-detail navigation capped at ten visible rows per section with per-work detail search by id.

**Affected files/docs:**
- `/studio/catalogue-work-detail/`
- `/studio/catalogue-work/`
- `work_details.json`
- [Catalogue Work Detail](/docs/?scope=studio&doc=catalogue-work-detail)

**Notes:**
This built on the earlier single-work editor and scoped JSON rebuild path.

## [2026-04-17] Added the first canonical work editor and scoped JSON rebuild path

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added the first canonical single-work editor together with the scoped JSON-source rebuild flow.

**Reason:**
Studio needed a practical proof that individual work metadata could be edited safely against canonical JSON without relying on workbook editing.

**Effect:**
`/studio/catalogue-work/` became the first canonical work metadata editor, local preview/apply plus `Save + Rebuild` were added for work edits, Studio transport/config wiring gained separate catalogue local-service health probing, and the catalogue write server response now returns the normalized saved record plus saved timestamp for editor baseline refresh.

**Affected files/docs:**
- `/studio/catalogue-work/`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Work](/docs/?scope=studio&doc=catalogue-work)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)

**Notes:**
This was the first end-to-end canonical JSON editor in the Studio catalogue workflow.

## [2026-04-17] Added catalogue status and activity Studio pages

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added early Studio surfaces for JSON-led catalogue maintenance: Catalogue Status and Catalogue Activity.

**Reason:**
The new catalogue source workflow needs useful visibility before full editing UI exists. Non-published records should be discoverable without opening Excel, and local JSON-source saves or validation failures should be visible without reading raw server logs.

**Effect:**
`/studio/catalogue-status/` reads canonical catalogue source JSON and lists records where `status` is not `published`. `/studio/catalogue-activity/` reads `assets/studio/data/catalogue_activity.json`, a small feed updated by the Catalogue Write Server for source-save and validation-failure events. Studio config now exposes the source and activity data paths used by those pages.

**Affected files/docs:**
- `studio/catalogue-status/index.md`
- `studio/catalogue-activity/index.md`
- `assets/studio/js/catalogue-status.js`
- `assets/studio/js/catalogue-activity.js`
- `assets/studio/data/catalogue_activity.json`
- `scripts/catalogue_activity.py`
- `scripts/studio/catalogue_write_server.py`
- [Catalogue Status](/docs/?scope=studio&doc=catalogue-status)
- [Catalogue Activity](/docs/?scope=studio&doc=catalogue-activity)

**Notes:**
The UI intentionally follows established Studio list and activity patterns. Refinement can happen after the first implementation is in use.

## [2026-04-17] Added the local catalogue source write service

**Status:** implemented

**Area:** Studio catalogue pipeline

**Summary:**
Added a localhost-only Catalogue Write Server for the JSON-led catalogue pipeline.

**Reason:**
Studio catalogue editors need a narrow local write boundary before the UI can replace workbook editing. The first service increment proves that canonical source JSON can be updated safely without writing media, prose, generated public JSON, or search artifacts.

**Effect:**
`scripts/studio/catalogue_write_server.py` exposes `GET /health` and `POST /catalogue/work/save`. The save endpoint updates existing work records in `assets/studio/data/catalogue/works.json`, validates the full catalogue source set before writing, supports optional stale-record hash checks, creates timestamped backup bundles, and writes minimal local event logs. `bin/dev-studio` now starts this service alongside Jekyll and the Tag Write Server.

**Affected files/docs:**
- `scripts/studio/catalogue_write_server.py`
- `bin/dev-studio`
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**
This service is intentionally narrow. Work detail, series, create, delete, bulk edit, import, and build endpoints remain later pipeline phases.

## [2026-04-01] Migrated moments from workbook rows to source-file front matter

**Status:** implemented

**Area:** moments pipeline

**Summary:**  
Moments are now sourced from `moments/*.md` front matter instead of the `Moments` worksheet in `works.xlsx`.

**Reason:**  
The old model duplicated moment metadata between source prose files and the workbook even though moments only need a small metadata surface and already have a canonical source file. Moving that metadata into front matter makes each moment self-contained, removes unnecessary workbook maintenance, and aligns the pipeline with how moment prose is actually authored.

**Effect:**  
`build_catalogue.py`, `copy_draft_media_files.py`, `generate_work_pages.py`, and the shared preflight now scan moment source files directly. Canonical moment metadata now lives in front matter as `title`, `status`, `published_date`, `date`, optional `date_display`, and optional `image_file`, with `moment_id` fixed by the filename stem. Moment publish writes now update source front matter while preserving the first `published_date`, missing source images are treated as optional, and the standalone `delete_moment.py` script now handles repo-side moment cleanup without requiring workbook rows.

**Affected files/docs:**  
- `scripts/moment_sources.py`
- `scripts/build_catalogue.py`
- `scripts/copy_draft_media_files.py`
- `scripts/generate_work_pages.py`
- `scripts/catalogue_preflight.py`
- `scripts/jekyll_markdown_renderer.rb`
- `scripts/delete_moment.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Copy Draft Media Files](/docs/?scope=studio&doc=scripts-copy-draft-media)
- [Delete Moment](/docs/?scope=studio&doc=scripts-delete-moment)

**Notes:**  
This change retires the `Moments` worksheet as a pipeline source. During the migration, older workbook-backed fallbacks were briefly retained and then removed once moment front matter had been completed across the source tree.

## [2026-04-01] Added a public recently added page and publication ledger

**Status:** implemented

**Area:** catalogue

**Summary:**  
Added a public `/recent/` page plus a generated `assets/data/recent_index.json` ledger for recent first-time series and work publications.

**Reason:**  
The public catalogue needed a lightweight way to surface newly published work without treating later title edits, series edits, or work moves as fresh additions. That requires a small persistent event ledger rather than a page derived only from current catalogue state.

**Effect:**  
`generate_work_pages.py` now records first-time `draft -> published` transitions into a capped recent-publications index, prunes entries whose target series or work has been deleted, and groups multiple newly published works in the same existing series into one entry anchored to the first work from that run. The public `/recent/` page renders that ledger, `/series/` now links to it with a `recently added` control, and series/work pages now show `← recently added` when opened from that route.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `scripts/backfill_recent_index_from_git_history.py`
- `recent/index.md`
- `series/index.md`
- `_layouts/series.html`
- `_layouts/work.html`
- `assets/css/main.css`
- `assets/data/recent_index.json`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)

**Notes:**  
The initial `/recent/` ledger can be seeded from workbook git history with `scripts/backfill_recent_index_from_git_history.py`. That one-off backfill only records provable `draft -> published` transitions and drops any historic series entry that cannot be mapped confidently onto a current live series ID.

## [2026-04-01] Preserved tag assignments across series-id renames

**Status:** implemented

**Area:** build pipeline

**Summary:**  
`build_catalogue.py` now migrates matching `assets/studio/data/tag_assignments.json` series rows when series IDs are renamed.

**Reason:**  
During the numeric series-id migration, the planner correctly treated old slug-style series IDs as removed and new numeric series IDs as added, but the previous cleanup path deleted the old tag-assignment rows and the later generator pass recreated empty rows for the new IDs. That dropped curator tags and per-work tag overrides.

**Effect:**  
Before generation and stale cleanup, the wrapper now compares the existing `assets/data/series_index.json` to the current workbook and infers series-ID renames by matching title, `primary_work_id`, and member works. Matching tag-assignment rows are migrated to the new IDs instead of being deleted. True removals still prune tag-assignment rows as before.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- `assets/studio/data/tag_assignments.json`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This protects future series-ID renames. Existing lost tags had to be restored once from the previous commit's tag-assignment data.

## [2026-04-01] Scoped wrapper generation artifacts to the planned flow

**Status:** implemented

**Area:** build pipeline

**Summary:**  
`build_catalogue.py` now passes a narrower `--only` artifact list into `generate_work_pages.py` based on the planned scope instead of always letting the generator run every work-side artifact type.

**Reason:**  
The planner could correctly report no `WorkDetails` row changes while the later generator phase still dry-ran or rewrote all `_work_details/*.md` pages for selected works. That made the plan harder to trust and caused unnecessary noise during work-only migrations such as the numeric series-id transition.

**Effect:**  
Work-only runs now skip `work-details-pages` unless the work-details flow actually needs them. Aggregate indexes still rebuild as before, and work JSON can still include detail metadata without regenerating `_work_details` route stubs.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This only changes which artifact groups are requested from `generate_work_pages.py`. It does not change planner diff detection or the underlying detail JSON model.

## [2026-04-01] Added numeric series-id support to the catalogue pipeline

**Status:** implemented

**Area:** series model migration

**Summary:**  
The catalogue planner, workbook preflight, generator, and audit tooling no longer require `series_id` to be slug-safe.

**Reason:**  
`series_id` is being migrated toward a numeric catalogue-style identifier instead of a user-authored slug. The pipeline needed to stop treating series IDs as route slugs before the workbook can be bulk-migrated safely.

**Effect:**  
`build_catalogue.py`, `generate_work_pages.py`, and the shared workbook preflight now normalize numeric series IDs such as `1` to `001`, accept those values in `Works.series_ids`, `Series.series_id`, `SeriesSort.series_id`, and `--series-ids*` CLI filters, and still tolerate the current legacy slug-style series IDs during transition. Generated artifact naming continues to follow whatever normalized series IDs are present in the workbook.

**Affected files/docs:**  
- `scripts/series_ids.py`
- `scripts/catalogue_preflight.py`
- `scripts/build_catalogue.py`
- `scripts/generate_work_pages.py`
- `scripts/audit_site_consistency.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

**Notes:**  
This is a transition step, not the workbook migration itself. The canonical workbook still needs to be bulk-edited from legacy slug-style series IDs to numeric series IDs before the site fully switches over.

## [2026-04-01] Preserved workbook formulas during generator writes

**Status:** implemented

**Area:** workbook writes

**Summary:**  
`generate_work_pages.py` now reads workbook values from a `data_only=True` workbook while saving updates through a separate non-`data_only` workbook.

**Reason:**  
The previous write path saved the same `data_only=True` workbook instance that was used for reading. That risks stripping formulas from the workbook when the generator updates status, `published_date`, or image dimensions.

**Effect:**  
Write runs now preserve existing workbook formulas while keeping the current generated-file and workbook-update behavior. This clears the way for supported formula-driven helper columns in `Works`, such as series-title lookup aids, without the generator destroying those formulas on save.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

**Notes:**  
The generator still relies on Excel's cached formula values when reading with `data_only=True`. If a formula result has not been calculated and saved by Excel yet, the read value may still be empty or stale.

## [2026-04-01] Added a default post-plan confirmation prompt to build_catalogue

**Status:** implemented

**Area:** build pipeline

**Summary:**  
`build_catalogue.py` now pauses after printing `==> Build Plan` and asks `Continue? [Y|N]` unless `--no-confirm` is passed.

**Reason:**  
The build plan is now detailed enough to act as a real operator checkpoint. Adding an explicit confirmation step makes it easier to catch scope mistakes before copy, srcset, workbook, or generated-file work begins.

**Effect:**  
Interactive runs now require a simple confirmation after the plan. `--no-confirm` skips that prompt and continues immediately, which is the intended path for unattended invocations. `--plan` still exits after printing the plan without prompting.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This change affects orchestration behavior only. Generation logic and output contracts are unchanged.

## [2026-04-01] Shortened local path output in catalogue pipeline logs

**Status:** implemented

**Area:** build pipeline

**Summary:**  
Catalogue pipeline command echoes and step logs now avoid printing machine-specific absolute filesystem roots during normal runs.

**Reason:**  
The previous output was noisy and leaked long local absolute paths for interpreters, repo files, canonical source media, staged media, and temporary manifest files. That made routine logs harder to scan and less portable.

**Effect:**  
`build_catalogue.py`, `copy_draft_media_files.py`, `make_srcset_images.py`, and `generate_work_pages.py` now render repo-owned paths as repo-relative, canonical source paths as `[projects]/...`, staged and derivative media paths as `[media]/...`, and temporary paths as `[tmp]/...`. Runtime behavior is unchanged; this is a display-only logging cleanup.

**Affected files/docs:**  
- `scripts/display_paths.py`
- `scripts/build_catalogue.py`
- `scripts/copy_draft_media_files.py`
- `scripts/make_srcset_images.py`
- `scripts/generate_work_pages.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

**Notes:**  
This change only affects human-readable output. The underlying commands and file writes still use the full resolved paths internally.

## [2026-04-01] Added fail-fast catalogue workbook preflight

**Status:** implemented

**Area:** validation

**Summary:**  
`build_catalogue.py` and `generate_work_pages.py` now run a shared workbook preflight before copy, generation, or workbook-write steps begin.

**Reason:**  
The catalogue pipeline could previously write work pages, stage media, or persist workbook status changes before a later workbook integrity error such as a missing `Series.primary_work_id` aborted the run. That made failures harder to recover from and left partial publish state behind.

**Effect:**  
Blocking workbook issues for actionable catalogue rows are now aggregated and reported before the run starts mutating outputs. The current preflight covers malformed IDs, unknown `Works.series_ids` references, missing or invalid `Series.primary_work_id` values, series primary works that are not members of the series, orphaned `WorkDetails.work_id` values, and invalid moment source filenames or front matter.

**Affected files/docs:**  
- `scripts/catalogue_preflight.py`
- `scripts/build_catalogue.py`
- `scripts/generate_work_pages.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This change adds an earlier validation gate but does not relax the underlying generator requirements. It moves the failure point earlier and makes the errors easier to fix in one pass.

## [2026-04-01] Added a Studio-only work storage index

**Status:** implemented

**Area:** studio

**Summary:**  
Added `assets/studio/data/work_storage_index.json` so `/studio/studio-works/` can continue surfacing storage without putting curator-only storage data back into the public `works_index.json`.

**Reason:**  
The public works index was intentionally slimmed for runtime use, but the Studio works page still needs a fast bulk answer to “where is a work stored?”. A separate Studio-only lookup keeps that curator use case intact without re-expanding the public artifact.

**Effect:**  
`generate_work_pages.py` now writes a Studio-only storage map keyed by `work_id`, `studio-works.js` merges it into the existing row rendering and storage sort behavior, and `delete_work.py` removes stale entries from that Studio index during one-off deletions.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `scripts/delete_work.py`
- `studio/studio-works/index.md`
- `assets/studio/js/studio-works.js`
- [Studio Works](/docs/?scope=studio&doc=studio-works)
- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

## [2026-04-01] Added `medium_caption` to derived catalogue search terms

**Status:** implemented

**Area:** search

**Summary:**  
Catalogue search now enriches work entries with `medium_caption` from per-work JSON, but keeps that value in derived search fields rather than exposing a new displayed result field.

**Reason:**  
The search builder already reads per-work JSON for work-only enrichment. Adding `medium_caption` improves public recall for material descriptions without re-bloating `works_index.json` or the visible result-row contract.

**Effect:**  
`build_search.rb` now reads `medium_caption` from `assets/works/index/<work_id>.json` and folds it into `search_terms` and `search_text` for work entries. Result rows still display `medium_type`, not `medium_caption`, and the serialized field inventory for catalogue search remains unchanged.

**Affected files/docs:**  
- `scripts/build_search.rb`
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
- [Search Normalisation Rules](/docs/?scope=studio&doc=search-normalisation-rules)
- [Search Validation Checklist](/docs/?scope=studio&doc=search-validation-checklist)

## [2026-04-01] Slimmed `works_index` and removed storage from public search

**Status:** implemented

**Area:** search

**Summary:**  
`works_index.json` no longer carries `storage` or `medium_type`, and public catalogue search no longer indexes or ranks on `storage`.

**Reason:**  
`works_index.json` is a shared runtime summary artifact and should stay as lean as possible. `storage` is no longer intended to be publicly searchable, and `medium_type` can be sourced directly from per-work JSON during the offline search build instead of being duplicated into the lightweight works index.

**Effect:**  
The lightweight works index now carries identity, title/year display, and series membership only. Catalogue search still exposes `medium_type`, but now resolves it from `assets/works/index/<work_id>.json`. `storage` has been removed from the public search artifact and from the current search ranking model.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `scripts/build_search.rb`
- `assets/js/search/search-page.js`
- `scripts/delete_work.py`
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Search Index Schema](/docs/?scope=studio&doc=search-index-schema)
- [Search Field Registry](/docs/?scope=studio&doc=search-field-registry)
- [Search Ranking Model](/docs/?scope=studio&doc=search-ranking-model)

## [2026-04-01] Added work and series prose tracking to build_catalogue planning

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now fingerprints work, series, and moment prose source files as part of planner state, so prose-only edits can be picked up by the default planner path.

**Reason:**  
After workbook rows, source images, and removed-row cleanup were covered, prose files were the remaining practical catalogue inputs still outside the planner. Bringing them into scope makes the default build path more complete without widening cleanup scope to canonical source trees.

**Effect:**  
Planner state now tracks work prose resolved from `Works.project_folder` plus `Works.work_prose_file`, series prose resolved from `Series.primary_work_id` plus `Series.series_prose_file`, and moment prose resolved from `moments/<moment_id>.md`. Work, series, and moment prose changes now trigger generation targeting only. They do not trigger copy/srcset and do not force a catalogue search rebuild on their own.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)

**Notes:**  
Planner state migration now rewrites earlier prose-tracking baselines to include moment prose.

## [2026-04-01] Extended removed-row cleanup to local staged and derivative media

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now removes stale local media outputs under `DOTLINEFORM_MEDIA_BASE_DIR` when workbook rows are removed.

**Reason:**  
Cleaning only repo-owned route stubs and JSON still left stale staged inputs, srcset outputs, and staged downloads on the local media side. Those files are owned by the same catalogue pipeline and should be cleaned by the same removed-row pass.

**Effect:**  
Removed work, work-detail, and moment rows now also delete matching files from the local `make_srcset_images` input folders, the generated `primary/` and `thumb/` srcset folders, and staged work downloads under `works/files/`. Aggregate catalogue JSON and search rebuilds still run afterward from the current workbook state.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This still does not touch canonical source media under `DOTLINEFORM_PROJECTS_BASE_DIR` or remote media such as R2.

## [2026-04-01] Added removed-row stale-artifact cleanup to build_catalogue

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now cleans up repo-owned generated artifacts when workbook rows are removed, instead of only warning that stale files may remain.

**Reason:**  
The planner already knew which workbook rows had disappeared. Turning that into concrete cleanup reduces drift in route stubs, per-record JSON, and Studio assignment data without requiring a separate manual delete pass for the common cases.

**Effect:**  
Removed work, work-detail, series, and moment rows now trigger deletion of the matching generated route stubs and per-record JSON files in the repo. The same pass also prunes removed series rows and removed per-work overrides from `assets/studio/data/tag_assignments.json`, then rebuilds aggregate indexes and catalogue search from the current workbook state.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Studio Scope](/docs/?scope=studio&doc=data-models-studio)

**Notes:**  
This first slice only cleans repo-owned generated artifacts and Studio assignment rows. External source media and derivative media cleanup still remain separate.

## [2026-04-01] Added explicit planner version metadata to build_catalogue state

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now writes `var/build_catalogue_state.json` with explicit top-level planner metadata so planner-state evolution is easier to reason about.

**Reason:**  
The planner state had already become important enough to deserve a clearer contract. Explicit versioning and a migration note make future planner changes easier to document and safer to evolve without turning state resets into the default workflow.

**Effect:**  
Planner state now includes `schema`, `planner_version`, and `migration_note`. Older compatible state files are still accepted, normalized in memory, and rewritten on the next successful write run.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This does not change canonical site data. It only makes the local planner-state contract more explicit.

## [2026-04-01] Added a curator-facing Studio build activity feed

**Status:** implemented

**Area:** studio

**Summary:**  
Added a curated build-activity journal and a Studio page at `/studio/build-activity/` so recent catalogue build runs can be reviewed without reading raw script logs.

**Reason:**  
The catalogue planner now has enough context to explain what changed and what it rebuilt. A lightweight recent-activity surface makes that information useful to the curator and creates a cleaner base for any later public “recent updates” work.

**Effect:**  
Successful non-dry-run `build_catalogue.py` runs now append a local journal under `var/build_activity/`, regenerate `assets/studio/data/build_activity.json`, and the new Studio page renders the latest entries with changed workbook/media groups plus action summaries.

**Affected files/docs:**  
- `scripts/build_activity.py`
- `scripts/build_catalogue.py`
- `assets/studio/data/studio_config.json`
- `assets/studio/js/studio-config.js`
- `assets/studio/js/build-activity.js`
- `studio/build-activity/index.md`
- [Build Activity](/docs/?scope=studio&doc=build-activity)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)

**Notes:**  
This feed is a local Studio summary surface, not the canonical low-level script log and not yet a public site history feed.

## [2026-04-01] Made work prose optional in catalogue generation

**Status:** implemented

**Area:** scripts

**Summary:**  
`generate_work_pages.py` no longer treats missing work prose mappings or missing work prose source files as a reason to skip work page or work JSON generation.

**Reason:**  
Work prose files are intentionally rare in this repo. Missing prose should show up as absent page prose on the site, not block unrelated metadata, routing, or JSON refresh.

**Effect:**  
`_works/<work_id>.md` stubs and `assets/works/index/<work_id>.json` now continue to generate when `Works.work_prose_file` is empty, unresolved, or points at a missing file. In those cases the work payload is written without prose content rather than emitting a per-work warning and skipping the record.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)

**Notes:**  
This changes only the work-prose boundary. Series and moment prose handling still follows their existing rules.

## [2026-04-01] Fixed moments index rebuild on scoped non-moment runs

**Status:** implemented

**Area:** scripts

**Summary:**  
Fixed a local-variable scoping bug in `generate_work_pages.py` that could crash scoped runs such as `--work-ids ...` when the script still rebuilt the global moments index JSON afterward.

**Reason:**  
The moments index rebuild path is meant to remain available even when moment page generation is not selected, but it was reusing column helper variables that were only initialized inside the moment-page branch.

**Effect:**  
Scoped work-only runs now complete normally while still allowing the global moments index pass to evaluate its inputs and write-skip correctly.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)

## [2026-04-01] Added workbook-aware planning to the catalogue pipeline entrypoint

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now plans workbook-backed generation before it runs, using a persisted planner state file to infer affected work IDs, series IDs, and moment IDs instead of requiring those scopes to be supplied manually most of the time.

**Reason:**  
The previous pipeline wrapper still depended on the user to translate workbook edits into `--mode`, `--work-ids`, `--series-ids`, and `--moment-ids`. That made safe incremental rebuilds harder to reason about and kept future pipeline enhancements tightly coupled to manual operator knowledge.

**Effect:**  
Default `./scripts/build_catalogue.py` runs now compare workbook-backed source records against `var/build_catalogue_state.json`, print an execution plan, skip generate/search when nothing relevant changed, and persist the new planner state after successful write runs. Copy/srcset stages remain draft-driven for now, so published media-only changes still need explicit flags.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- `.gitignore`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This was the first planner slice. Removed-row stale-artifact cleanup was added in a later follow-up on the same day.

## [2026-04-01] Extended catalogue planning to track canonical source media

**Status:** implemented

**Area:** scripts

**Summary:**  
`build_catalogue.py` now fingerprints canonical source images for works, work details, and moments in addition to workbook-backed rows, so published media replacements can be picked up without manual ID scoping.

**Reason:**  
Workbook-only planning was enough for metadata changes, but it still left source-image edits outside the default build path. That kept routine image replacement work dependent on user-supplied flags and IDs.

**Effect:**  
The planner state now includes source-media fingerprints and can infer copy/srcset plus downstream generation scope from file changes. Existing planner state files that predate media tracking are treated as a baseline until the next write run updates them.

**Affected files/docs:**  
- `scripts/build_catalogue.py`
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Pipeline Use Cases](/docs/?scope=studio&doc=pipeline-use-cases)
- [Scripts](/docs/?scope=studio&doc=scripts)

## [2026-03-30] Removed the docs compatibility mirror and legacy Studio doc-link fallback

**Status:** implemented

**Area:** architecture

**Summary:**  
Removed the flat Studio docs compatibility output and retired the old legacy-link fallback from the docs builder so the published docs data contract is now scope-owned only.

**Reason:**  
The repo now uses explicit scope-owned viewer routes and scoped docs JSON outputs. Keeping the old mirror and legacy path rewrite added dormant complexity without protecting any core site functionality.

**Effect:**  
The docs builder now writes only `assets/data/docs/scopes/studio/` and `assets/data/docs/scopes/library/`, legacy `/docs/.../` path rewriting is gone, Studio source-doc links now use `/docs/?scope=studio&doc=...`, and the shared docs viewer normalizes incoming Studio viewer URLs onto the scoped route.

**Affected files/docs:**  
- `scripts/build_docs.rb`
- `assets/js/docs-viewer.js`
- `AGENTS.md`
- `studio/index.md`
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)

## [2026-03-30] Documented when the shared docs viewer runtime should and should not fork

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a dedicated site-architecture note describing the current boundary between scope-specific docs route shells and the shared docs viewer runtime, including concrete examples of changes that should remain shell-level and the kinds of divergence that would justify a runtime fork later.

**Reason:**  
The docs system now serves both Studio and library scopes through one viewer runtime. The repo needed an explicit guardrail so future scope-specific changes can be evaluated against a stable “do not fork unless the product model changes” rule.

**Effect:**  
There is now a stable reference for deciding whether a new docs requirement belongs in route-shell composition, scope-owned data, a small shared option, or a true runtime split.

**Affected files/docs:**  
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Architecture](/docs/?scope=studio&doc=architecture)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)

**Notes:**  
The current recommendation remains to keep one docs viewer runtime and allow route-level shells to diverge as needed.

## [2026-03-30] Split the scripts reference into a high-level overview and child docs

**Status:** implemented

**Area:** documentation

**Summary:**  
Reduced the old scripts overview into the current [Scripts](/docs/?scope=studio&doc=scripts) navigation page and moved command-level script usage into dedicated child documents.

**Reason:**  
The single overview page had accumulated too much detailed operational content to remain useful as a quick architectural entry point.

**Effect:**  
The scripts docs are now easier to scan at the top level, while script-specific flags, outputs, and workflow notes have stable dedicated docs such as [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder), [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages), and [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server).

**Affected files/docs:**  
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Generate Work Pages](/docs/?scope=studio&doc=scripts-generate-work-pages)
- [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server)
- `AGENTS.md`

**Notes:**  
Script-specific documentation should now be added to the relevant `scripts-*.md` child doc rather than expanding the overview again.

## [2026-03-30] Added config-backed docs media tokens for remote images

**Status:** implemented

**Area:** architecture

**Summary:**  
Extended the docs-data builder so docs bodies can use `[[media:...]]` tokens that resolve against `_config.yml` `media_base` before Markdown rendering.

**Reason:**  
Library docs need to support remotely hosted full-size images without hardcoding the full media origin in every document and without storing full-size docs images in the repo.

**Effect:**  
Docs can now stay as ordinary `.md` source files while embedding raw HTML and config-backed remote media URLs, keeping the repo aligned with the “repo holds text and thumbnails, R2 holds full media” principle.

**Affected files/docs:**  
- `scripts/build_docs.rb`
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This change does not add native `.html` source ingestion. The intended authoring model remains `.md` files with YAML front matter, optionally containing raw HTML bodies.

## [2026-03-30] Made the docs library scope-aware and added a separate library docs route

**Status:** implemented

**Area:** architecture

**Summary:**  
Refactored the docs viewer data/build contract to support separate `studio` and `library` docs scopes, kept `/docs/` as the Studio docs route, and converted `/library/` from a stub page into a library-scoped docs viewer.

**Reason:**  
The existing docs system implicitly belonged to the Studio domain even though the code and data layout were still flat. Additional docs domains needed scope-owned routes and artifacts before library content could grow cleanly.

**Effect:**  
Studio docs now build into a scope-owned output tree under `assets/data/docs/scopes/studio/`, library docs have their own source root and scoped output tree, `/docs/?scope=studio&doc=...` is now the explicit Studio docs contract, and `/library/` now hosts the library docs viewer.

**Affected files/docs:**  
- `scripts/build_docs.rb`
- `assets/js/docs-viewer.js`
- `docs/index.md`
- `library/index.md`
- `_includes/docs_viewer_shell.html`
- `_docs_library_src/library.md`
- `_layouts/default.html`
- [Scripts](/docs/?scope=studio&doc=scripts)

## [2026-03-30] Added lightweight build-version cache busting to shared shell assets

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a lightweight build-version query token to shared shell CSS and JS asset URLs, using the current build timestamp rather than a separate fingerprint pipeline.

**Reason:**  
Local review was vulnerable to stale browser caches after JS/CSS renames or runtime changes, especially while the public search surface was moving and being renamed.

**Effect:**  
Shared shell assets now reload more reliably after a rebuild, the default layout publishes the current asset version in page metadata, and the search runtime can align its own module/data cache busting with that same build token.

**Affected files/docs:**  
- `_layouts/default.html`
- `_layouts/work.html`
- `_layouts/work_details.html`
- `_layouts/series.html`
- `_layouts/moment.html`
- `search/index.md`
- `assets/js/search/search-page.js`
- `assets/studio/js/studio-config.js`
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)

**Notes:**  
This is a pragmatic cache-busting layer for the current static setup. It is not a full hashed-asset pipeline.

## [2026-03-30] Merged moments browsing into the works catalogue

**Status:** implemented

**Area:** works

**Summary:**  
Merged the public moments index UI into the `/series/` works catalogue so one catalogue page now switches between `works` and `moments` with shared view, sort, and pagination controls.

**Reason:**  
The separate moments index duplicated the same catalogue interaction pattern and made the top-level browsing navigation more fragmented than it needed to be.

**Effect:**  
The public top nav now exposes only `works`, `/series/` owns the combined catalogue UI, individual moment pages keep their existing `/moments/<moment_id>/` URLs, and the standalone `/moments/` landing page is no longer published.

**Affected files/docs:**  
- `series/index.md`
- `moments/index.md`
- `_layouts/default.html`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`
- [Data Flow](/docs/?scope=studio&doc=data-flow)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)

**Notes:**  
The main regression risk is state handling when switching between works and moments modes on the merged catalogue page.

## [2026-03-29] Normalized published site and Studio doc references to docs-viewer links

**Status:** implemented

**Area:** architecture

**Summary:**  
Updated published site and Studio docs so references to other published docs now use `/docs/?scope=studio&doc=...` links instead of raw filenames or legacy doc URLs.

**Reason:**  
The docs set is increasingly used through the in-site viewer. Linking published docs through the viewer makes cross-document navigation consistent and keeps repo file references reserved for actual source files and unpublished notes.

**Effect:**  
Published docs now read more cleanly as a connected documentation system, while literal output paths, unpublished docs, and non-doc repo files remain explicit where needed.

**Affected files/docs:**  
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [CSS Audit Spec](/docs/?scope=studio&doc=css-audit-spec)
- [Studio](/docs/?scope=studio&doc=studio)
- [Tag Editor](/docs/?scope=studio&doc=tag-editor)
- [Series Tags](/docs/?scope=studio&doc=series-tags)

**Notes:**  
This change updates documentation navigation only; it does not change site runtime or pipeline behaviour.

## [2026-03-29] Established a dedicated site-wide change log for non-search history

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a dedicated [Site Change Log](/docs/?scope=studio&doc=site-change-log) plus supporting guidance so meaningful non-search site and Studio changes now have a focused historical record separate from search.

**Reason:**  
Search has become complex enough to justify its own subsystem log. The rest of the site still needs a concise historical record, but should not be mixed into the search log.

**Effect:**  
Future review of non-search development can now happen without reconstructing history from scattered commits or overloading the search change log.

**Affected files/docs:**  
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)
- `AGENTS.md`

**Notes:**  
This log should be updated for meaningful non-search site, Studio, and pipeline changes as part of normal close-out.

## [2026-03-20] Moved work-detail runtime to per-work JSON and retired the old aggregate work-details flow

**Status:** implemented

**Area:** works

**Summary:**  
Shifted work-detail runtime behaviour so work detail pages resolve from per-work JSON instead of relying on the old aggregate work details index flow.

**Reason:**  
The older aggregate flow added unnecessary coupling and no longer matched the JSON-first direction of the site data model.

**Effect:**  
Work detail runtime became simpler and closer to the canonical per-work data flow. The retired aggregate path and related sitemap/runtime dependencies were removed.

**Affected files/docs:**  
- `_layouts/work_details.html`
- `_layouts/work.html`
- `scripts/generate_work_pages.py`
- `scripts/audit_site_consistency.py`
- [Data Flow](/docs/?scope=studio&doc=data-flow)

**Notes:**  
This was part of the wider JSON-first site architecture shift.

## [2026-03-29] Search-specific history moved out of the general site history

**Status:** implemented

**Area:** architecture

**Summary:**  
Confirmed that search history should live in [Search Change Log](/docs/?scope=studio&doc=search-change-log) rather than the broader site log.

**Reason:**  
Search now has its own artifact, UI surface, policy surface, and document set, so combining it with wider site history would make both logs less useful.

**Effect:**  
The site log remains focused on the wider site and non-search Studio development, while search history is reviewed through its own dedicated log.

**Affected files/docs:**  
- [Search Change Log](/docs/?scope=studio&doc=search-change-log)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)
- [Site Change Log Guidance](/docs/?scope=studio&doc=site-change-log-guidance)

**Notes:**  
For changes that materially affect both areas, add short entries to both logs.

## [2025-08-19] Adopted JSON-first site data flow for works, series, and moments indexes

**Status:** implemented

**Area:** build pipeline

**Summary:**  
Shifted the main site toward generated JSON artifacts as the primary runtime data layer for works, series, and moments, with lighter collection stubs and index-driven runtime behaviour.

**Reason:**  
The site needed a more consistent and maintainable data flow than page-heavy or mixed-source runtime patterns.

**Effect:**  
The site now relies more heavily on generated JSON contracts and index artifacts, which simplified runtime logic and created a clearer basis for later features such as Studio tooling and search.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `assets/data/works_index.json`
- `assets/data/series_index.json`
- `assets/data/moments_index.json`
- [Data Flow](/docs/?scope=studio&doc=data-flow)
- [Scripts](/docs/?scope=studio&doc=scripts)

**Notes:**  
This entry summarizes the broader architectural shift rather than one single commit.
