---
doc_id: site-request-script-structural-review-generate-work-pages
title: Generate Work Pages Slices
added_date: 2026-05-09
last_updated: "2026-05-09 19:49"
ui_status: in-progress
parent_id: site-request-script-structural-review
sort_order: 40
viewable: true
---
# Generate Work Pages Slices

Status:

- initial implementation tracker created
- Slice 0 implemented
- Slice 1 implemented
- Slice 2 implemented
- Slice 3 implemented
- Slice 4 implemented
- Slice 5 implemented
- Slice 6 implemented
- Slice 7 implemented
- read-only extraction map recorded
- record projection helpers extracted
- series and work index builders extracted
- recent-publications builder extracted
- route-stub and generated JSON write-decision helpers extracted
- source update planners extracted
- moment artifact builder extracted
- generator orchestration cleanup completed

## Purpose

This child doc tracks the detailed review and implementation tasks for restructuring `scripts/generate_work_pages.py`.
The parent [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review) stays focused on the broader candidate queue, shared acceptance criteria, and completed priority summaries.

The intended end state is not to make the generator small for its own sake.
`generate_work_pages.py` should remain the internal JSON-source generator entrypoint used by `scripts/catalogue_json_build.py`, while catalogue projection, index payload construction, recent-publication merging, source update planning, and file write mechanics get explicit owners where the boundary is stable and useful.

## Current Shape

`scripts/generate_work_pages.py` currently owns several responsibilities in one file:

- CLI argument parsing, deprecated direct-entrypoint messaging, `--only` artifact selection, scoped work/series/moment filters, and run-mode decisions
- canonical source loading, validation, mutable source updates, and final canonical source write-back
- work, detail, series, and moment source projection into public runtime records
- series sort computation, published membership maps, series index payloads, works index payloads, work storage index payloads, moments index payloads, and recent-publications payloads
- route-anchor stub generation for works, series, work details, and moments
- per-record JSON rendering for work, series, and moment runtime payloads, including Markdown prose rendering through the local Jekyll stack
- source media dimension lookup and write-back-adjacent status/date/dimension mutations
- dry-run/write reporting, existing payload version checks, file writes, and generator event logging

That mix creates maintenance risk because a small generated-artifact change can require understanding selection rules, source mutations, publication transitions, recent-entry merging, prose rendering, and write behavior together.

## Target Boundary

The generator entrypoint should keep:

- CLI parsing and deprecated direct-entrypoint guard
- artifact selection and high-level orchestration order
- binding runtime dependencies such as paths, configured project roots, clock values, and Markdown rendering
- deciding when source write-back is allowed
- final user-facing run summaries and event logging

Extracted module owners should take:

- pure source projection and public record shaping
- series membership and sort context building
- aggregate index payload construction
- recent-publication entry merging
- route-stub and generated-file write decisions
- source update planning for status, published dates, and image dimensions

Keep `scripts/catalogue_json_build.py` as the supported public pipeline entrypoint.
Do not revive direct manual use of `generate_work_pages.py`, change generated payload schemas, move script folders, or change output paths as part of these slices.

## Slice Principles

- Define and test the behavior being moved before changing call sites.
- Prefer pure functions that accept source records and return payloads, write decisions, or update plans.
- Keep generated JSON schemas, route-anchor content, `--only` behavior, scoped refresh behavior, dry-run output meaning, and source write-back semantics stable.
- Keep Jekyll Markdown rendering and filesystem writes out of projection/index modules.
- Close each slice without broad compatibility aliases, duplicate schema constants, or temporary re-export layers.
- Use direct imports from the owning module once behavior is moved.
- Keep package moves for a later pass under [Scripts Directory Organization Request](/docs/?scope=studio&doc=site-request-scripts-directory-organization).

## Initial Acceptance Criteria

- `scripts/catalogue_json_build.py` continues to call the generator with the same internal command shape.
- Existing generated artifact paths and schemas stay stable:
  - `_works/<work_id>.md`
  - `_series/<series_id>.md`
  - `_work_details/<work_id>-<detail_id>.md`
  - `_moments/<moment_id>.md`
  - `assets/works/index/<work_id>.json`
  - `assets/series/index/<series_id>.json`
  - `assets/moments/index/<moment_id>.json`
  - `assets/data/series_index.json`
  - `assets/data/works_index.json`
  - `assets/data/recent_index.json`
  - `assets/data/moments_index.json`
  - `assets/studio/data/work_storage_index.json`
- Focused tests cover each extracted owner directly.
- The generator still passes syntax checks after every Python slice.
- After generator or pipeline-entrypoint changes, `scripts/catalogue_json_build.py` previews successfully through a dry-run.
- Script docs are updated when module ownership, command behavior, or generated-artifact responsibilities change.

## Planned Slice Sequence

The sequence below should be revised after the read-only map, but it gives the first implementation path.

### Slice 0: read-only extraction map

Status: implemented.

Task:

- map `generate_work_pages.py` by responsibility, call dependencies, and generated artifact contracts
- identify which nested functions can move without introducing path, clock, renderer, or write dependencies
- record the first concrete module names and test files before implementation starts

Likely output:

- update this doc with final proposed module owners
- no code movement in this slice

Acceptance checks:

- map identifies source projection, index building, recent merging, route/file writing, source update planning, and CLI orchestration boundaries
- map calls out any behavior that should stay in the generator because it binds filesystem, renderer, or run-mode state

Read-only review result:

- the supported external command contract comes from `scripts/catalogue_json_build.py`, which invokes `scripts/generate_work_pages.py` with `--internal-json-source-run`, `--source-dir`, scoped ids, repeated `--only` values, and optional `--write`, `--refresh-published`, and `--force`
- top-level scalar/id/date/list/YAML helpers currently mix three concerns: source value normalization, legacy front-matter dumping, and route-stub construction
- top-level JSON hash/compaction/version helpers are shared by record builders, aggregate indexes, recent index, and per-record JSON payloads
- most catalogue-specific builders are nested in `main()`, which makes them hard to test without invoking CLI, path setup, source loading, and write orchestration
- filesystem and process dependencies are concentrated in display path formatting, output directory creation, existing payload reads, Markdown rendering through Jekyll, `sips` image dimension reads, JSON writes, tag assignment writes, source write-back, and script logging

Responsibility map:

| Current area | Current owner | Target owner | Notes |
|---|---|---|---|
| CLI and internal-entrypoint contract | `main()` argument parser and direct-entrypoint guard | keep in `generate_work_pages.py` | must remain compatible with `scripts/catalogue_json_build.py` command construction |
| artifact selection and scoped ids | `main()` selected-artifact, work/series/moment id parsing, and scoped-run rules | keep in `generate_work_pages.py` for now | extraction would not help until artifact builders are pure and tested |
| source loading and validation | `records_from_json_source`, `validate_source_records`, write-back validation wrapper | keep in `generate_work_pages.py` | source-model ownership already lives in `scripts/catalogue_source.py`; generator should bind it |
| common value normalization | `slug_id`, `parse_date`, `parse_list`, `normalize_text`, coercers | defer; likely `scripts/catalogue_generation_common.py` only when first extracted module needs it | avoid duplicating helper code across new modules |
| YAML/front-matter route stubs | front-matter dump helpers and `build_route_stub_content()` | `scripts/catalogue_generation_writes.py` or a narrower route-stub helper | generated route anchors are metadata-free; legacy scalar YAML helpers may be more than route stubs need |
| payload hashing and compaction | `compute_payload_version`, hash helpers, `compact_json_object` | `scripts/catalogue_generation_payloads.py` or `scripts/catalogue_generation_common.py` | this is a dependency for records, indexes, recent, and moments; move before duplicating constants |
| work projection | `WORKS_SCHEMA`, `build_work_record_projection`, `build_canonical_work_record` | `scripts/catalogue_generation_records.py` | needs injected series title and sort context instead of closing over `main()` locals |
| detail projection | `build_canonical_detail_record`, `build_sections_from_detail_records` | `scripts/catalogue_generation_records.py` | can be pure once section resolution is passed in |
| series/work sort context | series title/status maps, project-folder aggregation, series sort fields, work ids by series | `scripts/catalogue_generation_indexes.py` | should expose one context object consumed by records, series pages, indexes, and recent |
| per-series JSON record | inline series page loop and `build_series_json_record` | records module for public record shape; generator for prose/render/write | split record shape from Markdown render and file write |
| series index JSON | published membership, primary work validation, `series_index_v2` payload | `scripts/catalogue_generation_indexes.py` | should accept generated timestamp as an injected value |
| work JSON | encountered work ids, detail grouping, `work_record_v3` payload | records module for work/detail shape; generator for prose/render/write | prose rendering must stay bound in generator until there is a renderer abstraction |
| works index JSON | `works_index_v4` and work storage payload loops | `scripts/catalogue_generation_indexes.py` | storage index can be built next to works index because it uses the same canonical work map |
| recent index JSON | retained entries, publish-transition merge rules, `recent_index_v1` payload | `scripts/catalogue_generation_recent.py` | stateful enough to isolate before touching surrounding page loops |
| work/detail source updates | status/date/dimension mutation logic inside page loops | `scripts/catalogue_generation_source_updates.py` | should return update plans and transition records; generator applies plans only when `--write` |
| moment source collection and records | duplicated per-moment and moments-index construction | `scripts/catalogue_generation_moments.py` | should keep prose rendering and actual file writes in the generator |
| tag assignment series sync | series page loop and `load_tag_assignments_payload` | defer; likely tag/source-model owner after series generation is clearer | current behavior follows `series-pages` selection and writes `assets/studio/data/tag_assignments.json` |
| file write/version decisions | repeated route exists checks, version reads, JSON writes, and dry-run messages | `scripts/catalogue_generation_writes.py` | start with decision objects; keep exact print wording in generator until stable |

Move candidates with low immediate risk:

- pure public record shapers: `build_work_json_record`, `build_series_json_record`, `build_moment_json_record`, `build_moment_index_record`
- detail section grouping once tests pin section ordering and payload pruning
- recent entry normalization and sorting, then recent merge rules
- aggregate payload builders after hash/version helpers have one owner

Keep generator-local for now:

- CLI parsing, deprecated direct-entrypoint message, and `catalogue_json_build.py` subprocess contract
- path resolution from CLI/config values and display-path formatting
- output directory creation
- `render_markdown_with_jekyll`
- `read_image_dims_px` process binding and warning presentation
- actual source-record mutation and final `write_source_record_payloads`
- local event logging
- exact dry-run/write print wording

First implementation constraint:

- before Slice 1 moves record helpers, either move shared compaction/hash/coercion helpers into one common owner or keep the first slice small enough that the generator remains the only helper owner; do not copy those helpers into multiple new modules

### Slice 1: record projection helpers

Status: implemented.

Proposed module owner:

- `scripts/catalogue_generation_records.py`

Target ownership:

- `WORKS_SCHEMA`
- work scalar projection
- work `series_ids` normalization from source records
- public work JSON record shaping
- public series JSON record shaping
- public moment JSON/index record shaping
- canonical detail record shaping
- detail section grouping for per-work runtime payloads

Implementation result:

- `scripts/catalogue_generation_records.py` now owns the pure work, series, detail, and moment record projection helpers
- `scripts/catalogue_generation_common.py` owns the shared coercion, normalization, compaction, and payload-version helpers needed by both the extracted record owner and the generator
- `scripts/generate_work_pages.py` imports the record owner as `records` and keeps CLI parsing, source loading, selection filters, path binding, prose rendering, file writes, and source write-back orchestration local
- `tests/python/test_catalogue_generation_records.py` pins projection field ordering, `series_ids` normalization, public record field pruning, canonical detail compaction, moment index thumb selection, and deterministic detail-section grouping

The generator should keep:

- source loading and validation
- selection filters
- path binding
- prose rendering
- file writes
- source write-back

Tests:

- add `tests/python/test_catalogue_generation_records.py`
- pin field ordering, empty-field compaction, work `series_ids`, public work/series/moment field pruning, detail section grouping, and deterministic detail ordering

Benefits:

- gives generated runtime record shapes a direct test owner
- reduces risk when adding or removing public payload fields

Risks:

- payload field pruning is runtime-facing; tests must pin omitted fields such as internal sort/checksum fields

### Slice 2: series and work index builders

Status: implemented.

Proposed module owner:

- `scripts/catalogue_generation_indexes.py`

Target ownership:

- series title/status maps
- series project-folder aggregation
- per-series work membership and sort context
- published series index payload construction
- lightweight works index payload construction
- Studio work storage index payload construction
- primary-work validation for generated series payloads

Implementation result:

- `scripts/catalogue_generation_indexes.py` now owns the pure series/work aggregate context and index payload builders
- `scripts/catalogue_generation_common.py` now owns the shared `slug_id`, status normalization, and numeric-aware sort helper used by the generator and index module
- `scripts/generate_work_pages.py` imports the index owner as `indexes` and keeps output paths, existing-version checks, JSON writes, and dry-run/write messages local
- `tests/python/test_catalogue_generation_indexes.py` pins custom `sort_fields`, title sort aliasing, numeric sort ordering, published-only series membership, missing/invalid primary work validation, works index payload shape, and storage-index omission for empty storage values
- `scripts/run_checks.py` quick syntax coverage now includes the extracted catalogue generation modules and direct generation helper tests

The generator should keep:

- output path selection
- existing-version comparison
- JSON writes
- dry-run/write messages

Tests:

- add focused tests for custom `sort_fields`, title sort aliasing, numeric sort values, published-only series membership, missing/invalid primary work behavior, works index shape, and work storage index omission when storage is empty

Benefits:

- separates catalogue aggregate semantics from the CLI loop
- makes future series/index schema changes easier to review without touching file-write orchestration

Risks:

- sorting drift would be user-visible on `/series/` and series detail pages; tests need representative mixed numeric/title/year cases

### Slice 3: recent-publications builder

Status: implemented.

Proposed module owner:

- `scripts/catalogue_generation_recent.py`

Target ownership:

- recent entry normalization and sorting
- retention of current published targets
- merge behavior for newly published series
- grouping newly published works by primary series
- absorption of work entries into the latest series entry
- final `recent_index_v1` payload construction

Implementation result:

- `scripts/catalogue_generation_recent.py` now owns pure recent-entry normalization, deterministic sorting, current-published target filtering, publication-transition merging, latest-series absorption, grouped work publication entries, and `recent_index_v1` payload construction
- `scripts/generate_work_pages.py` imports the recent owner as `recent` and keeps existing recent-index file loading, path selection, version comparison, JSON writes, and dry-run/write reporting local
- `tests/python/test_catalogue_generation_recent.py` pins retained-entry filtering, series publish entries, grouped work publish entries, latest-series absorption, same-series series/work suppression, cap behavior, and deterministic ordering
- `scripts/run_checks.py` quick syntax and test coverage now includes the extracted recent-publications module and direct helper tests

The generator should keep:

- loading the existing recent index file
- deciding whether to write the generated payload
- printing dry-run/write results

Tests:

- add `tests/python/test_catalogue_generation_recent.py`
- pin retained-entry filtering, series publish entries, grouped work publish entries, latest-series absorption, entry cap behavior, and deterministic ordering

Benefits:

- isolates the least obvious generated-index behavior from unrelated work/series generation
- makes `/recent/` changes reviewable through direct examples

Risks:

- recent-entry merge rules are stateful and easy to regress; tests should use small fixtures with explicit expected entries

### Slice 4: route-stub and file-write decisions

Status: implemented.

Proposed module owner:

- `scripts/catalogue_generation_writes.py`

Target ownership:

- metadata-free route-stub content
- generated JSON payload version comparison
- write/skip decision helpers for route stubs and JSON payloads
- common dry-run/write result objects used by work, series, detail, moment, and aggregate JSON writers

Implementation result:

- `scripts/catalogue_generation_writes.py` now owns metadata-free route-stub content, tolerant JSON header scalar extraction, route-stub write/skip decisions, JSON payload version-match decisions, and a shared generated-write decision object
- `scripts/generate_work_pages.py` imports the write-decision owner as `writes` and still owns filesystem reads/writes, path selection, artifact-specific labels, counters, status/source updates, and exact dry-run/write print wording
- `tests/python/test_catalogue_generation_writes.py` pins skip-on-existing route behavior, force overwrite behavior, JSON header extraction, version-match JSON skip behavior, force overwrite for matching versions, and no-file-write dry-run decision behavior
- `scripts/run_checks.py` quick syntax and focused test coverage now includes the extracted write-decision module

The generator should keep:

- actual print wording until a result contract is in place
- path selection and artifact-specific labels
- dependency binding for filesystem reads/writes

Tests:

- pin skip-on-existing route behavior, force overwrite behavior, version-match JSON skip behavior, and dry-run decision output without writing files

Benefits:

- removes repeated version-check and route-exists logic
- gives write behavior a direct test owner before page loops are simplified

Risks:

- dry-run wording and skip counts are used during manual runs; avoid changing visible reporting unless explicitly intended

### Slice 5: source update planning

Status: implemented.

Proposed module owner:

- `scripts/catalogue_generation_source_updates.py`

Target ownership:

- work status and `published_date` update plans for first-time publication
- work-detail status and `published_date` update plans
- work and detail image-dimension update plans
- publish-transition records used by recent-index generation

Implementation result:

- `scripts/catalogue_generation_source_updates.py` now owns pure work and work-detail source update planners for actionable status checks, first-time publication updates, recent work-transition records, source image path plans, structured path warnings, and dimension update suppression
- `scripts/generate_work_pages.py` imports the source-update owner as `source_updates` and still owns configured project-root binding, image dimension reads, warning print wording, applying planned updates only during `--write`, source validation, and canonical source write-back
- `tests/python/test_catalogue_generation_source_updates.py` pins draft publication updates, published refresh/force actionability without mutation, detail publication updates, unchanged dimension suppression, structured missing-path warnings, and no mutation during dry-run-style planning
- `scripts/run_checks.py` quick syntax and focused test coverage now includes the extracted source-update planner module

The generator should keep:

- image-dimension reader dependency binding
- source path resolution inputs from configured project roots
- final write-back execution through catalogue source utilities

Tests:

- pin draft-to-published transitions, published refresh behavior, force behavior, unchanged dimension suppression, missing source path warnings as structured warning records, and no mutation during dry-run planning

Benefits:

- separates generated source mutations from page/file writing
- makes source write-back semantics explicit before more generator logic moves

Risks:

- source update planning touches canonical catalogue data; keep dry-run behavior and write-back validation strict

### Slice 6: moment artifact builder

Status: implemented.

Proposed module owner:

- `scripts/catalogue_generation_moments.py`

Target ownership:

- moment metadata source collection from the source index
- moment runtime record shaping with image existence and dimensions
- moment record payload construction
- moments index payload construction
- moment selection/actionability decisions that do not require filesystem writes

Implementation result:

- `scripts/catalogue_generation_moments.py` now owns pure moment metadata source-record collection, slug/actionability/selection decisions, runtime moment record shaping, per-moment `moment_record_v1` payload construction, and `moments_index_v1` payload construction
- `scripts/generate_work_pages.py` imports the moment artifact owner and still owns configured project-root binding, source prose existence checks, source image dimension reads, Markdown rendering, route and JSON file writes, existing-version checks, and dry-run/write reporting
- `tests/python/test_catalogue_generation_moments.py` pins source-record ordering/default paths, slug-safe decisions, missing-prose skip decisions, image alt fallback, image omission when source media is missing, per-moment JSON payload shape, and moments index payload shape
- `scripts/run_checks.py` quick syntax and focused test coverage now includes the extracted moment artifact module

The generator should keep:

- prose existence checks and Markdown rendering
- route and JSON file writes
- project-root binding

Tests:

- pin slug-safe ids, missing prose skip decisions, image alt fallback, image omission when source image is missing, per-moment JSON payload shape, and moments index payload shape

Benefits:

- removes duplicated moment record construction between per-moment JSON and moments index generation
- keeps moment-specific rules out of work/series projection modules

Risks:

- moment generation depends on source prose and media availability; separate pure record decisions from filesystem checks carefully

### Slice 7: generator orchestration cleanup

Status: implemented.

Task:

- simplify `generate_work_pages.py` around explicit module calls
- remove nested helpers that have moved
- make dependency binding and run order visible
- keep CLI surface and `catalogue_json_build.py` subprocess contract stable

Implementation result:

- removed retired Studio-series route generation and the YAML/front-matter helpers that only supported that dead path
- removed unused legacy generator-local helpers for download/link entry shaping and tag-registry loading
- consolidated repeated aggregate JSON write/version decisions for series, works, recent, work-storage, and moments indexes behind a single generator-local orchestration helper
- kept per-record page and JSON generation in the generator because those paths still bind selection state, Markdown rendering, filesystem paths, and artifact-specific log wording
- kept generated schemas, output paths, `--only`, `--refresh-published`, `--force`, dry-run behavior, and `catalogue_json_build.py` subprocess arguments unchanged

Tests and checks:

- run syntax checks for changed Python modules
- run focused new tests for extracted modules
- run `./scripts/catalogue_json_build.py` dry-run for the smallest representative work/series/moment scope available
- run the smallest relevant run-checks profile only if the extraction touched shared catalogue behavior broadly enough to justify it

Benefits:

- leaves the generator as orchestration instead of a mixed domain/writeback implementation
- makes future catalogue generation changes easier to place and review

Risks:

- moving too much in one cleanup pass can obscure behavior changes; keep this as final call-site cleanup after the extracted owners are already tested

## Open Questions

- Should payload schema constants live with the index/record builders immediately, or stay in the generator until the first payload builder moves?
- Should source image path resolution be part of source update planning, or should it stay in the generator because it binds configured project roots?
- Should per-artifact dry-run output be normalized into structured result objects, or should existing print wording stay local to the generator until there is a second consumer?
- Should `render_markdown_with_jekyll` become a shared docs/catalogue rendering helper, or remain generator-local because it is currently only needed by catalogue generation?
- Should tag-assignment series-entry sync remain in the series page loop, or move to a tag-specific owner once series generation is clearer?
