---
doc_id: docs-viewer
title: "Docs Viewer"
last_updated: 2026-04-19
parent_id: ""
sort_order: 170
---
# Docs Viewer

The Docs Viewer is the shared documentation module used by the site's docs-domain routes.

It currently serves these scopes:

- Studio docs at `/docs/`
- Library docs at `/library/`

The current implementation uses:

- scope-specific route shells to define the route, scope, and generated data URLs
- one shared shell include in `_includes/docs_viewer_shell.html`
- one shared runtime in `assets/js/docs-viewer.js`
- scope-owned generated docs data under `assets/data/docs/scopes/<scope>/`

This section documents the current Docs Viewer implementation as a common module.
It explains how the shared viewer serves multiple scopes, how the current viewer behaves, and how source docs are organised.
Management-mode planning for local write behavior is tracked separately.

This section does not document:

- detailed payload schemas for generated docs JSON
- build-script usage and flags

Those boundaries are intentional:

- build mechanics belong in [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
- shared shell and route placement are also referenced in [Site Shell Runtime](/docs/?scope=studio&doc=site-shell-runtime)

## Documents

- [Overview](/docs/?scope=studio&doc=docs-viewer-overview) explains the shared route-shell, include, runtime, and URL/state model.
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation) explains the current source roots and how docs trees are organised by `parent_id` and `sort_order`.
- [Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) records when scope differences should stay in shells or data and when a true runtime fork would be justified.
- [Docs Viewer Favourites Spec](/docs/?scope=studio&doc=ui-request-docs-viewer-favourites-spec) captures the current shared bookmark/favourites request for `/docs/` and `/library/`.
- [Docs Viewer Favourites Task](/docs/?scope=studio&doc=ui-request-docs-viewer-favourites-task) breaks that request into implementation work.
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management) records the planned management-mode contract for local create/archive/delete operations and the required source-flattening prerequisite.
