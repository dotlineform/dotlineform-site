---
doc_id: catalogue-work-editor
title: "Catalogue Work Editor"
added_date: 2026-04-22
last_updated: 2026-04-29
parent_id: user-guide
sort_order: 30
---
# Catalogue Work Editor

Route:

- `/studio/catalogue-work/`
- focused record selection uses `?work=<work_id>`
- new draft mode uses `?mode=new`

This page edits canonical work source records from `assets/studio/data/catalogue/works.json` and writes changes through the local catalogue write service. It now supports focused single-record edit, bulk edit, and draft create mode on the same route.

The retired `/studio/catalogue-new-work/` route redirects immediately to `/studio/catalogue-work/?mode=new`.

## Current Scope

The first implementation covers:

- search by `work_id`
- switch to `new` mode from the same top control row
- create a draft work source record from the work editor route
- open one work record
- open multiple work records by comma-delimited `work_id` values and `start-end` ranges
- open the current search value either by pressing `Enter` in the search input or by using the `Open` button
- edit core scalar metadata fields
- edit ordered work series through a title-search series picker
- bulk-edit core scalar metadata across the selected works
- bulk-change `series_ids` by exact replacement or `+series_id` / `-series_id` diff entries
- show generated read-only fields (`work_id`, `width_px`, `height_px`)
- show a compact current-record media preview at the top of the summary rail
- list the current work's detail records grouped by `project_subfolder`
- show thumbnail images beside detail rows in those work-detail lists
- cap visible detail rows at 10 per section
- provide per-work detail search by `detail_uid`
- link into the dedicated work detail editor
- provide a direct `new work detail →` entry link to `/studio/catalogue-work-detail/?work=<work_id>&mode=new` for the current work
- list the current work's work-owned `downloads` metadata
- list the current work's work-owned `links` metadata
- add, edit, and delete work-owned downloads through modal forms
- add, edit, and delete work-owned links through modal forms
- validate basic field format before save
- save source JSON only
- preview the scoped rebuild impact for the current work
- show work media readiness plus staged work prose readiness for `var/docs/catalogue/import-staging/works/<work_id>.md`
- refresh local work image derivatives from the displayed source image path without changing source metadata
- run a narrow `Import staged prose` action when the staged work prose Markdown file is ready
- save with an optional `Update site now` path through the local catalogue service
- when `Update site now` runs for a published work, stage the resolved source image under `var/catalogue/media/`, generate local srcset derivatives, and copy thumbnails into `assets/works/img/`
- delete one work source record in single-record mode
- show saved-state feedback and rebuild-needed state after save

It does not yet:

- edit work details inline on the work page
- edit series records directly
- upload primary images to remote media storage
- paginate detail/member lists

## New Mode

New mode is entered from either:

- `/studio/catalogue-work/?mode=new`
- the `New` button beside `Open`

In new mode:

- the top input becomes the new `work_id` input
- the suggested next id is prefilled when available
- `status` is visible but fixed to `draft`
- `published_date` is unavailable until the record exists
- `Create` writes source JSON only through `POST /catalogue/work/create`
- no public site update runs during create
- after create, the page opens the new work in normal edit mode

Draft works can be found later from Catalogue Status using `/studio/catalogue-status/?view=draft-works`.

## Series Picker

For single-work edit and new mode, the `series` field is a title-search picker backed by `assets/studio/data/catalogue_lookup/series_search.json`.

The picker:

- searches by series title, with ids also accepted as a fallback search term
- shows selected series as chips with the title first and the id as secondary context
- stores canonical `series_ids` in the work source record
- blocks create/save when no series is selected

Bulk mode keeps the existing raw `series_ids` input for now because bulk add/remove semantics still use the `+id` / `-id` diff form.

Required create fields:

- `work_id`
- `title`
- `year`
- `year_display`
- `series_ids`

Edit-only surfaces are disabled while the draft does not yet exist:

- `Delete`
- `Update site now`
- generated dimensions
- public work link
- preview and readiness panels
- details
- downloads
- links

## Bulk Mode

Bulk mode is entered by opening more than one `work_id` from the search field.

Current bulk-selection rules:

- comma-delimited explicit ids are supported
- `start-end` ranges are supported
- explicit ids and ranges can be mixed in the same selection

Current bulk-edit behavior:

- the page stays on `/studio/catalogue-work/`
- untouched fields preserve per-record values
- an empty touched field clears that field across the selected works
- `series_ids` accepts either a plain comma-delimited replacement list or only `+id` / `-id` diff entries
- detail, file, and link sections are hidden while bulk mode is active
- `Save` can optionally run one scoped work rebuild per affected work scope after the bulk source save
- delete is disabled in bulk mode

## Save Boundary

Current action labels:

- `Save`
  writes source JSON and can optionally also update the public catalogue immediately when the saved work is published
- `Update site now`
  appears only when a published source record has been saved but runtime publication is still pending
- `Delete`
  removes the current source record in single-record mode after preview/confirmation

Current save/rebuild flow:

1. page loads derived lookup payloads for work search and series lookup, plus the canonical `assets/studio/data/catalogue/works.json` source map for editable work fields
2. opening a work fetches one focused work lookup record from `assets/studio/data/catalogue_lookup/works/<work_id>.json` for generated runtime context, but the editable form baseline comes from the canonical source record
3. browser computes stale-write protection against the full canonical source record rather than relying on the lookup payload alone
4. user edits form fields
5. `POST /catalogue/work/save` sends the current work id, the expected record hash, the normalized record patch, and optional `apply_build: true`; the editor and write server ignore `apply_build` unless the saved work status is `published`
6. the local write server validates the full source set, writes `works.json`, refreshes derived lookup payloads, and returns the normalized saved record plus nested build status when the user chose `Update site now` for a published work
7. the page reloads its focused work lookup payload for preview/detail/download/link context, but keeps the canonical saved record as the editable baseline so source-only fields such as `notes` and `provenance` do not disappear after save
8. `POST /catalogue/build-preview` reports the scoped rebuild impact for the saved work record
9. the same preview now also carries work media readiness and staged work prose readiness
10. the current-record rail resolves a compact work preview from the same public media naming conventions used by the public site
11. `Import staged prose` previews `var/docs/catalogue/import-staging/works/<work_id>.md` and writes `_docs_src_catalogue/works/<work_id>.md` after overwrite confirmation when needed
12. `POST /catalogue/build-apply` remains available for explicit follow-up update actions on published works; it stages source media under `var/catalogue/media/`, generates local primary and thumbnail derivatives, copies thumbnails into `assets/works/img/`, and leaves primary derivatives staged for remote publishing
13. generator lookup now reads `_docs_src_catalogue/works/<work_id>.md` for public work prose

The work media readiness panel also exposes `Refresh media` when the configured source image exists. That action calls the same build endpoint with `media_only: true` and `force: true`, so it refreshes thumbnails and staged primary variants from the displayed source path without saving metadata or rebuilding page/json/search outputs. The result message is `Thumbnails updated; primary variants staged for publishing.`

Bulk save flow:

1. page expands the requested work selection in the browser
2. page uses canonical source records for the bulk-edit baseline and only uses focused lookup records for generated runtime context
3. user edits only the fields that should apply across the selection
4. `POST /catalogue/bulk-save` sends selected `work_id` values, expected hashes, scalar field updates, optional series membership operations, and optional `apply_build: true`
5. the local write server validates the combined source write, writes `works.json` once, refreshes lookup payloads, and returns changed counts plus rebuild targets
6. when `apply_build` is true, the same save response also reports the nested site-update result; otherwise the page leaves `Update site now` available as a follow-up action

Delete flow:

1. single-record mode requests `POST /catalogue/delete-preview`
2. the server returns blockers, validation errors, and dependent source-record impact
3. if preview is clean, the page confirms and sends `POST /catalogue/delete-apply`
4. the server deletes the work plus dependent detail/file/link source records in one atomic write bundle
5. the server removes generated work/detail artifacts, published thumbnails, repo-local staged media, stale public index/search records, per-work tag overrides, and work-storage index entries

The current rebuild scope is intentionally narrow:

- the current work page/json
- affected series pages
- aggregate series/works/recent indexes
- catalogue search

## Detail Navigation Surface

The work editor now includes a detail navigation section below the main editor.

Locked constraints for this phase:

- grouping follows `project_subfolder`
- each section shows at most 10 rows by default
- the detail search box searches within the current work by `detail_uid`
- the detail search box only appears when at least one section exceeds the fixed visible row limit
- works with multiple detail sections render as multiple grouped lists
- this area is navigation into the detail editor, not inline editing

## Files And Links

The work editor includes editable sections for work-owned files and links.

Current behavior:

- list current `downloads` entries from the work source record
- list current `links` entries from the work source record
- `Add file`, `Edit`, and `Delete` mutate the draft `downloads` array
- `Add link`, `Edit`, and `Delete` mutate the draft `links` array
- modal edits are local draft changes until the parent work is saved
- clearing the final download or link omits the empty array from `works.json` after save
- downloads require `filename` and `label`
- links require `url` and `label`

The retired standalone work-file and work-link editors no longer own canonical writes. The work editor is the normal editing surface for work-owned file and link metadata.

## Current Editable Fields

- `status`
- `published_date`
- `series_ids`
- `project_folder`
- `project_filename`
- `title`
- `year`
- `year_display`
- `medium_type`
- `medium_caption`
- `duration`
- `height_cm`
- `width_cm`
- `depth_cm`
- `storage_location`
- `notes`
- `provenance`
- `artist`
- `downloads`
- `links`

Work prose is no longer edited through a source filename field. Use `Import staged prose` to copy staged Markdown into `_docs_src_catalogue/works/<work_id>.md`; the generator reads that ID-derived source file for public prose.

## Related References

- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
