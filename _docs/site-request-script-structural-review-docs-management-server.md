---
doc_id: site-request-script-structural-review-docs-management-server
title: Docs Management Server Slices
added_date: 2026-05-09
last_updated: "2026-05-09 13:03"
parent_id: site-request-script-structural-review
sort_order: 20
---
# Docs Management Server Slices

Status:

- Slice 1 implemented
- Slice 2 implemented
- Slice 3 implemented
- Slice 4 implemented
- later slices are planned, but should still be reconfirmed before editing

## Purpose

This child doc tracks the detailed implementation slices for restructuring `scripts/docs/docs_management_server.py`.
The parent [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review) stays focused on the broader review goals, candidate scripts, and acceptance criteria.

The intended end state is not a small file for its own sake.
The server should remain the Docs Viewer local-service HTTP and endpoint orchestration layer, while cohesive route inventory, source-model helpers, generated-data reads, import/apply flows, activity contracts, and rebuild/write mechanics get explicit owners only when the boundary is useful.

## Slice Principles

- Define the ownership boundary before moving code.
- Keep endpoint URLs, request payloads, response payloads, source-write semantics, backup behavior, dry-run behavior, and rebuild semantics stable.
- Keep write allowlist checks and local-only service guardrails visible.
- Prefer direct tests against the owning extracted module.
- Close each slice without broad compatibility aliases, duplicate endpoint constants, or duplicated path inventories.

## Implemented Slices

### Slice 1: route inventory and handler dispatch

Status: implemented.

The first implementation slice extracted Docs Management endpoint path constants from `scripts/docs/docs_management_server.py` into `scripts/docs/docs_management_routes.py`.
The server handler now uses explicit `GET_HANDLERS` and `POST_HANDLERS` dispatch tables instead of repeated path conditionals.
The moved route constants are also used by docs activity attachment helpers, so activity endpoint strings now share the route owner.
`tests/python/test_docs_management_routes.py` pins route uniqueness, OPTIONS coverage, and GET/POST handler coverage.

Target ownership:

- endpoint path constants
- GET and POST route inventories
- CORS preflight route coverage
- handler-dispatch coverage tests

The server keeps HTTP transport, request body parsing, endpoint orchestration, response status selection, local logging, source writes, rebuild calls, import/export adapter calls, and Studio Activity append timing.

Acceptance checks:

- every route in `GET_PATHS` has a handler table entry
- every route in `POST_PATHS` has a handler table entry
- route inventories do not contain duplicates
- the existing Docs Management server tests still pass

Benefits:

- gives endpoint path ownership a clear module home
- makes missing handler coverage easier to catch before broader extraction work
- removes repeated literal route strings from the handler and activity helpers
- follows the working pattern established by the catalogue write-server route slice

Risks:

- route tables are now part of the service contract; future endpoint additions must update `scripts/docs/docs_management_routes.py` and the handler dispatch table together
- this slice is structural only and does not reduce the larger source-write, import/apply, or rebuild helper bodies

### Slice 2: docs source model helpers

Status: implemented.

The second implementation slice extracted Docs source-model helpers from `scripts/docs/docs_management_server.py` into `scripts/docs/docs_source_model.py`.
The server still owns HTTP handlers, request extraction, dry-run decisions, backup timing, rebuild calls, generated-data reads, import/export adapter orchestration, activity append timing, and response assembly.
The server imports the source-model helpers it still orchestrates so this slice can keep endpoint behavior stable while later slices continue reducing handler-local logic.

Target ownership:

- `ScopeDoc`
- front matter parsing and formatting
- atomic source text writes for Docs source files
- published/viewable boolean interpretation
- scope normalization and source-root/path enumeration
- `load_scope_docs(...)` and duplicate/parent validation
- sort-order helpers, sibling ordering, descendant/direct-child lookup, and placement records
- source rewrite helpers for metadata and placement updates
- unique source stem generation

Acceptance checks:

- `tests/python/test_docs_source_model.py` covers front matter parsing/formatting, duplicate ids, unknown-parent behavior, Library's unknown-parent allowance, sort helpers, move placement normalization, descendant cycle support, source rewrite behavior, and unique stem generation
- `tests/python/test_docs_management_server.py` still passes
- `tests/python/test_docs_management_routes.py` still passes
- `tests/python/test_docs_import_service.py` still passes as a compatibility check for source-import flows that use the moved helpers
- `scripts/docs/docs_management_server.py`, `scripts/docs/docs_source_model.py`, and `tests/python/test_docs_source_model.py` compile with the configured Python interpreter

Benefits:

- gives the highest-reuse Docs source behavior a directly testable module
- makes later mutation-planner and write/rebuild slices smaller because source tree operations now have a single owner
- reduces pressure on the HTTP server file as import/export use cases continue growing

Risks:

- the server still calls the moved helpers directly, so file-size reduction is only partial until later handler cleanup
- front matter formatting remains a source-file contract; future helper changes should keep formatting tests close to the module
- source-write helpers remain Docs-source-specific until write/rebuild ownership is reviewed in Slice 5

## Planned Slice Sequence

The remaining sequence now moves from activity into rebuild/write and mutation-planning ownership.
Slice 5 is the next planned implementation slice and should still be reconfirmed before editing.

Remaining planned order:

1. Slice 5: rebuild and source-write follow-through helpers.
2. Slice 6: management mutation planners.
3. Slice 7: import-source orchestration cleanup, only if still useful.
4. Slice 8: final handler body cleanup and closeout.

Importer/exporter note:

The import/export adapters are expected to grow because only a small number of use cases have been implemented so far.
That argues against folding adapter internals into the docs-management server restructuring.
For now, `scripts/docs/docs_export.py`, `scripts/docs/docs_import.py`, and `scripts/docs/docs_html_import.py` should remain separate owners.
The docs-management server should keep only local-service orchestration around those adapters: request validation, dry-run/write decision, response status selection, activity attachment, and rebuild follow-through.
When adapter use cases expand enough to create their own structural confusion, review those modules as their own request or as a later adapter-specific child doc.

### Slice 2 original checklist: docs source model helpers

Status: implemented; retained here as the original implementation checklist.

Proposed module owner:

- `scripts/docs/docs_source_model.py`

Move only source-model and tree helpers that can be exercised without an HTTP handler, subprocess rebuild, or adapter call.

Target ownership:

- `ScopeDoc`
- front matter parsing and formatting
- source text formatting and atomic source text writes if kept source-specific
- published/viewable boolean interpretation
- scope normalization and source-root/path enumeration
- `load_scope_docs(...)` and duplicate/parent validation
- sort-order helpers, sibling ordering, descendant/direct-child lookup, and placement records
- source rewrite helpers for metadata and placement updates
- unique source stem generation

The server should keep:

- endpoint request extraction
- dry-run decisions
- backup bundle creation until write/rebuild ownership is reviewed
- rebuild calls and watcher suppression
- import/export adapter calls
- generated-data reads until Slice 3
- activity append timing until Slice 4
- response assembly

Acceptance checks:

- add a focused `tests/python/test_docs_source_model.py`
- cover front matter parsing/formatting for booleans, integers, quoted strings, and blank values
- cover source loading for duplicate `doc_id`, unknown parent rejection, and Library's current unknown-parent allowance
- cover sort ordering, next append order, move placement normalization, and descendant cycle support helpers
- cover source rewrite behavior preserving `added_date`, updating `last_updated`, and removing blank sort order where applicable
- keep existing `tests/python/test_docs_management_server.py` passing
- compile `scripts/docs/docs_management_server.py`, `scripts/docs/docs_source_model.py`, and the new test with the configured Python interpreter

Benefits:

- gives the highest-reuse docs source behavior a direct-testable home
- makes later management mutation planners smaller and safer
- reduces the chance that import/export growth increases pressure on the HTTP server file

Risks:

- front matter formatting is a source-file contract, so subtle ordering or quoting changes can create noisy docs diffs
- `load_scope_docs(...)` currently allows unknown Library parents; moving it must preserve that deliberate behavior
- source write helpers may look generic but remain docs-source-specific until write/rebuild ownership is reviewed

### Slice 3: generated-data read helpers

Status: implemented.

The third implementation slice extracted generated Docs Viewer JSON read helpers from `scripts/docs/docs_management_server.py` into `scripts/docs/docs_generated_reads.py`.
The server still owns GET route dispatch, query parameter extraction, scope normalization, HTTP status mapping, and raw JSON response writing.
The generated-read module owns generated artifact paths, JSON loading errors, payload safety checks, and generated-data availability probes used by `/capabilities`.

Module owner:

- `scripts/docs/docs_generated_reads.py`

Target ownership:

- generated docs index path resolution
- generated per-doc payload path resolution
- generated search index path resolution
- generated JSON parsing and error messages
- manage-mode payload safety checks that require a doc to be present in the generated scope index
- generated-read availability checks used by `/capabilities`

The server should keep:

- GET endpoint dispatch
- query parameter extraction
- HTTP status mapping
- raw payload response writing

Acceptance checks:

- `tests/python/test_docs_generated_reads.py` covers generated docs/search availability, unsafe `doc_id` rejection, non-viewable indexed payload reads, unlisted payload rejection, unexpected `content_url` rejection, external URL path handling, and invalid generated JSON errors
- `tests/python/test_docs_management_server.py` keeps `/capabilities` behavior covered
- `scripts/run_checks.py --profile docs` now includes the generated-read helper tests

Benefits:

- separates local generated-artifact reads from source mutation behavior
- keeps the public viewer runtime from becoming responsible for local manage-mode read safety
- gives generated-read safety checks a direct test owner before later write/rebuild extraction

Risks:

- generated read endpoints are used by local docs viewer manage mode; error and missing-file behavior should remain stable
- this module should not drift into docs build ownership
- the server imports the generated-read helpers directly, so future endpoint additions still need route and handler updates in the server layer

### Slice 4: docs activity helpers

Status: implemented.

The fourth implementation slice extracted Docs Management Studio Activity construction from `scripts/docs/docs_management_server.py` into `scripts/docs/docs_activity.py`.
The server still owns endpoint completion timing: each POST handler decides whether work completed far enough to call the activity helper, then tolerates activity append failure without failing the main endpoint.
The activity module owns docs-specific status selection, record-group id compaction, endpoint constants through `scripts/docs/docs_management_routes.py`, and the docs-management local log source reference used in activity rows.

Module owner:

- `scripts/docs/docs_activity.py`

Target ownership:

- docs activity status calculation
- compact id extraction for docs/file record groups
- activity row attachment helpers for broken-links audit, docs export, source import, and documents import apply
- docs activity endpoint constants via `scripts/docs/docs_management_routes.py`
- local log source references for docs-management service activity

The server should keep:

- deciding when an endpoint has completed enough work to attempt activity append
- passing request body and response payload into the helper
- tolerating activity append failure without failing the main endpoint

Acceptance checks:

- `tests/python/test_docs_activity.py` covers dry-run/export no-write suppression, successful export record groups/source refs, import-source preview and overwrite-confirmation suppression, import-apply confirmation suppression, and broken-link warning status when broken links are found
- activity helper tests use endpoint constants from `scripts/docs/docs_management_routes.py`
- `scripts/run_checks.py --profile docs` now includes the activity helper tests
- `scripts/docs/docs_activity.py`, `scripts/docs/docs_management_server.py`, `scripts/run_checks.py`, `tests/python/test_docs_activity.py`, and `tests/python/test_docs_management_server.py` compile with the configured Python interpreter
- `tests/python/test_docs_management_server.py` and `tests/python/test_docs_management_routes.py` still pass

Benefits:

- removes docs-specific activity construction from the HTTP server
- makes activity behavior easier to expand as importer/exporter use cases grow
- keeps the server focused on endpoint timing and response status rather than row assembly details

Risks:

- Studio Activity rows are user-facing operational history, so row status, record ids, and source refs should not drift
- do not generalize to a shared activity framework until catalogue/docs/tag patterns are compared after their own slices
- the server still calls the moved helpers directly, so later handler cleanup should keep endpoint timing easy to follow

### Slice 5: rebuild and source-write follow-through helpers

Status: planned.

Proposed module owner:

- `scripts/docs/docs_write_rebuild.py`

Target ownership:

- bundle executable detection if still only used for docs rebuilds
- same-scope docs payload rebuild command assembly
- same-scope docs-search rebuild command assembly, including targeted `--only-doc-ids` and `--remove-missing`
- all-scope docs rebuild helper if it still belongs to this service
- watcher suppression setup/clear/complete around source writes
- common write-operation wrapper that runs source writes followed by rebuilds

The server should keep:

- deciding which docs changed
- deciding whether search is included and which doc ids are targeted
- endpoint-specific dry-run and no-op behavior
- backup timing until the mutation-planner slice decides whether backups need a separate owner
- response payload assembly

Acceptance checks:

- add focused tests that stub rebuild execution rather than invoking Ruby
- preserve command shapes for `scripts/build_docs.rb --scope <scope> --write`
- preserve command shapes for `scripts/build_search.rb --scope <scope> --write`
- preserve targeted search behavior with `--only-doc-ids` and `--remove-missing`
- preserve watcher-suppression cleanup on exceptions
- keep `./scripts/run_checks.py --profile docs` passing

Benefits:

- isolates subprocess and watcher-suppression mechanics from endpoint bodies
- gives later docs viewer UI work a clearer local-service rebuild contract

Risks:

- rebuild command shape is part of the local workflow; do not change all-scope versus scope-specific behavior casually
- watcher suppression can hide useful rebuilds if filenames or status transitions are wrong

### Slice 6: management mutation planners

Status: planned after source model and write/rebuild helpers.

Proposed module owner:

- `scripts/docs/docs_management_mutations.py`

Target ownership:

- create-source planning
- metadata update planning
- single and bulk viewability update planning
- move and restore-move placement planning
- archive planning
- delete preview and delete apply planning
- backup document-set selection for these management mutations
- search target id planning for metadata, create, move, archive, delete, and viewability changes

The server should keep:

- endpoint request parsing
- endpoint response status mapping
- dry-run write suppression orchestration
- final response assembly where Studio currently expects specific keys
- calling source write/rebuild helpers
- activity timing if not already moved

Acceptance checks:

- move or add focused tests for create, metadata, viewability, move, restore, archive, delete-preview, and delete-apply planning
- preserve current blocker messages for delete preview
- preserve search target behavior documented in [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- preserve backup bundle contents and reported `backup_dir` shape
- preserve no-op behavior for already-archived docs and unchanged viewability updates

Benefits:

- makes local docs management behavior testable without HTTP transport
- leaves the server closer to request orchestration while keeping importer/exporter calls separate

Risks:

- this is the highest-risk docs-management slice because it touches source writes, backups, delete behavior, and search updates
- do not combine this with importer/exporter restructuring

### Slice 7: import-source orchestration cleanup

Status: optional planned slice.

Only do this after Slices 2-6 if `handle_import_source(...)` remains too dense.

Proposed module owner:

- `scripts/docs/docs_import_source_service.py`

Target ownership:

- local-service orchestration around staged source import previews and applies
- collision response shaping for create versus overwrite
- replacement `doc_id` and title handling
- source text construction using `docs_html_import` helpers
- inline media materialization call sequencing
- source backup selection for overwrite
- source write and rebuild handoff

The server should keep:

- endpoint route dispatch
- body parsing
- HTTP response status
- activity append timing if Slice 4 has not moved it

Explicit non-goal:

- do not move converter internals out of `scripts/docs/docs_html_import.py`

Acceptance checks:

- expand `tests/python/test_docs_import_service.py` around collision, preview-only, overwrite confirmation, replacement id, Markdown import, and media-write paths
- preserve existing import response keys such as `preview_only`, `requires_overwrite_confirmation`, `inline_media_written`, `backup_dir`, and `summary_text`
- preserve no-write behavior for dry-run and preview-only requests

Benefits:

- narrows the biggest remaining endpoint body without taking over importer internals
- creates a better surface for future import-source UI improvements

Risks:

- this flow mixes conversion, media staging, source writes, rebuilds, and collision UX; over-extraction could make it harder to trace
- importer/exporter growth should still happen in adapter-owned modules unless the local-service orchestration itself is the pain point

### Slice 8: final handler body cleanup and closeout

Status: planned closeout.

Target ownership:

- remove dead helpers and stale constants
- verify server call sites use explicit module namespaces
- refresh script docs and this slice plan with the final module boundary
- decide whether remaining candidates should be marked `leave` or moved to a separate request

Acceptance checks:

- no duplicate endpoint constants outside `docs_management_routes`
- no broad compatibility aliases or re-export layers for extracted helpers
- direct tests exist for each extracted owner
- `./scripts/run_checks.py --profile docs` passes
- rebuild Studio docs/search payloads when docs changed

Benefits:

- leaves `docs_management_server.py` as HTTP orchestration rather than a mixed domain module
- creates a stable handoff point before reviewing `tag_write_server.py`

Risks:

- closeout should not become a catch-all refactor; defer unclear work instead of folding it into the final cleanup
