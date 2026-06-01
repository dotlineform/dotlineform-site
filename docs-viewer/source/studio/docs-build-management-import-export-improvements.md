---
doc_id: docs-build-management-import-export-improvements
title: Docs Build Management Import Export Improvements
added_date: 2026-05-19
last_updated: 2026-05-25
ui_status: done
parent_id: studio-python-ruby-script-inventory
viewable: true
---
# Docs Build Management Import Export Improvements

This child doc defines the implementation plan for reducing risk in the Docs build, management, import, and export script path identified by [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory).

The goal is to make docs writes and rebuilds easier to maintain and faster to reason about without reopening broad server or builder refactors.
The preferred shape is two implementation slices plus one closeout slice.

## Current Risk

The Docs path used to cross language and ownership boundaries:

- Python owns `docs-viewer/build/build_docs.py`, `docs-viewer/services/docs_viewer_service.py`, `docs-viewer/services/docs_management_service.py`, source mutation planners, generated reads, import/export adapters, live rebuild orchestration, and docs-management response shaping.
- The live watcher and docs-management service both coordinate docs payload rebuilds and docs search updates.
- Semantic references add derived per-doc and per-target relationship artifacts, which makes affected-doc rebuild optimization useful but dependency-sensitive.

The current system is functional and incrementally writes unchanged payloads, but the rebuild input is still usually scope-level.
That means a small source edit can still require parsing a whole docs scope before unchanged outputs are skipped.

## Goals

- expose enough rebuild diagnostics to know which docs path is slow before optimizing
- define a durable affected-doc build contract for `build_docs.py`
- make targeted docs payload rebuilds safe around semantic references, deleted docs, metadata changes, and resolver-data changes
- keep Docs management service logic as orchestration, not as the owner of builder, import, export, or mutation rules
- keep import/export adapter behavior explicit and documented
- refresh the script inventory back to as-is after the implementation is complete

## Non-Goals

- do not replace the Ruby docs builder with Python
- do not redesign the Docs Viewer generated JSON schema unless a slice explicitly needs a versioned field
- do not move Data Sharing ownership out of the existing adapter pattern
- do not make public routes depend on local management services
- do not optimize by skipping correctness checks for parent/title/search/reference dependencies
- do not introduce a database or long-running docs graph service

## Slice 1: Diagnostics And Contract Map

Status: completed in the diagnostics slice.

Purpose:

- make the current rebuild/import/export path measurable
- record the exact response and command contracts before changing rebuild scope

Implementation scope:

- add builder diagnostics for scope, source files scanned, docs emitted, doc payloads changed, doc payloads removed, reference by-doc payloads changed/removed, reference by-target payloads changed/removed, warnings, and elapsed time
- expose docs-management rebuild/search diagnostics in management responses where they are already returned to Studio
- expose live-watcher fallback reasons and affected ids in its log output without adding noisy source paths
- map docs-management write actions to their current docs rebuild and docs search behavior
- map import/export apply actions to the source docs, generated payloads, search updates, backup behavior, and activity rows they can affect

Acceptance checks:

- `./docs-viewer/build/build_docs.py --scope studio` dry run still works without writing
- `./docs-viewer/build/build_docs.py --scope studio --write` reports the new diagnostics without changing generated payload schemas beyond intentional metadata or console output
- focused tests cover diagnostic payload shaping where the behavior is structured
- docs-management service responses keep existing keys stable
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder), [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server), [Docs Import](/docs/?scope=studio&doc=scripts-docs-import), and [Docs Export](/docs/?scope=studio&doc=scripts-docs-export) are updated if command output or response contracts change

Implementation note:

- `docs-viewer/build/build_docs.py` now emits one compact diagnostics JSON line per selected scope without changing generated Docs Viewer payload schemas.
- `docs-viewer/services/docs_write_rebuild.py` now parses docs-builder diagnostics, adds elapsed timing to rebuild steps, and returns additive `diagnostics.docs` and `diagnostics.search` objects.
- `docs-viewer/services/docs_live_rebuild_watcher.py` now logs affected doc ids for targeted search and fallback reasons when affected ids are unavailable.
- The owning builder, management, watcher, import, export, and site change-log docs were updated with the new command, response, and log contracts.

Risks:

- diagnostics can become noisy enough to hide real failures
- elapsed-time fields can make tests flaky if they are asserted too tightly
- response payload changes can break Studio UI assumptions if existing keys move

## Slice 2: Affected-Doc Build Input

Status: completed in the affected-doc build slice.

Purpose:

- implement a safe affected-doc rebuild path for `docs-viewer/build/build_docs.py`
- use it from docs-management and watcher paths only when dependency rules prove it is safe

Implementation scope:

- add a dry-run-first `--only-doc-ids` option to `./docs-viewer/build/build_docs.py --scope <scope>`
- keep full-scope rebuild as the fallback when dependency rules are incomplete or unsafe
- define affected-doc dependency rules for:
  - edited source body
  - changed `doc_id`
  - deleted source doc
  - changed title used by child rows, search rows, and semantic-reference reports
  - changed parent/order/viewability metadata
  - semantic-reference target moves between target buckets
  - resolver data changes outside docs source, such as catalogue title or route changes
- update semantic-reference output so affected-doc writes can update all changed by-doc and by-target payloads without leaving stale target buckets
- update `docs-viewer/services/docs_write_rebuild.py` to select targeted or full rebuilds and report why
- update `docs-viewer/services/docs_live_rebuild_watcher.py` to pass affected doc ids only when safe
- update docs-management write flows to pass affected doc ids for create, import overwrite, metadata, viewability, move, delete, and settings writes only where the dependency map allows it

Acceptance checks:

- full-scope rebuild remains the default and safe fallback
- targeted rebuild correctly handles a single body edit with unchanged metadata
- targeted rebuild correctly updates semantic-reference by-doc and by-target payloads when a doc changes references
- deleted or renamed docs remove stale generated payloads and stale semantic-reference buckets
- metadata changes that affect other rows either update the dependent docs or fall back to full-scope rebuild
- docs search updates still reconcile missing and non-viewable docs with `--remove-missing`
- focused tests cover `--only-doc-ids` planning and fallback reasons
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs` passes when the implementation is complete

Risks:

- stale generated references are the main correctness risk
- parent/title metadata can affect rows outside the edited doc
- resolver-data changes can make targeted docs rebuilds unsafe unless they trigger full-scope fallback
- watcher suppression must not hide a needed full rebuild after a management write

Implementation note:

- `docs-viewer/build/build_docs.py` now accepts `--only-doc-ids` for a single selected scope and reports `build_mode` plus `only_doc_ids` in builder diagnostics.
- Targeted docs payload rebuilds still build the scope index from current source metadata, render selected per-doc payloads only, and derive semantic-reference by-target artifacts from refreshed selected by-doc records plus existing unselected by-doc records.
- `docs-viewer/services/docs_write_rebuild.py` now returns a `rebuild.docs` object with mode, ids, and reason, and passes targeted docs ids separately from targeted search ids.
- Targeted orchestration falls back to a full docs payload rebuild when existing generated output is missing or incomplete.
- Docs-management mutation planners, source imports, Library returned-package apply flows, and the live watcher now pass docs payload ids only when they have an explicit affected-id set; source-config settings and explicit rebuilds stay full-scope.
- Focused tests cover targeted command shaping, and a temp-output smoke check covered semantic-reference by-doc and by-target stale removal under targeted rebuild.

## Slice 3: Import Export Management Closeout

Status: completed in the closeout slice.

Purpose:

- make the import/export/management path consistent after targeted build work lands
- move durable technical details out of this planning doc and refresh the inventory to reflect the new as-is state

Implementation scope:

- align import/export apply responses with the same rebuild/search diagnostic shape used by management writes
- keep source write and backup behavior adapter-owned:
  - `docs-viewer/services/docs_import.py`
  - `docs-viewer/services/docs_export.py`
  - `docs-viewer/services/docs_import_source_service.py`
  - `data-sharing/data_sharing/adapters/documents/adapter.py`
  - `docs-viewer/services/docs_data_sharing/`
  - `analytics-app/app/server/analytics_app/data_sharing_service.py`
- ensure Docs management service remains a transport/orchestration layer for Data Sharing and Docs Viewer management endpoints
- update existing technical docs with final behavior:
  - [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
  - [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
  - [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
  - [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
  - [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
  - [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references), if affected-doc behavior closes or changes its next-step note
- refresh [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory) so it reads as an as-is risk inventory, not an implementation tracker
- create a separate technical reference only if the affected-doc dependency rules are too detailed for the existing builder and management docs

Acceptance checks:

- the inventory reflects the implemented state and remaining risk classifications
- this implementation doc records completed slices and remaining deferred work only
- no generated docs/search payload update is treated as final unless the relevant docs payload/search rebuild has run intentionally
- command examples remain project-local and machine-agnostic
- final verification names the exact run-check profile or focused tests used

Implementation note:

- Library returned-package summary and hierarchy apply responses now use the same `rebuild` object shape as docs-management writes: `rebuild.steps`, `rebuild.docs`, `rebuild.search`, and `rebuild.diagnostics`.
- Documents package preparation remains source-read-only and does not run docs payload or docs-search rebuilds.
- The durable builder, management-server, watcher, import, export, semantic-reference, and script-inventory docs now carry the as-is behavior instead of this implementation record owning the technical contract.
- The focused import-service tests assert the returned-package apply rebuild shape for both summary and hierarchy writes.

Risks:

- closeout can leave duplicated details across request, script, and inventory docs
- inventory can become stale if it is updated before implementation behavior is verified
- import/export docs can drift from the Data Sharing adapter contracts if only management docs are updated

## Final State

This plan is complete.

- `docs-viewer/build/build_docs.py` has an explicit affected-doc input contract through `--only-doc-ids`
- docs-management, live-watcher, import, and export responses expose enough diagnostics to identify expensive rebuild paths
- targeted rebuilds are used only where dependency rules make them safe
- semantic-reference artifacts are preserved correctly under targeted docs rebuilds
- existing script docs own the durable technical behavior
- this doc remains a short implementation record
- [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory) is refreshed back to the current as-is risk state

Remaining deferred work:

- resolver-data changes outside docs source, such as catalogue title or route changes, still need explicit orchestration before they can safely request targeted docs payload rebuilds
- broader benchmarking is still deferred until diagnostics show a repeated slow path

## Related References

- [Studio Python And Ruby Script Inventory](/docs/?scope=studio&doc=studio-python-ruby-script-inventory)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher)
- [Docs Import](/docs/?scope=studio&doc=scripts-docs-import)
- [Docs Export](/docs/?scope=studio&doc=scripts-docs-export)
- [Docs Semantic References Request](/docs/?scope=studio&doc=site-request-docs-semantic-references)
