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
The public runtime should use `index-tree.json` for tree/navigation and read richer selected-document metadata from the by-id payload only when a selected surface needs it.

This request also owns the tree payload follow-through deferred from [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints).
Tasks 13 and 14 from that request should be implemented here, after the public/manage entrypoint boundary established separate public and manage runtime owners.

## Goals

- retire `assets/data/docs/scopes/<scope>/index.json` from the public Docs Viewer runtime contract
- add build-time public and manage `index-tree.json` payloads so browser runtimes do not construct the index tree from rich flat indexes
- switch public and manage index panels to route-appropriate tree-ready payloads through a payload-agnostic shared tree renderer
- remove `summary` from public tree/index loading after the info panel can read it from by-id payloads
- review and remove other public index fields after public Docs Viewer no longer loads `index.json`
- keep public read-only routes from depending on management/tooling metadata
- keep manage mode compatible with the shared runtime while allowing local/manage projections to be richer than public projections
- use the shared-core boundary maintained by the entrypoint split request rather than turning payload slimming into a shared-runtime cleanup project
- ensure scope lifecycle create/delete behavior creates and removes newly introduced generated `index-tree.json` outputs through manifest-recorded files only
- make the public info panel a route-appropriate surface instead of a generic metadata dump
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
The local manage route should load a richer manage tree payload such as `docs-viewer/generated/docs/<scope>/index-tree.json`.

Build time should own:

- parent/child tree construction
- root and sibling ordering
- public viewability filtering for public tree payloads
- manage visibility/loadability projection for manage tree payloads
- compact public tree record projection
- richer manage tree record projection only for confirmed manage behavior
- optional path, depth, trail, status, or side-reference fields only when a public reader or manage surface actually needs them

Runtime should own:

- loading the route-appropriate `index-tree.json` payload
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
- fields needed for public route features such as recently-added, only after confirming there is no better source

Fields to exclude from public `index-tree.json`:

- `summary`
- `last_updated`
- `source_path`
- `viewer_url`
- `content_text_length`
- any default or derivable values

Docs Viewer public route features should be served by `index-tree.json` and by-id payloads.
`summary` and selected-document `last_updated` should be read from the by-id payload when the selected public info surface needs them.
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
- create every required public generated output for public scopes, including the public `index-tree.json` payload
- create every required manage generated output for local/manage scopes, including the manage `index-tree.json` payload
- record generated tree files and directories in the scope manifest when they are created
- keep scope lifecycle action/menu/modal UI and copy manage-only

`Delete scope` should:

- remove only user-created, manifest-recorded scope files and generated scope outputs
- remove generated tree files for deleted user-created scopes when those files were manifest-recorded
- never delete shared public or manage entrypoint assets, shared CSS, shared route registries, shared UI text, or shared core modules

## Public Info Panel

The public info panel should not mirror the manage-mode metadata surface.

For public read-only routes, the info panel should display only public reader-facing document data:

- summary
- last updated
- optional route/canonical link if still useful

It should not display source path, visibility state, UI status internals, management-only fields, or editable metadata concepts.

Manage mode can keep a richer metadata/info surface, but it should not force public tree or by-id payloads to carry management metadata.

## Decisions

- Public `assets/data/docs/scopes/<scope>/index.json` should be retired from the Docs Viewer runtime contract after `index-tree.json` and by-id payloads cover public route needs.
- The tree-ready payload should be named `index-tree.json`, not `nav.json`.
- Public Docs Viewer should meet tree navigation, selected document loading, search/recently-added, and info-panel needs from `index-tree.json` and by-id payloads.
- [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index) owns the separate decision for how Data Sharing gets richer document metadata without relying on public `index.json`.

## Open Issues

Address these before or during implementation, then fold resolved decisions into the relevant contract, task, or acceptance section.

1. Define whether public by-id payloads are in scope for reader-facing metadata slimming. Public info-panel hydration from by-id may still expose or depend on fields produced by the current shared metadata entry, such as `source_path`, `viewer_url`, `ui_status`, and management/report-related fields.
2. Make `summary` in selected public by-id payloads an explicit generated-data contract if the public info panel will read summary from by-id after `summary` is removed from public tree/index loading.
3. Define the route/config migration for `index-tree.json` loading, including the new public and manage config fields, the manage generated-read endpoint if needed, and the visible failure behavior when a required tree payload is missing. Do not silently fall back to the old flat `index.json` tree path.
4. Specify the manage tree data contract for current manage behavior, including non-viewable state, non-loadable/group nodes, manage-only roots, status icons, drag/drop eligibility, context-menu/action eligibility, and source/metadata action targets. If some of this should not live in the tree payload, name the manage-owned projection or service that provides it.
5. Define public viewability edge-case behavior for viewable children under non-viewable parents: exclude the child, hoist it, or include a structural-only parent row. Current runtime behavior excludes docs with non-viewable ancestors.
6. Define search and recently-added ownership after public index retirement, using `index-tree.json` and by-id payloads rather than public `index.json`.
7. Add concrete Data Sharing follow-through for any current dependency on public `assets/data/docs/scopes/<scope>/index.json`, including coordination with [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index) before `content_text_length` or other tooling fields leave the public index.
8. Add migration/backfill coverage for existing scopes and manifests, not only new scope create/delete behavior. Existing `library`, `analysis`, `studio`, and `tmp` generated outputs and manifest records need a clear `index-tree.json` transition.
9. Update generated-output contract fixtures and projection checks as part of verification. Current fixtures still treat rich `index.json` fields such as `source_path`, `viewer_url`, and `content_text_length` as contract fields.

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Audit every browser/runtime, builder, service, export/import, data-sharing, and report call site for public `assets/data/docs/scopes/<scope>/index.json` fields and current browser-time tree construction. |
| 2 | planned | Define the public `index-tree.json` payload contract and manage `index-tree.json` payload contract, including allowed fields, ordering, viewability filtering, loadability, optional status/path/trail data, and future extension rules. |
| 3 | planned | Add build-time public tree payload generation at `assets/data/docs/scopes/<scope>/index-tree.json`, using public-safe compact records and public viewability filtering. |
| 4 | planned | Add build-time manage tree payload generation at `docs-viewer/generated/docs/<scope>/index-tree.json`, using the same basic tree shape plus only confirmed manage-needed fields. |
| 5 | planned | Switch public and manage route config/data loading so index-panel rendering uses route-appropriate `index-tree.json` payloads rather than building the tree from flat `index.json`. |
| 6 | planned | Add public and manage tree payload adapters that preserve the shared-core boundary owned by [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints); do not move manage-only controls, services, drag/drop, context menus, mutation calls, source/edit workflows, or local-service reads into public payloads or shared payload adapters. |
| 7 | planned | Coordinate with the entrypoint split request if tree payload switching exposes shared-core public/manage mode switches or manage-only rendering in shared modules; this request owns the payload/data contract, while the entrypoint split request owns shared-core cleanup tasks 10 and 11. |
| 8 | planned | Update scope lifecycle create/delete behavior so `write_generated_outputs` creates required `index-tree.json` payloads for new scopes and delete removes only manifest-recorded tree outputs for user-created scopes. |
| 9 | planned | Retire public flat `index.json` from Docs Viewer route loading after `index-tree.json` and by-id payloads support tree navigation, search/recently-added, selected-document routing, and public info-panel data. |
| 10 | planned | Add or update tests that assert public `index-tree.json` payloads and public route loads omit non-public or selected-document-only metadata, and that public routes do not request public `index.json`. |
| 11 | planned | Refactor the info-panel context so public read-only metadata can hydrate from the selected by-id payload when needed. |
| 12 | planned | Split public read-only info-panel rendering from manage-mode metadata rendering. |
| 13 | planned | Remove `summary` from public tree/index loading and confirm public info-panel summary still renders from by-id. |
| 14 | planned | Review `last_updated`, `source_path`, `viewer_url`, `content_text_length`, and other rich flat-index fields for removal after dependent call sites have moved. |
| 15 | planned | Run public Docs Viewer read-only smoke against a fresh temporary Jekyll build and focused manage-mode checks for shared runtime compatibility, including asset-load assertions for public and manage `index-tree.json` boundaries. |
| 16 | planned | Update [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory), [Data Models Library](/docs/?scope=studio&doc=data-models-library), [Data Models Analysis](/docs/?scope=studio&doc=data-models-analysis), and testing docs after the contract is durable. |

## Acceptance Criteria

- public Docs Viewer routes do not load public `index.json`
- public routes load a public `index-tree.json` payload for navigation instead of constructing the tree from a rich flat index
- manage routes load a manage `index-tree.json` payload for navigation instead of relying on public tree data or public payload fallbacks
- tree payload adapters preserve the shared-core boundary owned by the entrypoint split request and do not introduce public/manage mode switches, manage capability switches, hidden manage controls, drag/drop, context menus, mutation calls, source/edit actions, or local-service calls into public payload code
- scope lifecycle generated-output options create every required public/manage generated `index-tree.json` payload introduced by this request
- scope lifecycle delete removes only manifest-recorded user-created tree outputs and never removes shared public or manage entrypoint/config/CSS/runtime assets
- public info panel reads summary from by-id payloads, not public tree/index rows
- public info panel shows only reader-facing metadata
- public read-only routes do not load management-only JS/CSS or management service data
- manage mode still opens and edits metadata through its existing management surfaces
