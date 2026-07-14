---
doc_id: docs-viewer-overview
title: Overview
added_date: 2026-04-24
last_updated: 2026-07-14
ui_status: review
summary: Concise model of Docs Viewer capabilities, public/manage/review surfaces, architecture, and source-to-reader flow.
parent_id: docs-viewer
---
# Docs Viewer Overview

Docs Viewer is a shared documentation reader built around generated document collections. It provides tree navigation, rendered documents, URL-addressable selection, search, recent documents, bookmarks, metadata panels, and optional reports.

The local management surface adds source editing, import, rebuild, export, settings, and scope workflows. The separate review surface renders validated returned packages without gaining authority over canonical source.

The exact enabled features and current scope list live in `docs-viewer/config/routes/docs-viewer-routes.json` and `docs-viewer/config/scopes/docs_scopes.json`. [Configuration And Extension Points](/docs/?scope=studio&doc=config-docs-viewer) explains how those files interact with code registries and live capabilities.

## Three Surfaces

| surface | purpose | authority boundary |
| --- | --- | --- |
| Public routes | Read published Library, Analysis, or Moments content. | Static route config and published generated payloads; no local management services. |
| Manage route `/docs/` | Read configured scopes and perform explicitly available source and management workflows. | The manage entrypoint may load management modules, but backend capabilities and server validation authorize operations. |
| Review route `/docs-review/` | Read a validated returned-package preview, inspect its inventory, and hand its identity to Docs Import. | Package-rooted reads only; no canonical write, promotion, or general management authority. |

[Runtime](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) owns the detailed boundary. [Docs Review](/docs/?scope=studio&doc=docs-viewer-review) owns the returned-package workflow.

## Architecture At A Glance

```text
source Markdown -- builders --> generated docs + search payloads
                                      |
route shell + browser-safe config ----+----> shared browser runtime
                                                   |
                                                   v
                                      tree, document, search and panels

manage/review shell --> route-specific entrypoint --> focused local services
                                                        |
                                                        v
                                             capability-checked reads/writes
```

Route shells select an app kind and a browser-safe route record. Route-specific entrypoints then compose the shared reader with only the providers, views, and controls needed by that surface.

Public routes read published static payloads. The manage route can use local generated-data, source, and management services. The review route uses a package provider and review service instead of a configured Docs Viewer scope.

Shared code is not automatically public code. What a route imports, renders, exposes through config, and can reach through an authorized service determines its actual surface.

## Reader Workflow

1. The route shell identifies its route configuration and app kind.
2. App boot creates the route context, service context, collection provider, and reader state.
3. The provider loads the active collection's generated index.
4. The route workflow resolves the requested document and keeps canonical URL state in sync.
5. The selected generated payload is rendered into the document pane; search, recent documents, bookmarks, info views, and reports are composed only when enabled.
6. Manage-only writes go through management endpoints and server-side validation, then rebuild or refresh generated data as required.

The URL normally uses `doc` for document selection and a heading hash for in-document navigation. The local manage route also uses `scope`; the review route preserves `package`. Feature-specific parameters belong to their focused owner rather than this overview.

## Source And Publication Flow

Source Markdown and its front matter are the maintained content. Builders validate and render that source into scope-owned indexes, per-document payloads, search data, references, and report inputs. The browser reads those generated artifacts; it does not interpret the source tree directly.

Management workflows may change canonical source and trigger rebuild follow-through. Review previews are derived from validated package contents and remain separate from canonical source until Docs Import applies an explicit decision.

Use these focused references when exact detail matters:

- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation) for source roots and hierarchy
- [Builder](/docs/?scope=studio&doc=scripts-docs-builder) for build and publish commands
- [Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts) for payload and read ownership
- [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) for current browser-code responsibility
- [Management Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints) for local HTTP ownership

## Where The Code Lives

The stable code map is deliberately short:

- route and scope policy: `docs-viewer/config/`
- public-safe reader runtime: `site/docs-viewer/runtime/js/shared/`
- route-specific browser code: `site/docs-viewer/runtime/js/public/` and `docs-viewer/runtime/js/{management,review}/`
- local services: `docs-viewer/services/`
- builders: `docs-viewer/build/`
- contract and boundary checks: `docs-viewer/tests/`

For an exact module list, use [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) or search the code. This overview should change only when the architectural model changes, not whenever a helper is added or renamed.
