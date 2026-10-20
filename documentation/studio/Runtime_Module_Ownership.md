---
draft: false
doc_id: d-20260605-125108-1d1ef3
title: Runtime Module Ownership
added_date: 2026-06-05 12:51:08
last_updated: "2026-10-20"
summary: Grouped browser-code owners and a practical trace order for Docs Viewer runtime changes.
parent_id: d-20260331-000000-c313fd
---
# Docs Viewer Runtime Module Ownership

This is a grouped code map for [Docs Viewer Runtime](Docs_Viewer_Runtime.md). It identifies stable responsibility areas without maintaining a row for every JavaScript file.

## Entrypoints Define The Surface

- public: `docs-viewer/runtime/js/public/docs-viewer-public.js`
- manage: `docs-viewer/runtime/js/management/docs-viewer-manage.js`
- review: `docs-viewer/runtime/js/review/docs-viewer-review.js`

Each entrypoint contributes the providers, hosted views, controls, and shell pieces allowed on that surface. Public safety is an import-graph property, not a filename or a hidden-control convention.

## Shared Reader Owners

Shared browser code lives under `docs-viewer/runtime/js/shared/`.

| Area | Start here | Owns |
| --- | --- | --- |
| boot and composition | `docs-viewer-app-boot.js`, `docs-viewer-app-composition.js`, `docs-viewer-app-session.js` | startup context, providers/services, state domains, hosted-view registration, and startup order |
| private coordination | `docs-viewer-app-runtime.js` | focused controller wiring and the small returned app handle |
| routes | `docs-viewer-route-workflow.js`, `docs-viewer-router.js` | URL/query resolution, history, index/document loading orchestration, and route application |
| route and access policy | `docs-viewer-app-context.js`, `docs-viewer-route-config.js`, `docs-viewer-route-features.js`, `docs-viewer-access.js` | app kind, browser-safe route records, feature allowlisting, and visibility/composition projection |
| data and services | `docs-viewer-configured-scope-provider.js`, `docs-viewer-generated-data-runtime.js`, `docs-viewer-service-context.js` | collection reads and independent config/generated/source/management service surfaces |
| document state | `docs-viewer-document-index-state.js`, `docs-viewer-document-controller.js` | visibility/loadability, selection, payload states, and rendered-document transitions |
| views and panels | `docs-viewer-document-view-coordinator.js`, `docs-viewer-main-view-host.js`, `docs-viewer-info-panel-host.js`, `docs-viewer-view-registry.js` | hosted-view lifecycle, active mode/control projection, and panel composition |
| navigation and discovery | `docs-viewer-sidebar.js`, `docs-viewer-tree.js`, `docs-viewer-search-controller.js` | tree navigation and search/recent state |

Search the shared directory for the exact current helper set. The table should change only when responsibility moves between areas.

Public safety alone does not establish shared placement. A browser module with only a local composer remains under its local application owner even when it has no management authority. A later named public adopter promotes the one canonical implementation into the appropriate canonical public/shared directory and adds it to the explicit site-code manifest without leaving a duplicate or compatibility path.

## Public Deployment Projection

Local Manage and Review serve canonical runtime and stylesheets directly from `docs-viewer/`. Public preview and GitHub Pages serve the manifest-selected subset under the unchanged `/docs-viewer/...` URLs from tracked `site/docs-viewer/`. `site-tools/config/site-code-update.json` is the sole maintained inventory, and `bin/site-code-update` is its only producer. The projection is a deployment artifact, not a second code owner or local fallback.

When represented canonical code changes, run `bin/site-code-update`, inspect the exact tracked delta, then run `bin/site-code-update --check` and `bin/site-validate`. Change the manifest explicitly for an inventory or public-status change; do not include local-only siblings merely because they share a source directory.

## Local Report Owners

Local report implementations and their current local-only presentation capability live under `docs-viewer/runtime/js/reports/`.

- `docs-viewer-reports.js` owns local report metadata resolution, executable loading, mount-result handling, and optional presentation registration.
- `docs-viewer-report-presentation.js` owns exact live-report expansion registration, target validation, rehosting, restoration, and release. It has no management or service authority, but only Manage currently composes it, so possible future public reuse does not place it in the public artifact.
- focused report modules own their data reads, semantic structure, filtering, sorting, report actions, and optional presentation handle.

## Manage Owners

Manage-only browser code lives under `docs-viewer/runtime/js/management/`.

- `docs-viewer-management.js` coordinates capabilities and focused management controllers.
- `docs-viewer-management-context-actions.js` owns exact targets, disabled-state projection and dispatch for New in Actions and VS Code, Draft/Ready and Star in Edit. It consumes the exact displayed ordinary target or validated collection action context; it never infers a subdocument from a route. The shared collection report owns committed draft projection and refresh/open after creation. Workspace actions remain under their existing workflow owners.
- `docs-viewer-management-edit-menu.js` owns the stable Edit dropdown, Source editor dispatch, ordinary Copy link/Delete dispatch and disabled fallback items. Collection detail contributions retain their exact registrations, async state and existing Copy/Delete/Subject/Finder handlers; their retained action host mounts inside Edit rather than a second toolbar. The shared main-view runtime keeps this host connected in its hidden collection-action mount during Source and expanded views. The menu never infers a detail from a route or substitutes its collection host.
- `source-editor/directive-actions.js` owns Source's flat action menu, disclosure, keyboard navigation and captured adapter/selection. It calls existing Catalogue/document-link modal owners and the Source adapter's staged-media operation; VS Code reuses the existing management source-opening workflow with the adapter's immutable target. Source mode contributes only Return, Save and Directives to `main-view`. The former standalone insertion-control wrappers, definitions and image/file dispatch events are retired.
- `docs-viewer-runtime-lazy-controller.js` is the neutral shared-side lazy boundary that prevents public startup from importing management orchestration.
- `docs-viewer-action-definitions.js` owns action ids and workspace/collection/collection-selection/document/active-document/document-subtree target policy. It does not own handlers, placement, or mutations. Management resolves a subtree from an explicit ordinary row target and the complete loaded hierarchy without changing the displayed document.
- `docs-viewer-management-index-controller.js` owns Index Delete, Position and Sort Children dispatch plus Recent exclusions. The Index has no import, Export or Prepare package bridge, checkbox selection or selection commands. `docs-viewer-collection-selection.js` and the default collection contribution own checked targets; Collection Actions supplies Export/Prepare package with those exact IDs and both imports with the explicit collection, including empty lists.
- `packages/document-package-prepare-model.js` owns pure Prepare profile, format, checked-ID summary/limit filtering and request composition. `packages/document-package-prepare-workflow.js` owns the single collection modal and result projection; `docs-viewer-management-document-reports.js` owns its lazy bridge. `packages/document-package-client.js` owns `/docs/packages/*` transport; Python requires a configured collection and owns selected-source reads, rendering and package writes without ordinary Index traversal.
- `docs-viewer-management-import-controller.js` owns the shared Import docs modal, frozen invoking collection, lazy lifecycle, busy projection and terminal handoff. `docs-viewer-import-doc-workflow.js` owns synchronous native single-file selection and confirmation. Collection menu callbacks invoke both through `docs-viewer-management.js`; the shared runtime only forwards these callbacks and imports no management module. `docs-viewer-management-import-result.js` validates exact result routes, while committed records and terminal completion update retained collection views. Workspace dispatch, ordinary displayed-context/sibling placement and `?import=1` startup are removed.
- `docs-viewer/runtime/js/import/` owns candidate validation and presentation,
  ordinary or collection dispatch, confirmation, selected-row Docs Review
  handoff, and explicit result links. It does not classify staging files or
  infer package targets.
- focused controllers own metadata, settings, scope lifecycle, interactions,
  modal composition, reports, and source editing.
- `docs-viewer-management-client.js` owns management transport helpers; server endpoints remain authoritative.

When a manage workflow grows, extract a complete workflow boundary rather than adding more bridge callbacks to the main coordinator.

## Review Owners

Review-only browser code lives under `docs-viewer/runtime/js/review/`. The
returned-package provider adapts validated package reads to the shared reader.
Review controllers own package selection, inventory/repair UI, canonical
comparison, Build, and exact package-source opening. They do not initiate or
apply Import.

Python review services under `docs-viewer/services/` own package containment, trusted metadata, retained generated reads, browser-read-only route authorization, and the exact package-source handoff to VS Code.

## Trace A Change

Follow this order when behaviour is surprising:

1. entrypoint import and app kind
2. route record and feature allowlist
3. code registry or hosted-view contribution
4. provider and named service context
5. live capability response
6. focused controller or workflow
7. server endpoint validation

This is more reliable than looking for a single global capability switch.

## Non-Negotiable Boundaries

- shared helpers do not import route entrypoints or manage/review owners
- public modules do not reach local service clients or management workflows
- route config selects known code; it does not register executable behaviour
- service URLs and visible controls do not grant authority
- views attach through hosted-view/panel lifecycle rather than modifying route-shell markup
- the server validates every source or management operation again

Executable evidence lives in `docs-viewer/tests/python/test_docs_viewer_public_runtime_boundaries.py` and the focused runtime/service tests. Use code search for module-level ownership; do not recreate a manual JavaScript inventory.
