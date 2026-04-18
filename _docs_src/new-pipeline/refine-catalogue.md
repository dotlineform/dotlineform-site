---
doc_id: new-pipeline-refine-catalogue
title: Refine Catalogue
last_updated: 2026-04-18
parent_id: new-pipeline
sort_order: 50
---

# Refine Catalogue

This document defines the next planning pass after Phases 0-15 of the JSON-led catalogue pipeline.

The main implementation is now in place:

- canonical catalogue metadata is maintained in Studio-owned JSON
- Studio supports create, edit, delete, bulk edit, import, and scoped rebuild flows
- workbook-led pipeline entrypoints are retired from the live workflow

The next stage is refinement rather than architectural replacement. The goal is to improve usability, operational clarity, and confidence in the end-to-end workflow before wider review and testing.

## Goals

- make the Studio catalogue workflow easier to understand and safer to use
- tighten the end-to-end handling of media, prose, and rebuild activity around the new metadata flow
- remove remaining implementation shortcuts that are now acceptable only as transition scaffolding
- define a practical test checklist for manual and Codex-run verification

## Non-Goals

- no redesign of public catalogue runtime contracts unless a refinement task proves one is necessary
- no remote multi-user CMS work
- no broad tags-system redesign
- no speculative refactor without a clear workflow or maintenance payoff

## Current Constraints

- canonical metadata already lives under `assets/studio/data/catalogue/`
- media storage conventions remain unchanged
- scoped rebuilds still use the internal temporary workbook bridge inside `generate_work_pages.py`
- prose files are still external to canonical source JSON and are not yet first-class Studio-managed records
- current UI is functional but intentionally narrow and lightly refined

## Workstreams

### 1. Studio Workflow And UI Consistency

Focus:

- align list, form, button, and action patterns across work, detail, series, file, and link pages
- reduce dead ends and unclear next actions after create, save, rebuild, import, and delete flows
- improve navigation between related records and operational pages

Candidate work:

- review button hierarchy and wording across editors
- make next-step signposting consistent after save, save-and-rebuild, create, import, and delete
- review list summaries for works-in-series and details-on-work so counts, search, and caps read consistently
- review where the user is returned after destructive or create actions
- make status, rebuild-needed, and draft/published state more legible without adding visual noise
- review bulk-edit mode transitions and exit paths on work and detail pages

Acceptance:

- a user can move between status review, single-record edit, bulk edit, create, import, and activity pages without unclear route jumps
- shared Studio patterns are applied consistently enough that new catalogue pages do not feel like separate tools

Benefits:

- lowers operator friction
- reduces accidental misuse caused by inconsistent cues

Risks:

- UI refinement can sprawl into subjective redesign

Mitigation:

- keep refinement grounded in current documented Studio UI patterns
- prefer targeted consistency passes over broad visual rework

### 2. Studio Landing Page And Navigation

Focus:

- redesign the Studio landing page so the new catalogue workflow is visible and easy to enter

Candidate work:

- add clear entry points for:
  - catalogue status
  - work search/edit
  - series search/edit
  - bulk add work
  - catalogue activity
  - build activity
- separate everyday catalogue actions from lower-frequency maintenance actions
- make the current workflow boundary obvious so retired workbook commands are not implied anywhere in the UI

Acceptance:

- the landing page reflects the real current catalogue workflow rather than the earlier tag/build emphasis

### 3. Media Handling And Srcset Workflow

Focus:

- make the metadata workflow and media workflow fit together cleanly now that the workbook orchestrator is retired

Candidate work:

- document and possibly add Studio-facing signposting for when source media or srcset generation is still required
- define how missing media should be surfaced before or after rebuild
- review whether media readiness checks belong in build preview, status review, or dedicated maintenance surfaces
- decide whether any lightweight local action surface is needed for media copy/srcset commands

Acceptance:

- the user can tell when a metadata change is enough on its own and when media work is still required

Benefits:

- reduces partial publish states where metadata is updated but media is not ready

Risks:

- overly broad media automation could recreate the confusion of the retired orchestrator

Mitigation:

- keep media handling explicit and separate unless a concrete workflow proves safe to combine

### 4. Preview Media In Studio

Focus:

- make it easier to confirm the right work, detail, file, or linked media record is being edited

Candidate work:

- show the current primary image in the work editor
- show detail image previews in the detail editor and detail list context
- consider file/link previews only where they improve identification rather than clutter the page
- define clear fallback states for missing source media or missing generated media

Acceptance:

- users can visually confirm key records without leaving the editor or opening public pages

### 5. Prose File Handling

Focus:

- define how work and series prose should fit into the Studio-led catalogue workflow

Candidate work:

- document the current prose boundary clearly
- decide whether Studio should:
  - only signpost prose file locations
  - surface prose presence/state without editing
  - support opening, creating, or validating prose files locally
- review how missing prose should appear in editors and build previews
- consider whether prose readiness belongs in catalogue status or a separate maintenance view

Acceptance:

- prose handling is no longer a hidden side path outside the main workflow

Risks:

- direct prose editing inside Studio could broaden scope sharply

Mitigation:

- start with visibility and workflow signposting before considering browser editing

### 6. Catalogue Activity And Build Reporting

Focus:

- improve operational visibility without turning activity pages into raw logs

Candidate work:

- improve catalogue activity summaries for save, create, import, delete, and bulk-edit flows
- clarify what belongs in Catalogue Activity versus Build Activity
- surface aggregated rebuild consequences more clearly after scoped rebuilds
- review whether the current feed should expose more links back to affected records or actions
- keep import reporting aggregated by counts rather than dumping long record lists

Acceptance:

- activity pages help the user answer:
  - what changed
  - what rebuilt
  - what still needs attention

### 7. Internal Generator Refactor

Focus:

- remove the internal temporary workbook bridge that still underpins scoped JSON rebuilds

Candidate work:

- refactor `generate_work_pages.py` so normal JSON-source runs read normalized records directly from `JsonCatalogueSource`
- remove temporary workbook materialization from the live JSON build path
- keep workbook-shaped compatibility only where still needed for comparison or import-related tooling
- compare generated artifacts before and after refactor to confirm runtime stability

Acceptance:

- the live JSON rebuild path no longer depends on materializing `works.xlsx`
- generated artifacts remain equivalent aside from expected timestamps or documented metadata differences

Benefits:

- removes the last major internal coupling to the retired workbook-led model

Risks:

- this is the highest technical-risk refinement task because it touches the runtime writer path

Mitigation:

- isolate the refactor
- compare outputs before and after
- keep the public artifact contracts unchanged

### 8. End-To-End Testing Checklist

Focus:

- define a practical checklist for manual review and Codex-run verification across the whole workflow

Candidate checklist areas:

- create draft series without `primary_work_id`
- assign membership and publishability conditions
- create draft work
- create draft work detail
- edit work metadata and rebuild
- edit series membership while preserving `series_ids` order
- add/edit/delete work files and work links
- bulk import works and work details from `data/works.xlsx`
- bulk edit work metadata and work-detail metadata
- delete work detail, work, and series with correct blockers
- verify status and activity surfaces after each class of action
- verify build activity after scoped rebuilds
- verify missing-media and missing-prose states
- verify desktop and mobile rendering of key Studio pages

Acceptance:

- the checklist is concrete enough that a future implementation/testing session can execute it step by step

## Suggested Sequencing

Suggested order:

1. Studio workflow and UI consistency
2. Studio landing page and navigation
3. Catalogue activity and build reporting
4. Media handling and srcset workflow
5. Preview media in Studio
6. Prose file handling
7. End-to-end testing checklist
8. Internal generator refactor

Reasoning:

- workflow clarity should improve before deeper testing
- media and prose boundaries should be explicit before the checklist is finalized
- the internal generator refactor should come after the current flow is easier to test and compare

## Open Questions

- should Studio eventually expose lightweight media actions, or only explain the external commands?
- should prose remain external-only, or should Studio own some part of prose creation/validation?
- should build preview report media/prose readiness explicitly, or should those become separate status surfaces?
- how much of catalogue activity should link directly back to editor routes?
- should the Studio landing page become a workflow dashboard rather than a simple page list?

## Deliverables For The Next Session

- review and adjust this refinement plan
- choose the first refinement workstream to implement
- define the end-to-end testing document as a separate execution checklist rather than embedding test results into this plan
