---
doc_id: site-request-script-structural-review
title: Script Structural Review Request
added_date: 2026-05-08
last_updated: "2026-05-08 23:15"
ui_status: in_progress
parent_id: change-requests
sort_order: 210
viewable: true
---
# Script Structural Review Request

Status:

- in progress

## Summary

Review large Studio and catalogue scripts for structural confusion, not only file size.

The immediate trigger is `scripts/studio/catalogue_write_server.py`: it is large enough to be awkward, but the more important problem is that HTTP transport, source mutation, publication/delete planning, activity rows, lookup refreshes, generated-artifact cleanup, prose imports, and build orchestration all live in one file.
Small changes can therefore require broad local knowledge and can carry hidden side effects across unrelated workflows.

## Goals

- identify scripts where mixed responsibilities make maintenance harder than necessary
- split only where the boundary is clear and useful
- keep behavior and response payload contracts stable during extraction
- finish each implementation slice with clean module ownership, not temporary compatibility aliases or duplicate constants
- add or improve focused tests before moving risky logic
- document module ownership so future changes have an obvious home

## Non-Goals

- do not split files only because they are long
- do not redesign the Studio local-service architecture as part of this request
- do not change endpoint URLs, request payloads, response payloads, backup behavior, or generated artifact semantics unless a later implementation task explicitly calls that out
- do not move dependency registries from code to JSON/config unless there is a second real consumer
- do not leave extracted helpers re-exported through the old module as a long-term compatibility layer

## Candidate Scripts

| Priority | Script | Current size | Review focus | Likely extraction direction |
|---|---:|---:|---|---|
| 1 | `scripts/studio/catalogue_write_server.py` | 5648 lines | structural confusion around HTTP handlers, catalogue source writes, publication/delete planning, activity rows, lookup refreshes, build orchestration, prose imports, and generated cleanup | split request/domain planners, transaction helpers, refresh helpers, and keep the HTTP handler as orchestration |
| 2 | `scripts/docs/docs_management_server.py` | 3076 lines | docs source editing, generated-data reads, import/export adapters, rebuild orchestration, activity rows, and HTTP transport are tightly packed | separate docs source model helpers, import/apply flows, activity helpers, and handler routing |
| 3 | `scripts/studio/tag_write_server.py` | 2972 lines | tag assignment, registry, alias, import, promotion/demotion, activity, backups, and HTTP routing share one service file | separate tag domain mutations from transport and shared local-service write helpers |
| 4 | `scripts/generate_work_pages.py` | 2891 lines | generator internals contain source projection, validation, route stubs, aggregate indexes, recent entries, rendering, and writeback-adjacent logic | split catalogue record projection/index builders from CLI orchestration and page/file writers |
| 5 | `scripts/catalogue_json_build.py` | 1775 lines | scoped build planning, media readiness, media generation, field-aware planning, and subprocess orchestration are mixed | separate local media planning/execution from build-scope planning and CLI/reporting code |
| 6 | `scripts/audit_site_consistency.py` | 1354 lines | audit checks can grow into a dense list of unrelated validators | group checks by domain with shared report contracts |
| 7 | `scripts/docs/docs_html_import.py`, `scripts/docs/docs_export.py`, `scripts/docs/docs_import.py` | 1176-1305 lines | import/export adapters may need clearer boundaries as Library and Docs workflows evolve | review after docs-management boundaries are clearer |

The line counts are a starting signal, not the decision rule.
Files lower on the list should remain untouched unless a concrete maintenance pain appears.

## Priority 1 Review: Catalogue Write Server

`scripts/studio/catalogue_write_server.py` should be reviewed around responsibility boundaries.

Recommended review questions:

- Which functions are pure domain logic and can be tested without an HTTP server?
- Which helpers are local-service infrastructure that should be shared with docs or tag write services?
- Which response payload keys are public contracts for Studio pages and should be pinned by tests before extraction?
- Which transaction paths create backups, restore on failure, or update multiple generated artifacts?
- Which activity-row helpers are catalogue-specific, and which are shared Studio activity infrastructure?
- Which logic belongs with catalogue source models, lookup payloads, field-aware build planning, or generated artifact cleanup?

Likely safe extraction sequence:

1. Activity profile/context/row helpers.
2. Lookup and moment-build invalidation registries and refresh helpers.
3. Delete/publication preview and generated-cleanup planning.
4. Atomic write, backup, restore, and transaction helpers.
5. Prose and moment import preview/apply helpers.
6. Handler routing cleanup after the extracted helpers are stable.

Each step should be behavior-preserving and small enough to review independently.

Slice discipline:

- Define the target ownership boundary before editing.
- Keep slices conservative by scope, not by leaving cleanup for later.
- After moving logic, update call sites to use the owning module explicitly, such as `activity.*`, `invalidation.*`, or a domain-specific namespace.
- If two modules need the same constants, move those constants to one intentionally named owner in the same slice instead of duplicating them.
- Do not treat broad re-exports, duplicate endpoint strings, or compatibility aliases as an acceptable slice end state unless an external caller outside this repo truly requires a deprecation window.
- Tests should exercise the owning extracted module directly where practical; the old module should not remain the test access path for moved behavior.

## Shared-Service Review

The catalogue, docs, and tag write servers share several local-service concerns:

- loopback-only CORS handling
- JSON body limits and parse errors
- allowlisted write paths
- timestamped backups
- compact operational logs
- Studio activity row append behavior
- dry-run response conventions

This request should review whether those should become a small shared local-service utility module.
The risk is over-generalizing too early; shared code should be introduced only where it removes repeated, well-understood mechanics without hiding service-specific safety rules.

## Acceptance Criteria

- inventory the candidate scripts and mark each as `extract`, `leave`, or `defer`
- define target module boundaries before moving code
- add focused tests around the behavior being moved before or during each extraction
- remove temporary bridge code, compatibility aliases, and duplicated constants before closing a slice
- keep call sites explicit about the owning module for extracted behavior
- keep endpoint/request/response contracts stable unless a separate request approves a contract change
- keep backups, restore behavior, dry-run behavior, and allowlists at least as strict as before
- update the relevant script docs when module ownership or command behavior changes
- run the smallest relevant checks after each extraction slice, including syntax checks for moved Python modules

## Risks

- broad refactors can obscure behavior changes in write paths
- splitting helpers before their ownership is clear can make navigation worse
- shared utility modules can accidentally weaken service-specific security checks
- generated artifact cleanup and backup/restore paths are easy to regress without targeted tests
- response payload changes can silently break Studio pages if they are not pinned before extraction

## Suggested First Slice

Start with a read-only review of `scripts/studio/catalogue_write_server.py` and produce a concrete extraction map.

The first implementation slice should probably move only activity helpers or lookup invalidation helpers, because those are already relatively cohesive and have targeted tests.

## Implementation Notes

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
