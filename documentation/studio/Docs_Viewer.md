---
draft: false
doc_id: d-20260424-000000-50b63f
title: Docs Viewer
added_date: "2026-04-24 00:00:00"
last_updated: "2026-11-18"
summary: Entry point for using, operating, and changing the shared Docs Viewer reader and its local management and review surfaces.
parent_id: ""

---
# Docs Viewer

Docs Viewer provides the shared reader for the public site at `/`, local authoring and publication from Working at `/docs/`, and read-only review of validated returned packages at `/docs-review/`. Start with [How the site fits together](../guide/How_The_Site_Fits_Together.md) and [Publish and deploy](../guide/Publish_And_Deploy.md) for the workflow. [Docs Viewer Runtime](Docs_Viewer_Runtime.md#three-surfaces) explains how each route gets its data and capabilities.

## Use Docs Viewer

- [Docs Import](Docs_Import.md) — turn staged HTML, Markdown, documents, images, and reviewed collections into source docs.
- [Docs Review](Docs_Review.md) — inspect a validated returned package before choosing whether to import it.
- [Export](Export.md) — create a standalone HTML copy of selected collection documents from Working.
- [Media Handling](Media_And_Asset_Handling.md) — understand imported images, attachments, storage, and publication.

## Maintain Working Documents

- [Source Organisation](Source_Organisation.md) — source roots, front matter, hierarchy, and generated ordering.
- [Document Identity](Document_Identity.md) — immutable document codes, date provenance, and create-versus-update rules.
- [Builder](Builder.md) — document generation, discovery refresh and the publication handoff.
- [Document Diagrams](Document_Diagrams.md) — create diagrams externally and import finished SVG images.
- [Testing](Testing.md) — choose the appropriate repository check.

## Change The Architecture

- [Configuration And Extension Points](Configuration_And_Extension_Points.md) — what drives the workspace, routes, reports, views, actions, imports and service availability.
- [Reports](Reports.md) — author, validate, build, project, mount, and extend document report blocks.
- [Report Block Tokens](Report_Block_Tokens.md) — current registered report block tokens.
- [Runtime Architecture](Docs_Viewer_Runtime.md) — public, manage, and review execution paths, authority layers, extension method, and weak spots.
- [Generated Data Contracts](Generated_Data_Contracts.md) — generated payloads, read authority, and publishing.
- [Collection Manifests](Generated_Data_Contracts.md#collection-manifest-ownership) — generated lists for the local and public readers.
- [Runtime Module Ownership](Runtime_Module_Ownership.md) — grouped browser-module owners when a code change needs exact responsibility.
- [Source Tree Ownership](Source_Tree_Ownership.md) — repository-level source, runtime, config, service, and generated-output boundaries.

## Code Authority

Use documentation to find the relevant boundary, then verify exact behaviour in:

- `docs-viewer/config/routes/`, `docs-viewer/config/workspace/` and `docs-viewer/config/document-packages/` for route composition, storage and destinations, and package profiles
- `docs-viewer/runtime/js/{public,shared}/` for the canonical public entrypoint and shared reader primitives
- `docs-viewer/runtime/js/{management,review,import,reports}/` for route- and report-owned browser code; only the explicit public report loader is projected publicly
- `docs-viewer/static/css/` for canonical shared/public and local-only stylesheets
- `docs-viewer/services/` for local reads, authoring, publication, import, export and package review
- `docs-viewer/build/` and `docs-viewer/tests/` for generated contracts and executable evidence

The public site serves the shared/public runtime subset from the tracked `site/docs-viewer/` projection. See [Publish and deploy](../guide/Publish_And_Deploy.md#1-prepare-the-change) for the handoff from canonical runtime code.

Prefer code/config search for exact modules, endpoints, fields, and files. Copying those lists into overview pages makes them harder to trust.

## Plan Docs Viewer Work

- [Planned Features](Planned_Features.md) is used for feature, concept, architecture, and delivery model development.
