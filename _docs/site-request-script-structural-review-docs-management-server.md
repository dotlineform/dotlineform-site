---
doc_id: site-request-script-structural-review-docs-management-server
title: Docs Management Server Slices
added_date: 2026-05-09
last_updated: "2026-05-09 14:00"
parent_id: site-request-script-structural-review
sort_order: 20
---
# Docs Management Server Slices

Status:

- Slice 1 implemented
- Slice 2 implemented
- Slice 3 implemented
- Slice 4 implemented
- Slice 5 implemented
- Slice 6 implemented
- Slice 7 implemented
- Slice 8 remains planned closeout

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
- source-write helpers remain Docs-source-specific; rebuild follow-through is now owned by Slice 5's write/rebuild helper module

## Planned Slice Sequence

The remaining sequence now moves into final handler cleanup.

Remaining planned order:

1. Slice 8: final handler body cleanup and closeout.

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
- backup bundle creation until a later ownership review
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
- source write helpers may look generic but remain docs-source-specific; rebuild follow-through ownership is handled separately in Slice 5

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

Status: implemented.

The fifth implementation slice extracted Docs Management rebuild and source-write follow-through helpers from `scripts/docs/docs_management_server.py` into `scripts/docs/docs_write_rebuild.py`.
The server still decides which docs changed, when endpoint-specific dry-run or no-op behavior suppresses writes, which search doc ids are targeted, when backups are created, and how response payloads are assembled.
The extracted module owns the subprocess rebuild command shapes, bundle executable detection, watcher-suppression setup/cleanup/completion, search id de-duplication for rebuilds, and the common source-write followed by rebuild wrapper.

Module owner:

- `scripts/docs/docs_write_rebuild.py`

Target ownership:

- bundle executable detection for Docs Management rebuilds
- same-scope docs payload rebuild command assembly
- same-scope docs-search rebuild command assembly, including targeted `--only-doc-ids` and `--remove-missing`
- all-scope docs rebuild helper used by the explicit rebuild endpoint
- watcher suppression setup/clear/complete around source writes
- common write-operation wrapper that runs source writes followed by rebuilds

The server keeps:

- deciding which docs changed
- deciding whether search is included and which doc ids are targeted
- endpoint-specific dry-run and no-op behavior
- backup timing until the mutation-planner slice decides whether backups need a separate owner
- response payload assembly

Acceptance checks:

- `tests/python/test_docs_write_rebuild.py` stubs rebuild execution and covers full same-scope rebuild command shapes
- targeted search behavior preserves `--only-doc-ids` and `--remove-missing`
- empty targeted search ids still rebuild docs payloads without a search command
- watcher suppression is marked pending before writes, complete after successful rebuilds, and cleared on exceptions
- all-scope rebuild command sequence remains explicit for docs payloads plus studio, library, and analysis search
- `./scripts/run_checks.py --profile docs` now includes the write/rebuild helper tests

Benefits:

- isolates subprocess and watcher-suppression mechanics from endpoint bodies
- gives later docs viewer UI work a clearer local-service rebuild contract
- keeps rebuild command-shape tests close to the module that owns those commands

Risks:

- rebuild command shape is part of the local workflow; future changes should keep the helper tests updated with intentional behavior changes
- watcher suppression can hide useful rebuilds if filenames or status transitions are wrong
- the server still owns backup and mutation decisions, so Slice 6 should avoid re-moving write/rebuild mechanics back into mutation planning

### Slice 6: management mutation planners

Status: implemented.

The sixth implementation slice extracted Docs Management mutation planning from `scripts/docs/docs_management_server.py` into `scripts/docs/docs_management_mutations.py`.
The server still owns HTTP request handling, dry-run write suppression, backup bundle creation, source write/rebuild execution through `scripts/docs/docs_write_rebuild.py`, local logging after completed writes, and response status mapping.
The extracted module owns management mutation decisions: source write/delete plans, backup document-set and manifest metadata selection, delete-preview blockers and warnings, response payload bases, and targeted search doc ids.

Module owner:

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

The server keeps:

- endpoint request parsing
- endpoint response status mapping
- dry-run write suppression orchestration
- final response assembly for `dry_run`, `backup_dir`, and `rebuild` keys where Studio currently expects them
- calling source write/rebuild helpers
- completed-write local logging

Acceptance checks:

- `tests/python/test_docs_management_mutations.py` covers create, metadata, viewability, move, restore, archive no-op, delete-preview, and delete-apply planning
- delete-preview blocker text remains `1 child docs still depend on this parent`
- search target planning is pinned for create, metadata title changes, metadata status-only changes, viewability, move, restore, archive, and delete flows
- backup operation, document selection, and manifest metadata are planned by the mutation module while reported `backup_dir` shape stays assembled by the server
- no-op behavior is preserved for already-archived docs and unchanged viewability updates
- `./scripts/run_checks.py --profile docs` now includes the mutation planner tests

Benefits:

- makes local docs management behavior testable without HTTP transport
- leaves the server closer to request orchestration while keeping importer/exporter calls separate
- gives backup/search planning a direct test owner without moving subprocess rebuild mechanics back out of `scripts/docs/docs_write_rebuild.py`

Risks:

- this was the highest-risk docs-management slice because it touched source writes, backups, delete behavior, and search updates
- the server still wraps mutation plans with backup/write/rebuild execution, so future endpoint response changes should be tested both at planner and server levels
- importer/exporter restructuring remains out of scope

### Slice 7: docs-import source orchestration cleanup

Status: implemented.

The seventh implementation slice extracted staged source import orchestration from `scripts/docs/docs_management_server.py` into `scripts/docs/docs_import_source_service.py`.
The server still owns endpoint route dispatch, request body parsing, HTTP response status, dependency binding for existing backup/log/rebuild helpers, and Studio Activity append timing.
The extracted service owns the `/studio/docs-import/` source-import flow around staged source files: import preview/apply orchestration, create versus overwrite response shaping, collision handling, replacement ids/titles, source text construction, inline-media materialization sequencing, backup/rebuild handoff timing, and import-source file listing payloads.

Slice 7 is about the /studio/docs-import/ page flow, specifically the Docs Management endpoints around staged source files:

- GET /docs/import-source-files
- POST /docs/import-source
- compatibility alias POST /docs/import-html

That flow imports source-like documents from `var/docs/import-staging/` into Docs Viewer Markdown source files, including HTML, Markdown, text, SVG, image/file wrappers, collisions, overwrite confirmation, inline media materialization, backups, and rebuild follow-through.

It is not the export/import adapter system used by `/studio/export/` and `/studio/import/` for structured data workflows such as Library JSON/JSONL summary or hierarchy import.

- **In scope**: cleanup around handle_import_source(...) in docs_management_server.py
- **Out of scope**: `export_import_adapters.py`, `/studio/import/`, `/studio/export/`, `handle_documents_import_preview(...)`, `handle_documents_import_apply(...)`, and adapter dispatch logic

Module owner:

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
- dependency binding for backup/log/rebuild helpers that remain server-local or shared with other endpoint flows
- activity append timing

Explicit non-goal:

- do not move converter internals out of `scripts/docs/docs_html_import.py`

Acceptance checks:

- `tests/python/test_docs_import_service.py` now exercises source-import behavior through `scripts/docs/docs_import_source_service.py` while still using the server's dependency binding for backup/log/rebuild helpers
- existing coverage pins staged source listing, HTML create, Markdown import, text import, SVG sanitization, standalone image/file wrapper imports, inline-media materialization, invalid inline media skip behavior, and replacement-id collision recovery
- preserve existing import response keys such as `preview_only`, `requires_overwrite_confirmation`, `inline_media_written`, `backup_dir`, and `summary_text`
- preserve no-write behavior for dry-run and preview-only requests
- `scripts/run_checks.py --profile docs` includes the focused import-service tests
- `scripts/docs/docs_import_source_service.py`, `scripts/docs/docs_management_server.py`, `scripts/run_checks.py`, and `tests/python/test_docs_import_service.py` compile with the configured Python interpreter

Benefits:

- narrows the biggest remaining endpoint body without taking over importer internals
- creates a better surface for future import-source UI improvements
- keeps source-import tests pointed at the owning module rather than relying on the HTTP server as the test access path

Risks:

- this flow mixes conversion, media staging, source writes, rebuilds, and collision UX; over-extraction could make it harder to trace
- importer/exporter growth should still happen in adapter-owned modules unless the local-service orchestration itself is the pain point
- backup and rebuild mechanics are still supplied through server dependencies, so a later closeout should avoid turning this dependency seam into a broad compatibility layer

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
