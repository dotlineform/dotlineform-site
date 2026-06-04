---
doc_id: site-request-docs-viewer-public-manage-entrypoints-baseline
title: Docs Viewer Public/Manage Entrypoint Baseline Inventory
added_date: 2026-06-04
last_updated: 2026-06-04
ui_status: draft
parent_id: site-request-docs-viewer-public-manage-entrypoints
viewable: true
---
# Docs Viewer Public/Manage Entrypoint Baseline Inventory

Status:

- draft

## Purpose

This child document is the baseline inventory for [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints).

It should be filled before implementation starts.
The inventory is not a one-off audit; later tasks consume its named sections when defining entrypoints, shell renderers, CSS/UI-text splits, report gating, nav/tree payloads, tests, and compatibility cleanup.

## Inventory Sections

### Current Public Route Loads

Record the current network/import loads for public Docs Viewer routes, at minimum:

- `/library/`
- `/analysis/`

Include:

- entrypoint JavaScript
- static and dynamic JavaScript module imports
- CSS files
- route config
- Docs Viewer config
- UI text
- report registry loads
- generated docs index and by-id payloads
- generated search payloads

Consumed by parent tasks:

- task 3: target public/manage import graphs
- task 6: public/manage UI text split
- task 7: public/manage CSS split
- task 8: report runtime and registry gating
- task 15: public-route absence tests

### Current Manage Route Loads

Record the current network/import loads for the local `/docs/` manage route.

Include:

- entrypoint JavaScript
- static and dynamic JavaScript module imports
- CSS files
- route config
- Docs Viewer config
- UI text
- report registry loads
- generated docs and search payloads
- local generated-read service requests
- management service capability checks
- management service requests triggered during route boot

Consumed by parent tasks:

- task 3: target public/manage import graphs
- task 5: manage shell path
- task 16: manage-route smoke coverage

### Current Shared Static Import Graph

Record the static import graph rooted at the current shared entrypoint.

Classify modules as:

- public-safe shared primitive
- public app-owned
- manage app-owned
- report-owned
- source-editor/import/scope-lifecycle/settings/status-owned
- unclear or mixed responsibility

Consumed by parent tasks:

- task 3: target public/manage import graphs
- task 10: shared core boundary
- task 11: public/manage mode switch and manage capability switch cleanup
- task 13: nav/tree renderer and payload adapter placement

### Current JSON Config And Data Loads

Record JSON artifacts loaded by public and manage contexts.

Include:

- route config
- Docs Viewer config
- UI text
- report registry
- public docs indexes
- public by-id payloads
- public search indexes
- local/manage generated docs indexes
- local/manage generated search indexes
- generated references payloads if loaded by current route behavior

Consumed by parent tasks:

- task 6: UI text split
- task 8: report registry gating
- task 12: compatibility and fallback cleanup in boot/config/data surfaces
- task 13: public/manage nav/tree payload design
- task 14: public index slimming coordination

### Current CSS Loads And Selectors

Record current Docs Viewer CSS files and the selector groups they contain.

Classify selector groups as:

- public reader shell
- public index/main/info/search
- report
- management shell
- management actions/modals
- source editor/import/scope lifecycle/settings/status
- host public-site CSS outside Docs Viewer ownership

Consumed by parent tasks:

- task 7: public/manage CSS split
- task 9: public DOM cleanup for hidden manage controls
- task 15: public-route CSS absence tests

### Current Public DOM Controls

Record public-route DOM controls and hidden controls after boot.

Include:

- header controls
- index panel controls
- main-view toolbar controls
- info panel controls
- management toolbar hosts
- hidden edit/source/status/import/settings/scope lifecycle controls

Consumed by parent tasks:

- task 4: public shell renderer/path
- task 9: removal of public hidden manage DOM
- task 15: public-route DOM absence tests

### Current Manage DOM Controls

Record manage-route DOM controls and management-only hosts after boot.

Include:

- management toolbar
- action/menu/modal hosts
- main-view management controls
- source editor entry points
- import hosts
- settings controls
- status/viewability controls
- context menu and drag/drop surfaces

Consumed by parent tasks:

- task 5: manage shell renderer/path
- task 16: manage-route smoke coverage

### Current Fallback And Compatibility Paths

Record any compatibility aliases, legacy route/config field fallbacks, broad shared-entrypoint aliases, fallback data paths, or silent unavailable-data behavior found during the inventory.

For each item, record:

- owner file
- behavior
- whether it affects public, manage, or both
- removal target
- reason it cannot be removed immediately, if any
- verification required after removal

Consumed by parent tasks:

- task 11: shared module mode/capability cleanup where relevant
- task 12: compatibility and silent fallback cleanup

### Current Index Tree Construction

Record how public and manage index trees are currently derived.

Include:

- flat payloads used
- browser-time grouping/sorting/filtering
- build-time fields already available
- public fields needed for reader navigation
- manage fields needed for context menu, drag/drop, status indicators, viewability, source/metadata actions, or other manage-owned behavior
- fields that need confirmation before entering a manage nav/tree payload

Consumed by parent tasks:

- task 13: public/manage nav/tree payloads and payload-agnostic tree renderer
- task 14: public index slimming coordination

## Output Requirements

The completed baseline should make later slices traceable.

Each parent task that depends on the baseline should cite the relevant section name and summarize what decision it took from the inventory.
If a section is incomplete, the dependent task should not guess; it should either finish the section first or record a blocker.

Do not use compatibility fallbacks to compensate for unknown inventory state.
