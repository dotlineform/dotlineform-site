---
doc_id: new-pipeline-studio-implementation-plan
title: Studio Implementation Plan
last_updated: 2026-04-18
parent_id: new-pipeline
sort_order: 50
---

# Studio Implementation Plan

This document defines the next phased implementation pass after Phases 0-15 of the JSON-led catalogue pipeline.

[Phase 1. Studio Shell And Navigation Foundation](#phase-1-studio-shell-and-navigation-foundation)  
[Phase 2. Moments Create And Import Workflow](#phase-2-moments-create-and-import-workflow)  
[Phase 3. Catalogue Workflow And UI Consistency](#phase-3-catalogue-workflow-and-ui-consistency)  
[Phase 4. Catalogue Activity And Build Reporting](#phase-4-catalogue-activity-and-build-reporting)  
[Phase 5. Media And Prose Readiness](#phase-5-media-and-prose-readiness)  
[Phase 6. Preview Media In Studio](#phase-6-preview-media-in-studio)  
[Phase 7. Optional Canonical Prose Management](#phase-7-optional-canonical-prose-management)  
[Phase 8. Media Local Action Surfaces](#phase-8-media-local-action-surfaces)
[Phase 9. Internal Generator Refactor](#phase-9-internal-generator-refactor)  
[Phase 10. End-To-End Testing Checklist And Execution Prep](#phase-10-end-to-end-testing-checklist-and-execution-prep)  
[Phase 11. Cloud-Native Media Target](#phase-11-cloud-native-media-target)

It is now a wider Studio roadmap rather than a catalogue-only refinement note. Catalogue remains the main delivery thread, but Studio shell, navigation, and adjacent domain planning now need to move in parallel so work can continue across the product without waiting for catalogue to become fully complete or fully tested first.

Parallel domain planning lives in:

- **[Library Plan](/docs/?scope=studio&doc=new-pipeline-refine-library)**
- **[Analytics Plan](/docs/?scope=studio&doc=new-pipeline-refine-analytics)**
- **[Search Plan](/docs/?scope=studio&doc=new-pipeline-refine-search)**

## Goals

- establish the Studio shell and navigation early so the real workflow structure is visible
- continue refining the Catalogue domain without requiring it to be fully finished before other domains move forward
- make media, prose, moments, and rebuild behavior operationally clearer before end-to-end testing
- remove transitional implementation shortcuts where they materially affect reliability or maintainability
- define a practical execution checklist for later manual and Codex-run verification

## Non-Goals

- no broad redesign of public runtime contracts unless a specific refinement task proves one is needed
- no remote multi-user CMS work
- no attempt to finish every Studio domain before shipping improvements in one domain
- no recreation of the retired workbook orchestrator as a new all-in-one Studio automation layer

## Current Constraints

- canonical catalogue metadata already lives under `assets/studio/data/catalogue/`
- current Studio pages are functional but still uneven in layout, navigation, and operational cues
- scoped rebuilds still rely on the temporary workbook bridge inside `generate_work_pages.py`
- prose files remain external to canonical source JSON and are not yet Studio-managed records
- R2-backed primary media remains out of scope for current automation

## Working Decisions

- this plan is Studio-wide, but Catalogue remains the primary implementation thread
- Studio landing and top-level navigation should be established early so Catalogue, Library, Analytics, Search, and Docs have a visible home
- Catalogue work does not need to be 100 percent complete or fully tested before adjacent domain planning begins
- moments are a priority workflow and should get their own implementation phase
- the first moments phase should support explicit file-based create/import and rebuild flows, not automated scanning of moment folders
- the first prose/media refinement phase should stay narrow: visibility, readiness, validation, and targeted import/rebuild hooks first
- local create/edit actions for prose and local action surfaces for media belong in later phases
- local web-triggered script endpoints are in scope for repo-local tasks
- R2 automation is out of scope for now but should remain an explicit later target so cloud-native operation stays visible as a product direction

## Phase Structure

This roadmap is split into a completed Studio shell phase, a priority moments phase, Catalogue-focused refinement phases, one deferred cloud-native target phase, and parallel planning stubs for other Studio domains.

### Phase 1. Studio Shell And Navigation Foundation

Status:

- completed on 2026-04-18

Scope:

- redesign `/studio/` so it becomes a true landing page for the four functional domains: `Catalogue`, `Library`, `Analytics`, and `Search`
- establish one landing dashboard for each functional domain so users can enter workflows without reading docs first
- establish top-level Studio navigation as `Catalogue`, `Library`, `Analytics`, `Search`, and `Docs`
- keep `Docs` in the top nav, but do not give it a separate dashboard page
- surface the Docs rebuild action as a button beside the shared docs search field rather than as a dashboard destination
- make current and future pipelines discoverable from domain dashboards through signposted links, workflow summaries, maintenance actions, and lightweight counts
- reflect the live JSON-led workflow boundary so retired workbook commands are not implied anywhere in Studio entry surfaces

Out of scope:

- deep implementation of Library, Analytics, or Search workflows
- broad page-by-page visual redesign

Target state:

- `/studio/` contains a 2x2 panel grid only
- the four panels link to the four domain dashboards: `Catalogue`, `Library`, `Analytics`, and `Search`
- each panel contains only the domain title plus a short description
- no other links are needed on `/studio/`; all routes should be signposted from the domain dashboards
- the Studio top nav mirrors the dashboard structure and also retains `Docs`
- the main public site nav remains unchanged: `Works`, `Library`
- each domain dashboard can contain:
  - links to functional pages
  - links to guidance docs
  - buttons to run maintenance scripts
  - basic analytics such as counts
- the Catalogue dashboard should include direct entry points into work and series editing plus brief summaries of the workflows
- docs should support the workflow, but the dashboards should be sufficient for running the pipelines day to day

Deliverables:

- a `/studio/` home page with a four-panel grid for `Catalogue`, `Library`, `Analytics`, and `Search`
- domain descriptions on the home panels:
  - `Catalogue`: Publish and maintain the works portfolio
  - `Library`: Publish reference and research documents
  - `Analytics`: Tools to support the analysis and contextualisation of the portfolio
  - `Search`: Configure and manage site search
- top navigation aligned to `Catalogue`, `Library`, `Analytics`, `Search`, and `Docs`
- one landing dashboard route for each of the four functional domains
- a Docs rebuild button positioned next to the shared docs search field
- a first Catalogue dashboard with links to work and series editing flows and brief workflow summaries
- initial Library, Analytics, and Search dashboards that establish the entry surface even where deeper workflow implementation is still pending
- Studio-domain top-level nav on Studio and Docs routes only, with the public `Works` / `Library` top-level nav retained for the public site
- the public/studio crossover reduced to the site title link and the footer `studio` link

Delivered:

1. Defined the domain dashboard routes under `/studio/catalogue/`, `/studio/library/`, `/studio/analytics/`, and `/studio/search/`.
2. Implemented the Studio-domain top nav as `Catalogue`, `Library`, `Analytics`, `Search`, and `Docs`.
3. Replaced the old `/studio/` route list with the 2x2 domain landing page.
4. Added landing dashboards for all four Studio domains with workflow links, guidance links, and lightweight metrics.
5. Implemented the first Catalogue dashboard with work/series/status/activity/build entry points and workflow summary copy.
6. Added the Docs rebuild action beside the shared Studio docs search field.
7. Updated shared Studio docs so the dashboard/navigation model is now the documented entry path.

Verification:

- `/studio/` shows only the four domain panels and no extra route list
- user can move from `/studio/` into each domain dashboard directly
- the top nav and landing page describe the same domain structure
- `Docs` remains available from the top nav and the docs search area, without becoming a fifth dashboard
- the Catalogue dashboard provides enough signposting that the user does not need to read docs to find normal pipeline entry points
- no landing or nav copy suggests workbook-led maintenance

Benefits:

- gives Studio a stable information architecture before more page-level refinement lands
- makes dashboards rather than docs the primary way into Studio workflows

Risks:

- this can sprawl into a full Studio redesign if it is not kept structural

### Phase 2. Moments Create And Import Workflow

Status:

- completed on 2026-04-18

Scope:

- add the first functional Studio-backed moments workflow
- support adding a new moment by specifying an explicit source markdown filename on the webpage rather than scanning the `moments/` directory
- support the current metadata model where moment metadata is stored in the `.md` file front matter itself
- support optional image filename handling as explicit metadata, while preserving the current public runtime behavior when an image is missing
- support targeted import/rebuild for one moment or a small selected set

Out of scope:

- automatic scanning of moment folders for new or changed content
- srcset generation or wider media automation
- broad redesign of public `/moments/` runtime behavior

Deliverables:

- a moments-focused Studio entry surface
- file-driven import flow for one existing moment source markdown file
- source preview covering the resolved front matter, source-image state, and current generated/runtime state
- targeted moment validation and rebuild hooks
- moments status visibility sufficient for draft/published workflow handling without adding browser-side prose editing

Delivered:

1. Added `/studio/catalogue-moment-import/` as the first moments-focused Studio route.
2. Implemented filename-only preview/apply flow against the canonical moments source folder.
3. Added local write-service endpoints for moment import preview and apply.
4. Added targeted rebuild support in `catalogue_json_build.py` for `--moment-file`.
5. Reused the existing generator behavior so moment publish state and `published_date` remain generator-owned.
6. Kept missing source images non-blocking and left srcset generation out of scope.
7. Added first-pass build and catalogue activity reporting for moment imports.
8. Updated Studio/docs references so the file-driven moments path is now the documented entry flow.

Verification:

- user can add a new moment without relying on the retired automated scanning flow
- targeted moment import/rebuild succeeds for an explicit file-based markdown workflow
- the saved metadata shape matches the current moment front matter model
- missing images remain acceptable and the current public `/moments/.../` UI still handles them cleanly
- current moment runtime contracts remain stable unless a change is documented explicitly

Benefits:

- closes a priority workflow gap without recreating the old orchestration model

Risks:

- moment handling can blur into a second large prose-management project if the first phase is not kept narrow

### Phase 3. Catalogue Workflow And UI Consistency

Status:

- completed on 2026-04-18

Scope:

- align list, editor, status, and action patterns across work, detail, series, file, and link pages
- reduce dead ends after create, save, save-and-rebuild, import, bulk edit, and delete flows
- make related-record navigation more legible

Out of scope:

- new record families
- major changes to the underlying write or build boundaries

Deliverables:

- a consistent button hierarchy and action wording across Catalogue pages
- clearer return paths after create and delete flows
- clearer bulk-edit entry and exit behavior
- more legible draft/published and rebuild-needed states

Delivered:

1. Reworked the Catalogue dashboard from a card-grid route list into grouped directional link sections for create, edit, review, and guidance flows.
2. Added a shared Catalogue page-link strip across Catalogue-domain pages so the main workflow surfaces are mutually discoverable without returning to docs.
3. Normalized Catalogue metadata forms onto a single-column row layout with labels on the left and shared control/button sizing.
4. Made `/studio/catalogue-work-file/` and `/studio/catalogue-work-link/` standalone dashboard destinations by adding first-class search-and-open controls.
5. Extended Catalogue Status so it now links directly into all current editor families rather than only work records.
6. Made Catalogue Status sortable by clicking the list headers for `id`, `type`, `status`, `title`, and `reference`.
7. Kept the existing site visual language rather than introducing a separate Catalogue-only component style.

Verification:

- user can move between Catalogue status, activity, create, edit, bulk edit, and build actions without unclear route jumps
- key Catalogue pages follow the shared Studio UI patterns documented in **[Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)**

Notes:

On Catalogue dashboard, use a grouped vertical stack of links rather than panels as the links to pages. The links should be directional: e.g. Edit Work, Create New Work
check all the pages are navigable from dashboard e.g. /studio/catalogue-work/

UI elements should mirror existing site pages rather than introduce new patterns:

- metadata input boxes should be vertically stacked in a single column with labels to the left
- guidance notes should be centralised in a single panel where possible. obvious signposts to other pages should be links and not plain text
- lists should be minimal and by default fill content width, allowing new columns to be added easily
- lists are by default sortable by clicking headers
- items are only formatted as pills when the pill serves a recognisable purpose (e.g. colour coding, is clickable)
- buttons should all have same style and height
- text boxes should all be same height except for obvious candidates where expandability is useful e.g. ‘notes’

Task list:

1. Rework the Catalogue dashboard entry area from card panels into grouped directional link lists, with labels such as `Edit Work`, `Create New Work`, `Edit Series`, and `Import Moment`.
2. Audit all current Catalogue routes and make sure every live page is reachable from the dashboard, including direct signposts to routes such as `/studio/catalogue-work/`, `/studio/catalogue-series/`, `/studio/catalogue-status/`, `/studio/catalogue-activity/`, `/studio/build-activity/`, `/studio/bulk-add-work/`, and `/studio/catalogue-moment-import/`.
3. Define one shared pattern for Catalogue page headers so each page consistently shows the page title, current context, status/result messaging, and directional links back to the dashboard or next likely action.
4. Normalize action wording across Catalogue pages so create, save, rebuild, import, preview, delete, and navigation actions use one consistent verb set and button hierarchy.
5. Refactor metadata forms to a single-column vertical stack, with labels aligned on the left and input controls using shared widths, heights, and spacing.
6. Identify which fields should remain fixed-height inputs and which should become expandable text areas, then apply that rule consistently across work, detail, series, file, and link pages.
7. Consolidate guidance copy into one clear guidance panel per page where possible, and convert any plain-text references to other Studio routes into explicit links.
8. Review all list and table surfaces and switch them to the default minimal full-width list pattern so additional columns can be added later without redesigning the component.
9. Make sortable headers the default for list/table views where header-based sorting is appropriate, and remove one-off list-specific sorting affordances where they create inconsistency.
10. Review all current pill treatments and keep pills only where they communicate a distinct function such as state, color coding, or clickability; convert decorative pills back to plain text or links.
11. Standardize button styling and control height across Catalogue pages, including dashboard links where button-like actions currently use mismatched sizing.
12. Tighten post-action navigation so create, save, delete, import, and rebuild flows always leave the user with an obvious next step, link, or return path.
13. Run a page-by-page consistency pass across work, detail, series, file, link, status, activity, bulk-add, and moment-import pages, and capture any remaining exceptions explicitly rather than leaving them as accidental drift.


Benefits:

- lowers day-to-day operator friction

Risks:

- a subjective polish pass can consume time without improving workflow clarity

### Phase 4. Catalogue Activity And Build Reporting

Status:

- completed on 2026-04-18

Scope:

- improve operational visibility for save, create, import, delete, bulk-edit, and rebuild flows
- clarify the separation between Catalogue Activity and Build Activity
- strengthen links back to affected records and next actions

Out of scope:

- full field-level before/after diff views
- raw log dumping into Studio pages

Deliverables:

- clearer aggregated activity summaries for source writes and rebuilds
- clearer surfaced rebuild consequences after scoped runs
- more direct links from activity and build rows into affected records or follow-on actions
- cleaner list UI, more consistent with other Studio lists with sortable column headers, split 'Scoped rebuild' and 'Saved' into a status column, separate column for the actual scope (work detail xxx, works xxx...)
- stronger conventions for what belongs in Catalogue Activity versus Build Activity

Delivered:

1. Separated the two activity feeds more cleanly so `Catalogue Activity` now tracks source-side events while `Build Activity` carries rebuild/run outcomes.
2. Reworked both pages from expandable narrative cards into sortable operational lists with separate columns for type, status, scope, result or follow-up, and next action.
3. Added explicit scope labels to both feeds so rows now identify concrete targets such as `work 00460`, `work detail 00460-005`, or `moment keys`.
4. Added direct row-level links from activity rows into the relevant editor or follow-on route where a practical next step exists.
5. Tightened `Catalogue Activity` so source saves, imports, deletes, and validation failures remain visible without mixing in `build.apply` rows.
6. Tightened `Build Activity` so scoped rebuild rows surface their scope and search-rebuild outcome more directly.
7. Extended source-activity feed shaping so work-file and work-link events can identify their own record scope rather than only the parent work.

Verification:

- activity pages answer `what changed`, `what rebuilt`, and `what still needs attention`
- import activity stays aggregated by counts rather than turning into an unbounded record dump

Benefits:

- makes Studio feel like an operational front end rather than a set of isolated forms

Risks:

- activity surfaces can become noisy if they try to mirror logs too literally

Task list:

1. Review the current `catalogue_activity.json` and `build_activity.json` entry shapes and define one clear responsibility boundary for each page, so source-write events stay on Catalogue Activity and rebuild/run outcomes stay on Build Activity.
2. Decide which event families should appear in Catalogue Activity by default, covering save, create, import, delete, bulk-edit, validation failure, and any source-side no-op or conflict outcomes that materially affect operator follow-up.
3. Decide which run families should appear in Build Activity by default, covering scoped rebuilds, wider catalogue builds, no-op runs, failed runs, and any planner/build modes that still need to remain visible during the transition from older labels.
4. Replace any overly prose-heavy row summaries with clearer structured columns so the main list surfaces answer `when`, `what happened`, `what scope`, and `what next` at a glance.
5. Rework both activity pages onto the shared minimal full-width Studio list pattern, with sortable column headers and column naming that matches the rest of the Catalogue UI.
6. Split current mixed status text into clearer columns, so labels such as `Saved` and `Scoped rebuild` are treated as event/run type or status rather than bundled into one ambiguous summary field.
7. Add a dedicated scope column that explicitly shows what the action targeted, for example `work 01234`, `work detail 01234-002`, `series 009`, `moment keys`, or `bulk import`.
8. Define one compact convention for showing affected ids: keep counts visible by default, sample ids only where useful, and avoid expanding either page into an unbounded record dump.
9. Add direct row-level links back into the relevant Catalogue routes, including focused editor pages, Catalogue Status, Build Activity, or other next-step destinations where the event naturally leads the user onward.
10. Make sure activity rows surface whether further action is still needed, for example rebuild pending after a source save, validation follow-up after a failed write, or record review after a targeted import.
11. Tighten Build Activity so scoped JSON rebuild consequences are easier to read, including which records rebuilt, whether search regenerated, and whether the run was effectively a no-op.
12. Tighten Catalogue Activity so bulk add and moment import activity stays aggregated by counts and summaries, not as a long list of per-record write rows.
13. Review whether any current event data needs small backend feed changes to support the new columns and links, and document those schema additions before changing the page UI.
14. Run a final consistency pass across both activity pages so they feel like paired operational surfaces rather than two unrelated report pages with overlapping language.

### Phase 5. Media And Prose Readiness

Status:

- completed on 2026-04-18

Scope:

- make media and prose state visible inside Catalogue workflows
- define when metadata-only changes are sufficient and when follow-on actions are still required
- add targeted import/rebuild hooks for prose-driven updates without requiring browser-based editing yet

Out of scope:

- browser-based prose editing
- full media automation
- R2 upload or remote media management

Deliverables:

- explicit media/prose readiness states on relevant Catalogue surfaces
- build preview reporting that includes media/prose readiness where it materially affects a work
- clear signposting for external prose files and local media expectations
- targeted prose import/rebuild hooks for work and series prose flows

Verification:

- user can tell whether a record is metadata-complete but still blocked on prose or media follow-up
- prose is no longer a hidden side path outside the main Catalogue workflow

Benefits:

- reduces partial publish states and hidden workflow gaps

Risks:

- too much readiness detail can make editors noisy if it is not prioritised carefully

Implemented:

1. Added one compact readiness model to scoped build preview, covering work media, work prose, series prose, and detail media with consistent `ready`, `not configured`, `missing file`, `missing metadata`, and `unavailable` states.
2. Surfaced work media and work prose readiness directly on `/studio/catalogue-work/`, including resolved source paths and explicit next-step messaging.
3. Surfaced series prose readiness directly on `/studio/catalogue-series/`, including primary-work folder dependency handling and explicit next-step messaging.
4. Surfaced detail media readiness directly on `/studio/catalogue-work-detail/`, using detail-specific preview data rather than only the parent work scope.
5. Extended `POST /catalogue/build-preview` so detail previews can include `detail_uid` and return the relevant readiness rows without creating a separate detail rebuild planner.
6. Added narrow `Import prose + rebuild` actions on the work and series editors, reusing the existing scoped build endpoint rather than introducing a second prose pipeline.
7. Kept media actions out of scope for this phase; media readiness is visible, but derivative generation remains a later implementation phase.
8. Kept the UI compact by placing readiness in the existing right-hand summary area rather than adding new panels or routes.

### Phase 6. Preview Media In Studio

Status:

- completed on 2026-04-18

Scope:

- improve identification of the current work, detail, file, or link record through visual context

Out of scope:

- media editing
- rich preview components that are not operationally useful

Deliverables:

- primary image preview on the work editor
- detail image previews in the detail editor and relevant list contexts
- explicit fallback states for missing source media and missing generated media
- limited file/link preview treatment only where it helps identify the record

steer:
- small image preview with caption - can fit at top of the ‘current record’ panel
- details lists would be improved by being more consistent with /series/ list which includes thumbnail image

Verification:

- users can visually confirm key records without leaving Studio
- fallback states make missing media obvious without overwhelming the page

Benefits:

- reduces record-identification mistakes during editing

Risks:

- previews can add clutter if they are not kept subordinate to editing tasks

Implemented:

1. Reused the public media conventions already used on `/works/`, `/work_details/`, and `/series/`, including existing thumb sizes, suffixes, and asset-format assumptions.
2. Added a compact current-record preview block to the top of the work editor summary rail.
3. Added a compact current-record preview block to the top of the detail editor summary rail.
4. Kept both preview blocks small and captioned so they support identification without displacing source/readiness controls.
5. Improved work-detail rows on the work editor so they now use small thumbnails and a more consistent list pattern.
6. Added fallback states on focused work/detail previews to distinguish generated preview missing, source media missing, and readiness not configured.
7. Kept preview rendering out of bulk mode.
8. Reviewed work-file and work-link editors and kept them text-first for now; no preview surface was added in this phase.

### Phase 7. Optional Canonical Prose Management

Status:

- deferred unless prose stops being external/imported-only and becomes a Studio-managed canonical source

Scope:

- only pursue a further prose phase if work and series prose need to become repo-native, Studio-managed source records
- treat this as a separate prose-authoring project rather than a continuation of the current import-led workflow

Out of scope:

- the existing external-file import flow delivered in Phase 5
- ad hoc local actions where import and rebuild are already sufficient
- moments automation beyond the explicit file-based flow established earlier
- browser-based markdown editing unless separately justified and planned
- remote prose editing

Deliverables:

- an explicit architecture decision: prose remains external/imported, or prose becomes repo-native and Studio-managed
- if prose becomes repo-native, a separate implementation plan covering storage, editing, validation, rebuild, and migration
- no implementation work in this phase unless that architecture decision changes

Verification:

- the current plan is explicit that no further prose work is needed after Phase 5 for the external-file model
- any future prose-authoring work is separated into its own dedicated plan rather than leaking into catalogue refinement by accident

Benefits:

- prevents the catalogue roadmap from drifting into an unscoped prose-authoring project

Risks:

- if prose authoring is needed later, the work is substantial and should not be treated as a small follow-on task

### Phase 8. Media Local Action Surfaces

Scope:

- add local web-triggered action surfaces for repo-local media tasks such as thumbnail copy or srcset generation where those actions are safe and operationally clear

Out of scope:

- R2 automation
- remote source-media management
- bundling every media action into one opaque `publish` operation

Deliverables:

- local action endpoints or controlled command surfaces for repo-local media tasks
- explicit status/result reporting for those actions inside Studio
- integration with media readiness states so required follow-up work is visible before and after actions run

Verification:

- user can trigger the supported local media tasks from Studio without relying on terminal commands
- action surfaces report clear success/failure states and affected records

Benefits:

- reduces reliance on terminal-only operational steps for local workflows

Risks:

- broad or implicit automation could recreate the confusion of the retired orchestrator

### Phase 9. Internal Generator Refactor

Scope:

- remove the temporary workbook bridge from the live JSON rebuild path
- refactor `generate_work_pages.py` so JSON-source rebuilds operate from normalized records directly

Out of scope:

- public runtime contract redesign
- unrelated cleanup in the generator codebase

Deliverables:

- native normalized-record JSON generation path
- retained workbook-shaped compatibility only where still needed for comparison or import-related tooling
- before/after artifact comparison coverage

Verification:

- the live JSON rebuild path no longer depends on materializing `works.xlsx`
- generated artifacts remain equivalent aside from expected timestamps or documented metadata differences

Benefits:

- removes the last major internal coupling to the retired workbook-led model

Risks:

- this is the highest technical-risk phase because it touches the runtime writer path

### Phase 10. End-To-End Testing Checklist And Execution Prep

Scope:

- turn the current broad testing ideas into a concrete execution checklist
- define the manual and Codex-run verification split

Out of scope:

- recording test results inside this planning document
- pretending the checklist is full QA automation

Deliverables:

- a separate end-to-end execution checklist document
- scenario coverage for create, edit, bulk edit, import, delete, rebuild, media/prose readiness, and moments flows
- explicit desktop and mobile checks for key Studio pages

Verification:

- a future session can execute the checklist step by step without reinterpreting the plan
- checklist steps map clearly to the implemented Studio surfaces and commands

Benefits:

- creates a practical bridge from implementation to confidence-building review

Risks:

- testing can become unfocused if the checklist is not tied to the actual phase outcomes above

### Phase 11. Cloud-Native Media Target

Scope:

- capture the future target state in which source media management can move toward R2-backed or otherwise cloud-native workflows

Out of scope:

- current implementation
- current local-media task replacement

Deliverables:

- a documented target-state phase describing the desired cloud-native media boundary
- identified dependencies on source-media location, credentials, write services, and safe remote action design
- explicit statement that current Studio media actions remain local-first until this phase is intentionally started

Verification:

- the roadmap preserves cloud-native media as an explicit future direction rather than an implied idea

Benefits:

- keeps long-term architecture visible without forcing premature remote automation

Risks:

- readers may misread this as current scope unless it is labelled clearly as deferred

## Parallel Domain Plans

These domains should now develop in parallel as planning tracks, even where implementation remains lighter than Catalogue in the short term:

- **[Library Plan](/docs/?scope=studio&doc=new-pipeline-refine-library)** for `/library/` maintenance workflows and their Studio administration boundary
- **[Analytics Plan](/docs/?scope=studio&doc=new-pipeline-refine-analytics)** for tagging and future analytical tooling
- **[Search Plan](/docs/?scope=studio&doc=new-pipeline-refine-search)** for search configuration, validation, pipelines, and operational visibility

This document should only absorb work from those domains when the work directly affects the shared Studio shell or Catalogue workflows.

## Suggested Sequence

Suggested order:

1. Studio shell and navigation foundation
2. Catalogue workflow and UI consistency
3. Moments create and import workflow
4. Catalogue activity and build reporting
5. Media and prose readiness
6. Preview media in Studio
7. Prose local actions
8. Media local action surfaces
9. Internal generator refactor
10. End-to-end testing checklist and execution prep
11. Cloud-native media target

Reasoning:

- Studio structure and navigation need to land early so later work has a stable home
- moments are a priority workflow gap and should be addressed before lower-value polish
- media/prose readiness should be explicit before local action surfaces expand
- the generator refactor should happen before end-to-end execution passes depend on the current temporary bridge
- the cloud-native media target should stay visible but deferred

## Deliverables For The Next Session

- confirm or adjust the phase order
- choose the first implementation phase
- create the separate end-to-end execution checklist document when the earlier phase outcomes are concrete enough to test against
