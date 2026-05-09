---
doc_id: site-request-script-structural-review-tag-write-server
title: Tag Write Server Slices
added_date: 2026-05-09
last_updated: "2026-05-09 17:29"
ui_status: in-progress
parent_id: site-request-script-structural-review
sort_order: 30
viewable: true
---
# Tag Write Server Slices

Status:

- initial review tracker created
- Slice 1 implemented
- route inventory and POST dispatch are now owned by `scripts/tag_routes.py` plus `Handler.POST_HANDLERS`
- Slice 2 implemented
- tag activity status, changed-state, endpoint, record-group, and activity row helpers are now owned by `scripts/tag_activity.py`
- Slice 3 implemented
- tag source artifact paths, loading defaults, tag id/group/alias/weight validation, assignment normalization, import filename sanitization, and import assignment row validation are now owned by `scripts/tag_source_model.py`
- Slice 4 implemented
- tag assignment save planning, work override planning, assignment import preview/apply decisions, and assignment import response summary text are now owned by `scripts/tag_assignment_service.py`
- Slice 5 implemented
- tag registry import add/merge/replace behavior, canonical tag edit/delete planning, registry mutation summary text, alias import add/merge/replace behavior, alias edit/delete planning, alias target rewrite helpers, and alias mutation summary text are now owned by `scripts/tag_registry_mutations.py` and `scripts/tag_alias_mutations.py`
- next slice: promotion and demotion planners

## Purpose

This child doc tracks the detailed review and implementation slices for restructuring `scripts/studio/tag_write_server.py`.
The parent [Script Structural Review Request](/docs/?scope=studio&doc=site-request-script-structural-review) stays focused on the broader review goals, candidate scripts, completed priority summaries, and acceptance criteria.

The intended end state is not a small file for its own sake.
The tag write server should remain the Tag Studio local-service HTTP and endpoint orchestration layer, while cohesive route inventory, tag assignment model helpers, registry and alias mutation planning, promotion/demotion flows, activity contracts, and backup/write mechanics get explicit owners only when the boundary is useful.

## Analytics Context

Tags carry historical routing and naming baggage.
Conceptually, they are not generic Studio features: they are an Analytics metadata layer applied to catalogue works and series.
They are currently hosted in Studio because they are not surfaced on public catalogue routes such as `/series/`, but the product concept has since moved toward Analytics as the domain for catalogue data analysis and metadata layers.

Current state:

- the Analytics dashboard lives at `/studio/analytics/`
- Analytics dashboard links point to the tag pages
- tag docs such as [Series Tags](/docs/?scope=studio&doc=series-tags), [Tag Editor](/docs/?scope=studio&doc=tag-editor), and [Tag Aliases](/docs/?scope=studio&doc=tag-aliases) already sit under the Analytics docs parent
- tag UI routes now live under `/studio/analytics/`
- the write service still lives at `scripts/studio/tag_write_server.py`

Target concept:

- tags are the first implemented Analytics metadata layer, not the whole Analytics model
- future Analytics work may add more metadata or scoring layers over catalogue works and series
- [Registry-Driven Scoring Architecture](/docs/?scope=studio&doc=registry-driven-scoring-architecture) describes one likely expansion path: Analytics functionality will need its own registries and registry-driven scoring interfaces, which may need pages similar to the existing tag registry and series-tags pages, or extensions of those pages
- script ownership should align with that concept, so a later folder reorganization should use `scripts/analytics/` rather than a tag-specific package
- `scripts/studio/` should be reserved for general-purpose Studio admin and shared runtime services

Routing cleanup was related but separate from this server restructuring.
The tag routes were moved under `/studio/analytics/` without compatibility redirects or aliases in [Analytics Tag Route Cleanup Request](/docs/?scope=studio&doc=site-request-analytics-tag-route-cleanup), so tag write-server implementation slices can now depend on settled page route context.

Server naming is also an open architectural question.
If this local service remains limited to tag assignment, tag registry, and tag alias writes, `tag_write_server.py` remains accurate.
If the service becomes the write/service layer for broader Analytics registries, scoring dimensions, or future Analytics metadata workflows, the target name should probably become `analytics_server.py` or an equivalent Analytics service name rather than creating a second parallel local server for each new Analytics registry.
That decision should be made before final closeout, because it affects route constants, docs, `bin/dev-studio`, check profiles, and the future `scripts/analytics/` package layout.

Sequencing decision:

1. Use the completed [Analytics Tag Route Cleanup Request](/docs/?scope=studio&doc=site-request-analytics-tag-route-cleanup) as the settled page-route context.
2. Complete the tag write-server structural review in the current script layout.
3. Use top-level `scripts/tag_*.py` modules for extracted owners during this review so each slice can focus on behavior boundaries rather than package moves.
4. Decide during final closeout whether the service remains `tag_write_server.py` or becomes an Analytics service such as `analytics_server.py`.
5. Move Analytics-owned script files into `scripts/analytics/` through the separate [Scripts Directory Organization Request](/docs/?scope=studio&doc=site-request-scripts-directory-organization) after the structural boundaries and service name are stable.

This avoids moving a mixed-responsibility server into a new package before its ownership boundaries are understood.

## Current Shape

`scripts/studio/tag_write_server.py` currently owns several responsibilities in one file:

- localhost HTTP transport, CORS, JSON body parsing, route dispatch, response status mapping, and dry-run handling
- tag assignment normalization and series/work assignment update behavior
- tag registry import and canonical tag mutation behavior
- tag alias import, edit, delete, and promotion behavior
- tag demotion behavior that touches registry, aliases, and assignments together
- JSON source loading for assignments, registry, aliases, and generated series membership
- atomic single-file and multi-file writes with timestamped backups and rollback
- Studio Activity row construction and append timing
- local operational logging and endpoint response assembly

That mix is workable, but it creates the same maintenance risk seen in the completed catalogue and docs server reviews: a small endpoint change can require understanding unrelated mutation, backup, import, activity, and transport behavior.

## Slice Principles

- Define the ownership boundary before moving code.
- Keep endpoint URLs, request payloads, response payloads, backup behavior, dry-run behavior, and write allowlists stable.
- Keep local-only service guardrails visible in the server.
- Prefer direct tests against the owning extracted module.
- Close each slice without broad compatibility aliases, duplicate endpoint strings, duplicate constants, or temporary server re-export layers.
- Do not reorganize script folders as part of these slices; package moves happen after this review through [Scripts Directory Organization Request](/docs/?scope=studio&doc=site-request-scripts-directory-organization).
- Do not move Studio tag page routes as part of these slices; route migration belongs in [Analytics Tag Route Cleanup Request](/docs/?scope=studio&doc=site-request-analytics-tag-route-cleanup).

## Planned Slice Sequence

The sequence below should be revised after a read-only code review, but it gives the initial implementation map.

### Slice 1: route inventory and handler dispatch

Status: implemented.

The first implementation slice kept endpoint behavior stable while moving the route inventory into `scripts/tag_routes.py`.
The new route owner defines `HEALTH_PATH`, every public tag POST endpoint, `POST_PATHS`, and `OPTIONS_PATHS`.
`scripts/studio/tag_write_server.py` now imports those route constants, exposes `Handler.POST_HANDLERS`, dispatches POST requests through the table, and uses the parsed request path for OPTIONS, GET, and POST route matching.
`tests/python/test_tag_routes.py` pins route uniqueness, OPTIONS coverage, and handler coverage for every POST route.
The focused tag route test is included in the `quick` run-checks profile.

Proposed module owner:

- `scripts/tag_routes.py` during this structural review, then `scripts/analytics/tag_routes.py` during the later folder organization pass

Target ownership:

- endpoint path constants
- POST route inventory
- OPTIONS/CORS preflight route coverage
- handler-dispatch coverage tests

The server should keep:

- HTTP transport
- request parsing
- handler methods
- response status mapping
- endpoint orchestration

Acceptance checks:

- every POST route has a handler table entry
- route inventories do not contain duplicates
- OPTIONS coverage includes every public endpoint
- existing tag server behavior still passes focused tests

Benefits:

- creates a single endpoint path owner before activity extraction
- removes repeated literal endpoint strings from preflight and POST dispatch
- follows the successful catalogue and docs route-slice pattern

Risks:

- route constants become part of the service contract; future endpoint additions must update route owner and handler dispatch together
- this slice is structural only and does not reduce mutation bodies

### Slice 2: tag activity helpers

Status: implemented.

The second implementation slice kept endpoint behavior stable while moving tag-specific Studio Activity decisions and row construction into `scripts/tag_activity.py`.
The helper now owns write-endpoint coverage via route constants from `scripts/tag_routes.py`, changed-state detection, warning/error status decisions, tag/alias record-group enrichment from normalized activity context, source refs for the tag write-server log, and non-fatal append failure handling.
`scripts/studio/tag_write_server.py` still decides when a completed handler should attempt an activity append, passes request and response payloads into the helper, and continues to suppress preview/dry-run activity rows.
`tests/python/test_tag_activity.py` pins route-owned write endpoints, no-op suppression, dry-run/no-context suppression, tag and alias record groups, source refs, status decisions, and append failure tolerance.
The focused tag activity test is included in the `quick` run-checks profile.

Proposed module owner:

- `scripts/tag_activity.py` during this structural review, then `scripts/analytics/tag_activity.py` during the later folder organization pass

Target ownership:

- tag activity status and changed-state decisions
- record-group id compaction for tags, aliases, assignments, series, and works
- Studio Activity row construction for tag assignment save, assignment import, registry import/mutation, alias import/mutation, promotion, and demotion
- tag activity endpoint constants via the route owner

The server should keep:

- deciding whether the endpoint completed far enough to attempt activity append
- passing request body and response payload into the helper
- tolerating activity append failure without failing the main endpoint

Acceptance checks:

- activity helper tests cover no-op suppression, write-only activity behavior, alias/tag record groups, and warning/error status decisions
- existing Studio activity feed/context tests still pass

Benefits:

- removes user-facing operational history construction from HTTP handlers
- creates a direct test owner before mutation helpers are moved
- keeps tag-specific activity behavior out of shared activity utilities

Risks:

- Studio Activity rows are user-facing history; status, record ids, endpoint strings, and source refs should not drift
- over-generalizing catalogue/docs/tag activity behavior too early could hide service-specific contracts

### Slice 3: tag source model and validation helpers

Status: implemented.

The third implementation slice kept endpoint behavior stable while moving source artifact path constants, JSON loading defaults, tag id/slug/group/alias/manual-weight validation, assignment tag normalization, import filename sanitization, import registry/alias validation, import assignment row validation, normalized assignment comparison helpers, and series-index membership extraction into `scripts/tag_source_model.py`.
`scripts/studio/tag_write_server.py` now imports that source-model owner and still decides which artifacts each endpoint needs, performs write allowlist checks, executes writes/backups, logs local events, and maps validation failures to HTTP responses.
`tests/python/test_tag_source_model.py` pins valid and invalid tag ids, alias keys, group and manual-weight rules, assignment row normalization, import filename basename sanitization, import assignment work-id validation, and default payload loading.
The focused tag source-model test is included in the `quick` run-checks profile.

Proposed module owner:

- `scripts/tag_source_model.py` during this structural review, then `scripts/analytics/tag_source_model.py` during the later folder organization pass

Target ownership:

- tag id, slug, group, alias key, and manual weight validation
- assignment tag normalization
- registry, alias, assignment, and series-index JSON loading defaults
- allowed group extraction
- stable source artifact path constants if they are not route-owned

The server should keep:

- endpoint body extraction
- deciding which source artifacts are needed by an endpoint
- write allowlist checks
- local logging

Acceptance checks:

- focused tests cover valid and invalid tag ids, alias keys, groups, weights, assignment rows, import filename sanitization, and default payload loading
- server tests still cover endpoint status mapping for validation errors

Benefits:

- gives the highest-reuse tag validation behavior a direct module home
- makes later mutation planners smaller
- reduces duplication risk between registry, aliases, and assignment flows

Risks:

- validation error text may be visible in Studio UI; tests should pin important messages before moving
- source path constants must not be duplicated between the server and helper modules

### Slice 4: assignment import and save planners

Status: implemented.

The fourth implementation slice kept endpoint behavior stable while moving assignment-specific save and import planning into `scripts/tag_assignment_service.py`.
The helper now owns series assignment row creation, series save planning, work override save planning, inherited-tag stripping, explicit empty work rows, work-row deletion, assignment import preview conflict/missing/invalid decisions, assignment import overwrite/skip apply behavior, and assignment import response summary text.
`scripts/studio/tag_write_server.py` still reads HTTP request bodies, loads the needed source artifacts, decides preview versus apply endpoints, validates write allowlists, suppresses writes during dry-run, executes assignment writes/backups, logs local events, and appends Studio Activity after completed writes.
`tests/python/test_tag_assignment_service.py` pins series saves, work override saves, work-row deletion, empty explicit work rows, import conflict detection, overwrite/skip decisions, invalid/missing skip behavior, no-mutation preview/apply behavior, and response summary text.
The focused tag assignment-service test is included in the `quick` run-checks profile.

Proposed module owner:

- `scripts/tag_assignment_service.py` during this structural review, then `scripts/analytics/tag_assignment_service.py` during the later folder organization pass

Target ownership:

- series/work assignment update planning
- assignment import preview and apply behavior
- current versus staged row comparison
- generated series membership checks
- response payload bases and summary text for assignment flows

The server should keep:

- HTTP body parsing
- dry-run write suppression
- backup/write execution until the write helper slice
- activity append timing
- local logging after completed writes

Acceptance checks:

- focused tests cover series saves, work override saves, work-row deletion, empty explicit work rows, import conflict detection, overwrite/skip decisions, and no-write preview behavior
- endpoint tests preserve existing response keys used by Tag Studio

Benefits:

- separates the largest assignment behavior from transport
- makes the Series Tag Editor save contract testable without an HTTP server
- gives import conflict behavior a focused owner

Risks:

- assignment import response payloads are Studio-facing; shape drift can break import review UI
- work override behavior has subtle inherited-tag rules that need direct tests

### Slice 5: registry and alias mutation planners

Status: implemented.

The fifth implementation slice kept endpoint behavior stable while moving registry and alias mutation planning into focused owners.
`scripts/tag_registry_mutations.py` now owns registry import add/merge/replace behavior, duplicate import compaction, canonical tag edit/delete planning, canonical rename guards, and registry import/mutation summary text.
`scripts/tag_alias_mutations.py` now owns alias import add/merge/replace behavior, duplicate alias compaction, alias edit/delete planning, registry-target validation for aliases, alias target count and one-target-per-group constraints, alias target rewrite helpers, redundant alias cleanup, and alias mutation summary text.
`scripts/studio/tag_write_server.py` still reads endpoint bodies, loads the required artifacts, orchestrates cross-artifact registry mutation rewrites, checks write allowlists, suppresses writes during dry-run/preview, executes writes/backups, logs local events, and appends Studio Activity after completed writes.
`tests/python/test_tag_registry_mutations.py` and `tests/python/test_tag_alias_mutations.py` pin the new owners, and both focused tests are included in the `quick` run-checks profile.

Proposed module owners:

- `scripts/tag_registry_mutations.py`
- `scripts/tag_alias_mutations.py`

Target ownership:

- registry import add/merge/replace behavior
- canonical tag edit/delete planning
- alias import add/merge/replace behavior
- alias edit/delete planning
- alias target rewrite helpers
- summary text for registry and alias flows if it is domain-specific

The server should keep:

- endpoint orchestration
- write allowlist checks
- dry-run write suppression
- activity append timing
- local logging

Acceptance checks:

- focused tests cover registry import modes, duplicate handling, canonical tag edit/delete, alias import modes, alias edit/delete, max targets, one-target-per-group constraints, and redundant alias cleanup
- endpoint response keys remain stable

Benefits:

- separates canonical tag and alias domain behavior from HTTP handlers
- gives mutation edge cases direct tests before demotion/promotion cleanup

Risks:

- registry, aliases, and assignments are tightly coupled during delete/edit flows; keep cross-artifact behavior visible rather than hiding it behind a generic helper too early

### Slice 6: promotion and demotion planners

Proposed module owner:

- `scripts/tag_promotion_mutations.py` or a combined tag mutation planner if Slice 5 shows the boundary is simpler that way

Target ownership:

- alias promotion planning
- tag demotion planning
- cross-artifact rewrite plans for registry, aliases, and assignments
- changed-artifact selection
- response payload bases and summary text for promotion/demotion flows

The server should keep:

- endpoint request parsing
- preview/apply response status mapping
- backup/write execution until write helper extraction
- local logs and activity append timing

Acceptance checks:

- focused tests cover promotion where canonical tag already exists, promotion that creates a canonical tag, demotion target validation, demotion assignment rewrites, alias-reference rewrites, and preview no-write behavior
- multi-artifact response keys stay stable

Benefits:

- isolates the riskiest cross-artifact tag operations for direct testing
- makes apply versus preview behavior clearer before write helper extraction

Risks:

- promotion/demotion rewrites touch multiple source files; later write execution must preserve current atomicity and rollback behavior

### Slice 7: backup and write helpers

Proposed module owner:

- `scripts/tag_write_transactions.py`

Target ownership:

- timestamped backup names
- single-file JSON writes with backup
- multi-file JSON writes with backup and rollback
- write result payloads if a common shape is useful

The server should keep:

- write allowlist checks
- deciding which files are written
- dry-run suppression
- local logging and activity append timing

Acceptance checks:

- tests cover backup creation, no-existing-file writes, multi-file rollback, and backup restore after simulated write failure
- existing endpoint tests still pass

Benefits:

- removes low-level file transaction mechanics from endpoint handlers
- creates a clearer shared-service comparison point with catalogue transactions

Risks:

- write allowlists must remain visible and at least as strict as before
- multi-file rollback failures must remain surfaced clearly

### Slice 8: final handler body cleanup and closeout

Target ownership:

- remove stale imports and dead helpers
- verify server call sites use explicit module namespaces
- refresh [Tag Write Server](/docs/?scope=studio&doc=scripts-tag-write-server) and this slice plan with the final boundary
- decide whether `tag_write_server.py` should remain tag-specific or become `analytics_server.py`
- decide whether remaining candidates should be marked `leave` or linked to a separate request

Acceptance checks:

- no duplicate endpoint constants outside the route owner
- no broad compatibility aliases or re-export layers for extracted helpers
- direct tests exist for each extracted owner
- `./scripts/run_checks.py --profile quick` passes, or a narrower documented tag profile exists and passes
- rebuild Studio docs/search payloads when docs changed

Benefits:

- leaves `scripts/studio/tag_write_server.py` as HTTP orchestration rather than a mixed domain module
- creates a stable handoff point before reviewing generator or catalogue build scripts

Risks:

- closeout should not become a catch-all refactor; defer unclear work instead of folding it into the final cleanup

## Initial Acceptance Criteria

- endpoint URLs, request payloads, response payloads, backup behavior, dry-run behavior, and write allowlists remain stable unless a separate request approves a contract change
- route constants are not duplicated
- extracted behavior is tested through the owning module
- server tests remain focused on HTTP orchestration and endpoint status mapping
- script docs are updated in the same change set when module ownership or command behavior changes

## Open Questions

- Tag UI route migration is complete; future slices should use the canonical `/studio/analytics/...` routes.
- Should `tag_write_server.py` be renamed to `analytics_server.py` if Analytics registries and scoring workflows start sharing the same local service?
- Should backup/write helpers become tag-specific first, then be compared with catalogue/docs transaction helpers for a possible shared local-service utility?
- Is there enough overlap between registry mutation, alias mutation, promotion, and demotion to justify one mutation module, or are separate owners clearer?
- Should `scripts/run_checks.py` gain a dedicated `tags` profile before implementation slices start?

## Recommended First Slice

Start with a read-only review of `scripts/studio/tag_write_server.py` and produce a concrete extraction map.
The first implementation slice should probably move only the route inventory and handler dispatch because that creates a stable endpoint constant owner for later activity and mutation slices.
