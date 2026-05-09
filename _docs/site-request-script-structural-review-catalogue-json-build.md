---
doc_id: site-request-script-structural-review-catalogue-json-build
title: Catalogue JSON Build Slices
added_date: 2026-05-09
last_updated: "2026-05-09 21:05"
ui_status: in-progress
parent_id: site-request-script-structural-review
sort_order: 50
viewable: true
---
# Catalogue JSON Build Slices

Status:

- initial implementation tracker created
- Slice 0 read-only extraction map completed
- Slice 1 scoped build planning helpers implemented
- Slice 2 local media planning and readiness implemented
- Slice 3 field-aware build-plan adapter implemented
- Slice 4 command construction and execution-result helpers implemented

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

Status: completed.

Task:

- map `catalogue_json_build.py` by responsibility, call dependencies, and external contracts
- identify which functions can move without binding CLI state, filesystem writes, subprocess execution, or user-facing report wording
- record concrete module names and test files before implementation starts

Likely output:

- this doc records the proposed module owners, call boundaries, and test files
- no code movement in this slice

Acceptance checks:

- map identifies scope planning, media readiness, local media execution, field-aware planning, command construction, subprocess orchestration, and CLI/reporting boundaries
- map calls out any behavior that should stay in `catalogue_json_build.py` because it binds command-line state or user-facing preview/report output

#### Slice 0 Responsibility Map

Current `catalogue_json_build.py` responsibilities fall into these implementation bands:

| Responsibility | Current functions/constants | Main dependencies | Proposed owner |
| --- | --- | --- | --- |
| CLI, mode selection, preview text, write result exit behavior | `parse_args`, `main`, `print_preview` | `argparse`, scoped builders, command builders, media plan counts | keep in `scripts/catalogue_json_build.py` |
| Repo/source path and display helpers | `detect_repo_root`, `repo_relative_path`, `display_source_path`, `normalize_filename` | `Path`, `os`, configured project paths | keep minimal entrypoint helpers where CLI-bound; move reusable media display helpers to `scripts/catalogue_build_media.py` only when used by media owners |
| Projects-base detection for source media | `detect_projects_base_dir`, `detect_projects_base_dir_optional`, `PROJECTS_BASE_DIR_ENV_NAME` | `pipeline_config`, `local_env` runtime values | `scripts/catalogue_build_media.py` |
| Source media resolution and readiness payloads | `resolve_work_media_source`, `resolve_detail_media_source`, `resolve_moment_media_source`, `build_media_readiness_item`, `build_readiness_item`, `build_work_readiness`, `build_series_readiness`, `build_detail_readiness`, `build_moment_readiness` | `catalogue_source`, `moment_sources`, pipeline media roots, staging paths | `scripts/catalogue_build_media.py`, with prose-readiness helpers included because Studio readiness payloads combine prose and media status |
| Local media path planning and state checks | `thumb_output_dir`, `media_staging_kind_dir`, `media_staging_input_path`, `media_srcset_root`, `staged_thumb_output_paths`, `staged_primary_output_paths`, `thumb_output_paths`, `thumb_output_paths_for_kind`, `local_output_state`, `local_thumb_state`, `local_media_state`, `path_needs_refresh`, `build_local_media_task`, `build_local_media_plan` | media constants, filesystem state, source media resolution | `scripts/catalogue_build_media.py` |
| Local media execution | `run_ffmpeg_thumb`, `run_ffmpeg_primary`, `execute_local_media_plan` | `ffmpeg`, `subprocess`, `shutil`, local media plan payloads | `scripts/catalogue_build_media.py`, but keep process runners injectable or patchable so tests avoid real `ffmpeg` |
| Moment source preview/import metadata | `build_moment_paths`, `build_moment_import_metadata`, `preview_moment_source` | `moment_sources`, configured projects roots, `_docs_catalogue`, staged prose paths, generated moment artifacts | `scripts/catalogue_build_scopes.py` for build-preview metadata that feeds moment scope construction; leave write/import mutation ownership in existing prose/publication modules |
| Work, series, and moment scope construction | `normalize_series_ids`, `validate_buildable_series_scope`, `build_scope_for_work`, `build_scope_for_series`, `build_scope_for_moment`, `summarize_scope`, `summarize_moment_scope` | `catalogue_source`, `series_ids`, readiness builders, moment preview | `scripts/catalogue_build_scopes.py` |
| Field-aware build-plan adapter | `parse_csv_tokens`, `infer_record_family_for_scope`, `build_field_plan_for_scope`, `field_plan_explanation_lines` | `catalogue_field_registry`, source records, current scope payloads | `scripts/catalogue_build_field_plan.py`; explanation string construction can move with the adapter because it is registry-specific, while placement stays in `print_preview` |
| Generator and search command construction | `resolve_bundle_bin`, `build_generate_command`, `build_generate_moment_command`, `build_search_command` | `sys.executable`, Bundler binary detection, generator/search script paths | `scripts/catalogue_build_commands.py` |
| Subprocess step execution and result payload shaping | subprocess loop inside `run_scoped_build_scope`; media step normalization in the same function | command builders, `runtime_env`, media execution, Studio result payload keys | split command step normalization into `scripts/catalogue_build_commands.py`; keep top-level orchestration and final Studio response assembly in `catalogue_json_build.py` until call sites are updated |
| Compatibility wrappers for Studio/publication callers | `run_scoped_build`, `run_series_scoped_build`, `run_moment_scoped_build`, plus imported helper names | `catalogue_write_server.py`, `catalogue_publication.py`, `catalogue_prose_import.py`, `catalogue_cleanup.py`, tests | keep wrappers in `catalogue_json_build.py` during extraction, delegating to owner modules explicitly |

#### External Contracts To Preserve

Current in-repo consumers import these names from `catalogue_json_build.py`:

- `scripts/studio/catalogue_write_server.py`: `build_search_command`, `build_local_media_plan`, `build_moment_readiness`, `build_field_plan_for_scope`, `build_scope_for_moment`, `build_scope_for_series`, `build_scope_for_work`, `preview_moment_source`, `run_scoped_build_scope`
- `scripts/catalogue_publication.py`: `build_local_media_plan`, `build_scope_for_moment`, `build_scope_for_series`, `build_scope_for_work`, `preview_moment_source`
- `scripts/catalogue_prose_import.py`: `preview_moment_source`
- `scripts/catalogue_cleanup.py`: `CATALOGUE_MEDIA_STAGING_REL_DIR`
- `tests/python/test_catalogue_media_cleanup.py`: imports the script module directly and patches `build_local_media_plan`, `run_ffmpeg_thumb`, and `run_ffmpeg_primary`

During extraction, keep `catalogue_json_build.py` compatibility names until the importing modules are deliberately updated in the same slice.
Avoid a broad permanent re-export layer: each slice should either leave a compatibility wrapper for an active caller or update that caller to import the new owner directly.

#### Functions That Should Move First

- Move scope construction first because `build_scope_for_work`, `build_scope_for_series`, `build_scope_for_moment`, `validate_buildable_series_scope`, and the summary helpers are mostly pure once readiness builders are injected or imported from the media owner.
- Move field-aware planning independently because it already depends on `catalogue_field_registry` and mutates only the provided scope through the existing registry helper.
- Move command construction before subprocess normalization because command argv shapes are easy to pin without running external processes.
- Move local media in two steps if needed: planning/state/readiness first, then derivative execution. Execution has filesystem writes and `ffmpeg`, so its tests need fakes or monkeypatching.

#### Behavior To Keep In `catalogue_json_build.py`

- CLI argument parsing, exactly-one target validation, and top-level mode selection
- binding command-line `--repo-root`, `--source-dir`, `--write`, `--force`, `--media-only`, `--changed-fields`, and `--record-family` to the orchestration flow
- preview output ordering and wording in `print_preview`
- final `SystemExit` behavior and success messages
- top-level response keys consumed by Studio: `scope`, `status`, `write`, `force`, `media_only`, `refresh_published`, `steps`, `media`, `failed_step`, and `error`
- sequencing decisions: media step first, generator step second, catalogue search step last, and search suppression when field-aware plans disable it

#### Proposed Test Files

- `tests/python/test_catalogue_build_scopes.py`: work, series, moment, extra-id handling, detail UID inclusion, invalid series preconditions, stable scope payload keys
- `tests/python/test_catalogue_build_media.py`: source path resolution, readiness states, missing metadata reasons, pending/current/blocked/unavailable counts, staged output paths, force behavior, dry-run write suppression, execution with fake process runners
- `tests/python/test_catalogue_build_field_plan.py`: changed-field parsing, family inference, registry plan application, media-only and search/generator reductions, explanation lines
- `tests/python/test_catalogue_build_commands.py`: generator/search argv shapes for work, series, moment, write, force, refresh-published, and normalized failed subprocess step payloads
- keep or migrate `tests/python/test_catalogue_media_cleanup.py` with the local media execution owner so staged thumbnail cleanup remains pinned

#### Revised Slice Sequence After Mapping

The planned module names still look right:

- Slice 1: `scripts/catalogue_build_scopes.py`
- Slice 2: `scripts/catalogue_build_media.py`
- Slice 3: `scripts/catalogue_build_field_plan.py`
- Slice 4: `scripts/catalogue_build_commands.py`
- Slice 5: final `catalogue_json_build.py` orchestration cleanup and compatibility import cleanup

The main adjustment is that Slice 1 should depend on the existing readiness helpers through `catalogue_json_build.py` or a narrow temporary import until Slice 2 moves readiness ownership.
That avoids mixing scope construction and local media execution in the same first implementation slice.

### Slice 1: scoped build planning helpers

Status: implemented.

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

Implementation result:

- `scripts/catalogue_build_scopes.py` now owns work, series, and moment scope construction, scoped-series buildability validation, normalized extra-id handling, scope summaries, and moment import metadata merging
- `scripts/catalogue_json_build.py` keeps the existing public compatibility names and delegates scope planning to the new owner while still owning CLI parsing, preview/report wording, orchestration, media planning, generator/search execution, and Studio response payloads
- readiness and moment preview dependencies remain temporarily bound through the entrypoint wrappers until Slice 2 moves local media planning and readiness ownership
- `tests/python/test_catalogue_build_scopes.py` pins work, series, and moment scope payload shapes, extra-id dedupe, detail readiness inclusion, invalid series preconditions, and moment metadata merge behavior
- `scripts/run_checks.py` quick syntax and focused test coverage now include the extracted scope-planning module

Benefits:

- gives scoped build selection rules a direct test owner before media and command execution move
- keeps the Studio/publication import contract stable while reducing the mixed responsibility surface in `catalogue_json_build.py`

Risks:

- readiness is still entrypoint-owned for now, so Slice 2 must preserve the current readiness payload shape when moving media ownership

### Slice 2: local media planning and readiness

Status: implemented.

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

Implementation result:

- `scripts/catalogue_build_media.py` now owns projects-base detection, work/detail/moment source-media resolution, media/prose readiness item construction, local media state checks, media task planning, `ffmpeg` derivative execution, and local media result summaries
- `scripts/catalogue_json_build.py` keeps compatibility names for existing Studio/publication/cleanup callers, but delegates media and readiness behavior to the new owner
- local media execution now supports injected plan and process runners for focused tests while keeping the default `ffmpeg` runtime path unchanged
- `tests/python/test_catalogue_build_media.py` pins source path resolution, missing metadata reasons, local media pending/current/blocked/unavailable counts, forced refresh planning, staged output paths, readiness states, and dry-run write suppression
- `tests/python/test_catalogue_media_cleanup.py` continues to pass through the compatibility wrapper so staged thumbnail cleanup behavior remains pinned during the transition
- `scripts/run_checks.py` quick syntax and focused test coverage now include the extracted media module and tests

Benefits:

- gives media readiness and derivative planning a direct owner with focused tests before command construction and subprocess result shaping move
- keeps the supported CLI, Studio result payloads, media paths, and caller imports stable while reducing the entrypoint responsibility surface

Risks:

- `catalogue_json_build.py` still carries compatibility wrappers until later slices update import ownership deliberately
- the default runtime path still depends on local `ffmpeg`; tests use injection to avoid requiring real image processing

### Slice 3: field-aware build-plan adapter

Status: implemented.

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

Implementation result:

- `scripts/catalogue_build_field_plan.py` now owns changed-field token normalization, record-family inference, field registry plan lookup, field-plan application to scoped build payloads, and preview explanation line construction
- `scripts/catalogue_json_build.py` keeps compatibility wrappers for the existing CLI and Studio imports, but delegates field-aware planning behavior to the new owner
- `tests/python/test_catalogue_build_field_plan.py` pins CLI-style changed-field parsing, family inference for work/detail/series/moment scopes, empty changed-field behavior, focused work JSON reductions, local-media-only reductions, search rebuild reductions, and generator `--only` reductions
- `scripts/run_checks.py` quick syntax and focused test coverage now include the extracted field-plan module and tests

Benefits:

- separates registry-specific field-plan adaptation from scoped-build orchestration and preview placement
- gives changed-field behavior a direct test owner before command construction and subprocess result shaping move

Risks:

- `catalogue_json_build.py` still carries compatibility wrappers until later slices update import ownership deliberately
- field registry output is runtime-facing; tests pin representative reductions but do not replace full registry verification

### Slice 4: generator/search command construction and execution results

Status: implemented.

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

Implementation result:

- `scripts/catalogue_build_commands.py` now owns generator command construction for work/series scopes, generator command construction for moment scopes, catalogue search command construction, subprocess output tailing, per-step result shaping, and failed-step message selection
- `scripts/catalogue_json_build.py` keeps compatibility wrappers for existing callers while delegating command helpers and per-command execution result shaping to the new owner
- top-level orchestration remains in the entrypoint: local media still runs first, generator commands run second, catalogue search runs last, and field-aware plans can still suppress generation or search
- `tests/python/test_catalogue_build_commands.py` pins work, moment, and search argv shapes plus failed subprocess step payloads with an injected fake process runner
- `scripts/run_checks.py` quick syntax and focused test coverage now include the extracted command module and tests

Benefits:

- separates argv and subprocess-result contracts from the scoped-build orchestration path
- gives command shapes direct focused coverage before the final entrypoint cleanup slice

Risks:

- `catalogue_json_build.py` still carries compatibility wrappers until Slice 5 removes or narrows them deliberately
- focused tests pin representative command shapes, while the final dry-run previews remain the guard for user-facing preview ordering and wording

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
