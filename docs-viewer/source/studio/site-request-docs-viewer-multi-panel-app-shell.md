---
doc_id: site-request-docs-viewer-multi-panel-app-shell
title: Docs Viewer Multi-Panel App Shell Request
added_date: 2026-05-27
last_updated: 2026-05-27
ui_status: draft
parent_id: change-requests
sort_order: 13170
viewable: true
---
# Docs Viewer Multi-Panel App Shell Request

Status:

- proposed

## Summary

Introduce a client-owned multi-panel display model for Docs Viewer.

The target layout supports coordinated index, document, and optional info panels:

- the index panel can collapse, restore, or expand to a wider/full viewer surface
- the document panel can be visible or hidden while document selection remains active
- the info panel can be toggled visible or hidden next to the document panel
- each panel has lightweight toolbar chrome for choosing the active view and showing only allowed panel actions
- panel views are capability-gated so public installs and local manage mode use the same panel system with different available views/actions

This request is a product and architecture slice under [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell).
It should move one visible shell responsibility toward JavaScript ownership without requiring a broad `docs-viewer/runtime/js/docs-viewer.js` refactor first.

## Reason

The current Docs Viewer is effectively a two-panel shell:

- index/sidebar panel
- document panel, which also hosts document, search, recently-added, and report surfaces

Recent index-panel work introduced explicit index panel state, including collapsed, normal, and expanded modes.
That is useful, but the model remains index-specific and projects document visibility as a side effect of index expansion.

Future workflows need a more general display model:

- inspect metadata for the selected document while reading the document
- select a document in the index and show only info, without loading or showing the document body
- collapse the index and work with document plus info panels
- replace the index panel body with alternate index-oriented views
- add public-safe info views such as metadata, plus host-specific reference views when the host supplies that data
- add manage-only local views and actions such as edit metadata, source opening, move/archive/delete, rebuild, or import status

The panel system should become part of the JavaScript app shell rather than another set of hardcoded Liquid or route-specific controls.

## Goals

- support three coordinated panels: index, document, and info
- keep selected document state independent from document panel visibility
- add a shared panel toolbar pattern for active view selection and allowed panel actions
- allow panel content to vary by registered view rather than by hardcoded DOM assumptions
- allow panels to host richer internal or external modules, including future visualization components
- keep public read-only installs such as `/library/` on the same panel architecture
- gate manage-only panel views and actions by route config, management mode, backend capabilities, and selected document state
- keep source writes and local filesystem operations behind named backend endpoints
- advance the JavaScript app-shell direction while preserving current `/docs/`, `/library/`, and `/analysis/` behavior
- avoid a broad `docs-viewer.js` cleanup as a prerequisite

## Non-Goals

- rewriting the full Docs Viewer shell into JavaScript in the first implementation slice
- replacing the Python Docs Viewer backend
- changing generated docs payload schemas just to support panel layout
- making the info panel manage-mode only
- allowing browser JavaScript to write Markdown, source config, or local files directly
- refactoring all document/search/report rendering before panel infrastructure exists
- changing public route URLs or removing current Jekyll route adapters

## Product Model

Docs Viewer should have one shared panel system across public presentation and local editing contexts.

Panel availability and controls should be decided from:

- route config and shell boot context
- current scope
- current route mode, including `mode=manage`
- generated viewer config and feature flags
- backend capability response when a local server is available
- selected document state

The panel itself is not public-only or manage-only.
Individual panel views and actions are capability-gated.

Manage mode is also the preferred incubation surface for new or uncertain panel modules.
Views whose product fit, data contract, dependency cost, or public UX is still unclear can start as manage-only modules.
They should move into public presentation only after their generated-data contract, performance profile, accessibility behavior, and portable-install expectations are clear.

Example info panel views:

| View | Public | Manage mode | Notes |
| --- | --- | --- | --- |
| Metadata | Yes | Yes | Read-only in public; can share render helpers with editable metadata later. |
| References | Repo-specific | Yes | Reads host-provided relationship payloads when available; dotlineform semantic references are not portable Docs Viewer core. |
| Activity | No by default | Yes | Requires generated or backend-provided local activity contract. |
| Edit metadata | No | Yes | Calls management backend endpoints. |
| Source | No | Yes, local only | Can expose open-source actions only when backend capabilities allow it. |

The first info view should be a read-only metadata view for the selected document.
Editable metadata should remain a separate manage-only action or view until the capability and save flow are explicit.

A module should not be promoted to public presentation simply because it is technically read-only.
Promotion should be an explicit decision that the module is useful, stable, performant, accessible, and backed by generated/public-safe data.

## Panel State Model

Panel state should be explicit and projected into DOM attributes for CSS.

Candidate state:

```text
panels:
  index:
    state: collapsed | normal | expanded
    activeView: tree
  document:
    visible: true | false
    activeView: document | search | recent | report
  info:
    visible: true | false
    activeView: metadata
selectedDocId: <doc id>
```

Candidate projection:

```text
root data attributes:
  data-index-panel-state
  data-document-panel-state
  data-info-panel-state
  data-viewer-layout
```

The current index state helper can either become a compatibility wrapper or be replaced by a broader panel-layout module.
The important change is that document visibility should no longer be only a side effect of `indexPanelState`.

2026-05-27 implementation note: the narrow index-panel app-shell slice moved sidebar chrome and DOM projection application into `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, coordinated by `docs-viewer/runtime/js/docs-viewer-app-shell.js`.
It did not introduce the broader multi-panel state model above; `docs-viewer/runtime/js/docs-viewer-index-panel.js` remains the compatibility state/projection helper for collapsed, normal, and expanded index states.

2026-05-27 implementation note: the narrow document-shell app-shell slice moved `.docsViewer__main`, read-only metadata chrome, document content, results status, search/recent result list, and more-results mount into `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`.
It introduced only a compatibility projection helper for the current document/search/recent visibility states and results-status state.
It did not introduce the broader document/info panel state model, panel toolbar model, info panel, or hosted-view architecture.

## Panel Toolbar Model

Each panel should have small shared chrome:

- a view selector for available panel views
- allowed panel controls, rendered as icon buttons
- a stable panel title or accessible label
- optional status or secondary actions where needed

Initial controls:

- index panel: view selector, collapse/restore, direct expand
- document panel: view selector only if document/search/recent/report become explicit choices; otherwise minimal chrome can be deferred
- info panel: view selector and hide/close

The toolbar should render from panel projection rather than hardcoding per-panel button behavior.
It should emit simple intents such as:

```text
panel:view:set
panel:visibility:toggle
panel:index:collapse
panel:index:expand
panel:index:restore
```

The layout controller should validate and apply those intents.

## Panels As Module Hosts

Use a modular hosted-view architecture, not a plugin architecture.

The panel model should treat each panel body as a host for named view modules.
Some modules will be simple first-party Docs Viewer views, such as tree navigation or metadata.
Other future modules may use external libraries for richer displays, such as data visualization, graph browsing, or relationship maps.
That does not mean Docs Viewer is building a plugin system now.

Potential future examples include:

- D3.js-backed charts or relationship diagrams
- Cytoscape.js-backed document/reference graphs
- generated report tables or dashboards
- host-specific relationship or semantic-reference explorers
- scope health or build-status views
- custom downstream project modules in portable Docs Viewer installs

### Current Repo First

The current repo's needs should drive the design.
Panels should facilitate data exchange between the hosted view, the Docs Viewer app, generated repo artifacts, repo-local helper code, and the local Docs Viewer backend where manage mode needs it.
The integration can be manually glued together and tightly coupled where that is the pragmatic choice.

Panel modules are ordinary repo JavaScript modules.
They are not shells, sandboxes, independently installable plugins, or generic adapters.
They are allowed to know about this repo's data shapes when they are repo-specific modules.

For this repo now:

- panels host named view modules
- modules receive explicit app context, such as selected doc, scope, route mode, generated data readers, backend client when available, and view config
- modules may call repo-local helper code directly where that is the pragmatic integration path
- modules may manually import third-party libraries when this repo needs them
- modules own their UI, data shaping, third-party imports, and tight integration logic
- modules are not expected to run in arbitrary host projects

### Third-Party Libraries

The first implementation does not need to choose or integrate D3.js, Cytoscape.js, or any other visualization library.
It should, however, avoid a panel design that blocks such libraries later or assumes every panel view is static HTML or a small local renderer.
Portable Docs Viewer should be able to support optional visualization modules conceptually, but it should not include third-party visualization dependencies or user-facing config for them until a host/module data contract exists.
Host projects are responsible for data supplied to such modules unless Docs Viewer later defines a document-derived data class.
Docs Viewer is not promising that these integrations will be easy.
It should only preserve enough room for repo-specific modules to lazy-load a library, mount it in a stable panel body, exchange data with the app/repo, and clean it up.

### Portability And Extraction

The modular boundary should make future portable packaging easier without designing a plugin architecture now.

For future portability:

- keep modules in clear folders
- keep registration explicit
- control module availability through generated route/config data
- make absence graceful: if a module folder or config entry is missing, omit the related view/action rather than failing route boot
- avoid hardcoded dotlineform assumptions in the core panel host
- keep dotlineform-only behavior in dotlineform-specific modules

For example, the semantic Markdown editor can live in one source-editor module folder and be included only in this repo:

```text
docs-viewer/runtime/js/modules/source-editor/
```

Portable installs can omit that folder or leave the module unregistered.
Docs Viewer core should then simply not present the source editor as a built-in feature.

### Future Plugin Architecture

Do not design a plugin architecture in this request.

Avoid adding:

- adapter layers
- package manifests
- sandbox protocols
- marketplace assumptions
- generic data APIs
- automatic third-party asset bundling

Also avoid choices that would make a plugin system difficult later, such as:

- global DOM mutations
- untracked lifecycle cleanup
- hidden dependencies on one route
- core code directly importing every optional module

The practical contract is:

- core Docs Viewer owns panel regions, view selection, lifecycle, access gating, and explicit module registration
- repo-specific modules own their UI, data exchange, data shaping, third-party imports, and integration logic

### Minimal Lifecycle

Panel-hosted modules should still have a simple lifecycle:

```text
register -> mount -> update -> unmount -> dispose
```

Candidate lightweight view-module shape:

```text
id
label
access: public | manage | manage-local
panel: index | document | info
load()
mount(container, context)
update(context)
unmount()
dispose()
```

The panel host should provide:

- a stable container element
- selected document and scope context
- generated data access helpers
- backend client when the current route/mode supports it
- route/history helpers where appropriate
- capability and route-mode information
- cleanup calls when the active view changes

External-library modules should be lazy-loaded only when their view is selected or otherwise needed.
They should not add route-wide boot cost for public installs that never use them.

CSS and DOM ownership also need a clear boundary.
Panel modules should render inside their assigned container and should not mutate unrelated panel chrome, route controls, or global document structure.
If a library needs dedicated styles, those styles should be scoped to the module or loaded through an explicit module asset contract.

## Client And Backend Boundary

This request should keep the work as client-side as practical within the current architecture.

JavaScript should own:

- panel state and persistence
- layout projection
- panel toolbar rendering
- view registration and view selection
- panel module lifecycle and cleanup
- public-safe metadata rendering from generated doc rows and payloads
- manage-only view/action registration after capability checks

Generated data and config should own:

- docs index rows
- per-document rendered payloads
- search indexes
- host-specific relationship payloads when a host integration supplies them
- UI text
- scope and feature configuration

The backend should own:

- source Markdown writes
- metadata saves
- move/archive/delete/import workflows
- source opening
- generated payload rebuilds
- filesystem allowlists and validation

Public routes should not load or expose management-only modules unless management is enabled.
Backend endpoints must still enforce capability server-side even when client controls are hidden.

## Relationship To `docs-viewer.js`

The multi-panel work should not wait for a broad `docs-viewer/runtime/js/docs-viewer.js` refactor.

The preferred implementation is:

- add focused modules for panel state, projection, toolbar rendering, and info-panel views
- keep `docs-viewer.js` as the orchestration adapter for boot context, DOM refs, existing controllers, and event handoff
- touch `docs-viewer.js` only to initialize the panel controller, pass callbacks, and respond to panel intents
- avoid moving unrelated route, management, search, bookmark, or payload-loading behavior in the same slice

This follows the existing JavaScript inventory guidance: `docs-viewer.js` is high-risk shared runtime code, but useful future slices should reduce coupling through focused owners rather than by turning the entry module into an opaque pass-through.

If panel wiring reveals a genuinely blocking coupling in `docs-viewer.js`, address that coupling as a narrow enabling extraction with focused tests.
Do not start with a broad cleanup.

## Proposed Module Boundaries

Candidate new modules:

- `docs-viewer/runtime/js/docs-viewer-panels.js` for pure panel state, persistence keys, transitions, and layout projection
- `docs-viewer/runtime/js/docs-viewer-panel-toolbar.js` for shared toolbar rendering and intent dispatch
- `docs-viewer/runtime/js/docs-viewer-info-panel.js` for info panel orchestration
- `docs-viewer/runtime/js/docs-viewer-info-metadata-view.js` for read-only selected-document metadata rendering

Repo-specific optional modules can live under clearly named folders, for example:

- `docs-viewer/runtime/js/modules/source-editor/`

Docs Viewer core should discover or register only the modules available for the current install/config.
If a module folder is absent or disabled, core should degrade by omitting its view/action rather than failing route boot.

Existing modules should keep their current ownership where possible:

- `docs-viewer/runtime/js/docs-viewer-sidebar.js` remains the tree renderer inside the index panel body
- `docs-viewer/runtime/js/docs-viewer-document-controller.js` remains document payload rendering and document/search/recent pane behavior until document panel views are explicitly extracted
- management modules remain lazy-loaded and management-gated

## Proposed Implementation Steps

### 1. Define Panel State And Projection

Tasks:

- create a pure panel state/projection module
- model index, document, and info panel states
- preserve existing index collapse/expand behavior
- keep existing legacy sidebar storage migration if needed
- add module-level smoke coverage for transitions and projections

Acceptance:

- current index panel behavior can be represented by the new projection
- document panel visibility can be controlled independently from selected document state
- mobile unavailable states still normalize to a stable stacked layout

### 2. Add Panel Shell Mount Points

Tasks:

- add stable panel containers for index, document, and info
- separate panel toolbar/chrome from panel body
- keep Liquid markup minimal and compatible with current boot behavior
- add CSS data-attribute hooks for panel combinations

Acceptance:

- current two-panel layout remains visually equivalent when info panel is hidden
- index expanded/collapsed behavior remains intact
- public routes still render without management dependencies

### 3. Add Shared Panel Toolbar Rendering

Tasks:

- render panel view selectors and allowed icon controls from projection
- wire index collapse/restore/expand through panel intents
- add info hide/show intent
- source toolbar labels and visible copy from UI text/config where appropriate

Acceptance:

- toolbar controls are stable across index, document, and info panels
- controls appear only when allowed by projection
- keyboard focus and accessible labels remain usable

### 4. Add Read-Only Info Metadata View

Tasks:

- register an info panel `metadata` view
- render selected document title, doc id, parent/path, summary, dates, status/viewability metadata, and scope where available
- update metadata view when index selection or route doc changes
- allow info panel to remain visible when document panel is hidden

Acceptance:

- `/library/` can show the info metadata view without management mode
- `/docs/?mode=manage` can show the same read-only metadata view before edit actions are added
- selecting a different index entry updates the info panel

### 5. Gate Manage-Only Views And Actions

Tasks:

- define access metadata for panel views/actions, such as public, manage, and manage-local
- register management-only views/actions only when route and backend capabilities allow them
- keep editing flows behind existing or new named management endpoints
- verify public routes do not lazy-load management-only modules
- treat experimental, operational, or dependency-heavy panel modules as manage-only until promoted explicitly

Acceptance:

- public routes show only public-safe panel views/actions
- manage mode shows additional controls only after capability checks
- backend write boundaries remain unchanged
- manage-only panel modules can be developed without committing their UI or data contract to public installs

### 6. Document And Verify The App-Shell Slice

Tasks:

- update Docs Viewer overview/runtime docs after implementation
- update JavaScript inventory notes if module ownership changes material risk
- add focused route smoke tests for panel combinations
- add public and manage-mode checks

Acceptance:

- docs describe the shared panel model and public/manage split
- smoke tests cover index/document/info, collapsed index plus document/info, info-only with selected doc, and public route behavior
- generated docs payloads are rebuilt only as part of the normal docs build workflow

## Open Questions

- Should panel layout state be URL-addressable, localStorage-only, or split between shareable route state and local preference?
- Should document/search/recent/report become explicit document panel views in the first slice or remain inside the existing document controller until later?
- What is the best initial toolbar view selector: buttons, select menu, segmented control, or compact menu?
- Should info panel visibility persist per scope, per route, or globally across Docs Viewer installs?
- How much metadata should come from the index row versus the loaded document payload?
- Should selecting a document while document panel is hidden load the payload in the background or wait until document panel is shown?

## Risks

- adding panel coordination directly to `docs-viewer.js` would increase the highest-risk runtime file
- public and management contexts could drift if panel views are registered through separate code paths
- layout combinations could become fragile on mobile if CSS is only designed for desktop
- hiding document content while preserving selected document state could expose assumptions in document, search, bookmark, and management rendering
- management-only controls could leak into public routes if capability checks are only visual
- external visualization libraries could add large boot cost or leak DOM/CSS behavior outside their panel host if loaded without a module lifecycle boundary

Mitigations:

- keep panel state and projection in pure modules with focused tests
- use one shared panel registration path with access gating
- lazy-load heavier panel modules and external libraries only when selected
- require panel modules to mount, update, unmount, and dispose inside their assigned container
- incubate uncertain modules in manage mode before exposing them in public presentation
- verify both public and manage-mode routes
- keep backend enforcement independent from client visibility
- avoid changing generated payload schema in the first slice
- leave `docs-viewer.js` as adapter/orchestration code only

## Verification

Suggested checks for implementation slices:

```bash
$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_index_panel_modules.py --site-root .
$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_index_panel_route.py --site-root /tmp/dlf-jekyll-build
```

Add new focused checks for:

- panel projection helper contracts
- info metadata rendering from fixture docs
- public route panel availability
- manage-mode capability-gated controls
- desktop and mobile panel layout screenshots or DOM geometry checks

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory)
- [Docs Viewer JavaScript App Shell Request](/docs/?scope=studio&doc=site-request-docs-viewer-javascript-app-shell)
- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
