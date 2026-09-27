---
draft: false
doc_id: d-20260424-000000-50b63f
title: Docs Viewer
added_date: "2026-04-24 00:00:00"
last_updated: "2026-09-03 21:33:37"
summary: Entry point for using, operating, and changing the shared Docs Viewer reader and its local management and review surfaces.
parent_id: ""

---
# Docs Viewer

Docs Viewer turns Markdown collections into navigable documentation sites. It provides the shared reader used by public routes, the local management route, and validated-package review.

This page is a task router. [Overview](Docs_Viewer_Overview.md) gives the short capabilities and architecture model.

## Use Docs Viewer

- [Docs Import](Docs_Import.md) — turn staged HTML, Markdown, documents, images, and reviewed collections into source docs.
- [Docs Review](Docs_Review.md) — inspect a validated returned package before choosing whether to import it.
- [Export](Export.md) — create a standalone HTML copy from generated local-scope payloads.
- [Media Handling](Media_And_Asset_Handling.md) — understand imported images, attachments, storage, and publication.

## Maintain Docs And Scopes

- [Source Organisation](Source_Organisation.md) — source roots, front matter, hierarchy, and generated ordering.
- [Document Identity](Document_Identity.md) — immutable document codes, date provenance, and create-versus-update rules.
- [Builder](Builder.md) — build and publish generated document and search payloads.
- [Document Diagrams](Document_Diagrams.md) — author, build, publish, edit, and extend scope-owned Mermaid diagrams.
- [Scope Lifecycle](Scope_Lifecycle.md) — create, rename, and delete configured scopes through previewed local-service plans.
- [Testing](Testing.md) — choose the appropriate repository check.

## Change The Architecture

- [Configuration And Extension Points](Configuration_And_Extension_Points.md) — what drives routes, scopes, reports, views, actions, imports, and service availability.
- [Reports](Reports.md) — author, validate, build, project, mount, and extend document report blocks.
- [Report Block Tokens](Report_Block_Tokens.md) — current registered report block tokens.
- [Runtime Architecture](Docs_Viewer_Runtime.md) — public, manage, and review execution paths, authority layers, extension method, and weak spots.
- [Generated Data Contracts](Generated_Data_Contracts.md) — generated payloads, read authority, and publishing.
- [Sub-Scope Public And Manage Manifests](Sub_Scope_Public_And_Manage_Manifests.md) — define sibling generated list projections, document-owned grouping, and the shared report-loading boundary.
- [Runtime Module Ownership](Runtime_Module_Ownership.md) — grouped browser-module owners when a code change needs exact responsibility.
- [Source Tree Ownership](Source_Tree_Ownership.md) — repository-level source, runtime, config, service, and generated-output boundaries.

## Code Authority

Use documentation to find the relevant boundary, then verify exact behaviour in:

- `docs-viewer/config/routes/`, `docs-viewer/config/scopes/`, and `docs-viewer/config/document-packages/` for routes, available features, scopes, package profiles, and output locations
- `docs-viewer/runtime/js/{public,shared}/` for the canonical public entrypoint and shared reader primitives
- `docs-viewer/runtime/js/{management,review,import,reports}/` for route- and report-owned browser code; only the explicit public report loader is projected publicly
- `docs-viewer/static/css/` for canonical shared/public and local-only stylesheets
- `docs-viewer/services/` for local reads, writes, imports, exports, document packages, review, and scope workflows
- `docs-viewer/build/` and `docs-viewer/tests/` for generated contracts and executable evidence

`site/docs-viewer/` is the tracked static deployment projection for the shared/public runtime subset, not code authority. [Run Checks](Run_Checks.md) owns the `bin/site-code-update` handoff sequence.

Prefer code/config search for exact modules, endpoints, fields, and files. Copying those lists into overview pages makes them harder to trust.

## Plan Docs Viewer Work

- [Planned Features](Planned_Features.md) is used for feature, concept, architecture, and delivery model development.
