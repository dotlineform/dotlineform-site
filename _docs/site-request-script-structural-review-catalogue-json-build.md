---
doc_id: site-request-script-structural-review-catalogue-json-build
title: Catalogue JSON Build Slices
added_date: 2026-05-09
last_updated: "2026-05-09 20:05"
ui_status: in-progress
parent_id: site-request-script-structural-review
sort_order: 50
viewable: true
---
# Catalogue JSON Build Slices

Status:

- initial implementation tracker created
- Slice 0 planned

## Purpose

This child doc tracks the detailed review and implementation tasks for restructuring `scripts/catalogue_json_build.py`.
The parent [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review) stays focused on the broader candidate queue, shared acceptance criteria, and completed priority summaries.

The intended end state is not to make the scoped build entrypoint small for its own sake.
`catalogue_json_build.py` should remain the supported CLI and Studio-callable orchestration entrypoint for focused catalogue rebuilds, while scope planning, local media planning/execution, field-aware build reduction, command construction, and subprocess result shaping get explicit owners where the boundary is stable and useful.

## Current Shape

`scripts/catalogue_json_build.py` currently owns several responsibilities in one file:

- CLI argument parsing for work, series, detail, moment, changed-field, force, write, and media-only modes
- source-dir and projects-base-dir detection
- work, series, detail, and moment scoped build planning
- field-aware build planning through the catalogue field registry
- source media resolution and readiness summaries
- local media derivative planning and execution with `ffmpeg`
- generator and search subprocess command construction
- subprocess execution, result payload assembly, and preview reporting
- compatibility wrappers used by Studio catalogue write flows

That mix creates maintenance risk because a small scoped-build change can require understanding source lookup, readiness copy, local media state, generated artifact selection, search rebuild policy, subprocess behavior, and CLI output together.

## Target Boundary

The scoped build entrypoint should keep:

- CLI parsing and top-level mode selection
- high-level orchestration between scope planning, optional local media work, generator runs, and search rebuilds
- user-facing preview/report output
- compatibility function names used by Studio write flows until call sites are intentionally updated

Extracted module owners should take:

- pure scope construction for work, series, detail, and moment builds
- source media resolution and readiness item construction
- local media task planning and derivative execution
- field-aware build-plan application to a scope
- generator/search command construction
- subprocess result normalization

Keep `scripts/generate_work_pages.py` as the internal generator engine.
Do not change generated payload schemas, search behavior, media output paths, CLI flags, response payload keys consumed by Studio, or write behavior as part of the structural slices unless a later slice explicitly records that contract change.

## Slice Principles

- Start with a read-only extraction map before moving code.
- Move behavior in narrow slices with direct tests against the owning module.
- Keep the CLI surface, preview output meaning, write behavior, media output paths, and generated command shapes stable.
- Keep filesystem writes and subprocess execution out of pure planning modules.
- Avoid broad re-export layers; update internal call sites to use the owning module explicitly once behavior moves.
- Do not reorganize script folders as part of this tracker; package/path moves belong to [Scripts Directory Organization Request](/docs/?scope=studio&doc=site-request-scripts-directory-organization).

## Initial Acceptance Criteria

- `./scripts/catalogue_json_build.py --work-id <work_id>` still previews the same internal generator and search command shape.
- `./scripts/catalogue_json_build.py --series-id <series_id>` still previews the same scoped work/series generation behavior.
- `./scripts/catalogue_json_build.py --moment-file <moment_id>.md` still previews the same moment generation behavior.
- `--write`, `--force`, `--media-only`, `--changed-fields`, and `--record-family` keep their current meanings.
- Local media staging and public asset output paths stay stable.
- Studio catalogue write flows keep receiving the same result payload keys.
- Focused tests cover each extracted owner directly.
- Syntax checks pass after every Python slice.
- Script docs are updated when module ownership or command behavior changes.

## Planned Slice Sequence

The sequence below should be revised after the read-only map.

### Slice 0: read-only extraction map

Status: planned.

Task:

- map `catalogue_json_build.py` by responsibility, call dependencies, and external contracts
- identify which functions can move without binding CLI state, filesystem writes, subprocess execution, or user-facing report wording
- record concrete module names and test files before implementation starts

Likely output:

- update this doc with final proposed module owners
- no code movement in this slice

Acceptance checks:

- map identifies scope planning, media readiness, local media execution, field-aware planning, command construction, subprocess orchestration, and CLI/reporting boundaries
- map calls out any behavior that should stay in `catalogue_json_build.py` because it binds command-line state or user-facing preview/report output

### Slice 1: scoped build planning helpers

Status: planned.

Likely module owner:

- `scripts/catalogue_build_scopes.py`

Target ownership:

- work scope construction
- series scope construction
- moment scope construction
- buildability validation for scoped series
- scope summary construction
- moment source preview metadata that does not require subprocess execution

The entrypoint should keep:

- CLI parsing
- source-dir binding
- final preview/report wording
- orchestration between scopes, media, generator, and search

Tests:

- add focused tests for work, series, moment, extra ids, detail uid inclusion, invalid series scopes, and stable scope payload keys

### Slice 2: local media planning and readiness

Status: planned.

Likely module owner:

- `scripts/catalogue_build_media.py`

Target ownership:

- project-base detection helpers used by media lookup
- work/detail/moment source media resolution
- media readiness item construction
- local media state checks
- local media task planning
- local media derivative execution with dependency-injected process runner where practical

The entrypoint should keep:

- whether a run selected media work
- how media status is summarized in the top-level result payload
- user-facing preview/report placement

Tests:

- pin source path resolution, missing metadata reasons, pending/current/blocked/unavailable states, force behavior, staged output paths, and dry-run write suppression

### Slice 3: field-aware build-plan adapter

Status: planned.

Likely module owner:

- `scripts/catalogue_build_field_plan.py`

Target ownership:

- changed-field token normalization
- record-family inference
- field registry plan lookup
- application of field plans to scoped build payloads
- explanation line construction

The entrypoint should keep:

- CLI argument parsing for `--changed-fields` and `--record-family`
- where explanation lines appear in preview output

Tests:

- pin work/detail/series/moment family inference, empty changed-field behavior, media-only reductions, search rebuild reductions, and generator `--only` reductions

### Slice 4: generator/search command construction and execution results

Status: planned.

Likely module owner:

- `scripts/catalogue_build_commands.py`

Target ownership:

- generator command construction for work/series scopes
- generator command construction for moment scopes
- catalogue search command construction
- subprocess step result normalization

The entrypoint should keep:

- top-level command ordering decisions
- preview/report wording
- final success/failure status mapping

Tests:

- pin command argv shapes for work, series, moment, write, force, refresh-published, and search rebuild modes
- pin failure-result payload shape without running real subprocesses

### Slice 5: final orchestration cleanup

Status: planned.

Task:

- simplify `catalogue_json_build.py` around explicit module calls
- remove helpers that have moved
- keep compatibility wrappers only where current Studio call sites still need them
- keep CLI surface and Studio build response contract stable

Tests and checks:

- run syntax checks for changed Python modules
- run focused tests for extracted modules
- run representative dry-run previews for work, series, and moment scopes
- run the smallest relevant run-checks profile if shared catalogue behavior changed broadly enough to justify it

## Validation Plan

Codex-run checks should include:

- syntax checks for changed Python modules
- focused tests for new extracted modules
- `./scripts/catalogue_json_build.py --work-id 00008`
- `./scripts/catalogue_json_build.py --series-id 105`
- `./scripts/catalogue_json_build.py --moment-file leaves.md`
- a `--changed-fields` preview for one work scope after field-plan slices
- a `--media-only` preview after media slices

Manual checks should include:

- confirm Studio work, series, and moment save/rebuild previews still show understandable scope and media summaries
- confirm public rebuild buttons still produce the same success/failure shape in Studio

## Out Of Scope

- changing public generated payload schemas
- changing media output paths
- changing R2 publishing behavior
- replacing `generate_work_pages.py` as the internal generator engine
- moving files into new package folders
- broad audit cleanup outside `catalogue_json_build.py`
