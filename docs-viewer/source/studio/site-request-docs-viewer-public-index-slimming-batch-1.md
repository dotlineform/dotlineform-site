---
doc_id: site-request-docs-viewer-public-index-slimming-batch-1
title: Docs Viewer Public Index Slimming Batch 1
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: done
parent_id: site-request-docs-viewer-public-index-slimming-tasks
---
# Batch 1: Discovery and Contract Lock

This is the delivery specification for [Batch 1 in Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 1: Discovery and Contract Lock

Summary: Audit current public flat-index generation and consumption, then define the generated-data contracts before implementation starts.

| ID | status | action |
| --- | --- | --- |
| 1.1 | done | Audit current public flat-index generation and consumption, including browser/runtime tree construction, info-panel reads, search build inputs, recently-added behavior, scope lifecycle, tests/fixtures, reports, export/import, and Data Sharing references. Classify dependencies as Docs Viewer-owned work for this request or separate tooling ownership such as [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index). |
| 1.2 | done | Define the generated-data contracts before implementation: shared public/manage `index-tree.json`, small recently-added payload, selected by-id reader metadata for the info panel, route config fields, visible missing-payload behavior, and public flat `index.json` retirement semantics. |

## Steer for these tasks

- Start by locating every current public `index.json` producer and consumer before proposing code edits.
- Separate Docs Viewer-owned dependencies from tooling consumers such as Data Sharing, reports, export/import, and generated-output inspection.
- Lock the payload names and field contracts before builder or runtime changes begin.
- If the audit finds a consumer that still needs rich document metadata, classify it as either selected by-id hydration, search/build input, manage-only data, or separate tooling ownership.

## Deliverables

- Dependency inventory for public flat-index generation and consumption.
- Confirmed contract for public and manage `index-tree.json`.
- Confirmed contract for recently-added payloads.
- Confirmed selected by-id metadata contract for info-panel hydration.
- Confirmed route config fields and missing-payload behavior.
- Confirmed retirement semantics for public flat `index.json`.

## Implementation and policy guidance

- Follow the parent request: no fallback to `index.json` after the route contract moves.
- Do not treat tests or generated fixtures as the implementation contract; update them to match the locked contract.
- Avoid compatibility aliases or dual-read paths. If a temporary transition path appears necessary, record the exception with removal criteria before implementation.
- Coordinate with [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index) for non-Docs Viewer metadata needs.

## Proposed verification set

- Source review and scoped `rg` evidence for producers and consumers.
- `git diff --check` if the audit or contract is recorded in source docs.
- No browser smoke is expected for this batch unless executable contract probes are added.

## Completed Audit

### Current producers

- `docs-viewer/build/build_docs.py` is the canonical docs payload producer. It currently emits `<docs_scope.output>/index.json`, `<docs_scope.output>/by-id/<doc_id>.json`, and references payloads.
- `build_docs.py` also writes browser config records with `index_url` pointing at the flat docs index. Public read-only configs are projected into `docs-viewer/config/defaults/docs-viewer-public-config.json`.
- `docs-viewer/config/routes/docs-viewer-routes.json` and `docs-viewer/config/routes/docs-viewer-public-routes.json` currently expose `docs_paths.index_url` for the flat index on `/docs/`, `/library/`, and `/analysis/`.
- `docs-viewer/services/docs_scope_manifest.py` and scope lifecycle preview/apply paths currently record and create generated docs `index.json` as the docs index artifact.
- `docs-viewer/build/build_search.py` currently uses `<docs_scope.output>/index.json` as its default search builder input.

### Docs Viewer-owned consumers for this request

- Runtime route loading uses `docs-viewer-generated-data-runtime.js`, `docs-viewer-data.js`, and `docs-viewer-route-workflow.js` to read the configured `index_url`, populate `allDocs`, build visible `docs`, and initialize navigation state.
- Tree and visibility behavior is owned by `docs-viewer-document-index-state.js`, `docs-viewer-tree.js`, and `docs-viewer-sidebar.js`. Current tree behavior depends on `doc_id`, `title`, `parent_id`, `viewable`, `ui_status`, `content_url`, and `viewer_options`.
- Recently-added is currently derived in `docs-viewer-search-controller.js` from loaded docs rows by sorting on `added_date` or `last_updated`. This is Docs Viewer-owned and must move to a separate small generated payload.
- Public and manage info-panel metadata currently resolves selected docs from index-backed `docsById`/`allDocsById` through `docs-viewer-info-panel-controller.js`, `docs-viewer-view-context.js`, and `docs-viewer-metadata-info-view.js`. This is Docs Viewer-owned and must hydrate from selected by-id payloads.
- Search runtime already reads a separate search payload through `search_index_url`; the runtime path should remain separate. Search builder input is Docs Viewer-owned and must stop relying on retired public flat indexes.
- Manage reports loaded from selected by-id payloads can request docs indexes through `docs-viewer-management-document-reports.js`. These are manage-only consumers. Any report that still needs richer document rows after runtime moves must read a manage/internal metadata source, not public `index-tree.json`.
- Scope lifecycle create/delete and generated-read capability checks are Docs Viewer-owned follow-through for Batch 2.
- Generated-output fixtures and smoke tests that name `index.json` or require rich index fields are test contracts to update after implementation, not implementation constraints.

### Separate tooling ownership

- Data Sharing export/import currently reads `assets/data/docs/scopes/<scope>/index.json` through `docs-viewer/services/docs_export.py` and `docs-viewer/services/docs_import.py` for rich metadata, relationship expansion, viewability, current summary comparison, and payload lookup.
- That dependency is not a reason to keep public `index.json`. It belongs to [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index), which should define an internal/local metadata projection.
- Broken-link reports, source-config reports/settings, and capabilities checks that inspect generated index state are manage/tooling consumers. They should either remain manage-local or move to a named internal generated contract if they still need richer metadata after public flat-index retirement.

## Locked Contracts

### `index-tree.json`

Each scope gets one generated tree payload beside its by-id payload root:

- public: `assets/data/docs/scopes/<scope>/index-tree.json`
- manage/local: `docs-viewer/generated/docs/<scope>/index-tree.json`

Public and manage tree payloads use the same structure:

```json
{
  "schema": "docs_index_tree_v1",
  "generated_at": "<stable generated timestamp>",
  "viewer_options": {
    "non_loadable_doc_ids": [],
    "manage_only_tree_root_ids": [],
    "show_updated_date": true
  },
  "docs": [
    {
      "doc_id": "example",
      "title": "Example",
      "content_url": "/assets/data/docs/scopes/library/by-id/example.json"
    }
  ]
}
```

Tree rows allow only:

- `doc_id`
- `title`
- `content_url`
- `parent_id`, only when non-empty
- `viewable: false`, only when needed
- `ui_status`, only when non-empty

Tree rows must not carry `summary`, `added_date`, `last_updated`, `source_path`, `viewer_url`, `content_text_length`, report metadata, source/edit metadata, management action metadata, or default/derivable values.

### Recently-added

Each scope gets a small generated recently-added payload beside `index-tree.json`:

- public: `assets/data/docs/scopes/<scope>/recently-added.json`
- manage/local: `docs-viewer/generated/docs/<scope>/recently-added.json`

Payload shape:

```json
{
  "schema": "docs_recently_added_v1",
  "generated_at": "<stable generated timestamp>",
  "limit": 10,
  "docs": [
    {
      "doc_id": "example",
      "title": "Example",
      "content_url": "/assets/data/docs/scopes/library/by-id/example.json",
      "added_date": "2026-06-05"
    }
  ]
}
```

Recently-added rows allow `doc_id`, `title`, `content_url`, `added_date`, optional `parent_id`, and optional `parent_title`.
The payload is limited at build time by the configured Docs Viewer recently-added limit.
Do not add date-only fields to `index-tree.json` for recent sorting.

### Selected by-id metadata

Selected-document rendering continues to load by-id payloads.
Info-panel metadata must come from the selected by-id payload, not from tree rows and not from flat `index.json`.

Public info-panel display fields are limited to:

- title
- summary
- last updated

Manage info surfaces may display richer metadata where allowed, but manage requirements must not force public tree rows to carry those fields.

### Route config

Route config should move from a generic flat `docs_paths.index_url` to explicit generated-data paths:

- `docs_paths.index_tree_url`
- `docs_paths.recently_added_url`
- `docs_paths.search_index_url`

`docs_paths.index_url` is retired from the Docs Viewer route contract when runtime loading moves.
There is no dual-read fallback from `index-tree.json` to `index.json`.

### Missing payload behavior

Missing required `index-tree.json` or `recently-added.json` should fail visibly in the Docs Viewer UI with the same style of generated-data load error used today.
Missing selected by-id payloads should remain selected-document load failures.
Public routes must not probe local/generated-read management services to recover missing public payloads.

### Public flat `index.json` retirement

Public `assets/data/docs/scopes/<scope>/index.json` is retired from public Docs Viewer route loading after:

- `index-tree.json` covers navigation and route resolution
- selected by-id payloads cover rendering and info-panel metadata
- search reads the separate search payload
- recently-added reads its small generated payload

Search build inputs, reports, Data Sharing, export/import, generated-read services, source-config reports/settings, fixtures, and tests must not preserve public `index.json` as a route dependency.
Rich metadata consumers need manage/internal owner contracts.

## completed verification

- Source review and scoped `rg` audit completed for producers and consumers:
  - `build_docs.py`, `build_search.py`, route configs, generated-data runtime, route workflow, tree/index state, search/recent, info-panel, reports, scope lifecycle, generated reads, export/import, broken links, source-config reports/settings, fixtures, and smoke tests.

## follow-on tasks

- Batch 2 should implement the locked payloads and route config fields above, then update tests/fixtures to assert the new public payload boundaries.
- Coordinate rich Data Sharing metadata needs through [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index), not through public tree/recent/search payloads.

## task close

- Batch 2 handoff added.
- Tracker row status set to `done`.
