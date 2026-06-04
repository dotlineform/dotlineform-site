---
doc_id: site-request-docs-viewer-public-index-slimming
title: Docs Viewer Public Index Slimming Request
added_date: 2026-06-03
last_updated: 2026-06-04
ui_status: in-progress
parent_id: change-requests
viewable: true
---
# Docs Viewer Public Index Slimming Request

Status:

- in progress

## Summary

Retire public Docs Viewer scope indexes from the `/library/` and `/analysis/` runtime contract so those routes load only tree and selected-document payloads needed for public navigation and document selection.

The current public index rows carry metadata that is useful to management and tooling, but not needed to build the public docs tree.
The public runtime should use `index-tree.json` for tree/navigation and read selected-document metadata from the by-id payload when the info panel needs it.

This request also owns the tree payload follow-through deferred from [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints).
Tasks 13 and 14 from that request should be implemented here, after the public/manage entrypoint boundary established separate public and manage runtime owners.

## Goals

- keep current public and manage index UI behavior while changing data shape and loading responsibilities
- ensure that the public payload is as small as possible
- make tree structure a build-time concern so the index runtime does less work
- keep basic index loading and behavior consistent across public and manage scopes
- ensure that additional manage-mode functionality is only loaded and exposed in manage scopes
- retire `assets/data/docs/scopes/<scope>/index.json` from the public Docs Viewer runtime contract
- add build-time public and manage `index-tree.json` payloads so browser runtimes do not construct the index tree from rich flat indexes
- switch public and manage index panels to route-appropriate tree-ready payloads through a payload-agnostic shared tree renderer
- remove `summary` from public tree/index loading after the info panel can read it from by-id payloads
- review and remove other public index fields after public Docs Viewer no longer loads `index.json`
- keep public read-only routes from depending on management/tooling metadata
- keep manage mode compatible with the shared runtime while allowing local/manage generated outputs outside the shared `index-tree.json` structure to be richer than public outputs
- use the shared-core boundary maintained by the entrypoint split request rather than turning payload slimming into a shared-runtime cleanup project
- ensure scope lifecycle create/delete behavior creates and removes newly introduced generated `index-tree.json` and recently-added outputs through manifest-recorded files only
- make the public info panel a route-appropriate surface backed by by-id payload metadata instead of a generic index-row metadata dump
- preserve public route behavior for tree navigation, selected document loading, search, recently-added, and info-panel opening

## Non-Goals

- no removal of public by-id rendered document payloads
- no change to docs source front matter fields
- no management metadata modal redesign
- no broad rewrite of the Docs Viewer builder pipeline beyond the public tree projection and public index retirement needed for this work
- no public promotion of management controls, reports, imports, settings, scope lifecycle UI, source editor, drag/drop, context menus, or local-service reads

## Current Problem

Public scope `index.json` files are doing two jobs:

- building the public docs viewer index tree
- carrying extra document metadata that is useful to management, info surfaces, export/import review, or Data Sharing

That coupling makes public payloads larger than they need to be and makes tooling consumers depend on public artifacts.
The recent management-client static-import regression also showed that public/read-only and management/tooling boundaries need stronger tests around what public routes publish and load.

The entrypoint split request created the public/manage runtime boundary but intentionally left tree construction on the existing flat index path.
Current runtime code still filters and groups flat index rows in the browser, including public/manage mode and visibility logic in shared index modules.
This request should move that work to build time with separate public and manage tree payloads, then let each entrypoint load the correct payload directly.

## Proposed Direction

Split the public runtime contract from local/tooling metadata needs.

Public and manage routes should move from browser-time tree shaping to build-time `index-tree.json` projection.
The public route should load a public-safe tree payload such as `assets/data/docs/scopes/<scope>/index-tree.json`.
The local manage route should load its scope's tree payload, such as `docs-viewer/generated/docs/<scope>/index-tree.json`, using the same data structure as public tree payloads.

Build time should own:

- parent/child tree construction
- root and sibling ordering
- public viewability filtering for public tree payloads
- manage visibility/loadability projection for manage tree payloads
- compact public tree record projection
- small recently-added payloads limited to the configured recently-added count
- the same tree record structure for public and manage scopes
- optional path, depth, trail, or side-reference fields only when a public reader or manage surface actually needs them

Runtime should own:

- loading the route-appropriate `index-tree.json` payload
- loading recently-added data from the route-appropriate small build-time payload
- adapting the route-appropriate tree payload to the existing renderer contract
- expanding and collapsing UI state
- highlighting the selected document
- routing to selected documents

Shared-core and shared-renderer cleanup remains owned by the entrypoint split request.
This request should not move management behavior into public payloads or shared payload adapters.
If tree implementation exposes shared-core public/manage mode switches, resolve that in the entrypoint split request or explicitly coordinate the change there rather than silently absorbing it into payload slimming.

Public `index-tree.json` rows should be as close as possible to:

- `doc_id`
- `title`
- `parent_id`, only when non-empty
- `viewable: false`, only when needed
- `ui_status`
- `content_url`

Fields to exclude from public `index-tree.json`:

- `summary`
- `last_updated`
- `source_path`
- `viewer_url`
- `content_text_length`
- any default or derivable values

Docs Viewer public route navigation should be served by `index-tree.json`, selected document loading and info-panel metadata should be served by by-id payloads, search should be served by the existing search payload, and recently-added should be served by a small build-time payload.
Selected-document `title`, `summary`, and `last_updated` should be read from the by-id payload when the selected info surface needs them.
`viewer_url` is derivable from route config and `doc_id`.
`source_path` is not public runtime data.
`content_text_length` is not public runtime data.

`assets/data/docs/scopes/<scope>/index.json` should be retired from public Docs Viewer route loading.
[Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index) owns the decision for how Data Sharing gains the richer document data it needs without relying on public `index.json`.
Do not keep rich public flat indexes only to support the old tree-construction path or tooling consumers.

## Scope Lifecycle Follow-Through

The scope lifecycle workflow must be updated in the same implementation slice that introduces tree outputs.

`New scope` should:

- create public read-only route files that continue to load the public entrypoint, public route config, public UI text, and public CSS
- create every required public generated output for public scopes, including the public `index-tree.json` and recently-added payloads
- create every required manage generated output for local/manage scopes, including the manage `index-tree.json` and recently-added payloads
- record generated files and directories in the scope manifest when they are created
- keep scope lifecycle action/menu/modal UI and copy manage-only

`Delete scope` should:

- remove only user-created, manifest-recorded scope files and generated scope outputs
- remove generated outputs for deleted user-created scopes when those files were manifest-recorded
- never delete shared public or manage entrypoint assets, shared CSS, shared route registries, shared UI text, or shared core modules

## Public Info Panel

The info panel should read selected-document metadata from by-id payloads, not public index rows and not `index.json`.
This principle applies to both public read-only routes and local/manage routes.

The public info panel should not mirror the manage-mode metadata surface.

For public read-only routes, the info panel should display only public reader-facing document data:

- title
- summary
- last updated

It should not display source path, visibility state, UI status internals, management-only fields, or editable metadata concepts.

Manage mode can keep a richer metadata/info surface, but it should also hydrate selected-document metadata from the selected by-id payload rather than index rows.
Manage metadata surfaces should not force public tree or by-id payloads to carry management metadata.

## Decisions

- Public `assets/data/docs/scopes/<scope>/index.json` should be retired from the Docs Viewer runtime contract after `index-tree.json`, by-id payloads, search payloads, and recently-added payloads cover public route needs.
- The tree-ready payload should be named `index-tree.json`, not `nav.json`.
- Public Docs Viewer should meet tree navigation and selected document loading from `index-tree.json` and by-id payloads, search from the search payload, recently-added from a small build-time recently-added payload, and info-panel metadata from by-id payloads.
- Info-panel metadata should hydrate from selected by-id payloads for both public read-only and local/manage routes, not from public index rows or `index.json`.
- Public read-only info panels should display only `title`, `summary`, and `last_updated`.
- Public by-id payloads are in scope for reader-facing metadata slimming where needed to support that public info-panel contract without carrying management-only metadata.
- Public and manage route config should point the frontend JS at the route-appropriate `index-tree.json` data source. No manage generated-read endpoint is needed for tree loading unless a later manage-only capability creates a separate server-side need.
- Missing required `index-tree.json` is a normal visible data-load failure. There is no fallback to `index.json`, because `index.json` is being retired from the Docs Viewer route contract.
- Each scope, public or manage, has one generated `index-tree.json` and generated by-id payloads. Do not introduce a third tree-adjacent metadata projection for this request.
- Public and manage `index-tree.json` should use exactly the same data structure.
- `viewable` or equivalent non-viewable state and `ui_status` are fundamental tree behavior fields for both public and manage scopes. Public scopes need them for current read-only tree display; manage scopes also need them because manage can set their values.
- Current manage-mode scan found no pre-by-id need for `summary`, `source_path`, `viewer_url`, `content_text_length`, source-open metadata, context-menu action eligibility, or drag/drop eligibility fields in `index-tree.json`. Context actions and drag/drop use shared tree fields such as `doc_id`, `title`, parent/child relationships, and loadable target state.
- Current UI behavior should be preserved. This request should not change public viewability behavior, manage tree behavior, selection behavior, search/recently-added behavior, info-panel opening behavior, or existing treatment of viewable children under non-viewable parents.
- Search runtime ownership and capabilities do not change. Search continues to read its own search payload through `search_index_url`, such as `assets/data/search/<scope>/index.json` or `docs-viewer/generated/search/<scope>/index.json`.
- Search build inputs must stop depending on retired public docs `index.json`; that is a builder-source adjustment, not a public search runtime capability change.
- Recently-added should move from runtime sorting of loaded tree records to its own small build-time JSON payload, limited by the configured recently-added count. Do not add `added_date` or `last_updated` to `index-tree.json` only to support a 10-record recently-added list.
- Existing scope migration/backfill should use the normal generated-docs write path for the target scope, for example `./docs-viewer/build/build_docs.py --scope studio --write`.
- [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index) owns the separate decision for how Data Sharing gets richer document metadata without relying on public `index.json`.

## Open Issues

None currently.

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Audit every browser/runtime, builder, service, export/import, data-sharing, and report call site for public `assets/data/docs/scopes/<scope>/index.json` fields and current browser-time tree construction. |
| 2 | planned | Define the shared public/manage `index-tree.json` payload contract, including allowed fields, ordering, viewability filtering, loadability, optional path/trail data, and future extension rules. Public and manage scopes should use exactly the same data structure. |
| 3 | planned | Add build-time public tree payload generation at `assets/data/docs/scopes/<scope>/index-tree.json`, using public-safe compact records and public viewability filtering. |
| 4 | planned | Add build-time manage tree payload generation at `docs-viewer/generated/docs/<scope>/index-tree.json`, using the same tree record structure as public scopes while preserving manage visibility/loadability behavior. |
| 5 | planned | Switch public and manage route config/data loading so frontend index-panel rendering reads route-appropriate `index-tree.json` payloads rather than building the tree from flat `index.json`; missing required tree payloads should surface as visible data-load failures. |
| 6 | planned | Add public and manage tree payload adapters that preserve the shared-core boundary owned by [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints); do not move manage-only controls, services, drag/drop, context menus, mutation calls, source/edit workflows, or local-service reads into public payloads or shared payload adapters. |
| 7 | planned | Coordinate with the entrypoint split request if tree payload switching exposes shared-core public/manage mode switches or manage-only rendering in shared modules; this request owns the payload/data contract, while the entrypoint split request owns shared-core cleanup tasks 10 and 11. |
| 8 | planned | Update scope lifecycle create/delete behavior so `write_generated_outputs` creates required `index-tree.json` and recently-added payloads for new scopes and delete removes only manifest-recorded generated outputs for user-created scopes; existing scopes are backfilled through the normal `build_docs.py --scope <scope> --write` path. |
| 9 | planned | Retire public flat `index.json` from Docs Viewer route loading after `index-tree.json`, by-id payloads, search payloads, and recently-added payloads support tree navigation, selected-document routing, search, recently-added, and public info-panel data; keep search runtime on its separate search payload and update search build inputs so they no longer depend on retired public docs indexes. |
| 10 | planned | Add or update tests, generated-output contract fixtures, and projection checks that assert public `index-tree.json` payloads and public route loads omit non-public or selected-document-only metadata, and that public routes do not request public `index.json`. |
| 11 | planned | Refactor the info-panel context so selected-document metadata hydrates from by-id payloads for both public read-only and local/manage routes. |
| 12 | planned | Split public read-only info-panel rendering from manage-mode metadata rendering, with public read-only limited to title, summary, and last updated. |
| 13 | planned | Remove public info-panel metadata reads from public tree/index rows and confirm title, summary, and last updated render from by-id. |
| 14 | planned | Review `last_updated`, `source_path`, `viewer_url`, `content_text_length`, and other rich flat-index fields for removal after dependent call sites have moved. |
| 15 | planned | Run public Docs Viewer read-only smoke against a fresh temporary Jekyll build and focused manage-mode checks for shared runtime compatibility, including asset-load assertions for public and manage `index-tree.json` boundaries. |
| 16 | planned | Update [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory), [Data Models Library](/docs/?scope=studio&doc=data-models-library), [Data Models Analysis](/docs/?scope=studio&doc=data-models-analysis), and testing docs after the contract is durable. |

## Acceptance Criteria

- public Docs Viewer routes do not load public `index.json`
- public routes load a public `index-tree.json` payload for navigation instead of constructing the tree from a rich flat index
- manage routes load a manage `index-tree.json` payload with the same data structure as public tree payloads instead of relying on public tree data
- recently-added reads from a small build-time payload and does not require `added_date` or `last_updated` fields in `index-tree.json`
- generated-output contract fixtures and projection checks no longer require rich public `index.json` fields such as `source_path`, `viewer_url`, or `content_text_length`
- tree payload adapters preserve the shared-core boundary owned by the entrypoint split request and do not introduce public/manage mode switches, manage capability switches, hidden manage controls, drag/drop, context menus, mutation calls, source/edit actions, or local-service calls into public payload code
- scope lifecycle generated-output options create every required public/manage generated `index-tree.json` and recently-added payload introduced by this request
- scope lifecycle delete removes only manifest-recorded user-created generated outputs and never removes shared public or manage entrypoint/config/CSS/runtime assets
- public and local/manage info-panel metadata hydrates from selected by-id payloads, not public tree/index rows or `index.json`
- public info panel shows only title, summary, and last updated
- public read-only routes do not load management-only JS/CSS or management service data
- manage mode still opens and edits metadata through its existing management surfaces
