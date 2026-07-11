---
doc_id: docs-viewer-runtime-surfaces
title: Runtime Surfaces
added_date: 2026-06-05
last_updated: 2026-07-11
summary: Current Docs Viewer route, shell, entrypoint, config, CSS, generated-data, and public/manage surface matrix.
parent_id: docs-viewer-runtime-boundary
---
# Docs Viewer Runtime Surfaces

This document records route, shell, entrypoint, config, and CSS surfaces for [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary).
It is the current-state surface map; fine-grained browser module risk lives in [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory).

## Route Surface Matrix

| Surface | Public `/library/` | Public `/analysis/` | Local/manage `/docs/` |
| --- | --- | --- | --- |
| Route owner | public page | public page | standalone Docs Viewer service |
| Route file | `site/library/index.html` | `site/analysis/index.html` | `docs-viewer/shell/docs-viewer-manage.html` |
| Shell source | tracked static route shell; new shells copy `docs-viewer/templates/public-route/index.html` and read per-route values from route config | tracked static route shell; new shells copy `docs-viewer/templates/public-route/index.html` and read per-route values from route config | service-served static shell with dynamic route config |
| Entrypoint | `site/docs-viewer/runtime/js/public/docs-viewer-public.js` | `site/docs-viewer/runtime/js/public/docs-viewer-public.js` | `docs-viewer/runtime/js/management/docs-viewer-manage.js` |
| Route registry | `site/docs-viewer/config/routes/docs-viewer-public-routes.json` served at `/docs-viewer/config/routes/docs-viewer-public-routes.json` | `site/docs-viewer/config/routes/docs-viewer-public-routes.json` served at `/docs-viewer/config/routes/docs-viewer-public-routes.json` | `docs-viewer/config/routes/docs-viewer-routes.json` served with service-local URLs |
| UI text | design-time runtime text in public/shared JavaScript | design-time runtime text in public/shared JavaScript | design-time runtime text in manage/import JavaScript |
| Management controls | absent | absent | present when management is enabled |
| Report runtime | absent unless explicitly public-promoted | absent unless explicitly public-promoted | available through manage-owned report mounting |
| Scope query | ignored/normalized away | ignored/normalized away | allowed |
| Management query | ignored/normalized away | ignored/normalized away | normalized away; `/docs/` owns management |

Public `/moments/` uses the same public entrypoint, route registry, static generated-data authority, and read-only boundary as Library and Analysis. Its route config currently narrows the main-view toolbar through UI policy. The route is part of the Phase 0 public baseline even though the compact matrix above uses Library and Analysis as the two representative public installs covered by the focused browser smoke.

## Entrypoint And Shell Surface

| Surface | Public | Manage | Shared? | Boundary rule |
| --- | --- | --- | --- | --- |
| ES module entrypoint | `docs-viewer-public.js` | `docs-viewer-manage.js` | no | Route shells load exactly one route-appropriate entrypoint. |
| App boot owner | `docs-viewer-app-boot.js` | `docs-viewer-app-boot.js` | yes | Boot remains shared while receiving route-specific settings from the entrypoint. |
| App shell owner | `docs-viewer-app-shell.js` | `docs-viewer-app-shell.js` plus manage-owned shell composition | partial | Shared shell code must not import management shell/action renderers directly. |
| Manage shell composition | absent | `docs-viewer-management-shell-composition.js` | no | Supplied by the manage entrypoint only. |
| Management shell renderer | absent | `docs-viewer-management-shell-renderer.js` | no | Context menu, metadata modal, import modal, settings modal, and import host refs stay manage-owned. |
| Selected-document management actions | absent | `docs-viewer-management-document-actions-renderer.js` | no | Status/edit/source controls stay manage-owned. |
| Manage hosted views | absent | `docs-viewer-management-hosted-views.js` | no | Source editor and other manage-only hosted views stay out of public imports. |

## CSS Surface

| CSS | Public routes | Manage route | Boundary rule |
| --- | --- | --- | --- |
| `site/assets/css/main.css` | inherited from the public site layout | absent from standalone shell | Host public-site CSS is not a Docs Viewer runtime dependency. |
| `site/docs-viewer/static/css/docs-viewer.css` | loaded via `/docs-viewer/static/css/docs-viewer.css` | loaded via service mapping for the same URL | Basic/public viewer styling and portable Docs Viewer tokens. |
| `docs-viewer/static/css/docs-viewer-reports.css` | absent unless explicitly public-promoted | loaded | Report styling is manage-only until a report is promoted. |
| `docs-viewer/static/css/docs-viewer-manage.css` | absent | loaded | Management shell/modal styling only. |

`site/docs-viewer/static/css/docs-viewer.css` supplies portable Docs Viewer tokens, shell utilities such as `visually-hidden`, `muted`, `small`, hidden-state handling inside `.docsViewer`, and viewer component tokens with Docs Viewer theme-token and host-token fallbacks.

## Route Config Surface

| Config surface | Public | Manage |
| --- | --- | --- |
| Registry shape | `docs_viewer_route_config_registry_v1` with `routes` array | `docs_viewer_route_config_registry_v1` with `routes` array |
| Route record shape | `docs_viewer_route_config_v3` snake_case | `docs_viewer_route_config_v3` snake_case |
| Route config resolver | `docs-viewer-route-config.js` | `docs-viewer-route-config.js` |
| Local `/docs/` route present | no | yes |
| Manage-only hosted views | omitted | allowed |
| App kind | `public` | `manage` |
| Route access | scope query and management UI disabled | scope query enabled; management UI projected independently of service URLs |
| Route features | configured-scope discovery, search, recently added, bookmarks, reports | configured-scope discovery, scope selection, search, recently added, bookmarks, reports, source editing, management |
| Generated-data service | static generated assets; local URL blank | local URL injected when generated reads are enabled, independently of management |
| Source service | absent | URL injected when source services are enabled |
| Management service | absent | URL injected when management services are enabled |

Route config resolution no longer reads inline config scripts, legacy `#docsViewerRoot` data attributes, camelCase field aliases, or object-map route registries.
Route records declare `app_kind`, narrow `access` policy, and `services.generated_data`, `services.source`, and `services.management` surfaces. Backend reachability and write availability are not browser-side route-config authority; they remain in the owning capability flow.

Route config resolution rejects entrypoint/route app-kind mismatches. Public route records contain no local service URLs. The local service injects each enabled loopback surface independently when it serves the manage route registry.

`docs-viewer-route-features.js` normalizes the explicit route `features` array and rejects unknown ids. Disabled search, recently-added, and report features do not require their payload URLs. Disabled feature controllers, bindings, hosted views/modes, shell controls, and startup phases are omitted rather than initialized against missing elements.

Configured-scope discovery is a separate startup operation from general viewer-settings loading. Both current route families enable discovery; a future non-scope provider may omit it while still loading browser-safe viewer settings.

## Scope-Owned Data Roots

| Scope kind | Docs output root | Search output root | Notes |
| --- | --- | --- | --- |
| Manage/local | `docs-viewer/generated/docs/<scope>/` | `docs-viewer/generated/search/<scope>/index.json` | Used by the standalone manage route and generated-read service. |
| Public read-only | `site/assets/data/docs/scopes/<scope>/` | `site/assets/data/search/<scope>/index.json` | Published as static public data for route-owned scopes such as Library and Analysis. |

Generated payload contracts live in [Docs Viewer Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts).

## Route Payload Surfaces

Current Docs Viewer route payload ownership:

- public `/library/` and `/analysis/` route configs point navigation at public nested-tree payloads in `site/assets/data/docs/scopes/<scope>/index-tree.json`
- local/manage `/docs/` route config points navigation at the manage nested-tree payload in `docs-viewer/generated/docs/<scope>/index-tree.json`
- public and manage routes point recently-added mode at the route-appropriate `recently-added.json`
- search remains on the route-appropriate search payload such as `site/assets/data/search/<scope>/index.json` or `docs-viewer/generated/search/<scope>/index.json`
- selected-document rendering and info-panel metadata hydrate from selected by-id payloads
- public route smoke assertions prove management JS/CSS, report runtime, scope lifecycle, import, settings, source-editor surfaces, and public docs `index.json` requests are absent
- scope lifecycle create/delete behavior records only user-created route/generated outputs, not shared entrypoints, CSS, route registries, or shared runtime modules
