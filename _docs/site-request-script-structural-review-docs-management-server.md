---
doc_id: site-request-script-structural-review-docs-management-server
title: Docs Management Server Slices
added_date: 2026-05-09
last_updated: "2026-05-09 12:27"
parent_id: site-request-script-structural-review
sort_order: 20
---
# Docs Management Server Slices

Status:

- Slice 1 implemented
- remaining slices are candidates, not yet committed

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

## Candidate Next Slices

Potential follow-on slices, subject to review:

- source-model helpers for front matter parsing, source formatting, scope loading, tree placement, and viewability planning
- generated-data read helpers for local manage-mode reads of generated docs/search payloads
- docs activity helpers for import/export/import-apply and broken-links activity rows
- rebuild/write suppression helpers for source writes that trigger docs/search rebuilds
- import-source apply helpers if the source import path remains too dense after source-model extraction

Do not extract import/export adapter internals merely because they are called by this server.
Those modules already have separate owners, and the server's job is to orchestrate them through the local write surface.
