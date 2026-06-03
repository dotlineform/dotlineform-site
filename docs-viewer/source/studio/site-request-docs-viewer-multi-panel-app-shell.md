---
doc_id: site-request-docs-viewer-multi-panel-app-shell
title: Docs Viewer Multi-Panel App Shell Request
added_date: 2026-05-27
last_updated: 2026-06-02
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Viewer Multi-Panel App Shell Request

Status:

- partly implemented
- remaining work is prioritized below

## Summary

This request originally proposed a broad multi-panel app-shell direction for Docs Viewer.

The completed design and implementation material has moved to [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts).
That durable doc now owns the current panel regions, hosted-view lifecycle, access gating, read-only metadata info view, and non-plugin module boundary.

This request should no longer carry implemented architecture notes.
It now tracks the remaining multi-panel app-shell priorities that are not already split into smaller requests.

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

## Implementation Priorities

The current implementation is documented in [Docs Viewer Panel Hosts](/docs/?scope=studio&doc=docs-viewer-panel-hosts).
The priorities below are the remaining multi-panel app-shell requirements that are not already covered by smaller requests.

### Priority 1. Main-View Hosted-View Lifecycle

User-facing outcome:

- Docs Viewer can switch the main view between explicit views without breaking current document, search, recent, and report behavior.
- The future Markdown source editor can attach as a main-view hosted view instead of bolting controls onto the existing document renderer.

Current gap:

- `docs-viewer-main-view-host.js` validates switch requests and projects active main-view state for `rendered-document`, `search-results`, and `recent-results`.
- `docs-viewer-hosted-views.js` has main-view records for `rendered-document`, `search-results`, `recent-results`, and disabled manage-only `markdown-source`.
- Existing document, search, recent, and report controllers still own their current rendering behavior.
- There is no full main-view lifecycle equivalent to `docs-viewer-info-panel-host.js` for independently mounted main-view modules.

Scope:

- finish the main-view mounted-module lifecycle
- preserve existing document/search/recent route behavior while the host owns replacement intents
- preserve selected-document state independent from main-view visibility
- preserve public read-only and local manage behavior
- define graceful unavailable states for manage-only main-view views

Open decisions:

- whether any future main-view state beyond current document/search/recent route continuity should be URL-addressable
- whether hidden main-view modules keep payloads loaded
- whether report documents remain a document payload mode or become a main-view hosted view

### Priority 2. Panel Toolbar Projection

User-facing outcome:

- panel controls are predictable across index, document, and info panels.
- future source editor, info views, and index views can add controls without route-local DOM mutations.

Current gap:

- index controls are projected through app-shell helpers.
- info panel has close/view-option chrome.
- the main-view toolbar surface owns the current rendered-document metadata controls while preserving existing rendered-document controller IDs.
- search, recent, and reports still use their existing controls.

Scope:

- extend the toolbar projection model for index, main, and info panels only when a concrete view needs it
- decide which controls are icon buttons, menus, segmented controls, or text buttons
- wire controls through explicit panel intents
- source labels and accessible names from UI text/config
- keep keyboard focus behavior and mobile layout stable

Open decisions:

- whether the current index controls are sufficient for the next slice
- whether info panel needs only close/hide plus view selector
- which main-view controls are part of panel chrome versus view-specific UI

### Priority 3. Info-View Expansion Contract

User-facing outcome:

- additional info views can be added without weakening public/manage access boundaries or overloading the metadata view.

Current gap:

- only `metadata-info` is implemented.
- no activity, semantic-reference, relationship, source-status, or build-status info views exist.

Scope:

- define a repeatable data/access/lifecycle checklist for new info views
- keep operational or write-adjacent views manage-only by default
- ensure public-safe views receive only public-safe context
- keep failures local to the info panel

Open decisions:

- which info view has enough value to implement first
- whether semantic-reference information belongs in an info view, Analytics view, report, or source editor companion UI

### Priority 4. Panel State Persistence And URL Policy

User-facing outcome:

- panel state behaves predictably across reloads, route changes, and public/manage routes.

Current gap:

- index collapsed/normal state has current persistence behavior.
- expanded state is capability-driven and normalized when unsupported.
- info open/closed state and active view are transient browser state.
- main-view state beyond existing rendered-document/search/recent route continuity is not a route contract.

Scope:

- decide which panel layout state is local preference
- decide which state belongs in URL/query/hash
- define per-scope, per-route, or global persistence behavior
- preserve current route/document/history behavior

Open decisions:

- whether source editor state should ever be URL-addressable
- whether expanded index view should persist per scope or per route
- whether info-panel open state should persist at all

### Priority 5. Optional Visualization Modules

User-facing outcome:

- future graph/chart/relationship views can be evaluated against real data and interaction requirements before choosing a visualization library.

Current gap:

- `index-graph` is a manage-only placeholder that proves capability projection.
- no real graph, chart, relationship explorer, or external visualization library is implemented.

Scope:

- define the data contract and user workflow first
- lazy-load heavy dependencies only when selected
- keep module CSS and lifecycle scoped to the panel body
- keep public exposure as a separate decision

Open decisions:

- whether the first visualization should be an index graph, semantic-reference explorer, Analytics relationship view, or something else
- whether graph/reference planning belongs in Docs Viewer, Analytics, or a shared generated-data layer

This is not a plugin-system request.
Do not add plugin manifests, package protocols, marketplaces, generic adapter layers, or automatic third-party asset bundling without a separate architecture request.

## Split-Out Requests

The following work is related to panels but now has its own request:

- [Docs Viewer Markdown Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor) owns the manage-mode Markdown source editor and source read/write/rebuild workflow.
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor) owns semantic-token insertion inside the Markdown editor.
- [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2) owns the semantic-reference registry needed by semantic editor and future reference views.

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
- [Docs Viewer Markdown Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-markdown-editor)
- [Docs Viewer Semantic Reference Editor Request](/docs/?scope=studio&doc=site-request-docs-viewer-semantic-reference-editor)
- [Docs Semantic References v2 Request](/docs/?scope=studio&doc=site-request-docs-semantic-references-v2)
