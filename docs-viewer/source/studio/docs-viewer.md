---
doc_id: docs-viewer
title: Docs Viewer
added_date: 2026-04-24
last_updated: 2026-07-12
parent_id: ""
viewable: true
---
# Docs Viewer

The Docs Viewer is the shared documentation module used by the site's docs-domain routes.

## Knowledge Workspace Role

Docs Viewer gathers human-, data-, and AI-developed material into navigable knowledge collections. In this system, `canonical` means the currently accepted source used to build and render a scope; it does not imply exclusively human authorship or finality.

[Knowledge System Vision](/docs/?scope=studio&doc=knowledge-system-vision) owns the broader Studio + Analytics + Docs Viewer model, including the hybrid `/analysis/` ambition and repeated AI-assisted knowledge-development loop.

It currently serves these scopes:

- Studio docs at `/docs/`
- Library docs at `/library/`
- Analysis docs at `/analysis/`
- Moments docs as `/moments/`

At a high level, the current implementation is split into:

- route shells and route config that select the active scope, access mode, and generated payload URLs
- shared browser runtime modules under `docs-viewer/runtime/js/`, with separate public and manage entrypoints
- generated scope payloads for index trees, document bodies, search, recent documents, references, and report data
- service-side management support under `docs-viewer/services/` for local write, import, export, generated-read, and scope workflows
- static CSS under `docs-viewer/static/css/`, with public, manage-only, and report-specific layers
- source docs under `docs-viewer/source/<scope>/`

Do not treat this page as a file inventory.
Use runtime and source-boundary docs for current module ownership when an implementation change depends on those details.

Public viewer routes are read-only:

- `/library/` loads the Library scope directly and does not expose management query state
- `/analysis/` loads the Analysis scope directly and does not expose management query state
- `/docs/` is the local management shell served by the standalone Docs Viewer service and can load `studio`, `library`, or `analysis` through its `scope` query parameter

The CSS base contract is explicit.
Public `/library/` and `/analysis/` intentionally inherit `site/assets/css/main.css` from the public site layout so generated docs content keeps host prose and media styling.
The shared Docs Viewer include also loads `/docs-viewer/static/css/docs-viewer.css`, backed by `site/docs-viewer/static/css/docs-viewer.css`, which supplies Docs Viewer-owned tokens, small utilities, and public reader, index, main, info, search, and bookmark surfaces.
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

## Key Documents

- [Overview](/docs/?scope=studio&doc=docs-viewer-overview) explains the route-shell, runtime, and URL/state model.
- [Docs Viewer Documentation Cleanup](/docs/?scope=studio&doc=docs-viewer-documentation-register) tracks focused entrypoint, owner, workflow, and request cleanup. The `studio` corpus remains the single reference scope for development and maintenance documentation.
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation) explains source roots, parent/child structure, and generated ordering.
- [Docs Viewer Static Route Template](/docs/?scope=studio&doc=docs-viewer-static-route-template) explains public/manage route shell ownership, stable mount points, and runtime entrypoint boundaries.
- [Docs Viewer Public Route Shell Template](/docs/?scope=studio&doc=docs-viewer-public-route-shell-template) explains how new public route shells are rendered from the canonical template into tracked `site/` HTML.
- [Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) records how shared runtime behavior, scope differences, and forks are handled.
- [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) is the current implementation map for browser runtime ownership.
- [Info Panel](/docs/?scope=studio&doc=docs-viewer-info-panel) explains the panel hosting model, context-driven view selection, and public/manage metadata separation.
- [Export](/docs/?scope=studio&doc=docs-viewer-export) documents static HTML export from generated Docs Viewer payloads.
- [Semantic References Editor](/docs/?scope=studio&doc=docs-viewer-semantic-references-editor) explains manage-mode semantic target search and token insertion in the Markdown source editor.
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder) covers build mechanics, generated payloads, and command usage.
- [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling) covers docs media paths, import staging, extraction, and media-copy behavior.
- [Reports](/docs/?scope=studio&doc=docs-viewer-reports) covers report metadata, report modules, and access rules.
- [Embedded Detail Documents](/docs/?scope=studio&doc=site-request-docs-viewer-embedded-detail-documents) covers sub-scope detail documents, the `docs_subscope` report, embedded detail URL state, and sub-scope build/publish contracts.
- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) records repo-level ownership boundaries for Docs Viewer source, runtime, config, services, and generated payloads.
