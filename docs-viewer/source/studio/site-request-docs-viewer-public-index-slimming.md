---
doc_id: site-request-docs-viewer-public-index-slimming
title: Docs Viewer Public Index Slimming Request
added_date: 2026-06-03
last_updated: 2026-06-03
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Public Index Slimming Request

Status:

- draft
- related request: [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index)

## Summary

Slim public Docs Viewer scope indexes so `/library/` and `/analysis/` load only the data needed for public navigation and document selection.

The current public index rows carry metadata that is useful to management and tooling, but not needed to build the public docs tree.
The public runtime should use a small index for tree/navigation and read richer selected-document metadata from the by-id payload only when a selected surface needs it.

## Goals

- make `assets/data/docs/scopes/<scope>/index.json` a lightweight public runtime tree/index payload
- remove `summary` from public index rows after the info panel can read it from by-id payloads
- review and remove other non-tree public index fields where there is no active public-runtime need
- keep public read-only routes from depending on management/tooling metadata
- keep manage mode compatible with the shared runtime while allowing local/manage projections to be richer than public projections
- make the public info panel a route-appropriate surface instead of a generic metadata dump
- preserve public route behavior for tree navigation, selected document loading, search, recently-added, and info-panel opening

## Non-Goals

- no Data Sharing contract migration in this request; that belongs to [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index)
- no removal of public by-id rendered document payloads
- no change to docs source front matter fields
- no management metadata modal redesign
- no broad rewrite of the Docs Viewer builder pipeline beyond the public index projection needed for this slimming work

## Current Problem

Public scope `index.json` files are doing two jobs:

- building the public docs viewer index tree
- carrying extra document metadata that is useful to management, info surfaces, export/import review, or Data Sharing

That coupling makes public payloads larger than they need to be and makes tooling consumers depend on public artifacts.
The recent management-client static-import regression also showed that public/read-only and management/tooling boundaries need stronger tests around what public routes publish and load.

## Proposed Direction

Split the public runtime contract from local/tooling metadata needs.

Public scope index rows should be as close as possible to:

- `doc_id`
- `title`
- `parent_id`, only when non-empty
- `viewable: false`, only when needed
- `ui_status`, only if the public tree still displays status indicators
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
| 1 | planned | Audit every browser/runtime and service call site for public `assets/data/docs/scopes/<scope>/index.json` fields. |
| 2 | planned | Define the public index row contract and document which fields are tree/navigation, selected-document routing, or optional public feature data. |
| 3 | planned | Add or update tests that assert public scope indexes omit non-public or selected-document-only metadata. |
| 4 | planned | Refactor the info-panel context so public read-only metadata can hydrate from the selected by-id payload when needed. |
| 5 | planned | Split public read-only info-panel rendering from manage-mode metadata rendering. |
| 6 | planned | Remove `summary` from public index rows and confirm public info-panel summary still renders from by-id. |
| 7 | planned | Review `last_updated`, `source_path`, `viewer_url`, and `content_text_length` removal after dependent call sites have moved. |
| 8 | planned | Run public Docs Viewer read-only smoke against a fresh temporary Jekyll build and focused manage-mode checks for shared runtime compatibility. |
| 9 | planned | Update [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary), [Data Models Library](/docs/?scope=studio&doc=data-models-library), [Data Models Analysis](/docs/?scope=studio&doc=data-models-analysis), and testing docs after the contract is durable. |

## Acceptance Criteria

- public scope indexes carry only the fields needed for public tree/navigation and confirmed public runtime features
- public info panel reads summary from by-id payloads, not public index rows
- public info panel shows only reader-facing metadata
- public read-only routes do not load management-only JS/CSS or management service data
- manage mode still opens and edits metadata through its existing management surfaces
- Data Sharing no longer depends on public scope indexes for tooling metadata before `content_text_length` or similar tooling fields are removed
