---
doc_id: docs-viewer-generated-data-contracts
title: Generated Data Contracts
added_date: 2026-06-05
last_updated: 2026-07-11
summary: Public and manage generated Docs Viewer payload roots, schemas, read authority, publishing, and builder ownership contracts.
parent_id: docs-viewer-runtime-boundary
---
# Docs Viewer Generated Data Contracts

This document records generated-data ownership for [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).
It separates public read-only route data from local/manage route data so payload-size and management-safety decisions have a durable home.

## Ownership Rules

- Public routes load only public-reader data needed for navigation, selected-document rendering, search, recently-added, and reader-facing metadata.
- Manage routes may load manage generated data and local-service data, but manage needs should not force public payloads to carry management/tooling metadata.
- Public and manage payload names and shapes should be explicit route contracts, not incidental current renderer requirements.
- Generated-data runtime helpers are read owners only; backend writes and management capability truth remain in management services.
- There should be no compatibility fallback to retired public payloads once a route contract has moved.
- Data Sharing document source-context reads are not generated-data runtime reads; they use Docs Viewer-owned helpers over scope config and source Markdown.
- The current generated-data runtime is the transport/retry owner, not a collection-provider abstraction. Phase 2 adds a configured-scope provider over its named reads; provider presence does not grant backend or write authority.

## Current Payload Roots

| Scope kind | Docs root | Search root |
| --- | --- | --- |
| Public read-only working generated | `docs-viewer/generated/docs/<scope>/` | `docs-viewer/generated/search/<scope>/index.json` |
| Public read-only published snapshot | `site/assets/data/docs/scopes/<scope>/` | `site/assets/data/search/<scope>/index.json` |
| Manage/local | `docs-viewer/generated/docs/<scope>/` | `docs-viewer/generated/search/<scope>/index.json` |

Public-scope builders and docs-management rebuild follow-through write only the working generated roots.
The public route contract reads only the published snapshot roots under `site/assets/data/`.
Publishing is an explicit local management action that syncs the working docs/search payloads to the published snapshot roots after confirmation.

## Route Payload Contract

| Capability | Public route source | Manage route source | Notes |
| --- | --- | --- | --- |
| Navigation tree | `index-tree.json` | `index-tree.json` | Public and manage tree nodes share the same nested structure. |
| Selected document render | by-id payload | by-id payload | By-id payloads remain in scope for selected documents. |
| Info-panel metadata | selected by-id payload | selected by-id payload | Public reader metadata is limited to title, summary, and last updated. |
| Search | search payload | search payload | Search runtime reads separate search payloads. |
| Recently-added | small generated recently-added payload | small generated recently-added payload | Do not add date-only fields to tree rows to support recently-added. |
| Management metadata/actions | not public route data | management services and manage payloads as needed | Public tree/by-id payloads should not carry management-only metadata. |

## `index-tree.json` Contract

Public and manage `index-tree.json` use exactly the same nested data structure.
Manage tree generation may preserve manage visibility/loadability behavior, but it should not add richer row fields unless a manage interaction needs them before selected by-id is loaded.

`docs` is an array of root nodes. Child relationships are expressed with each node's optional `children` array.
Generated tree nodes do not carry `parent_id`; `docs-viewer-tree-payload-adapter.js` derives runtime-only parent ids while normalizing the nested payload for existing renderer and management state.

Public `index-tree.json` nodes should stay as close as possible to:

- `doc_id`
- `title`
- `children`, only when non-empty
- `viewable: false`, only when needed
- `ui_status`
- `content_url`

Fields excluded from public `index-tree.json`:

- `summary`
- `last_updated`
- `viewer_url`
- `content_text_length`
- default or derivable values

`viewable` or equivalent non-viewable state and `ui_status` are tree behavior fields for both public and manage scopes.
Public scopes need them for current read-only tree display; manage scopes also need them because manage can set their values.

## By-Id Payload Contract

Selected document loading stays by-id.
The public info panel reads selected-document metadata from the selected by-id payload, not public tree rows and not `index.json`.

Public reader-facing by-id metadata for the info panel is:

- title
- summary
- last updated

Public by-id payloads should not expose source path, visibility state, UI status internals, management-only fields, or editable metadata concepts for the public info panel.
Manage mode can keep a richer metadata surface, but it should hydrate selected-document metadata from selected by-id payloads rather than public tree/index rows.

## Search Contract

Search runtime reads the separate search payload through `search_index_url`, such as:

- `site/assets/data/search/<scope>/index.json`
- `docs-viewer/generated/search/<scope>/index.json`

Search build inputs should not depend on retired public docs `index.json`.
That is a builder-source responsibility, not a public search runtime capability change.

## Recently-Added Contract

Recently-added reads from a small generated payload limited by the configured recently-added count.
Do not add `added_date` or `last_updated` to `index-tree.json` only to support the recently-added list.

## Public Flat `index.json` Retirement

Public flat `site/assets/data/docs/scopes/<scope>/index.json` is retired from the Docs Viewer route contract.
Public Docs Viewer routes do not publish or load it.
The route contract is covered by:

- `index-tree.json` covers navigation
- by-id payloads cover selected-document rendering and info-panel metadata
- search reads its separate search payload
- recently-added reads its small generated payload

Data Sharing needs for richer document data are covered by `docs_data_sharing.source_context`, `docs_data_sharing.source_records`, and `docs_data_sharing.rendered_content`.
Those helpers read configured docs source and source-rendered content for Data Sharing workflows.
It must not fall back to public flat indexes, generated by-id payloads, search payloads, recently-added payloads, manage/local generated indexes, or generated metadata JSON.
Other tooling needs for richer generated data still need their own owning contract.

Manage/local rich flat indexes under `docs-viewer/generated/docs/<scope>/index.json` remain valid for manage/report/tooling consumers.
Do not treat those local artifacts as public route dependencies.

## Verification Coverage

Current verification covers:

- generated-output fixtures for public tree, recently-added, and public by-id payload shape
- builder projection tests for public tree/recent/by-id metadata omission and public flat-index removal
- public `/library/` and `/analysis/` route smokes for `index-tree.json`, `recently-added.json`, selected by-id, and search requests
- negative public smoke assertions that public routes do not request `site/assets/data/docs/scopes/<scope>/index.json`
- manage-route smoke assertions that generated reads use `index-tree`, selected payload, recently-added, and search endpoints without falling back to `/docs/generated/index`
