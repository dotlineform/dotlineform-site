---
doc_id: docs-viewer-generated-data-contracts
title: Docs Viewer Generated Data Contracts
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: reference
parent_id: docs-viewer-runtime-boundary
viewable: true
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

## Current Payload Roots

| Scope kind | Docs root | Search root |
| --- | --- | --- |
| Public read-only | `assets/data/docs/scopes/<scope>/` | `assets/data/search/<scope>/index.json` |
| Manage/local | `docs-viewer/generated/docs/<scope>/` | `docs-viewer/generated/search/<scope>/index.json` |

## Route Payload Contract

| Capability | Public route source | Manage route source | Notes |
| --- | --- | --- | --- |
| Navigation tree | `index-tree.json` after public-index slimming | `index-tree.json` after public-index slimming | Public and manage tree records should share the same structure. |
| Selected document render | by-id payload | by-id payload | By-id payloads remain in scope for selected documents. |
| Info-panel metadata | selected by-id payload | selected by-id payload | Public reader metadata is limited to title, summary, and last updated. |
| Search | search payload | search payload | Search runtime reads separate search payloads. |
| Recently-added | small generated recently-added payload | small generated recently-added payload | Do not add date-only fields to tree rows to support recently-added. |
| Management metadata/actions | not public route data | management services and manage payloads as needed | Public tree/by-id payloads should not carry management-only metadata. |

## `index-tree.json` Contract

Public and manage `index-tree.json` should use exactly the same data structure.
Manage tree generation may preserve manage visibility/loadability behavior, but it should not add richer row fields unless a manage interaction needs them before selected by-id is loaded.

Public `index-tree.json` rows should stay as close as possible to:

- `doc_id`
- `title`
- `parent_id`, only when non-empty
- `viewable: false`, only when needed
- `ui_status`
- `content_url`

Fields excluded from public `index-tree.json`:

- `summary`
- `last_updated`
- `source_path`
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

- `assets/data/search/<scope>/index.json`
- `docs-viewer/generated/search/<scope>/index.json`

Search build inputs should not depend on retired public docs `index.json`.
That is a builder-source responsibility, not a public search runtime capability change.

## Recently-Added Contract

Recently-added reads from a small generated payload limited by the configured recently-added count.
Do not add `added_date` or `last_updated` to `index-tree.json` only to support the recently-added list.

## Public Flat `index.json` Retirement

Public flat `assets/data/docs/scopes/<scope>/index.json` is retired from the Docs Viewer route contract after:

- `index-tree.json` covers navigation
- by-id payloads cover selected-document rendering and info-panel metadata
- search reads its separate search payload
- recently-added reads its small generated payload

Data Sharing or other tooling needs for richer document data are not a reason to preserve rich public flat indexes as public route data.
Those consumers need their own owning contract.

## Batch 7 Update Targets

After [Docs Viewer Public Index Slimming Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming) is implemented, update this document to confirm:

- exact public and manage `index-tree.json` paths
- exact recently-added payload path and shape
- final public by-id metadata fields used by the info panel
- final route config field names for tree, search, by-id, and recently-added payloads
- public flat `index.json` retirement status
- tests or fixtures that assert public tree/by-id/recent payloads omit management-only metadata
- any remaining non-Docs Viewer owner for rich document metadata, such as Data Sharing
