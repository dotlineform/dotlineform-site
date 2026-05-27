---
doc_id: docs-viewer
title: Docs Viewer
added_date: 2026-04-24
last_updated: 2026-05-27
parent_id: ""
sort_order: 5000
viewable: true
---
# Docs Viewer

The Docs Viewer is the shared documentation module used by the site's docs-domain routes.

It currently serves these scopes:

- Studio docs at `/docs/`
- Library docs at `/library/`
- Analysis docs at `/analysis/`

The current implementation uses:

- scope-specific route shells to define the route, scope, and generated data URLs
- one shared shell include in `_includes/docs_viewer_shell.html`, with minimal public route adapters where read-only Jekyll routes need them
- a standalone manage shell template in `docs-viewer/shell/docs-viewer-shell.html`, served by `docs-viewer/services/docs_viewer_service.py`
- a browser-safe route-config registry in `docs-viewer/config/routes/docs-viewer-routes.json`, with route shells carrying only route id and route-config URL as boot context
- one shared runtime entry module in `docs-viewer/runtime/js/docs-viewer.js`
- app-shell-owned route config, access projection, shell refs, header, index panel shell, document shell, info panel shell, view-state skeleton, selected-document hosted-view context, compatibility panel projection, hosted-view registration, info-panel hosted-view lifecycle, and management action coordination in `docs-viewer/runtime/js/docs-viewer-app-shell.js`, `docs-viewer/runtime/js/docs-viewer-app-context.js`, `docs-viewer/runtime/js/docs-viewer-route-config.js`, `docs-viewer/runtime/js/docs-viewer-access.js`, `docs-viewer/runtime/js/docs-viewer-view-state.js`, `docs-viewer/runtime/js/docs-viewer-view-context.js`, `docs-viewer/runtime/js/docs-viewer-panel-layout.js`, `docs-viewer/runtime/js/docs-viewer-hosted-views.js`, and `docs-viewer/runtime/js/docs-viewer-info-panel-host.js`, with header controls rendered by `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`, index panel chrome rendered by `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, document shell chrome rendered by `docs-viewer/runtime/js/docs-viewer-document-shell-renderer.js`, info panel chrome rendered by `docs-viewer/runtime/js/docs-viewer-info-panel-renderer.js`, read-only metadata info rendered by `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js`, and management-only action markup rendered by `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`
- document pane, payload rendering, and report mount handoff in `docs-viewer/runtime/js/docs-viewer-document-controller.js`
- pure tree and visibility helpers in `docs-viewer/runtime/js/docs-viewer-tree.js`
- pure inline-search and recently-added helpers in `docs-viewer/runtime/js/docs-viewer-search.js`
- bookmark record and storage helpers in `docs-viewer/runtime/js/docs-viewer-favourites.js`
- browser-visible report metadata in `assets/data/docs/reports.json`
- report module allowlist and access checks in `docs-viewer/runtime/js/docs-viewer-reports.js`
- report modules under `docs-viewer/runtime/js/reports/`
- generated semantic-reference artifacts under `assets/data/docs/scopes/<scope>/references/`
- browser-safe Docs Viewer settings in `docs-viewer/config/defaults/docs-viewer-config.json`, projected from `docs-viewer/config/scopes/docs_scopes.json`
- public read-only Docs Viewer config source in `docs-viewer/config/defaults/docs-viewer-public-config.json`
- browser-safe Docs Viewer route records in `docs-viewer/config/routes/docs-viewer-routes.json`
- Docs Viewer UI text in `docs-viewer/config/ui-text/ui-text.json`
- Docs Viewer base CSS in `docs-viewer/static/css/docs-viewer-base.css`
- reusable Docs Viewer CSS in `docs-viewer/static/css/docs-viewer.css` and `docs-viewer/static/css/docs-viewer-reports.css`
- scope-owned generated docs data under `assets/data/docs/scopes/<scope>/`
- a management-only stylesheet in `docs-viewer/static/css/docs-viewer-management.css`, loaded only by management-enabled shells
- a standalone service runner at `docs-viewer/bin/docs-viewer`, using `var/local/site.env` for the static local Docs Viewer host, port, base URL, and capability flags

Public viewer routes are read-only:

- `/library/` loads the Library scope directly and does not expose `?mode=manage`
- `/analysis/` loads the Analysis scope directly and does not expose `?mode=manage`
- `/docs/` is the local management shell served by the standalone Docs Viewer service and can load `studio`, `library`, or `analysis` through its `scope` query parameter

The CSS base contract is explicit.
Public `/library/` and `/analysis/` intentionally inherit `assets/css/main.css` from the public site layout so generated docs content keeps host prose and media styling.
The shared Docs Viewer include also loads `docs-viewer/static/css/docs-viewer-base.css`, which supplies Docs Viewer-owned tokens and small utilities required by the viewer shell.
Standalone/local Docs Viewer shells can opt into the base page layer with a Docs Viewer shell body class instead of depending on Studio CSS or dotlineform public `main.css`.

This section documents the current Docs Viewer implementation as a common module.
It explains how the shared viewer serves multiple scopes, how the current viewer behaves, and how source docs are organised.
Management-mode planning for local write behavior is tracked separately.

This section does not document:

- detailed payload schemas for generated docs JSON
- build-script usage and flags

Those boundaries are intentional:

- build mechanics belong in [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- shared shell and route placement are also referenced in [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)
- repo-level ownership is maintained in [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership)

## Documents

- [Overview](/docs/?scope=studio&doc=docs-viewer-overview) explains the shared route-shell, include, runtime, and URL/state model.
- [Reports](/docs/?scope=studio&doc=docs-viewer-reports) describes the report component purpose, source metadata, JSON registry, and report module allowlist.
- [Semantic References](/docs/?scope=studio&doc=docs-viewer-semantic-references) is the management report for generated semantic-reference targets and source docs.
- [Docs Viewer Report Components Request](/docs/?scope=studio&doc=site-request-docs-viewer-report-components) records the report component design and first Library Documents use case.
- [Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) records what currently needs copying into another Jekyll project and how to add a Library-style scope with a management route and read-only route.
- [Dependencies](/docs/?scope=studio&doc=docs-viewer-dependencies) records the Docs Viewer Python dependency boundary, the Docs HTML import parser/sanitizer stack, and the role of `requirements.txt`.
- [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling) records Docs Viewer media path conventions, import staging, standalone media imports, inline raster extraction, SVG handling, and media-copy handoff behavior.
- [New Scopes Builder](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder) records the technical design, route-creation model, publishing choices, and implementation notes for the local New scope workflow.
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation) explains the current source roots and how docs trees are organised by `parent_id` and `sort_order`.
- [Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) records when scope differences should stay in shells or data and when a true runtime fork would be justified.
- [JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) tracks the Docs Viewer-specific browser JavaScript risk scores, priorities, and follow-up tasks.
- [Viewability Workflow Spec](/docs/?scope=studio&doc=docs-viewer-draft-publishing-spec) records the `viewable: true | false` visibility workflow.
- [Import Source Registry Spec](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec) documents staged source-format dispatch, preview payloads, media planning, and service write boundaries for Docs Import.
- [Docs Viewer Favourites Spec](/docs/?scope=studio&doc=ui-request-docs-viewer-favourites-spec) captures the current shared bookmark/favourites request for `/docs/` and `/library/`.
- [Docs Viewer Favourites Task](/docs/?scope=studio&doc=ui-request-docs-viewer-favourites-task) breaks that request into implementation work.
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management) records the management-mode contract for local create/archive/delete, structure edits, and draft viewability operations.
- [Documents Package Preparation Script](/docs/?scope=studio&doc=scripts-docs-export) documents the `docs_export.py` engine used by the documents Data Sharing adapter.
- [Documents Returned Package Script](/docs/?scope=studio&doc=scripts-docs-import) documents the `docs_import.py` parser and Markdown review renderer used by the documents Data Sharing adapter.
