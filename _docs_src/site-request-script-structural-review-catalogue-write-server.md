---
doc_id: site-request-script-structural-review-catalogue-write-server
title: Catalogue Write Server Slices
added_date: 2026-05-08
last_updated: "2026-05-09 00:35"
parent_id: site-request-script-structural-review
sort_order: 10
---
# Catalogue Write Server Slices

Status:

- Slices 1-12 implemented
- Slice 13 is the next planned implementation slice

## Purpose

This child doc tracks the detailed implementation slices for restructuring `scripts/studio/catalogue_write_server.py`.
The parent [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review) stays focused on the broader review goals, candidate scripts, and acceptance criteria.

The intended end state is not a small file for its own sake.
The write server should remain the catalogue local-service HTTP and endpoint orchestration layer, while cohesive domain planning, lookup refresh execution, source mutation planning, cleanup, transactions, activity contracts, and route inventories have explicit module owners and focused tests.

## Slice Principles

- Define the module ownership boundary before moving code.
- Move behavior in reviewable slices that keep endpoint URLs, request payloads, response payloads, backup behavior, dry-run behavior, and generated artifact semantics stable.
- Keep endpoint-specific allowlist checks visible before writes.
- Prefer direct tests against the owning extracted module.
- Close each slice without broad compatibility aliases, duplicate endpoint strings, or duplicate constants.

## Implemented Slices

### Slice 1: catalogue invalidation rules

Status: implemented.

The first implementation slice extracted lookup and moment-build invalidation constants, registries, and helper functions from `scripts/studio/catalogue_write_server.py` into `scripts/catalogue_invalidation.py`.
The write server now references those helpers through the `invalidation.*` namespace, so endpoint behavior and response payloads remain unchanged while helper ownership stays visible.
`tests/python/test_catalogue_invalidation.py` pins representative work, detail, series, and moment invalidation outcomes directly against the extracted module.

Benefits:

- gives field-to-derived-artifact invalidation rules a single obvious module home
- reduces the write server's mixed responsibility surface without touching write, backup, HTTP, or refresh execution behavior
- keeps the existing Studio activity context tests able to pin the moment invalidation contract during the move

Risks:

- the new module is still catalogue-specific, so it should not become a shared local-service utility
- future changes must keep lookup rule ownership in `scripts/catalogue_invalidation.py` rather than reintroducing registry edits in the HTTP server

### Slice 2: catalogue activity helpers

Status: implemented.

The second implementation slice extracted catalogue-specific Studio Activity profiles, context normalization, row builders, and response-count bookkeeping from `scripts/studio/catalogue_write_server.py` into `scripts/catalogue_activity.py`.
It also introduced `scripts/catalogue_routes.py` as the single endpoint-path source used by both the write server and activity profiles.
The write server now references activity helpers as `activity.*`, invalidation helpers as `invalidation.*`, and route paths as `routes.*`, so moved helper ownership stays visible instead of being re-exported through the server module.
`tests/python/test_studio_activity_context.py` now exercises `scripts/catalogue_activity.py` and `scripts/catalogue_invalidation.py` directly.

Benefits:

- gives catalogue activity contracts a clear module home separate from HTTP routing and source writes
- gives catalogue endpoint constants a single module home shared by route dispatch and activity profiles
- makes the earlier invalidation extraction explicit at call sites through the `invalidation.*` namespace
- keeps catalogue-specific page/action/profile knowledge out of a generic shared utility until a real shared boundary is clear
- reduces the write server's mixed activity/build/delete helper surface without touching backup, write, or endpoint orchestration behavior

Risks:

- context normalization for catalogue record ids now has its own local normalizers in `scripts/catalogue_activity.py`; keep behavior aligned with request extraction helpers when id formats evolve
- `scripts/catalogue_routes.py` is intentionally small, but future endpoint additions should go there first so route dispatch and activity profiles do not drift

### Slice 3: generated cleanup helpers

Status: implemented.

The third implementation slice extracted generated public-artifact cleanup planning from `scripts/studio/catalogue_write_server.py` into `scripts/catalogue_cleanup.py`.
The new module owns cleanup path collection for works, work details, series, and moments; cleanup allowlist checks; generated JSON cleanup payload mutation/finalization; and the small file-deletion helper used by delete and unpublish flows.
The write server now references those helpers as `catalogue_cleanup.*`, keeping HTTP orchestration, source writes, transaction backup timing, and response assembly in the server.
Shared catalogue id-list and detail-uid normalization moved into `scripts/catalogue_source.py` so the cleanup module and write server use one owner for source identity normalization.
`tests/python/test_catalogue_cleanup.py` exercises cleanup preview counts, cleanup scope rejection, and generated payload mutation directly against the extracted module.

Benefits:

- gives generated cleanup behavior a clear module home separate from canonical source writes and HTTP routing
- keeps delete and unpublish response payloads stable while making cleanup path ownership explicit
- avoids duplicating catalogue id normalization between the server and the extracted cleanup module
- pins the cleanup allowlist and generated payload mutation behavior in a focused direct-module test
- reduces the write server's delete/publication surface without moving transaction backup and restore behavior before that boundary is reviewed separately

Risks:

- delete and unpublish transactions still span the write server and cleanup module, so future transaction-helper extraction must preserve the current backup and restore ordering
- generated JSON payload mutation now depends on `scripts/catalogue_cleanup.py`; future generated artifact schema changes should update that module and its focused test rather than adding ad hoc cleanup edits in the server

### Slice 4: catalogue transaction helpers

Status: implemented.

The fourth implementation slice extracted timestamped backup names, transaction backup copying, best-effort restore behavior, transaction path de-duplication, and atomic multi-file JSON writes from `scripts/studio/catalogue_write_server.py` into `scripts/catalogue_transactions.py`.
The write server still owns endpoint orchestration, delete/unpublish transaction timing, cleanup calls, lookup refreshes, search rebuilds, and response assembly, but it now calls transaction mechanics through the `transactions.*` namespace.
`tests/python/test_catalogue_transactions.py` pins backup bundle layout, restore behavior for restored and newly-created files, and rollback after a simulated multi-file atomic write failure.

Benefits:

- gives backup and rollback mechanics a clear direct-testable module home
- reduces the write server's write-path surface without changing endpoint payloads or moving delete/unpublish orchestration prematurely
- keeps transaction backup timing visible in the write server while removing low-level file-copy and rollback mechanics from it
- provides focused regression coverage before any later extraction of full delete/unpublish transaction orchestration

Risks:

- delete and unpublish orchestration still spans the write server, `scripts/catalogue_cleanup.py`, and `scripts/catalogue_transactions.py`; the next slice should avoid hiding service-specific allowlist checks inside a generic helper
- `scripts/catalogue_transactions.py` imports cleanup only for existing-path de-duplication, so future shared-service extraction should revisit whether that helper belongs in a neutral local-service module

### Slice 5: moment cleanup transaction consolidation

Status: implemented.

The fifth implementation slice consolidated the duplicated moment delete/unpublish public-cleanup transaction path inside `scripts/studio/catalogue_write_server.py` and moved moment index cleanup payload mutation into `scripts/catalogue_cleanup.py`.
The write server still performs the source metadata allowlist check, generated payload allowlist check, cleanup-scope check, backup timing, search rebuild call, lookup/activity orchestration, and response assembly.
`scripts/catalogue_cleanup.py` now owns `build_moment_delete_generated_payloads(...)`, matching its existing ownership of catalogue generated JSON cleanup payload mutation.

Benefits:

- removes duplicated moment index mutation and backup/delete/search transaction scaffolding from the delete and unpublish branches
- keeps the endpoint-specific allowlist checks visible in the write server instead of hiding them behind a generic transaction helper
- keeps moment cleanup payload mutation covered directly alongside other cleanup payload tests
- narrows the next delete/publication cleanup slice because catalogue and moment cleanup now use more similar server-side transaction shapes

Risks:

- the write server still owns delete/unpublish orchestration, so future slices must preserve the current source-write, generated-write, cleanup, search, lookup, activity, and response ordering
- moment cleanup response keys are still intentionally different from catalogue cleanup response keys because existing Studio contracts distinguish `moments_index_updated` from generic generated JSON update counts

### Slice 6: catalogue prose import helpers

Status: implemented.

The sixth implementation slice extracted staged catalogue prose import and draft moment source import helpers from `scripts/studio/catalogue_write_server.py` into `scripts/catalogue_prose_import.py`.
The new module owns prose import target normalization, staged Markdown validation, preview payload construction, no-backup prose writes, and the draft moment import metadata/prose apply helper.
The write server still owns endpoint conflict responses, endpoint-specific allowlist sets, local log events, Studio Activity append timing for moment imports, and response payload assembly.
The no-backup atomic text write primitive moved into `scripts/catalogue_transactions.py` so write mechanics have one module owner.
`tests/python/test_catalogue_prose_import.py` pins staged prose preview/apply behavior, allowlist rejection, and draft moment metadata/prose application directly against the extracted module.
The new focused prose-import and transaction tests are included in the `quick` run-checks profile.

Benefits:

- gives staged catalogue prose imports a direct-testable module home separate from HTTP handlers
- keeps moment import application behavior explicit without moving Studio Activity response assembly out of the write server
- keeps no-backup text writes owned by the transaction helper module instead of the HTTP server
- documents that the shared prose import endpoint also handles existing moment prose imports, not only work and series prose

Risks:

- prose import apply still intentionally has no backup bundle, so future changes should not accidentally make it look equivalent to source JSON transactions
- draft moment import still writes prose before metadata as before; any later transaction-level change should be deliberate and covered by endpoint tests

### Slice 7: handler route dispatch cleanup

Status: implemented.

The seventh implementation slice cleaned up catalogue write-server route dispatch without changing endpoint URLs or handler bodies.
`scripts/catalogue_routes.py` now owns the route inventory for POST endpoints and CORS preflight handling through `POST_PATHS` and `OPTIONS_PATHS`.
`scripts/studio/catalogue_write_server.py` now uses a single `Handler.POST_HANDLERS` dispatch table instead of repeating the same endpoint inventory as a long `if` cascade.
`tests/python/test_catalogue_routes.py` pins route uniqueness, OPTIONS coverage, activity-profile endpoint coverage, and write-server POST dispatch coverage directly against the route owner and handler table.
The focused route test is included in the `quick` run-checks profile.

Benefits:

- makes the route inventory reviewable in one module instead of splitting it between CORS preflight, POST dispatch, and activity profiles
- keeps endpoint behavior stable while making missing handler coverage easier to catch
- keeps handler orchestration in the write server rather than introducing a broader local-service framework too early

Risks:

- `Handler.POST_HANDLERS` still lives in the write server because it points to server-local handler methods; future endpoint additions must update both `routes.POST_PATHS` and the dispatch table
- this slice only cleans routing structure; it does not reduce the larger endpoint method bodies or extract source-write orchestration

### Slice 8: lookup refresh execution helpers

Status: implemented.

The eighth implementation slice extracted lookup refresh execution helpers from `scripts/studio/catalogue_write_server.py` into `scripts/catalogue_lookup_refresh.py`.
The new module owns full lookup refresh execution, focused work/detail/series refresh writes, result payload shape, artifact labels, written counts, and written path reporting.
The write server still decides when a refresh runs, inserts `lookup_refresh` into endpoint responses, writes local service log rows, and appends Studio Activity rows.
`tests/python/test_catalogue_lookup_refresh.py` pins representative full, work, detail, and series refresh result payloads directly against the extracted module.
The focused lookup refresh test is included in the `quick` run-checks profile.

Benefits:

- reduces repeated handler body logic without moving source-write transactions
- completes the extraction path started by `scripts/catalogue_invalidation.py`
- gives refresh execution a focused module owner that can be tested without HTTP routing
- keeps `scripts/catalogue_lookup.py` as the payload builder/writer owner instead of duplicating lookup construction

Risks:

- `lookup_refresh` payloads are Studio-facing contracts, so result keys and artifact names must stay stable
- focused refresh paths depend on invalidation classifications; avoid re-encoding invalidation rules in the refresh module
- the write server still computes invalidation decisions before and after save writes, so later save-flow cleanup should avoid diverging those two paths

### Slice 9: save/build follow-through helper

Status: implemented.

The ninth implementation slice extracted the repeated post-save build decision and execution wrapper used by work, work-detail, series, and moment saves into `scripts/catalogue_save_build.py`.
The new module owns `build_requested` and `build_skipped` response decisions, no-public-artifact skip payloads, and the common save-time build runner call.
The write server still owns source mutation, backup/write timing, changed-state detection, endpoint-specific build target selection, response assembly outside build keys, and Studio Activity append timing.
`tests/python/test_catalogue_save_build.py` pins representative published, draft, no-public-artifact, moment-message-key, and build-failure payload behavior directly against the extracted module.
The focused save-build test is included in the `quick` run-checks profile.

Target ownership:

- `build_requested` and `build_skipped` response decisions
- no-public-artifact skip handling
- common scoped build execution payload wrapping
- build activity row construction should stay in `scripts/catalogue_activity.py` unless a clearer owner emerges

The write server should keep source mutation, backup/write timing, changed-state detection, endpoint-specific response assembly, and the endpoint decision to request a build.

Acceptance checks:

- representative published and draft save responses keep the same build-related keys
- no-build-required field changes still skip public builds with the same reason payload
- build failure response behavior stays unchanged

Benefits:

- starts reducing the larger save handler bodies after the route cleanup
- centralizes a repeated build follow-through pattern without taking over source writes
- keeps build activity rows and endpoint-specific target selection visible in the write server

Risks:

- build response payloads are visible to Studio save flows, so the helper should stay covered by direct payload-shape tests
- moving too much build orchestration could blur the boundary with `scripts/catalogue_json_build.py`

### Slice 10: source mutation planners for save/create paths

Status: implemented.

The tenth implementation slice extracted pure source mutation planning for work, work-detail, series, and moment save/create paths into `scripts/catalogue_source_mutation.py`.
The new module owns source record normalization, changed-field calculation, validation against already-loaded source records, generated section-id planning for new details, series member-work update planning, and source JSON payload construction.
The write server still owns request body extraction, source payload reads, existence/conflict checks before planner calls, endpoint-specific write allowlist checks, actual transaction writes/backups, lookup/build/activity orchestration, and response assembly.
`tests/python/test_catalogue_source_mutation.py` pins representative work, detail, series, and moment planner behavior directly against the extracted module.

Target ownership:

- request update normalization
- changed-field calculation
- updated source record construction
- validation target selection
- payload-to-write planning where no file writes occur

The write server should keep source payload reads, endpoint conflict and error responses, actual writes and backups, refresh/build/activity orchestration, and response assembly.

Acceptance checks:

- direct planner tests cover work, detail, series, and moment save/create cases
- source validation error text remains stable where Studio relies on it
- the planner returns plain data structures and performs no file writes

Benefits:

- moves pure source-record logic out of HTTP handlers
- makes source mutation behavior testable without running the local service
- prepares for a later transaction-executor slice without changing write timing yet
- keeps save/create write allowlist checks and transaction calls visible in the write server

Risks:

- canonical source record shape is high-value behavior; planner extraction can silently change omitted fields, field ordering, or validation
- keep this slice planner-only to avoid combining source-shape changes with transaction behavior changes
- lower-level normalization helpers still have legacy server call sites in bulk, delete, and publication flows; later planner/executor slices should continue migrating those paths without broad compatibility aliases

### Slice 11: save/create transaction executor

Status: implemented.

The eleventh implementation slice added a shared source JSON write executor in `scripts/catalogue_transactions.py` and switched save, create, bulk-save, and workbook-import apply paths to use it after their existing endpoint-specific allowlist checks.
The executor owns source payload-map validation, dry-run write suppression, calls into the atomic multi-file JSON writer, and backup path formatting for response payloads.
The write server still owns request parsing, existence/conflict validation, endpoint-specific allowlist checks, lookup/build/activity timing, and final response assembly.
`tests/python/test_catalogue_transactions.py` now covers executor dry-runs, response backup paths, empty payload-map rejection, and rollback behavior through the executor path.

Target ownership:

- target path to payload map validation
- atomic JSON write calls through `scripts/catalogue_transactions.py`
- backup path formatting for response payloads
- dry-run write suppression behavior where it is actually shared

The write server should keep endpoint-specific allowlist checks, endpoint-specific validation and conflict responses, lookup/build/activity timing, and final response assembly.

Acceptance checks:

- dry-run and non-dry-run save/create paths keep existing response payloads
- backups are still created in the same location and reported the same way
- failed multi-file writes still roll back through the transaction helper behavior

Benefits:

- addresses a risky repeated area only after source mutation planning has an owner
- reduces handler body size around write mechanics while preserving visible endpoint orchestration

Risks:

- backup timing, dry-run behavior, and rollback behavior are safety contracts
- do not hide service-specific write allowlists inside a generic executor

## Planned Slices

### Slice 12: delete/publication preview planners

Status: implemented.

The twelfth implementation slice extracted preview-side delete and publication planning into `scripts/catalogue_delete_plans.py` and `scripts/catalogue_publication.py`.
The write server now calls those modules for delete preview/apply preflight and publication preview/apply preflight, while keeping HTTP request extraction, apply transaction execution, endpoint-specific allowlist checks, response assembly, and Studio Activity timing in `scripts/studio/catalogue_write_server.py`.
`tests/python/test_catalogue_delete_plans.py` pins representative work, work-detail, series, and moment delete preview payloads.
`tests/python/test_catalogue_publication.py` pins representative publication blockers, unpublish cleanup attachment, series publish bootstrap behavior, and `save_published` status-change rejection.

Target ownership:

- delete preview construction
- publication target normalization
- publication blockers
- affected-record calculation
- build impact planning
- cleanup preview attachment

The write server should keep HTTP response handling, apply transaction execution, and activity timing.

Acceptance checks:

- preview response payloads for work, detail, series, and moment delete stay stable
- publish, unpublish, and save-published preview blockers stay stable
- cleanup preview attachment still uses `scripts/catalogue_cleanup.py` as the cleanup owner

Benefits:

- moves a large pure planning block out before touching apply transactions
- gives publication/delete rules a clearer home than the HTTP server
- lets apply-transaction extraction start from direct-tested preflight contracts

Risks:

- preview payloads are used to gate destructive UI actions
- publication blockers combine source metadata, generated readiness, and build impact, so ownership must stay explicit
- apply execution still spans the write server, cleanup, publication, delete-plan, and transaction modules until Slice 13

### Slice 13: delete/publication apply transaction orchestration

Status: planned.

Extract the riskiest remaining apply transaction orchestration only after preview planners have focused coverage.

Target ownership:

- apply transaction plan execution for delete, unpublish, publish, and save-published paths
- ordered source writes, generated writes, cleanup deletes, search rebuild, and restore behavior
- structured transaction result payloads for server response assembly

The write server should keep endpoint request parsing, allowlist checks before execution, final response assembly, and activity append orchestration unless a narrower later activity boundary is justified.

Acceptance checks:

- backup and restore ordering is pinned for successful and failing apply paths
- cleanup allowlist failures still block before writes
- generated payload keys stay stable, including moment-specific keys such as `moments_index_updated`
- catalogue search rebuild behavior and failure reporting stay stable

Benefits:

- finally addresses the most complex delete/publication handler bodies
- makes destructive apply paths direct-testable around explicit transaction results

Risks:

- this is the highest-risk slice because it can silently affect destructive writes, cleanup, rollback, search rebuilds, and Studio response contracts
- keep this slice smaller than the module name suggests; avoid moving unrelated save/create behavior at the same time

### Slice 14: handler body cleanup and closeout

Status: planned.

Clean up the remaining write-server surface after the extracted modules own their domains.

Target ownership:

- remove dead local helpers
- remove duplicated constants
- verify explicit module namespaces
- update `scripts-catalogue-write-server.md`
- update this slice plan and the parent request with final status

Completion checks:

- endpoint handlers no longer contain large blocks of pure domain planning
- source mutation, lookup refresh, cleanup, publication/delete planning, transactions, activity, and routes each have clear module owners
- endpoint-specific allowlist checks remain visible before writes
- no broad compatibility aliases or duplicated endpoint/path constants remain
- focused direct-module tests cover each extracted owner
- the smallest relevant checks pass, including syntax checks for moved Python modules and the relevant `quick` checks

Benefits:

- leaves the write server as transport and orchestration rather than a mixed domain module
- gives future catalogue service changes an obvious module home

Risks:

- cleanup-only edits can accidentally become behavior changes if stale helpers are removed without coverage
- do not continue extracting once the remaining server responsibilities are genuinely orchestration concerns
