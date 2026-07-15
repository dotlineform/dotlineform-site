---
doc_id: docs-viewer
title: Docs Viewer
added_date: 2026-04-24
last_updated: 2026-07-15
summary: Entry point for using, operating, and changing the shared Docs Viewer reader and its local management and review surfaces.
parent_id: ""
viewable: true
---
# Docs Viewer

Docs Viewer turns Markdown collections into navigable documentation sites. It provides the shared reader used by public routes, the local management route, and validated-package review.

This page is a task router. [Overview](/docs/?scope=studio&doc=docs-viewer-overview) gives the short capabilities and architecture model.

## Use Docs Viewer

- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import) — turn staged HTML, Markdown, documents, images, and reviewed collections into source docs.
- [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) — inspect a validated returned package before choosing whether to import it.
- [Export](/docs/?scope=studio&doc=docs-viewer-export) — create a standalone HTML copy from generated local-scope payloads.
- [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling) — understand imported images, attachments, storage, and publication.

## Maintain Docs And Scopes

- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation) — source roots, front matter, hierarchy, and generated ordering.
- [Builder](/docs/?scope=studio&doc=scripts-docs-builder) — build and publish generated document and search payloads.
- [Scope Lifecycle](/docs/?scope=studio&doc=docs-viewer-new-scopes-builder) — create, rename, and delete configured scopes through previewed local-service plans.
- [Portability Snapshot](/docs/?scope=studio&doc=docs-viewer-portable-setup) — inactive record of earlier portability thinking; revisit only if it becomes real work.
- [Testing](/docs/?scope=studio&doc=testing) — choose the appropriate repository check.

## Change The Architecture

- [Configuration And Extension Points](/docs/?scope=studio&doc=config-docs-viewer) — what drives routes, scopes, reports, views, actions, imports, and service availability.
- [Runtime Architecture](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) — public, manage, and review execution paths, authority layers, extension method, and weak spots.
- [Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts) — generated payloads, read authority, and publishing.
- [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) — grouped browser-module owners when a code change needs exact responsibility.
- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) — repository-level source, runtime, config, service, and generated-output boundaries.

## Code Authority

Use documentation to find the relevant boundary, then verify exact behaviour in:

- `docs-viewer/config/routes/` and `docs-viewer/config/scopes/` for routes, available features, scopes, and output locations
- `site/docs-viewer/runtime/js/shared/` for public-safe reader primitives
- `docs-viewer/runtime/js/` for manage-, review-, import-, and report-owned browser code
- `docs-viewer/services/` for local reads, writes, imports, exports, review, and scope workflows
- `docs-viewer/build/` and `docs-viewer/tests/` for generated contracts and executable evidence

Prefer code/config search for exact modules, endpoints, fields, and files. Copying those lists into overview pages makes them harder to trust.

## Plan Docs Viewer Work

- [Docs Viewer Roadmap](/docs/?scope=studio&doc=docs-viewer-roadmap) — current importance, dependencies, features, and finishable outcomes.
- [Roadmap](/docs/?scope=studio&doc=roadmap) — the shared app-roadmap, feature, concept, architecture, and delivery model.
