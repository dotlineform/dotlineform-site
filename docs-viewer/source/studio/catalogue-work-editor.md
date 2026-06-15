---
doc_id: catalogue-work-editor
title: Catalogue Work Editor
added_date: 2026-04-22
last_updated: 2026-06-14
parent_id: studio
viewable: true
---
# Catalogue Work Editor

- route: `/studio/catalogue-work/`
- current record: `?work=<work_id>`
- draft mode: `?mode=new`
- source records: `studio/data/canonical/catalogue/works.json`

## Browser Modules

`studio/app/frontend/js/`

| Module | Path | Owns |
| --- | --- | --- |
| route entry | `catalogue-work-editor.js` | route startup, focused lookup reads, draft state, validation, dirty state interpretation, modal sequencing, route-ready state, and local-service coordination |
| helper | `catalogue-work-fields.js` | work field metadata, id normalization, series parsing, draft shaping, and source-record payload helpers. |
| helper | `catalogue-work-form.js` | editable field rendering, read-only field rendering, series picker UI behavior, form text synchronization, field value synchronization, field availability, and field validation message rendering. |
| helper | `catalogue-work-sections.js` | current-record preview rendering, readiness rendering, work-detail section rendering, work-owned file/link section rendering, and the summary rail. |
| helper | `catalogue-work-actions.js` | save, create, build-preview, build, prose import, publish/unpublish, media refresh, and delete workflow orchestration for the route. |
| helper | `catalogue-work-selection.js` | work-id parsing, numeric range parsing, search-token matching, search result rendering, search/open control binding, initial URL selection, open-selection, and open-by-id behavior for the route. |
| helper | `catalogue-project-media-picker.js` | project-folder search, source-image file modal rendering, subfolder/file selection state, and derived project media field application. |

The form renderer receives route-owned callbacks for text lookup, field input handling, and route state refresh.
It does not call write services directly.

The section renderer receives route-owned callbacks for text lookup, publication-state checks, embedded file/link actions, and route message writing.
It does not call write services directly.

The action workflow module receives route-owned callbacks for text lookup, status writing, validation, route-state transitions, preview/readiness rendering, and create-mode record opening.
It keeps local-service transport in `catalogue-editor-service-client.js` and does not import route globals.

The selection module receives route-owned callbacks for text lookup, focused lookup reads, route-state transitions, build-preview refresh, and create-mode save/open behavior.
It does not read generated lookup JSON directly and does not own route-state mutation.

## Current Scope

The first implementation covers:

- search by `work_id`
- switch to `new` mode from the same top control row
- create a draft work source record from the work editor route
- open one work record
- open multiple work records by comma-delimited `work_id` values and `start-end` ranges
- open the current search value either by pressing `Enter` in the search input or by using the `Open` button
- edit core scalar metadata fields
- edit optional `project_subfolder` source-image path metadata for work media
- choose source images through a Local Studio project-media picker that fills `project_folder`, `project_subfolder`, and `project_filename`
- show `status` with the Readonly Display treatment controlled by `Publish` / `Unpublish`
- edit ordered work series through a title-search series picker
- bulk-edit core scalar metadata across the selected works
- bulk-change `series_ids` by exact replacement or `+series_id` / `-series_id` diff entries
- show generated read-only fields (`work_id`, `width_px`, `height_px`)
- show a compact current-record media preview at the top of the summary rail
- list the current work's detail records grouped by `section_id` and labeled by `section_title`
- show thumbnail images beside detail rows in those work-detail lists
- cap visible detail rows at 10 per section
- provide per-work detail search by `detail_uid`
- link into the dedicated work detail editor
- provide a direct `new work detail →` entry link to `/studio/catalogue-work-detail/?work=<work_id>&mode=new` for the current work when the work is published
- list the current work's work-owned `downloads` metadata
- list the current work's work-owned `links` metadata
- add, edit, and delete work-owned downloads through modal forms
- add, edit, and delete work-owned links through modal forms
- validate basic field format before save
- save metadata, with published-work saves updating the public catalogue internally
- preview the scoped public update impact for the current work
- show work media readiness plus staged work prose readiness for `var/docs/catalogue/import-staging/works/<work_id>.md`
- refresh local work image derivatives from the displayed source image path without changing source metadata
- run a narrow `Import staged prose` action when the staged work prose Markdown file is ready
- publish draft works through a dedicated `Publish` command
- unpublish public works through a dedicated `Unpublish` command
- when the public update path runs for a published work, stage the resolved source image under `var/catalogue/media/`, generate local srcset derivatives, and copy thumbnails into `site/assets/works/img/`
- delete one work source record in single-record mode
- show saved-state feedback and public-update failure state after save
- expose the shared Studio route-ready attributes on `#catalogueWorkRoot` for browser smoke tests and future automation

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
- `Create` writes source JSON only through `POST /studio/api/catalogue/work/create`
- no public site update runs during create
- after create, the page opens the new work in normal edit mode

Draft works can be found later from Catalogue Drafts using `/studio/catalogue-status/?family=works`.

Work details are added only after the parent work is published. The `new work detail →` link is disabled while the current work is still draft.

## Series Picker

For single-work edit and new mode, the `series` field is a title-search picker backed by the local catalogue service's series-search lookup.

The picker:

- searches by series title, with ids also accepted as a fallback search term
- shows selected series as chips with the title first and the id as secondary context
- stores canonical `series_ids` in the work source record
- blocks create/save when no series is selected

Bulk mode keeps the existing raw `series_ids` input for now because bulk add/remove semantics still use the `+id` / `-id` diff form.

## Local App Migration

The page shell now lives in `studio/app/server/studio/studio_app_views.py` and is mounted at `/studio/catalogue-work/` by `studio/app/server/studio/studio_app_server.py`.
It reuses the existing browser module and calls local-app catalogue endpoints under `/studio/api/catalogue/...`.
The local app adapter reuses the existing catalogue write handler in-process, so save/build/publication behavior stays aligned with the retired sibling service.

Focused smoke coverage:

- `studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`

Required create fields:

- `work_id`
- `title`
- `year`
- `year_display`
- `series_ids`

Edit-only surfaces are disabled while the draft does not yet exist:

- `Delete`
- `Publish`
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
- `status` remains read-only
- an empty touched field clears that field across the selected works
- `series_ids` accepts either a plain comma-delimited replacement list or only `+id` / `-id` diff entries
- detail, file, and link sections are hidden while bulk mode is active
- `Save` internally updates public catalogue output for changed records that are already published
- delete is disabled in bulk mode

## Save Boundary

Current action labels:

- `Save`
  writes work source JSON. If the work is already `published`, the save also runs the internal public catalogue update.
- `Publish`
  appears for saved draft works when the form is clean, required publication fields are valid, and the work already belongs to at least one published series
- `Unpublish`
  appears for published works, ignores unsaved form edits after confirmation, changes source status back to `draft`, and cleans public catalogue output
- `Delete`
  removes the current source record in single-record mode after preview/confirmation

Current save/publication flow:

1. page loads work search and series search lookup payloads through `GET /studio/api/catalogue/read`
2. opening a work fetches one focused work lookup record through `GET /studio/api/catalogue/read?key=catalogue_lookup_work_base&record_id=<work_id>`; that focused payload carries the editable record plus generated runtime context
3. browser computes stale-write protection against the full canonical source record rather than relying on the lookup payload alone
4. user edits form fields
5. `POST /studio/api/catalogue/work/save` sends the current work id, the expected record hash, the normalized record patch, and internal `apply_build: true` when the current work is already `published`
6. the local app adapter validates the full source set, writes `works.json`, refreshes derived lookup payloads, and returns the normalized saved record plus nested public-update status for published saves
7. the page reloads its focused work lookup payload for preview/detail/download/link context, but keeps the canonical saved record as the editable baseline so source-only fields such as `provenance` do not disappear after save
8. `POST /studio/api/catalogue/build-preview` reports the scoped public-update impact for the saved work record and carries work media readiness plus staged work prose readiness
9. the current-record rail resolves a compact work preview from the same public media naming conventions used by the public site

changed image from object-fit: cover to contained natural sizing, with a 70vh / 42rem max-height for very tall images.

10. `Import staged prose` previews `var/docs/catalogue/import-staging/works/<work_id>.md` and writes `studio/data/canonical/catalogue-markdown/works/<work_id>.md` after overwrite confirmation when needed
11. `Publish` and `Unpublish` use `POST /studio/api/catalogue/publication-preview` followed by `POST /studio/api/catalogue/publication-apply`
12. the public update path stages source media under `var/catalogue/media/`, generates local primary and thumbnail derivatives, copies thumbnails into `site/assets/works/img/`, and leaves primary derivatives staged for remote publishing
13. generator lookup now reads `studio/data/canonical/catalogue-markdown/works/<work_id>.md` for public work prose

## Project Media Picker

`project_folder` is a searchable Local Studio field backed by `GET /studio/api/catalogue/project-media?mode=folders`.
It lists direct folders under `DOTLINEFORM_PROJECTS_BASE_DIR/projects`.

Selecting a project folder in single-work or new-work mode opens the image picker modal immediately.
The modal calls `GET /studio/api/catalogue/project-media?mode=files&project_folder=<folder>&project_subfolder=<subfolder>`.
It uses listbox controls for one optional direct subfolder and the image files in the current folder/subfolder.
The modal defaults to no selected subfolder and lists files directly in `project_folder`.
Selecting a subfolder reloads the file list for that subfolder.
The file list selects an available file on open; pressing Enter with the file list focused or pressing the modal OK button commits the selected file and writes the derived fields together:

- `project_folder`: selected direct project folder
- `project_subfolder`: selected direct subfolder, or blank
- `project_filename`: selected image filename

The endpoint rejects absolute paths, `..`, hidden names, and nested subfolder paths.
The browser never receives or stores absolute local filesystem paths.
Bulk mode keeps manual media fields available but disables the image picker button.

## Refresh media

The work media readiness panel exposes `Refresh media` when the saved or draft media-source fields resolve a source image. That action calls the same build endpoint with `media_only: true`, `force: true`, and a transient `media_source` object containing `project_folder`, `project_subfolder`, and `project_filename` from the current draft.

The server overlays those three fields onto the saved work record only for media planning. It does not write `works.json`, rebuild public page/json/search outputs, or change the preview link target.

After the refresh, the editor image element prefers the staged local primary derivative under `var/catalogue/media/works/srcset_images/primary/` and adds a cache-bust token so the regenerated asset is visible in the panel before the record is saved or the primary variants are copied to R2. While that staged preview is active, the caption uses source-image dimensions reported by the media plan when available. Opening the preview still goes to the published work page. Loading or saving the record clears the staged-preview token, so the panel returns to the normal published media URL (`https://media.dotlineform.com/works/img/...`) and saved `width_px`/`height_px` once the JSON source metadata has been committed.

## Route Ready State

The page root `#catalogueWorkRoot` implements the shared Studio ready-state contract:

- `data-studio-ready="false"` during initial route setup
- `data-studio-ready="true"` after the initial empty, new, single-work, or bulk-work render completes
- `data-studio-busy="true"` while route-level commands are running
- `data-studio-busy="false"` when the route is stable for interaction

Route-specific state attributes:

- `data-studio-route="catalogue-work"`
- `data-studio-mode="empty|single|bulk|new"`
- `data-studio-service="available|unavailable"`
- `data-studio-record-loaded="true|false"`

Initial `?work=<work_id>` loading is awaited before the ready attribute switches to `true`, so smoke tests do not need to race the focused lookup payload, source-record hydration, current-record render, detail lists, media preview, or public-update preview.

Bulk save flow:

1. page expands the requested work selection in the browser
2. page uses canonical source records for the bulk-edit baseline and only uses focused lookup records for generated runtime context
3. user edits only the fields that should apply across the selection
4. `POST /studio/api/catalogue/bulk-save` sends selected `work_id` values, expected hashes, scalar field updates, optional series membership operations, and internal `apply_build: true` when the selection includes published records
5. the local app adapter validates the combined source write, writes `works.json` once, refreshes lookup payloads, and returns changed counts plus published-record public-update targets
6. changed draft records remain source-only; changed published records update public catalogue output in the same save response

Delete flow:

1. single-record mode requests `POST /studio/api/catalogue/delete-preview`
2. the server returns blockers, validation errors, and dependent source-record impact
3. blockers and validation errors remain visible in the page status area
4. if preview is clean, the page confirms and sends `POST /studio/api/catalogue/delete-apply`
5. the server deletes the work plus dependent detail records and work-owned file/link metadata in one atomic write bundle
6. if a draft series uses the deleted work as `primary_work_id`, the server clears that draft-only pointer; published series still block deletion until reassigned or unpublished
7. the server removes generated work/detail artifacts, published thumbnails, repo-local staged media, stale public index/search records, per-work tag overrides, and work-storage index entries

The current public update scope is intentionally narrow:

- the current work page/json
- affected series pages
- aggregate series/works/recent indexes
- catalogue search

## Detail Navigation Surface

The work editor now includes a detail navigation section below the main editor.

Locked constraints for this phase:

- grouping follows `section_id`, labels display `section_title`, and section order follows `sort_order` when present
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
- `provenance`
- `artist`
- `downloads`
- `links`

Work prose is no longer edited through a source filename field. Use `Import staged prose` to copy staged Markdown into `studio/data/canonical/catalogue-markdown/works/<work_id>.md`; the generator reads that ID-derived source file for public prose.

## Related References

- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Catalogue Scope](/docs/?scope=studio&doc=data-models-catalogue)
