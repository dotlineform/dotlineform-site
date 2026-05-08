---
doc_id: site-request-script-structural-review
title: Script Structural Review Request
added_date: 2026-05-08
last_updated: "2026-05-08 21:33"
ui_status: proposed
parent_id: change-requests
sort_order: 210
viewable: true
---
# Script Structural Review Request

Status:

- proposed

## Summary

Review large Studio and catalogue scripts for structural confusion, not only file size.

The immediate trigger is `scripts/studio/catalogue_write_server.py`: it is large enough to be awkward, but the more important problem is that HTTP transport, source mutation, publication/delete planning, activity rows, lookup refreshes, generated-artifact cleanup, prose imports, and build orchestration all live in one file.
Small changes can therefore require broad local knowledge and can carry hidden side effects across unrelated workflows.

## Goals

- identify scripts where mixed responsibilities make maintenance harder than necessary
- split only where the boundary is clear and useful
- keep behavior and response payload contracts stable during extraction
- add or improve focused tests before moving risky logic
- document module ownership so future changes have an obvious home

## Non-Goals

- do not split files only because they are long
- do not redesign the Studio local-service architecture as part of this request
- do not change endpoint URLs, request payloads, response payloads, backup behavior, or generated artifact semantics unless a later implementation task explicitly calls that out
- do not move dependency registries from code to JSON/config unless there is a second real consumer

## Candidate Scripts

| Priority | Script | Current size | Review focus | Likely extraction direction |
|---|---:|---:|---|---|
| 1 | `scripts/studio/catalogue_write_server.py` | 6655 lines | structural confusion around HTTP handlers, catalogue source writes, publication/delete planning, activity rows, lookup refreshes, build orchestration, prose imports, and generated cleanup | split activity helpers, request/domain planners, transaction helpers, lookup refresh helpers, and keep the HTTP handler as orchestration |
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
