---
doc_id: new-pipeline-studio-implementation-plan
title: Studio Implementation Plan
last_updated: 2026-04-18
parent_id: new-pipeline
sort_order: 50
---

# Studio Implementation Plan

This document defines the next phased implementation pass after Phases 0-15 of the JSON-led catalogue pipeline.

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

This roadmap is split into a shared Studio shell phase, Catalogue-focused implementation phases, one priority moments phase, one deferred cloud-native target phase, and parallel planning stubs for other Studio domains.

### Phase 1. Studio Shell And Navigation Foundation

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

Task list:

1. Define the route structure for the four domain dashboards and confirm where they live under `/studio/`.
2. Update the shared Studio shell so the top nav becomes `Catalogue`, `Library`, `Analytics`, `Search`, and `Docs`.
3. Remove any need for extra `/studio/` links outside the four-panel grid.
4. Implement the `/studio/` landing page as a 2x2 domain panel layout with the approved copy.
5. Add one landing dashboard for each domain with space for workflow links, guidance docs, maintenance actions, and lightweight analytics.
6. Implement the first Catalogue dashboard content, including links to work and series edit pages and short workflow summaries.
7. Add the Docs rebuild action beside the docs search field and keep Docs as a nav item rather than a dashboard.
8. Review current Studio routes and move or relabel any entry points that bypass the dashboard structure unnecessarily.
9. Update shared Studio docs so the new landing/navigation model is the documented entry path.

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

### Phase 2. Catalogue Workflow And UI Consistency

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

Verification:

- user can move between Catalogue status, activity, create, edit, bulk edit, and build actions without unclear route jumps
- key Catalogue pages follow the shared Studio UI patterns documented in **[Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)**

Benefits:

- lowers day-to-day operator friction

Risks:

- a subjective polish pass can consume time without improving workflow clarity

### Phase 3. Catalogue Activity And Build Reporting

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
- more direct links from activity rows into affected records or follow-on actions
- stronger conventions for what belongs in Catalogue Activity versus Build Activity

Verification:

- activity pages answer `what changed`, `what rebuilt`, and `what still needs attention`
- import activity stays aggregated by counts rather than turning into an unbounded record dump

Benefits:

- makes Studio feel like an operational front end rather than a set of isolated forms

Risks:

- activity surfaces can become noisy if they try to mirror logs too literally

### Phase 4. Moments Create And Import Workflow

Scope:

- add the first functional Studio-backed moments workflow
- support adding a new moment by specifying a source prose file and associated metadata explicitly
- support targeted import/rebuild for one moment or a small selected set

Out of scope:

- automatic scanning of moment folders for new or changed content
- broad redesign of public `/moments/` runtime behavior

Deliverables:

- a moments-focused Studio entry surface
- create/import flow for a moment based on an explicitly specified file
- targeted moment validation and rebuild hooks
- moments status visibility sufficient for draft/published workflow handling

Verification:

- user can add a new moment without relying on the retired automated scanning flow
- targeted moment import/rebuild succeeds for an explicit file-based workflow
- current moment runtime contracts remain stable unless a change is documented explicitly

Benefits:

- closes a priority workflow gap without recreating the old orchestration model

Risks:

- moment handling can blur into a second large prose-management project if the first phase is not kept narrow

### Phase 5. Media And Prose Readiness

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

### Phase 6. Preview Media In Studio

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

Verification:

- users can visually confirm key records without leaving Studio
- fallback states make missing media obvious without overwhelming the page

Benefits:

- reduces record-identification mistakes during editing

Risks:

- previews can add clutter if they are not kept subordinate to editing tasks

### Phase 7. Prose Local Actions

Scope:

- add local create/open/edit/validate actions for prose where the narrow readiness phase proves insufficient
- bring work and series prose handling further inside the Studio-led workflow

Out of scope:

- moments automation beyond the explicit file-based flow established earlier
- remote prose editing

Deliverables:

- a defined local action boundary for work and series prose files
- Studio-triggered prose create/open/import/validate actions as needed
- clear integration between prose actions and rebuild flows

Verification:

- user can complete normal prose maintenance from Studio without dropping into ad hoc terminal work for routine cases
- prose actions remain explicit and bounded rather than hidden behind unrelated save flows

Benefits:

- pulls another operational side path into the main Studio workflow

Risks:

- scope can expand sharply if prose editing becomes too ambitious too early

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
