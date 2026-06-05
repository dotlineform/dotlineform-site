---
doc_id: site-request-data-sharing-docs-internal-index
title: Data Sharing Docs Source Metadata Request
added_date: 2026-06-03
last_updated: 2026-06-05
ui_status: in-progress
parent_id: change-requests
viewable: true
---
# Data Sharing Docs Source Metadata Request

Status:

- in porgress

## Summary

Create an internal/local source-derived docs metadata read model for Data Sharing document workflows so they do not rely on public Docs Viewer artifacts or generated publication artifacts.

Data Sharing needs access to richer document metadata than a public read-only tree index should carry.
That data must come from Docs Viewer source parsing and rendering code for every configured Docs Viewer scope, not from `assets/data/docs/scopes/<scope>/index.json`, `docs-viewer/generated/docs/<scope>/index.json`, by-id rendered payloads, search payloads, recently-added payloads, or other generated publication artifacts.
Public docs `index.json` has now been retired from the public Docs Viewer route contract rather than slimmed into a Data Sharing dependency.

## Terminology

In this request, `generated` means data artifacts produced for a Docs Viewer publication, preview, management, report, route, search, or other site-surface workflow.
That definition applies regardless of whether the artifact is public, private, manage-only, local-only, or checked in.
Generated data follows publication/surface rules about what data is exposed, how it is shaped, and when it is written.

Data Sharing is not a generated-data workflow.
It is a first-class canonical-data service.
It shares canonical-equivalent data with external services and can use returned data to update canonical docs source.
Its source of truth is the canonical docs source model: scope config plus docs source front matter and body content processed through shared Docs Viewer parsing/rendering code.
Data Sharing must not be affected by changes to what Docs Viewer generated data publishes, omits, slims, nests, renames, or routes.

## Current Position

[Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming) is done.
The current route payload contract is:

- public `/library/` and `/analysis/` routes do not publish or load public flat `assets/data/docs/scopes/<scope>/index.json`
- public and manage navigation use nested `index-tree.json`
- selected-document rendering and info-panel metadata come from by-id payloads
- search and recently-added remain separate payloads
- manage/local rich flat indexes under `docs-viewer/generated/docs/<scope>/index.json` remain valid for existing manage/report consumers where the configured scope output is local/manage, but Data Sharing does not use them as its metadata source

That means this request no longer unblocks public flat-index retirement.
Its job is now to restore and harden Data Sharing document metadata workflows after public flat-index retirement, without reintroducing public flat indexes or replacing them with another generated-publication dependency.

Current implementation state:

- `docs-viewer/services/docs_data_sharing/package.py` uses `docs_generated_reads.read_generated_docs_index(...)`; for public scopes this still resolves to the retired configured public `index.json`, so selectable document records need a new internal metadata read contract.
- `docs-viewer/services/docs_export.py` hard-codes `assets/data/docs/scopes/<scope>/index.json` for package/export preparation.
- `docs-viewer/services/docs_import.py` hard-codes `assets/data/docs/scopes/<scope>/index.json` for returned-package review context.
- Existing tests and adapter fixtures still create or assert public docs `index.json` paths for Data Sharing/export/import behavior.

## Goals

- define a config-driven local/internal docs source metadata read model for Data Sharing document workflows
- move Data Sharing selectable-record, package-preparation, export, and returned-package review reads away from public data, generated indexes, and generated publication payloads
- keep current Data Sharing behavior, UI options, package workflows, and selectable-record fields, including `published`
- keep the read model shaped for the Data Sharing workflows that need it now
- avoid broadening the read model name or field shape for hypothetical future consumers
- read source metadata through shared scope-config-driven code, without scope-specific modules or repeated per-scope implementation blocks

## Current Problem

Data Sharing previously benefited from metadata that happened to be present in public docs scope indexes.
That is the wrong dependency direction.

Public `assets/data/docs/scopes/<scope>/index.json` files have been removed from the Docs Viewer runtime contract.
Public navigation uses nested `index-tree.json`, selected-document reader metadata comes from by-id payloads, search uses the existing search payload, and recently-added uses a small build-time payload.
None of those public runtime payloads should become Data Sharing's rich metadata source.
Manage/local generated docs indexes and by-id payloads are also generated artifacts for Docs Viewer publication, preview, management, or reporting surfaces.
Data Sharing must not rely on those generated artifacts as its metadata source.

Data Sharing is a first-class local workflow and needs a richer, stable metadata source that is not constrained by public payload size or public-safe field exposure.
The Data Sharing source of truth must be directly equivalent to canonical docs source data: scope config plus docs source front matter and body content processed through shared Docs Viewer parsing/rendering code.

Current functionality that must be moved includes:

- selectable document records,
- package/export preparation,
- returned-package review context that checks current docs, parent relationships, viewability, source existence/renderability, current summaries, rendered content, and content text length.

## Direction

Add a source-derived internal docs metadata read model for every configured Docs Viewer scope.
Current scopes are determined from the existing docs scope config.
New scopes are covered automatically through the shared scope-config-driven read path.

There is no replacement generated index path.
Do not add `metadata-index.json`, `tooling-index.json`, or another generated metadata JSON as the Data Sharing source.

The read model is Docs Viewer-owned because Docs Viewer owns source parsing, doc-link/media rendering behavior, content text extraction, parent relationships, public/manage scope config, and by-id payload emission.
Data Sharing consumes this read model through service helpers; Data Sharing does not know or reconstruct filesystem paths.
Implementation must not create scope-specific modules, route-specific metadata builders, repeated `library`/`analysis` code blocks, or generated-publication-artifact fallbacks.

The read model is designed for the Data Sharing workflows in this request.
Do not broaden the shape or name in anticipation of possible future consumers.
When another workflow later needs similar data, decide then to reuse, extend, or create a separate projection based on that concrete requirement.
Do not name any replacement `index.json`; that name is being removed as a generic docs-index dependency to make accidental fallback to retired public indexes easier to catch.

## Required Record Fields

The source-derived read model exposes the fields Data Sharing currently uses for selection, export, rendered-content extraction, and returned-package review:

- `doc_id`
- `scope`
- `title`
- `published`
- `summary`
- `added_date`
- `last_updated`
- `parent_id`
- `parent_title`
- `viewable`
- `ui_status`
- `source_path`
- viewer URL, only where current exported fields require it
- source-derived rendered HTML or a helper that renders source HTML on demand for source-text extraction
- `content_text_length`

`published` remains part of selectable-record behavior.
This request does not change current Data Sharing UI options, selection behavior, package formats, or workflows.

The read model includes a compact `generated_from` or `source_scope` provenance field only when a focused test proves Data Sharing uses it for stale/missing diagnostics.
The read model must not include fields merely because another report or future tool might find them convenient.

## Current Dependencies To Replace

The implementation audit starts with these known Data Sharing document paths:

- `docs-viewer/services/docs_data_sharing/package.py` builds selectable records from `docs_generated_reads.read_generated_docs_index(...)` and exposes `summary`, `parent_id`, `viewable`, `published`, and `content_text_length`; this is not enough for public scopes now that configured public `index.json` is retired.
- `docs-viewer/services/docs_export.py` loads `assets/data/docs/scopes/<scope>/index.json` for package preparation and uses it for selected ids, hierarchy expansion, parent/child fields, summary/current-summary fields, visibility filtering, and rendered by-id payload lookup for source text extraction.
- `docs-viewer/services/docs_import.py` loads `assets/data/docs/scopes/<scope>/index.json` for returned-package review context, including current doc existence, current viewability, parent existence, generated payload existence, and current summary comparison.

These reads move to the source-derived read model, with rendered content produced from source through shared rendering helpers.
They must not switch to public `index-tree.json`, public by-id payloads as an implicit index, public search index, recently-added payload, manage/local generated `index.json`, or manage/local generated by-id payloads.

## Implementation Batches

Implementation is tracked in [Data Sharing Docs Source Metadata Tasks](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index-tasks).

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

Work is batched to reduce churn and keep the new path contract inside its owner before consumers move.

| Batch ID | status | title | actions |
| --- | --- | --- | --- |
| 1 | done | [Contract and dependency audit](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index-batch-1) | Confirm every Data Sharing/export/import field and rendered-content lookup that currently comes from docs indexes or by-id payloads. Lock the source-derived record shape, config-driven scope behavior, and missing-source behavior. |
| 2 | done | [Source metadata read API](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index-batch-2) | Add Docs Viewer service helpers that build Data Sharing metadata records directly from scope config and docs source files, including source rendering/text extraction helpers. Do not add a generated metadata output. |
| 3 | done | [Data Sharing consumer migration](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index-batch-3) | Move selectable document records, package/export preparation, source rendering, source-text extraction, and returned-package review context to the source metadata read API. Remove hard-coded public `assets/data/docs/scopes/<scope>/index.json` reads and generated by-id payload reads from Data Sharing-owned flows. |
| 4 | done | [Contract tests and stale-path guards](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index-batch-4) | Update fixtures and focused tests so Data Sharing works without public flat docs indexes or generated publication payloads, and rejects accidental reads from public flat indexes, public nested trees, search, recently-added, manage/local flat indexes, or generated by-id payloads for tooling metadata. |
| 5 | planned | [Durable docs and closeout](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index-batch-5) | Update Data Sharing, Docs Viewer source/generated-data/data-model docs, adapter config docs, and this request with the final source-read contract, verification log, generated payload status, and remaining non-goals. |

## Batch Details

### Batch 1: Contract and dependency audit

Deliverables:

- field matrix for selectable records, export configs, rendered-content extraction, returned-package review, and preview generation
- ownership record: Docs Viewer-owned source metadata read model consumed by Data Sharing through service helpers
- source-derived record shape and helper API names
- missing-source behavior for local Data Sharing calls
- scope coverage record confirming records are produced for every configured Docs Viewer scope through shared scope-config-driven code

### Batch 2: Source metadata read API

Deliverables:

- read helpers that derive records from scope config and docs source files
- source rendering/text extraction helper used by export flows instead of generated by-id payloads
- no generated-output/scope-lifecycle manifest updates, because this request does not add generated metadata artifacts
- focused read-helper tests for record fields, path resolution, duplicate handling, missing source handling, content text extraction, and config-driven scope coverage

### Batch 3: Data Sharing consumer migration

Deliverables:

- `docs_data_sharing/package.py` selectable records read the source metadata helper
- `docs_export.py` selection, hierarchy expansion, filters, field mapping, headings, source rendering, and source-text extraction read through the source metadata helper
- `docs_import.py` current-doc review context reads current source existence/renderability through the source metadata helper
- no Data Sharing path switches to public `index-tree.json`, public search, public recently-added, generated flat indexes, or generated by-id payload enumeration as an implicit index

### Batch 4: Contract tests and stale-path guards

Deliverables:

- tests for Data Sharing/export/import behavior when public `assets/data/docs/scopes/<scope>/index.json` and generated by-id payloads are absent
- tests that fail on accidental public flat-index, public tree, public search, recently-added, manage/local flat-index, or generated by-id metadata coupling
- missing-source handling tests with user-facing error/warning expectations
- updated adapter/config fixtures that no longer describe public docs flat indexes or generated docs payloads as active Data Sharing sources

### Batch 5: Durable docs and closeout

Deliverables:

- update Data Sharing docs, Docs Viewer source/generated-data/data-model docs, and [Config Data Sharing Adapters](/docs/?scope=studio&doc=config-data-sharing-adapters)
- record verification commands and generated payload status
- close this request only after executable checks prove Data Sharing works without public flat docs indexes or generated publication payloads

## Acceptance Criteria

- Data Sharing no longer depends on public docs scope index rows, manage/local generated docs index rows, generated by-id payloads, search payloads, or recently-added payloads for document metadata
- Data Sharing prepare/export/selectable-record and returned-package review-context workflows keep current behavior with public docs `index.json` and generated publication artifacts absent
- source metadata has an explicit owner, helper API, and record shape
- the source metadata read model includes the fields Data Sharing needs without bloating public runtime payloads
- public flat-index retirement remains intact and no public flat-index fallback is reintroduced
- tests cover both the source metadata read model and the absence of public/generated-artifact coupling

## Proposed Verification

Run the smallest useful checks per batch:

- Batch 1: source audit only; no generated writes.
- Batch 2: Python syntax checks for changed source/read helpers and focused read-helper pytest.
- Batch 3: Python syntax checks and focused pytest for `docs_data_sharing/package.py`, `docs_export.py`, `docs_import.py`, and management/API wrappers that call them.
- Batch 4: focused negative-path tests proving public flat indexes and generated publication payloads are absent and not read; smoke coverage changes only when browser/API route behavior changes.
- Batch 5: `git diff --check`, stale-reference scans for public `assets/data/docs/scopes/<scope>/index.json` and generated docs payload reads in active Data Sharing paths, and final generated-payload status.
