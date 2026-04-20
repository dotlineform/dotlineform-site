---
doc_id: new-pipeline-implementation-plan
title: "Implementation Plan"
last_updated: 2026-04-18
parent_id: new-pipeline
sort_order: 40
---

# Implementation Plan

This document records the phased implementation from the workbook-led catalogue pipeline to the JSON-led Studio workflow.

## Phase 0: Baseline And Migration Fixture

Goal:

- establish a safe baseline before changing the generator or UI

Work:

- add `scripts/export_catalogue_source.py` to read `data/works.xlsx` and write proposed JSON source files under `assets/studio/data/catalogue/`
- include `Works`, `Series`, `SeriesSort`, `WorkDetails`, `WorkFiles`, and `WorkLinks`
- normalize IDs and field names during export
- include migration metadata in `meta.json`
- add `scripts/validate_catalogue_source.py` to read the exported JSON source and report the same classes of errors as the current workbook preflight
- add `scripts/compare_catalogue_sources.py` to load workbook source and JSON source into normalized records and report differences
- keep shared Phase 0 source loading and normalization logic in `scripts/catalogue_source.py`

Acceptance:

- exported JSON contains the same effective source data as `data/works.xlsx`
- validation passes on exported JSON
- comparison against workbook-normalized records is empty or only contains documented normalization differences
- no runtime-critical JSON files are changed by this phase
- source JSON headers are deterministic and avoid volatile timestamps

Benefits:

- creates the canonical JSON candidate without changing runtime behavior
- gives later phases test fixtures

Risks:

- hidden workbook quirks such as formula cache values, numeric ID coercion, or blank columns may export differently
- field naming decisions made here become sticky

Mitigation:

- keep exporter repeatable
- compare normalized records, not raw cell formatting
- document every intentional difference

## Phase 1: JSON Source Adapter For Generation

Goal:

- let `generate_work_pages.py` build existing runtime artifacts from JSON source instead of the workbook

Work:

- add an explicit internal JSON-run boundary to `generate_work_pages.py`
- use `scripts/catalogue_source.py` to load canonical source JSON and remove the temporary workbook bridge from the live rebuild path
- keep any retained workbook-shaped compatibility in-memory and isolated from the live JSON runtime boundary
- write generator-updated mutable fields back into canonical source JSON directly after JSON-source write runs
- compare generated artifacts across the transitional paths while the workbook-led tooling still exists

Acceptance:

- JSON-source generation writes the same route stubs and runtime JSON payloads as workbook-source generation for the current catalogue, aside from expected generated timestamp differences
- existing public runtime JSON schemas remain unchanged
- `assets/data/series_index.json`, `assets/data/works_index.json`, `assets/data/recent_index.json`, and per-record JSON contracts remain stable
- workbook-shaped compatibility remains available only where still needed for import or comparison tooling, not as the live rebuild path

Benefits:

- separates source truth from Excel before building UI
- preserves public site behavior

Risks:

- generator code currently interleaves workbook reads, workbook writes, and artifact writes
- recent-index publish transitions depend on status changes
- the temporary workbook bridge is transitional and should not become the final architecture

Mitigation:

- refactor in small adapter seams, starting with a compatibility bridge
- keep current artifact writer functions intact where possible
- test draft-to-published transitions against fixture copies
- move toward native normalized-record generation in later phases once JSON-source behavior is proven

## Phase 2: Local Catalogue Write Service

Goal:

- add a localhost-only service that can safely write canonical catalogue source JSON

Work:

- create `scripts/studio/catalogue_write_server.py`
- implement `GET /health`
- implement `POST /catalogue/work/save`
- enforce CORS and loopback binding
- implement source file allowlist
- implement backup bundle writes
- implement minimal event logging
- add shared request/response helpers or copy the smallest safe pattern from `tag_write_server.py`
- update `bin/dev-studio` to start the catalogue write service after the first UI needs it

Acceptance:

- server can update one work record in `works.json`
- writes create backups
- invalid writes are rejected
- only allowlisted source JSON and backup/log paths are writable
- existing tag write service behavior is unchanged

Benefits:

- creates the write boundary needed for Studio catalogue pages

Risks:

- accidental broadening of local write scope
- duplicate server code with tag write service

Mitigation:

- keep first implementation separate and narrow
- extract shared utilities only after the catalogue service proves stable

## Phase 3: Status Review And Activity Surfaces

Goal:

- make non-published records and local catalogue activity visible early in Studio

Work:

- add a status review page listing source records where `status` is not `published`
- group status rows by works, work details, series, work files, and work links
- link each status row to its focused editor when that editor exists
- add counts by record family
- add a catalogue activity page modelled on `/studio/build-activity/`
- write a small Studio-facing activity summary artifact such as `assets/studio/data/catalogue_activity.json`
- surface local write events, validation failures, imports, and build runs as those capabilities become available
- provide easy access to underlying log references even before a complete field-level change UI exists
- implemented first increment as `/studio/catalogue-status/`, `/studio/catalogue-activity/`, `assets/studio/data/catalogue_activity.json`, and `scripts/catalogue_activity.py`

Acceptance:

- user can find all draft, blank, or otherwise non-published source records without opening Excel
- user can see recent catalogue source saves and build/import events in Studio
- the activity page can start as a compact log index and does not need to render every field-level change

Benefits:

- replaces useful CLI awareness early
- creates a place to surface pipeline behavior as implementation scope grows
- gives the user a daily maintenance entry point before all editors exist

Risks:

- activity UI can become too ambitious too early
- status review may surface warnings before validators are fully mature

Mitigation:

- start with simple status grouping and operation summaries
- link to logs for detail rather than building a full diff viewer first
- add validation-warning filters only after shared validation summaries exist

## Phase 4: Single Work Metadata Editor

Goal:

- deliver the first useful Studio UI increment: edit metadata for one work

Work:

- add a Studio route for work editing
- add work search by `work_id`
- load `works.json`, `series.json`, and current generated indexes as needed
- render a form for core work metadata
- implement dirty state, validation messages, save button, and saved-state feedback
- save through `POST /catalogue/work/save`
- add UI copy to `assets/studio/data/studio_config.json`
- document the page under Studio docs after implementation

Acceptance:

- user can search for a work by ID
- user can edit and save one work's metadata
- canonical JSON source updates
- backups are written
- invalid values are rejected
- no public runtime artifacts are changed until generation is explicitly run

Benefits:

- proves the end-to-end local edit path with low UI scope

Risks:

- users may expect save to update the public site immediately
- the first editor loads full `works.json` and `series.json` into the browser, which is acceptable for the current catalogue size but should not become the long-term loading model

Mitigation:

- label source save and rebuild actions separately
- show "source changed, rebuild needed" state after save
- implemented first increment as `/studio/catalogue-work/` with work-id search, single-record metadata editing, and local source save
- replace full-source page loads in a later phase with narrower lookup/query loading, such as focused record fetches plus lightweight search/index payloads

## Phase 5: Scoped Build From JSON Source

Goal:

- make edited JSON source flow into existing public runtime artifacts

Work:

- add a command path for JSON-source generation of selected work IDs
- add a build preview that reports affected work IDs, series IDs, and search rebuild need
- add a local endpoint or documented command for `Save and rebuild`
- rebuild catalogue search after scoped generation
- update build activity logging to support JSON-source builds
- implemented first increment as `scripts/catalogue_json_build.py`, `POST /catalogue/build-preview`, `POST /catalogue/build-apply`, and `Save + Rebuild` on `/studio/catalogue-work/`

Acceptance:

- editing one work and running rebuild updates `_works/<work_id>.md`, `assets/works/index/<work_id>.json`, aggregate indexes as needed, and catalogue search
- generated public JSON schemas remain unchanged
- current Jekyll build still succeeds

Benefits:

- closes the loop from Studio edit to public site update

Risks:

- planner behavior may be duplicated between old `build_catalogue.py` and new JSON build preview

Mitigation:

- reuse planner helper functions where possible
- treat the old workbook planner as transitional

## Phase 6: Work Detail Editor

Goal:

- add detail metadata maintenance after the single-work editor is stable

Work:

- list a work's details on the work editor
- group detail lists by `project_subfolder`
- cap visible detail rows at 10 per section on the work editor
- add per-work detail search by `detail_uid` so long sections remain navigable
- keep the work editor detail area as navigation into the detail editor, not inline detail editing
- add a detail editor route
- implement search/open by `detail_uid`
- implement save endpoint for one detail record
- validate parent work references
- support scoped rebuild for the parent work

Acceptance:

- user can edit a work detail's title, status, project subfolder, and project filename
- works with multiple detail sections render as multiple grouped lists on the work editor
- sections with more than 10 details still remain reachable by per-work detail search
- source JSON updates
- parent work rebuild updates detail page stubs and work JSON sections

Benefits:

- covers the second major editing family without changing series logic yet

Risks:

- detail section grouping depends on `project_subfolder`
- dimension updates may need media source access
- works with more than 100 details can create unwieldy editor pages

Mitigation:

- keep dimensions read-only in the UI initially
- rely on the generator/media probe to refresh dimensions
- keep the work page at 10 visible rows per section and use detail search instead of rendering full long lists

## Phase 7: Series Editor And Membership Changes

Goal:

- edit series metadata and change work-to-series relationships

Work:

- add series search by title
- add series editor route
- edit series scalar fields and `sort_fields`
- display member works by scanning source `works.json`
- preserve each work's `series_ids` order exactly as edited; do not sort membership lists during save
- allow adding/removing works from a series by updating work `series_ids`
- allow changing a work's primary series by reordering `series_ids`
- validate `primary_work_id` membership
- implement save endpoint that can write both `series.json` and affected `works.json`

Acceptance:

- user can edit series metadata
- user can change a work's series
- works that belong to multiple series keep their edited `series_ids` order
- generated `series_index.json` remains equivalent to current behavior after rebuild
- invalid `primary_work_id` states are blocked

Benefits:

- moves the core relationship model out of Excel

Risks:

- membership edits touch both series behavior and work records
- duplicate series titles can make search ambiguous
- series with more than 100 works can create unwieldy membership editors

Mitigation:

- route and save by `series_id`
- always show `series_id` in search results and editor headings
- use preview for multi-record membership edits
- reuse the same capped list pattern used for work details, with member search for longer lists

## Phase 8: Source Access Optimisation

Goal:

- replace full-source browser page loads with narrower read models before larger editors and bulk tools depend on them

Work:

- add lightweight search/index payloads for work and series lookup
- add focused record fetches for work, detail, and series editors
- place the new read artifacts under `assets/studio/data/catalogue_lookup/`
- keep canonical source JSON unchanged while adding browser-efficient read artifacts
- avoid requiring editors to load full `works.json` or `series.json` to open one record
- keep the new read path compatible with later bulk-edit and activity surfaces

Acceptance:

- the work editor no longer needs full `works.json` and `series.json` in the browser to open and edit one work
- search/open remains fast and stable
- canonical source JSON remains unchanged
- new read artifacts stay explicitly non-canonical

Benefits:

- keeps the early editor implementation from becoming a structural constraint
- reduces browser coupling to full source payloads before larger Studio features arrive

Risks:

- extra read artifacts can become shadow source if ownership is unclear

Mitigation:

- keep canonical source JSON as the only write target
- label read artifacts as derived lookup payloads
- keep search/index artifacts narrow and deterministic

## Phase 9: Add New Series

Goal:

- support adding a series without opening Excel

Work:

- add new-series route
- allow explicit `series_id`
- validate uniqueness and required metadata
- save new series as `draft` by default
- allow draft series to exist without `primary_work_id`
- keep `primary_work_id` required before a series can be published to runtime
- optionally add initial member works in later increments
- save `series.json` plus affected `works.json`
- add build preview for new series once the series is publishable

Acceptance:

- user can create a new series from Studio
- draft series can be saved before member works and `primary_work_id` are complete
- source JSON is valid
- scoped build is blocked until a publishable `primary_work_id` is set
- generation creates the expected series route and JSON after rebuild once the series is publishable

Benefits:

- removes a common reason to return to the workbook

Risks:

- ID policy may be unclear for new series
- users may forget to return and assign `primary_work_id` after draft creation

Mitigation:

- start with explicit user-entered IDs
- add suggested ID helpers only after the JSON source is stable
- surface draft series without `primary_work_id` in status review and keep rebuild blocked until the field is valid

## Phase 10: Add New Work And Work Detail Records

Goal:

- support creating catalogue records from Studio

Work:

- add create-work flow
- derive or suggest next work ID
- add create-detail flow under a work
- derive next detail ID within the selected work
- validate required fields before saving
- leave source media placement unchanged
- show media filename/path expectations instead of uploading media
- keep this phase scoped to single-record creation in Studio; do not assume bulk-add via web UI
- implement the first increment as narrow draft-create pages that redirect into the existing work and detail editors after save

Acceptance:

- user can create a draft work record
- user can create draft detail records for a work
- the work editor provides a direct entry point into detail creation for the current work
- media scripts can still copy and derive images using the same source path conventions

Benefits:

- moves day-to-day additions into Studio

Risks:

- creating metadata before media exists can generate warnings
- pushing bulk-add into Studio too early would create a higher-complexity UI without clear day-to-day value

Mitigation:

- allow draft records with missing media
- surface media warnings clearly in build preview
- keep workbook import available for bulk-add workflows in a later phase
- defer any multi-record create UI unless a clear use case appears

## Phase 11: Work Files And Work Links

Goal:

- replace the remaining `WorkFiles` and `WorkLinks` workbook editing workflows in Studio

Work:

- add work-files summary to the work editor
- add work-links summary to the work editor
- add focused add/edit/delete flows for work-file records
- add focused add/edit/delete flows for work-link records
- validate parent `work_id` on save
- preserve existing work-page metadata contracts fed by files and links
- add local write endpoints for work-file and work-link saves and deletes
- include affected parent work IDs in rebuild preview/apply responses
- keep files and links as focused child editors, not large inline work-page forms

Acceptance:

- user can maintain `WorkFiles` records for a work without opening Excel
- user can maintain `WorkLinks` records for a work without opening Excel
- source JSON remains valid after file/link updates
- scoped rebuild of the parent work updates the expected work-page metadata

Benefits:

- closes a real workbook dependency that still feeds published work-page metadata
- keeps the work editor as the operational hub for work-attached child records

Risks:

- files and links are easy to treat as secondary, even though they affect public metadata
- adding too much inline editing to the work page could turn it into an unbounded editor

Mitigation:

- keep files and links as focused work-attached child editors, similar to work details
- keep the initial UI narrow: list current records on the work editor and open focused add/edit flows for changes
- implemented first increment as work-editor file/link summaries plus focused create/edit routes for `WorkFiles` and `WorkLinks`

## Phase 12: Workbook Import And Export

Goal:

- keep Excel useful for bulk adding without making it canonical again

Work:

- add one Studio route for workbook import with two modes: `works` and `work_details`
- read a fixed workbook source at `data/works.xlsx`
- works import adds new work records only
- work-details import adds new detail records only
- imported records default to `draft`
- ignore workbook `status` fields during import
- do not write anything back into the workbook
- works import requires referenced series to already exist in canonical source
- work-details import requires the parent work to already exist in canonical source
- preview reports importable rows, duplicates, blocked rows, and blocked reasons
- duplicate existing records are reported and skipped, not updated
- apply is blocked while invalid workbook rows remain
- write aggregated import counts into Catalogue Activity, not one entry per imported record

Acceptance:

- user can import new work records from `data/works.xlsx` without opening JSON files
- user can import new work-detail records from `data/works.xlsx` without opening JSON files
- existing source records are reported as duplicates and are not overwritten
- canonical source JSON remains valid after import
- workbook remains a transient import surface rather than a write target

Benefits:

- keeps the bulk-add workflow available
- avoids forcing a complex bulk-create web UI before it proves necessary

Risks:

- workbook could become a shadow source again

Mitigation:

- make import one-way into JSON
- allow only additive imports in this phase
- block apply when workbook rows are invalid
- require the user to clear imported workbook rows after successful apply

## Phase 13: Bulk Edit

Goal:

- replace the remaining Excel filtering and fill-down metadata workflows for existing records

Work:

- add bulk-edit mode to the existing work editor and work-detail editor pages
- treat a comma-delimited list or `-` ranges in the editor search field as a bulk selection
- support bulk edits for work core metadata only; exclude work files and work links
- support bulk edits for work-detail metadata only
- exclude bulk series metadata editing
- support work `series_ids` changes in bulk mode
- allow a plain comma-delimited `series_ids` list to replace memberships for the selected works
- allow `+series_id` and `-series_id` entries to add or remove memberships for the selected works without sorting the resulting `series_ids` list
- apply one validated source write per bulk operation, with stale-hash checks for every selected record
- return changed counts and affected work scopes for rebuild
- keep rebuild as a follow-on scoped work rebuild, not a separate bulk build system

Acceptance:

- user can bulk-edit work metadata from the work editor by entering multiple `work_id` values or ranges
- user can bulk-edit work-detail metadata from the work-detail editor by entering multiple `detail_uid` values or same-work detail ranges
- untouched fields preserve per-record values across the selected set
- an empty touched field clears that field across the selected set
- invalid records block apply
- affected work IDs are returned for rebuild

Benefits:

- preserves the main productivity advantage of spreadsheet editing for existing records while keeping source writes inside validated JSON workflows

Risks:

- bulk operations can damage many records quickly
- bulk mode can become confusing if it tries to look like single-record edit while behaving differently
- bulk series membership changes can accidentally replace memberships when the intent was additive or subtractive

Mitigation:

- keep bulk edit on the existing editor pages instead of adding a separate surface
- keep the initial selector model narrow: explicit IDs plus ranges only
- show mixed-value hints and require fields to be touched before they apply
- distinguish replace vs add/remove behavior for bulk `series_ids`
- include changed count and unchanged count
- write one backup bundle per apply
- keep initial operations narrow
- keep initial bulk-edit scope focused on metadata changes to existing records, not bulk creation

## Phase 14: Delete Workflows

Goal:

- replace workbook-led and script-led delete workflows with explicit Studio preview/apply delete flows

Work:

- add delete preview and apply endpoints for works, work details, and series
- add delete buttons to the work, work-detail, and series editor pages
- keep work and work-detail delete disabled while those pages are in bulk-edit mode
- validate dependent impacts before delete apply
- make work delete preview include dependent details, files, links, generated outputs, and series-primary impacts
- make series delete preview include member work impacts and primary-work consequences
- keep media and prose cleanup rules explicit rather than implicit

Acceptance:

- user can preview delete impact before removing a work, work detail, or series
- delete apply blocks when the source model would become invalid
- affected runtime rebuild scopes are identified clearly
- the delete workflow no longer depends on workbook status flags

Benefits:

- makes destructive operations explicit and reviewable

Risks:

- delete behavior has more edge cases than metadata edits
- overreaching delete cleanup can remove files the user intended to keep

Mitigation:

- preview before apply
- backup bundle before write
- keep source-record deletion separate from optional media/prose cleanup
- start with clearly bounded delete scope and expand only where behavior is deterministic

## Phase 15: Retire Workbook-Led Pipeline

Goal:

- make the JSON-led Studio workflow the only live catalogue workflow

Work:

- keep workbook import available only through the dedicated import flow
- retire direct workbook-led entrypoints such as `build_catalogue.py`, `copy_draft_media_files.py`, and `export_catalogue_source.py`
- keep `generate_work_pages.py` as an internal JSON-build engine rather than a user-facing command
- remove user-facing dual-mode guidance from active docs
- archive legacy workbook-led docs under the docs viewer archive and mark them deprecated
- update active docs so they describe only the JSON-led Studio workflow and current validation/build helpers

Acceptance:

- normal catalogue maintenance no longer requires opening or saving `data/works.xlsx`
- `data/works.xlsx` is not used to edit currently published works
- workbook-led commands exit cleanly with deprecation guidance instead of running legacy behavior
- the active docs viewer surfaces only the JSON-led workflow while retaining deprecated references in the archive
- public runtime artifacts remain stable
- the current scoped JSON build flow remains the live rebuild path

Benefits:

- removes testing confusion caused by legacy command paths that still imply workbook ownership

Risks:

- old habits and old bookmarks may still send the user toward retired scripts or docs

Mitigation:

- make active docs explicit
- add warnings to retired workbook commands
- keep the current JSON-source validation and build commands simple

## Cross-Phase Risks

### Data Loss

Risk:

- local write endpoints overwrite source JSON incorrectly

Mitigation:

- backups before every write
- atomic writes
- stale version/hash checks
- preview/apply for multi-record changes

### Source Drift

Risk:

- source JSON and generated runtime JSON fall out of sync

Mitigation:

- show rebuild-needed state after source saves
- build preview reports affected IDs
- audit script checks source versus generated artifacts

### Runtime Contract Regressions

Risk:

- refactoring generator source input changes public JSON payloads

Mitigation:

- compare generated artifacts from workbook and JSON source
- preserve artifact writer functions first
- run Jekyll build and catalogue audit after generator changes

### Recent Index Semantics

Risk:

- publish transition detection changes when status is stored in JSON instead of Excel

Mitigation:

- isolate publish transition logic
- test draft-to-published transitions
- preserve snapshot behavior for `/recent/`

### Series Membership Integrity

Risk:

- editing work `series_ids` and series `primary_work_id` independently creates invalid state

Mitigation:

- server-side cross-file validation
- series editor writes affected work records in the same operation
- block invalid primary work references

### Large Record Sets

Risk:

- a few series have more than 100 works and a few works have more than 100 details
- naive editor pages could become slow, visually noisy, or hard to navigate

Mitigation:

- use pagination, progressive loading, or grouped lists for large memberships and detail sets
- reuse existing catalogue page list and pager models where practical
- keep focused editor pages separate from long summary lists

### Media Decoupling

Risk:

- no longer orchestrating media from `build_catalogue.py` could leave source metadata published before media derivatives exist

Mitigation:

- build preview includes media readiness warnings
- keep media copy/srcset commands visible in Studio
- avoid changing media file conventions

### Local Server Safety

Risk:

- adding more write endpoints broadens local write risk

Mitigation:

- separate catalogue write service
- narrow allowlists
- loopback-only binding
- localhost-only CORS
- minimal logs

## Recommended First Implementation Slice

The first implementation should include only:

1. export workbook to canonical source JSON
2. validate source JSON
3. load one work in Studio by `work_id`
4. edit and save one work's metadata to `works.json`
5. keep generation manual until JSON-source generation is proven

This slice is intentionally not a complete CMS. It proves the new source truth and write boundary with the smallest useful UI.
