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

Slim public Docs Viewer scope indexes so `/library/` and `/analysis/` load only the data needed for public navigation and document selection.

The current public index rows carry metadata that is useful to management and tooling, but not needed to build the public docs tree.
The public runtime should use a small index for tree/navigation and read richer selected-document metadata from the by-id payload only when a selected surface needs it.

This request also owns the nav/tree payload follow-through deferred from [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints).
Tasks 13 and 14 from that request should be implemented here, after the public/manage entrypoint boundary established separate public and manage runtime owners.

## Goals

- make `assets/data/docs/scopes/<scope>/index.json` a lightweight public runtime tree/index payload
- add build-time public and manage nav/tree payloads so browser runtimes do not construct the index tree from rich flat indexes
- switch public and manage index panels to route-appropriate tree-ready payloads through a payload-agnostic shared tree renderer
- remove `summary` from public index rows after the info panel can read it from by-id payloads
- review and remove other non-tree public index fields where there is no active public-runtime need
- keep public read-only routes from depending on management/tooling metadata
- keep manage mode compatible with the shared runtime while allowing local/manage projections to be richer than public projections
- use the shared-core boundary maintained by the entrypoint split request rather than turning payload slimming into a shared-runtime cleanup project
- ensure scope lifecycle create/delete behavior creates and removes newly introduced generated nav/tree outputs through manifest-recorded files only
- make the public info panel a route-appropriate surface instead of a generic metadata dump
- preserve public route behavior for tree navigation, selected document loading, search, recently-added, and info-panel opening

## Non-Goals

- no removal of public by-id rendered document payloads
- no change to docs source front matter fields
- no management metadata modal redesign
- no broad rewrite of the Docs Viewer builder pipeline beyond the public index projection needed for this slimming work
- no public promotion of management controls, reports, imports, settings, scope lifecycle UI, source editor, drag/drop, context menus, or local-service reads

## Current Problem

Public scope `index.json` files are doing two jobs:

- building the public docs viewer index tree
- carrying extra document metadata that is useful to management, info surfaces, export/import review, or Data Sharing

That coupling makes public payloads larger than they need to be and makes tooling consumers depend on public artifacts.
The recent management-client static-import regression also showed that public/read-only and management/tooling boundaries need stronger tests around what public routes publish and load.

The entrypoint split request created the public/manage runtime boundary but intentionally left tree construction on the existing flat index path.
Current runtime code still filters and groups flat index rows in the browser, including public/manage mode and visibility logic in shared index modules.
This request should move that work to build time with separate public and manage nav payloads, then let each entrypoint load the correct payload directly.

## Proposed Direction

Split the public runtime contract from local/tooling metadata needs.

Public and manage routes should move from browser-time tree shaping to build-time nav/tree projection.
The public route should load a public-safe nav payload such as `assets/data/docs/scopes/<scope>/nav.json`.
The local manage route should load a richer manage nav payload such as `docs-viewer/generated/docs/<scope>/nav.json`.
Exact filenames can change during implementation, but the ownership split should not.

Build time should own:

- parent/child tree construction
- root and sibling ordering
- public viewability filtering for public nav payloads
- manage visibility/loadability projection for manage nav payloads
- compact public nav record projection
- richer manage nav record projection only for confirmed manage behavior
- optional path, depth, trail, status, or side-reference fields only when a public reader or manage surface actually needs them

Runtime should own:

- loading the route-appropriate nav/tree payload
- adapting the route-appropriate nav/tree payload to the existing renderer contract
- expanding and collapsing UI state
- highlighting the selected document
- routing to selected documents

Shared-core and shared-renderer cleanup remains owned by the entrypoint split request.
This request should not move management behavior into public payloads or shared payload adapters.
If nav/tree implementation exposes shared-core public/manage mode switches, resolve that in the entrypoint split request or explicitly coordinate the change there rather than silently absorbing it into payload slimming.

Public scope index rows should be as close as possible to:

- `doc_id`
- `title`
- `parent_id`, only when non-empty
- `viewable: false`, only when needed
- `ui_status`
- `content_url`
- fields needed for public route features such as recently-added, only after confirming there is no better source

Fields to review for removal from the public index:

- `summary`
- `last_updated`
- `source_path`
- `viewer_url`
- `content_text_length`
- any default or derivable values

`summary` and selected-document `last_updated` should be read from the by-id payload when the selected public info surface needs them.
`viewer_url` is derivable from route config and `doc_id`.
`source_path` is not public runtime data.
`content_text_length` should move out of the public index once any Data Sharing dependency has moved to an internal/local projection.

Once public navigation uses `nav.json`, `assets/data/docs/scopes/<scope>/index.json` can either become the slimmer public feature index or be retired from public route loading if all remaining public features have moved to better inputs.
Do not keep rich public flat indexes only to support the old tree-construction path.

## Scope Lifecycle Follow-Through

The scope lifecycle workflow must be updated in the same implementation slice that introduces nav/tree outputs.

`New scope` should:

- create public read-only route files that continue to load the public entrypoint, public route config, public UI text, and public CSS
- create every required public generated output for public scopes, including the public nav/tree payload
- create every required manage generated output for local/manage scopes, including the manage nav/tree payload
- record generated nav/tree files and directories in the scope manifest when they are created
- keep scope lifecycle action/menu/modal UI and copy manage-only

`Delete scope` should:

- remove only user-created, manifest-recorded scope files and generated scope outputs
- remove generated nav/tree files for deleted user-created scopes when those files were manifest-recorded
- never delete shared public or manage entrypoint assets, shared CSS, shared route registries, shared UI text, or shared core modules

## Public Info Panel

The public info panel should not mirror the manage-mode metadata surface.

For public read-only routes, the info panel should display only public reader-facing document data:

- summary
- last updated
- optional route/canonical link if still useful

It should not display source path, visibility state, UI status internals, management-only fields, or editable metadata concepts.

Manage mode can keep a richer metadata/info surface, but it should not force public index rows to carry management metadata.

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Audit every browser/runtime, builder, service, export/import, data-sharing, and report call site for public `assets/data/docs/scopes/<scope>/index.json` fields and current browser-time tree construction. |
| 2 | planned | Define the public nav/tree payload contract and manage nav/tree payload contract, including allowed fields, ordering, viewability filtering, loadability, optional status/path/trail data, and future extension rules. |
| 3 | planned | Add build-time public nav/tree payload generation, for example `assets/data/docs/scopes/<scope>/nav.json`, using public-safe compact records and public viewability filtering. |
| 4 | planned | Add build-time manage nav/tree payload generation, for example `docs-viewer/generated/docs/<scope>/nav.json`, using the same basic tree shape plus only confirmed manage-needed fields. |
| 5 | planned | Switch public and manage route config/data loading so index-panel rendering uses route-appropriate nav/tree payloads rather than building the tree from flat `index.json`. |
| 6 | planned | Add public and manage nav/tree payload adapters that preserve the shared-core boundary owned by [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints); do not move manage-only controls, services, drag/drop, context menus, mutation calls, source/edit workflows, or local-service reads into public payloads or shared payload adapters. |
| 7 | planned | Coordinate with the entrypoint split request if nav/tree switching exposes shared-core public/manage mode switches or manage-only rendering in shared modules; this request owns the payload/data contract, while the entrypoint split request owns shared-core cleanup tasks 10 and 11. |
| 8 | planned | Update scope lifecycle create/delete behavior so `write_generated_outputs` creates required nav/tree payloads for new scopes and delete removes only manifest-recorded nav/tree outputs for user-created scopes. |
| 9 | planned | Define the public flat index row contract after nav/tree route loading is in place, and document which remaining fields support search, recently-added, selected-document routing, or optional public feature data. |
| 10 | planned | Add or update tests that assert public nav/tree payloads and public scope indexes omit non-public or selected-document-only metadata. |
| 11 | planned | Refactor the info-panel context so public read-only metadata can hydrate from the selected by-id payload when needed. |
| 12 | planned | Split public read-only info-panel rendering from manage-mode metadata rendering. |
| 13 | planned | Remove `summary` from public index rows and confirm public info-panel summary still renders from by-id. |
| 14 | planned | Review `last_updated`, `source_path`, `viewer_url`, `content_text_length`, and other rich flat-index fields for removal after dependent call sites have moved. |
| 15 | planned | Run public Docs Viewer read-only smoke against a fresh temporary Jekyll build and focused manage-mode checks for shared runtime compatibility, including asset-load assertions for public nav/tree and manage nav/tree boundaries. |
| 16 | planned | Update [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory), [Data Models Library](/docs/?scope=studio&doc=data-models-library), [Data Models Analysis](/docs/?scope=studio&doc=data-models-analysis), and testing docs after the contract is durable. |

## Acceptance Criteria

- public scope indexes carry only the fields needed for public tree/navigation and confirmed public runtime features
- public routes load a public nav/tree payload for navigation instead of constructing the tree from a rich flat index
- manage routes load a manage nav/tree payload for navigation instead of relying on public nav data or public payload fallbacks
- nav/tree payload adapters preserve the shared-core boundary owned by the entrypoint split request and do not introduce public/manage mode switches, manage capability switches, hidden manage controls, drag/drop, context menus, mutation calls, source/edit actions, or local-service calls into public payload code
- scope lifecycle generated-output options create every required public/manage generated nav/tree payload introduced by this request
- scope lifecycle delete removes only manifest-recorded user-created nav/tree outputs and never removes shared public or manage entrypoint/config/CSS/runtime assets
- public info panel reads summary from by-id payloads, not public index rows
- public info panel shows only reader-facing metadata
- public read-only routes do not load management-only JS/CSS or management service data
- manage mode still opens and edits metadata through its existing management surfaces
