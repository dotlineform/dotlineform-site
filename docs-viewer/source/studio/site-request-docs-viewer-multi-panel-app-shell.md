---
doc_id: site-request-docs-viewer-multi-panel-app-shell
title: Docs Viewer Multi-Panel App Shell Request
added_date: 2026-05-27
last_updated: 2026-05-28
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Multi-Panel App Shell Request

Status:

- partly implemented
- needs re-specification

## Summary

This request originally proposed a broad multi-panel app-shell direction for Docs Viewer.

The completed design and implementation material has moved to [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts).
That durable doc now owns the current panel regions, hosted-view lifecycle, access gating, read-only metadata info view, and non-plugin module boundary.

This request should no longer carry implemented architecture notes.
It remains only as a reminder that the unfinished work needs to be reviewed and split into concrete change requests before more implementation.

## Already Moved Out

Completed or durable material now lives in [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts):

- JavaScript app-shell route/access/view-state foundation
- index, document, and info panel shell ownership
- current panel layout projection
- hosted-view registration and lifecycle
- selected-document hosted-view context
- public/manage access gating model
- read-only metadata info view
- non-plugin module-hosting boundary
- optional future module principles

Do not re-expand this request with that implemented material.
Update the durable Docs Viewer docs instead when current panel-host behavior changes.

## Remaining Work To Re-Specify

The remaining work is too broad for one implementation slice.
Each item below should become a concrete change request with owner, user-facing outcome, scope, risks, and focused verification.

### Generalized Panel Toolbar

Potential scope:

- define a shared toolbar projection for index, document, and info panels
- decide which panel controls are icons, menus, segmented controls, or text buttons
- wire controls through explicit panel intents
- source labels and accessible names from UI text/config
- keep keyboard focus behavior and mobile layout stable

Open decisions:

- whether the current index controls are enough for now
- whether the info panel needs only close/hide or a full view selector
- whether document/search/recent/report should wait for document-panel view work

### Document Panel View Switching

Potential scope:

- decide whether document, search, recent, report, and future source views should become explicit document-panel views
- define view selection behavior without breaking current route/search/recent/report flows
- keep selected document state independent from document-panel visibility
- preserve public read-only and local manage behavior

Open decisions:

- whether document-panel view state should be URL-addressable
- whether hidden document panel state loads payloads in the background
- how search/recent route state maps to a document-panel view model

### Source Editor And Semantic Reference Editor

Potential scope:

- define a manage-only document-panel source editor
- define any companion info-panel views for references, target search, insertion controls, or validation
- keep all source writes behind management endpoints
- decide the generated/reference data contract required by the editor

Related active requests:

- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
- [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2)

### Additional Info Views

Potential scope:

- activity view
- semantic-reference view
- generated relationship view
- source/status view
- scope health or build-status view

Each view needs a data contract and access decision.
Uncertain or operational views should start manage-only.

### Optional Visualization Modules

Potential scope:

- decide whether any real use case needs a graph/chart/relationship module
- choose the data contract before choosing a visualization library
- lazy-load any heavy dependency only when selected
- keep module CSS and lifecycle scoped to its panel body

This is not a plugin-system request.
Do not add plugin manifests, package protocols, marketplaces, generic adapter layers, or automatic third-party asset bundling without a separate architecture request.

### Panel State Persistence

Potential scope:

- decide which panel layout state is local preference
- decide which state belongs in URL/query/hash
- define per-scope, per-route, or global persistence behavior
- preserve current route/document/history behavior

## Deferred Route Checks

More detailed route checks can be left for later.
When a concrete panel request changes route behavior, focused checks should cover:

- public route boot and management omission
- manage-mode boot and capability-gated controls
- index/document/info panel combinations
- search/recent/report continuity
- selected-doc updates in info views
- desktop and mobile layout geometry where the UI changes

## Closeout Direction

Before continuing implementation, create smaller requests from the remaining work above.
Each request should name:

- the panel or view it changes
- the user-facing workflow
- the owner modules
- public vs manage availability
- data/backend contracts
- verification commands and browser checks

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell)
