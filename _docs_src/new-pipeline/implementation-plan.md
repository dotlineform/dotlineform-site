---
doc_id: new-pipeline-implementation-plan
title: Implementation Plan
last_updated: 2026-04-17
parent_id: new-pipeline
sort_order: 40
---

# Implementation Plan

This document defines a phased path from the current workbook-led catalogue pipeline to a JSON-led Studio workflow.

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

- add `--source json` and `--source-dir` to `generate_work_pages.py`
- keep `xlsx` as the default source during migration
- use `scripts/catalogue_source.py` to load canonical source JSON and materialize a temporary workbook adapter
- run the existing artifact writer against the temporary workbook so current runtime contracts stay stable
- sync generator-updated mutable fields back into canonical source JSON after JSON-source write runs
- compare generated artifacts from workbook mode and JSON mode

Acceptance:

- JSON-source generation writes the same route stubs and runtime JSON payloads as workbook-source generation for the current catalogue, aside from expected generated timestamp differences
- existing public runtime JSON schemas remain unchanged
- `assets/data/series_index.json`, `assets/data/works_index.json`, `assets/data/recent_index.json`, and per-record JSON contracts remain stable
- workbook mode still works as a fallback

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

Acceptance:

- user can create a draft work record
- user can create draft detail records for a work
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

## Phase 12: Workbook Import And Export

Goal:

- keep Excel useful for bulk adding without making it canonical again

Work:

- add import preview for `data/works.xlsx` or a selected workbook
- support `add-new-only`
- support `update-draft-only`
- reject updates to published existing records by default
- add export-to-workbook/report command if useful for offline review

Acceptance:

- new records can be staged from a workbook into source JSON
- published existing JSON records are not overwritten in default import mode
- preview reports all blocked rows and normalization decisions

Benefits:

- keeps the bulk-add workflow available
- avoids forcing a complex bulk-create web UI before it proves necessary

Risks:

- workbook could become a shadow source again

Mitigation:

- make import one-way into JSON
- block published-record overwrites by default
- label exported workbooks as reports or import templates, not canonical source

## Phase 13: Bulk Edit

Goal:

- replace Excel filtering/fill-down use cases with safer preview/apply flows

Work:

- add bulk edit route
- implement selectors for work ID range, explicit IDs, works in series, details under work, and explicit detail UIDs
- implement scalar set/clear operations
- implement series membership operations
- implement preview endpoint
- implement apply endpoint with backup bundle

Acceptance:

- user can apply one metadata field change to a range of works
- preview lists old and new values before apply
- invalid records block apply
- affected IDs are returned for rebuild

Benefits:

- preserves the main productivity advantage of spreadsheets while reducing accidental edits

Risks:

- bulk operations can damage many records quickly
- bulk web UI can become more complex than the actual need if it tries to absorb bulk-add workflows that workbook import already covers

Mitigation:

- require preview before apply
- include changed count and unchanged count
- write one backup bundle per apply
- keep initial operations narrow
- keep initial bulk-edit scope focused on metadata changes to existing records, not bulk creation

## Phase 14: Retire Workbook-Led Pipeline

Goal:

- make JSON source the default and workbook source optional

Work:

- make JSON source the default for generation
- refactor `generate_work_pages.py` so normal JSON-source generation reads normalized records directly from `JsonCatalogueSource`
- remove the temporary workbook materialization bridge from normal `--source json` runs
- keep the workbook reader only for legacy fallback, source comparison, and workbook import/export workflows
- update pipeline docs and script docs
- demote `build_catalogue.py` to legacy or replace it with JSON-source build commands
- keep workbook import/export commands documented separately
- remove workbook status/dimension writeback from normal runs

Acceptance:

- normal catalogue maintenance no longer requires opening or saving `data/works.xlsx`
- `data/works.xlsx` is not used to edit currently published works
- JSON-source generation no longer depends on creating a temporary workbook
- generated artifacts remain equivalent to the Phase 1 bridge output, aside from expected timestamps or documented version metadata changes
- public runtime artifacts remain stable
- media scripts remain available but are not coupled to workbook orchestration

Benefits:

- reaches the target operating model

Risks:

- old habits and old commands may still update the workbook

Mitigation:

- make command docs explicit
- add warnings to legacy workbook commands
- keep JSON-source validation and build commands simple

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
