---
doc_id: site-request-docs-import-reviewed-package-preparation-refactor
title: Docs Import Reviewed Package Preparation And Refactor
added_date: 2026-07-12
last_updated: 2026-07-12
ui_status: done
summary: Resolve collection-import semantics and establish the focused frontend, service, plan/apply, and authority boundaries required by reviewed-package import.
parent_id: site-request-docs-import-reviewed-package
viewable: true
---
# Docs Import Reviewed Package Preparation And Refactor

## Status

Completed 2026-07-12. P0-P7 and all downstream implementation phases in [Docs Import Reviewed Package Implementation](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-implementation) are complete, including the read-only Docs Review boundary.

The parent [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package) remains the authority for product behavior, artifact roles, security, acceptance criteria, and non-goals. This request owns the unresolved batch decisions and the smallest enabling refactors needed before collection-import implementation.

## Why This Request Exists

The completed Phase 7 management work was driven primarily by the need to add Docs Review without leaking management authority into the review app. It produced explicit management domains, focused import/modal/lifecycle owners, and a narrow management event router.

Reviewed-package import creates a different pressure:

- one immutable staged JSONL file contains many related document records
- create/overwrite/skip decisions, hierarchy, and media must be resolved as one collection plan covering every package record
- all document collision choices must be resolved before any configured-source write
- one batch may require several source/media writes followed by coordinated Docs payload and search rebuilds
- cancellation and failure semantics apply to the complete operation rather than one staged file at a time

The existing `docs-html-import-workflow.js` can process several independent staged files sequentially. That is not the required one-file-to-many-document collection transaction and must not become the collection orchestrator.

## Relationship To Existing Requests

- [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package) owns product decisions and final acceptance criteria.
- This request owns prerequisite batch decisions, owner contracts, and targeted refactor evidence.
- [Docs Import Reviewed Package Implementation](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-implementation) owns end-to-end feature execution after the applicable preparation gates are resolved.
- [Docs Viewer Architecture Assessment And Refactor Roadmap](/docs/?scope=studio&doc=site-request-docs-viewer-architecture-refactor-roadmap) Phase 7 is complete for concrete management-coordinator work. This request must consume those boundaries rather than reopen general management refactoring.

## Decision

Create a focused collection-import family inside managed Docs Import.

Do not add collection state or record-level command behavior to `docs-viewer-management.js`, `docs-viewer-management-actions.js`, `docs-viewer-management-import-controller.js`, Docs Review, or Data Sharing.

The intended composition is:

```text
safe reviewed-package handoff or staged-file selection
  -> managed Docs Import collection controller
  -> wrapper-specific adapter
  -> normalized ImportContent records
  -> collection plan
  -> explicit collision decisions
  -> final validated batch plan
  -> confirmed batch apply
  -> coordinated rebuild and result
```

## Target Ownership

### Management Shell

`docs-viewer-management-import-controller.js` remains limited to lazy Docs Import initialization and modal handoff. The management event router may dispatch a named import handoff, but it must not receive package records, collision state, plans, or write behavior.

### Existing Single-Source Import

Retain the existing single-source workflow for HTML, Markdown, text, SVG, media, files, interactive HTML, and Markdown packages.

Ordinary staged sources should continue through the same user-visible create/overwrite behavior after shared lower-level helpers are extracted.

### Collection Import Frontend

Add a focused collection controller/workflow under `docs-viewer/runtime/js/import/`. Exact filenames can follow implementation conventions, but the owner must hold the complete operation state:

- safe staged package identity
- target scope
- normalized records
- collision and create/overwrite/skip decisions
- parent and media plan summaries
- blockers and warnings
- preview, decision, confirmation, applying, and result state, with cancellation available only before apply

This is the command family whose independent state and lifecycle justify extraction. It is not a reason to split unrelated management action commands.

### Collection Import Service

Add a focused collection orchestrator, such as `docs_import_data_sharing_documents.py`, that:

- validates the immutable staged package identity and schema
- obtains normalized records from the Data Sharing documents adapter
- plans the complete package before writing
- coordinates shared per-document plan/apply helpers
- reports precise record and batch results
- invokes a batch rebuild boundary rather than the single-document HTTP/service entrypoint once per record

### Shared Per-Document Plan And Apply

Extract the smallest reusable per-document boundary from `docs_import_source_service.py`:

- collision and action validation
- create/overwrite source formatting
- allowed front-matter mapping and preservation
- media planning and materialization
- target-path writes
- activity and result shaping

The existing single-source orchestrator must use the extracted boundary too. Do not keep parallel single and collection implementations of ordinary document formatting, media handling, writes, or rebuild follow-through.

The shared plan/apply boundary must also distinguish content replacement from a metadata/hierarchy-only update. For an existing record whose returned content is omitted, apply reads the current configured canonical source and changes only the explicitly supplied allowed front-matter fields, such as `parent_id`. It preserves the current body and unrelated front matter and never writes the exported or preview body back. For a new structural record whose content is omitted, create uses a standard empty body.

### Generated Rebuilds

Plan all affected source targets before apply. Rebuild Docs payloads and search through the existing write/rebuild owner after the chosen batch mutation boundary completes.

Do not rebuild once per record.

## Authority And Data Boundaries

- The immutable staged JSONL is the authority for returned fields and content intent. For preserve-existing rows, the current configured canonical source remains authoritative for every field and body region not explicitly changed by the returned record.
- Persistent Docs Review Markdown is a derived read-only projection and is never import input.
- Docs Review may pass only a safe package/staged-file identity to managed Docs Import.
- Managed Docs Import owns target-scope selection, planning, confirmation, configured-source/media writes, and rebuilds.
- Data Sharing owns package provenance and staging contracts but has no general configured-source mutation authority.
- Browser requests must never supply arbitrary filesystem paths.
- Target-scope changes must be revalidated at apply even though the staged package itself is immutable.

## Resolved Batch Semantics

P0 was completed on 2026-07-12. The former O1-O12 questions were resolved through review and their approved product contracts were copied into [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package), which remains the authority. This preparation request has no remaining open batch-semantics issue.

The resolved direction is deliberately simple:

- import every package record; subset selection is deferred
- reuse existing parents or create explicitly supplied new parent documents
- preserve body links and non-blocking asset problems for the user to repair after import
- block unsafe package/identity and invalid hierarchy states; require explicit skip/cancel for record-level source errors
- use per-document atomic writes without batch rollback, in package order
- reuse the existing per-record media behavior and one managed targeted rebuild
- resolve collisions sequentially with `Overwrite`, `Skip`, `Cancel`, and `Apply to all`
- keep apply synchronous, cancellable only before writes, with no speculative progress/limit system
- reuse the existing import listing and POST routes and recompute target state at apply
- require reconfirmation only when collision, target identity, parent resolution, hierarchy validity, or blocker facts change
- write a grouped Markdown result through the small shared JSON-to-Markdown helper

Implementation details and verification remain in the work packages below and in [Docs Import Reviewed Package Implementation](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-implementation).

## Preparation Work Packages

### P0. Resolve Batch Semantics — Complete 2026-07-12

- O1-O12 resolved
- approved product decisions copied into the parent request
- implementation checklist updated with the resulting contracts

### P1. External Staging Root Contract — Complete 2026-07-12

- existing Docs Import formats use `configured_workspace_paths(repo_root).import_staging`
- listing, source resolution, Markdown packages, interactive companions, inline media, and package media receive the explicit W0-resolved root
- API and activity-facing external paths use `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/...` marker paths
- missing, invalid, unreadable, or unwritable staging disables Docs Import capability without disabling ordinary Docs management
- direct-child, traversal, suffix, symlink, and containment checks remain enforced
- production code no longer reads, writes, or configures repo-local Docs Import staging
- retired `/docs/import-html-files` and `/docs/import-html` compatibility aliases were removed; the supported `/docs/import-source-files` and `/docs/import-source` routes remain

#### P1 Verification And Handoff

Changed implementation owners:

- `data-sharing/services/paths.py` adds required configured-path validation to the existing workspace status contract
- `docs_management_import_service.py` resolves and supplies the W0 roots
- `docs_import_source_service.py` reports clean availability and passes explicit roots through the workflow
- preview, media, Markdown-package, and interactive-asset services use marker-rooted paths and no repo-local fallback
- current import fixtures write into an isolated temporary `DOTLINEFORM_PROJECTS_BASE_DIR`

Verification completed on 2026-07-12:

- `python -m pytest docs-viewer/tests/python/test_docs_import*.py -q` — 54 passed
- the expanded focused source-listing, format, media/package, interactive HTML, capability, route, activity, service-config, and shared Data Sharing workspace set — 95 passed
- `git diff --check` passed
- focused production scans found no `STAGING_REL_DIR` or `var/docs/import-staging` reference in Docs Import services, runtime, or service config

No known P1 blocker remains. P2 should define the generic normalized content record and content-based adapter entrypoints without reintroducing path resolution into format adapters.

### P2. Normalized Content And Adapter Boundary — Complete 2026-07-12

- `docs_import_content.py` owns the wrapper-neutral `ImportContent` record and validates `replace`, `preserve-existing`, and `empty-new` intent
- the generic record carries stable source/record identities, optional content, explicit body format, allowed front matter, hierarchy, links, assets, diagnostics, and optional provenance
- `docs_import_preview.py` exposes content-based Markdown, HTML, and plain-text entrypoints; the existing file wrappers call those same entrypoints
- `data-sharing/adapters/documents/import_content.py` maps only the declared `document-content` and `document-full-source` contracts
- compact packages use only the explicit `content` mapping and declared package content format
- full-source packages parse `canonical_markdown` front matter once, require matching `doc_id`, prefer parsed title/hierarchy over duplicated row metadata, and pass only the body to standard content conversion
- omitted content becomes `preserve-existing` for current trusted records or `empty-new` for valid new structural records; it never becomes replacement content
- adapter provenance remains optional on the generic record, so a future standalone collection adapter can emit the same contract without fabricated Data Sharing identity
- persistent compact/full-source review materialization now consumes the same documents adapter, rehydrates current body only for the read-only preserve-existing projection, and records content intent in the trusted manifest

#### P2 Verification And Handoff

Focused coverage proves:

- generic records do not require Data Sharing provenance and reject ambiguous intent/content combinations
- file-based Markdown, HTML, and text previews match their content-based entrypoints
- compact Markdown/plain-text and full canonical-source mappings remain explicit
- arbitrary wrapper fields are diagnostics, not inferred source content
- canonical front matter identity and duplicate-field failures are blocking
- existing omitted-content rows retain their current projection body while new structural rows materialize an empty body
- compact and full-source persistent review packages use the shared adapter and retain content intent

Verification completed on 2026-07-12:

- `python -m pytest docs-viewer/tests/python/test_docs_import*.py -q` — 70 passed
- adjacent Docs Review, Docs Data Sharing, Analytics Data Sharing API, adapter, and service checks — 52 passed
- focused Python compilation and `git diff --check` passed

P3 should consume `ImportContent` records when extracting the shared per-document plan/apply boundary. It must not move Data Sharing provenance checks, content-format conversion, or collection state into the generic record or the management coordinator.

### P3. Shared Per-Document Plan And Apply — Complete 2026-07-12

- extract reusable document planning and apply helpers
- support surgical metadata/hierarchy-only updates against current canonical source without replacing existing bodies or unrelated front matter
- move the existing single-source orchestrator onto them without behavior change
- keep rebuild orchestration in the existing write/rebuild owner

#### P3 Verification And Handoff

- `docs_import_document.py` owns wrapper-neutral per-document create/overwrite validation, allowed front-matter application, source formatting, media/source apply, changed target ids, and result/activity shaping
- plans consume `ImportContent` records and reject unsafe target ids, create/overwrite collisions, and content intents that do not match the target action
- `preserve-existing` reads the current configured canonical source, applies only allowed returned metadata, and preserves its current body plus unrelated front matter
- `empty-new` creates an empty body; `replace` continues to use the normalized preview/conversion result
- the ordinary staged-source orchestrator now maps its preview to `ImportContent`, calls the shared plan/apply helpers, and passes their changed path and ids to the existing one-document managed rebuild boundary
- package provenance checks, content conversion, collection state/order, and rebuild invocation remain outside the per-document owner

Verification completed on 2026-07-12:

- `python -m pytest docs-viewer/tests/python/test_docs_import*.py -q` — 80 passed
- focused Python compilation and `git diff --check` passed

P4 should compose these write-free per-document plans across every normalized package record, adding complete collision, hierarchy, new-parent dependency, media, blocker, and warning planning without calling `apply_import_document()`.

### P4. Collection Dry-Run Orchestrator — Complete 2026-07-12

- normalize every package record
- produce collision, hierarchy, new-parent dependency, media, blocker, and warning plans
- prove complete planning performs no configured-source or media writes

#### P4 Verification And Handoff

- `docs_import_data_sharing_documents.py` is a thin orchestration entrypoint over the wrapper-specific `docs_import_data_sharing_package.py` intake/normalization owner and wrapper-neutral `docs_import_collection_plan.py` planner
- typed `CollectionRecordState` replaces the first-pass cross-phase state dictionary; every raw row remains represented in package order while normalized rows retain internal `ImportContent` and P3 document plans and the API projection omits source bodies and generated source text
- non-colliding rows produce candidate create plans, collisions expose only `Overwrite`, `Skip`, and `Cancel`, and invalid front matter or unsupported content formats expose only explicit `Skip` or `Cancel`
- existing parents and supplied new-parent chains resolve without row reordering; missing parents, cycles, malformed schemas, unsafe/duplicate identities, and mismatched collision targets are blockers
- body links pass through the internal planned source unchanged without link diagnostics
- embedded data-URL media uses the shared preview planner; declared package assets without an authorized materialization mapping remain non-blocking warnings
- planning calls the P3 per-document planner but never calls apply, materializes media, writes configured sources, or invokes rebuilds

Verification completed on 2026-07-12:

- `python -m pytest docs-viewer/tests/python/test_docs_import_collection_plan.py -q` — 9 passed
- `python -m pytest docs-viewer/tests/python/test_docs_import*.py -q` — 89 passed
- focused Python compilation, write-surface scans, sanitization scans, and `git diff --check` passed

P5 should register supported collection files ahead of the generic JSON/JSONL file fallback, connect `preview_only: true` to this planner through the existing import POST, and add a focused collection controller/view state without moving package records or decisions into the management coordinator.

### P5. Collection Frontend Boundary — Complete 2026-07-12

- establish a focused collection controller and view state
- keep the existing single-source workflow separate
- connect only safe package identity and named management service commands through the existing import host
- reuse the existing import-source listing/POST routes rather than adding a collection route family

#### P5 Verification And Handoff

- supported trusted `document-content` and `document-full-source` JSON/JSONL files are registered as `data_sharing_documents` before the generic file-media fallback; unsupported JSON/JSONL behavior is unchanged
- the existing `/docs/import-source` POST dispatches registered collections to the P4 planner only for `preview_only: true` or service dry-run; apply without an approved batch plan remains rejected pending P6
- `docs-import-collection-controller.js` owns safe staged identity, target scope, preview request state, body-free collection plan state, sequential record decisions, apply-to-all state, cancellation, and confirmation readiness
- `docs-import-collection-view.js` owns the body-free counts, blockers, warnings, record summaries, current decision, and read-only final-plan rendering
- collisions expose `Overwrite`, `Skip`, `Cancel`, and an unchecked `Apply to all` checkbox; invalid-record decisions expose only `Skip` and `Cancel`
- `docs-html-import.js` performs only source-family selection/dispatch and route-state projection; the ordinary sequential single-source workflow remains separate and excludes collection packages from its all-files run
- the management import controller remains unchanged and receives no package records, plan state, or record decisions
- the immediate responsibility review retained the controller/view split: the controller is the complete operation-state owner, the view is the focused renderer, and neither responsibility needs another split before P6

Verification completed on 2026-07-12:

- `python -m pytest docs-viewer/tests/python/test_docs_import*.py -q` — 91 passed
- focused adjacent static-route, public-runtime-boundary, review-session, and management-route checks — 32 passed
- `docs_import_collection_modules.py` passed the safe POST, body-free render, sequential-decision, unchecked/apply-to-all, and pre-apply cancellation module smoke
- `docs_viewer_service_manage.py` passed the existing lazy import-modal manage-shell smoke
- focused Python compilation, sanitization scan, and `git diff --check` passed

P6 should accept only the controller's explicit record decisions plus the safe staged identity and target scope, recompute the complete plan against current target facts, reject browser-authored plan/path data, and enter apply only after an unchanged final plan is confirmed.

### P6. Approved Batch Apply Boundary — Complete 2026-07-12

- implement the O5/O6/O7 mutation and revalidation decisions
- perform coordinated writes and rebuilds
- return the O12 result contract
- write the focused O12 Markdown report under `import-staging/results/`

#### P6 Verification And Handoff

- `docs_import_collection_decisions.py` owns the exact apply request allowlist, explicit decision parsing, confirmed package identity/hash comparison, collision-target checks, skipped-parent checks, and refreshed-plan responses
- `docs_import_collection_apply.py` owns package-order mutation, asset-level best effort, first-source-failure stopping, applied/failed/not-attempted classification, one managed rebuild call, and batch activity logging
- `docs_import_collection_result.py` owns body-free grouped result JSON, safe generation projection, manual-copy instructions, report payload shaping, marker-rooted report paths, and non-blocking report failure
- apply rereads the staged package, recomputes the P4 plan, accepts no browser target paths/generated source/hierarchy/media plan, and returns a refreshed write-free plan when package, collision, decision, parent, hierarchy, or blocker facts require reconfirmation
- preserve-existing rows do not use source revision/body hashes; apply reads the current canonical source and preserves unrelated front matter and the current body
- source writes remain per-document atomic and package ordered with no rollback; the first source failure stops later rows, while earlier writes remain and still receive one targeted rebuild attempt
- generation failure stays separate from successful source mutation and is returned synchronously without import retry, jobs, polling, or result retrieval
- embedded data-URL media uses the shared planner/materializer; asset failure warns and does not block the source write or later records, and document overwrite decisions do not grant asset overwrite authority
- the focused collection controller expands apply-to-all into explicit decisions, submits the safe package identity/hash, removes cancellation once apply begins, handles refreshed plans, and renders the body-free grouped result/report path
- confirmed completed, partial, all-skipped, source-failed, and generation-failed applies write one grouped report under `import-staging/results/`; planning, rejected/refreshed plans, and pre-write cancellation do not
- `results/` is explicitly excluded from direct-child source/package discovery
- Studio Activity records the safe report path, grouped counts, applied doc ids, and optional skipped-record notes without source bodies or absolute paths

Immediate responsibility review:

- the first-pass apply module mixed request revalidation with mutation and was split into `docs_import_collection_decisions.py` and `docs_import_collection_apply.py`
- result/report shaping remains in `docs_import_collection_result.py`; moving it back into apply would recreate mixed ownership
- `docs_write_rebuild.perform_source_write_and_rebuild()` now accepts an optional mutable `written_paths` projection so a partial batch completes watcher suppression only for actual writes
- the controller, view, result owner, and shared helper are each cohesive and need no further split before the review handoff

Verification completed on 2026-07-12:

- `python -m pytest docs-viewer/tests/python/test_docs_import*.py -q` — 102 passed
- adjacent write/rebuild, activity, route, public-boundary, static-asset, activity-contract, and shared-helper checks — 51 passed
- `docs_import_collection_modules.py` passed planning, sequential decisions, unchecked/apply-to-all, final confirmation, exact apply-request agreement, result rendering, and pre-apply cancellation
- `docs_viewer_service_manage.py` passed the existing lazy management-modal smoke
- focused Python compilation, activity-contract JSON validation, sanitization scan, and `git diff --check` passed

The review-to-import handoff, persistent preview publication/read boundary, and removal of Docs Review source editing are complete. Docs Review passes only a safe package identity; managed Docs Import matches it to the immutable manifest association projected onto a server-listed staged record. Validated review publication retains package-local generated output, ordinary reads continue after the staged return is removed, and no review source mutation surface remains.

### P7. Shared JSON-To-Markdown Report Helper — Complete 2026-07-12

- add `studio/shared/python/json_markdown_report.py` with the narrow render/write API defined by O12
- add deterministic escaping, ordering, nested mapping/list, and atomic-write tests under `studio/tests/python/`
- keep path selection, marker projection, app grouping semantics, and activity behavior caller-owned
- make the reviewed-package result report the first consumer without introducing a reporting framework

`studio/shared/python/json_markdown_report.py` now provides only the approved render/write entrypoints. Focused tests cover JSON compatibility, supplied/default ordering, nested mappings/lists, Markdown escaping, deterministic output, validation failures, and atomic replacement. Output roots, marker paths, group semantics, activity, templates, plugins, and registry behavior remain caller-owned.

## Non-Goals

- reopening Phase 7 management-coordinator refactoring
- splitting unrelated management action families
- a plugin or generic handler framework
- a general application store or event bus
- invoking the single-document HTTP endpoint once per collection record
- importing persistent preview Markdown
- giving Docs Review or Data Sharing configured-source mutation authority
- implementing the future standalone collection schema
- broad scope-manifest, HTTP-dispatch, config, CSS, or test-suite cleanup
- automatic remote media upload

## Verification Strategy

- pure adapter and normalized-record tests
- pure collection-plan tests covering complete-package inclusion, collisions, hierarchy, and media
- focused adapter tests proving body links pass through unchanged without resolution diagnostics
- focused asset tests proving unsupported or failed materialization preserves source references, warns, and continues without unsafe copies
- single-source regression tests against the extracted per-document helpers
- direct service tests proving plan requests do not write
- direct service tests for the approved no-rollback partial-failure, revalidation, and result contract
- focused browser coverage only for route/module wiring and plan/apply request agreement
- public import-boundary tests proving collection/import modules remain management-only
- focused sanitization scans for external paths, logs, and result payloads

Do not make modal timing, focus choreography, table layout, or button copy part of permanent workflow tests.

## Completion Criteria

This preparation request is complete when:

- O1-O12 are resolved and the parent request carries the approved product decisions
- named frontend, adapter, service, plan, apply, rebuild, and result owners are documented
- the focused grouped Markdown result-report owner and safe `import-staging/results/` path are documented
- the small cross-app JSON-to-Markdown helper is implemented and verified without app-specific dependencies
- the existing single-source importer uses the shared per-document plan/apply boundary without behavior change
- a collection dry run can produce the complete-package plan with no writes
- the batch mutation, target-drift, rebuild, and partial-failure contracts are approved and testable
- no collection state or write authority has moved into the management coordinator, Docs Review, or Data Sharing
- the implementation tracker is updated to consume the approved preparation outcomes

## Related References

- [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package)
- [Docs Import Reviewed Package Implementation](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package-implementation)
- [Library Import Generated Parent Nodes Request](/docs/?scope=studio&doc=site-request-library-import-generated-parent-nodes)
- [Docs Viewer Architecture Assessment And Refactor Roadmap](/docs/?scope=studio&doc=site-request-docs-viewer-architecture-refactor-roadmap)
- [Docs Import Source Registry](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec)
- [Create And Import Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-create-import)
- [Data Sharing Full Document Package](/docs/?scope=studio&doc=site-request-data-sharing-full-document-package)
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review)
