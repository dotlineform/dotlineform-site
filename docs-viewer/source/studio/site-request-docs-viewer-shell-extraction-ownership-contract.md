---
doc_id: site-request-docs-viewer-shell-extraction-ownership-contract
title: Docs Viewer Shell Extraction Ownership Contract
added_date: 2026-05-24
last_updated: 2026-05-24
ui_status: draft
parent_id: site-request-docs-viewer-shell-extraction
sort_order: 10023
viewable: true
---
# Docs Viewer Shell Extraction Ownership Contract

This contract resolves the ambiguous ownership points found in [Docs Viewer Shell Extraction Inventory](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-inventory).
It is the `DVSE-004` handoff into the target layout and implementation slices.

The decisions here are intentionally about ownership and integration boundaries.
They do not define the final directory layout, file move order, service launcher implementation, or verification baseline.
Those remain assigned to the later implementation tasks.

## Ownership Decisions

| Surface | Owner after extraction | Decision | Follow-through task |
| --- | --- | --- | --- |
| Core browser runtime | Docs Viewer | Navigation, rendering, search, router, generated-data loading, bookmarks/favourites, report dispatch, and document display belong under `docs-viewer/`. Host pages must reference the configured runtime asset path rather than `/studio/docs-viewer/...`. | `DVSE-010` |
| Management browser runtime | Docs Viewer | Management actions, modal lifecycle, import UI, scope lifecycle UI, drag/drop, capability reads, and write-client calls belong under `docs-viewer/`. Management mode is enabled only through explicit local capability config. | `DVSE-010`, `DVSE-013`, `DVSE-014` |
| Shell markup | Split ownership | Docs Viewer owns the reusable shell template/markup contract: DOM roots, data attributes, viewer controls, management modal markup, import markup, script/style asset requirements, and minimum page structure. Host repos own the adapter that mounts that shell into a public route or local service page. | `DVSE-005`, `DVSE-010`, `DVSE-014`, `DVSE-017` |
| Built-in `/docs/` route | Docs Viewer service | The local Docs Viewer service owns built-in `/docs/` manage mode after extraction. Local Studio must stop rendering or serving this shell. | `DVSE-014`, `DVSE-016` |
| Public scope route files | Host repo/Jekyll | Public read-only route files such as `library/index.md` and `analysis/index.md` remain host-owned Jekyll routes. They may call a Docs Viewer-provided read-only route adapter, but the route file itself is a host integration artifact. | `DVSE-017` |
| Public route adapter include | Split ownership | The reusable read-only adapter contract belongs to Docs Viewer; the concrete Jekyll include location and minimal route files are host-owned integration. Extraction should avoid a Studio-specific adapter and avoid old-path shims. | `DVSE-005`, `DVSE-010`, `DVSE-017` |
| Local Studio navigation links | Studio integration | Studio owns navigation entries and help/doc links, but those links must be built from repo-local Docs Viewer service config and must not probe service availability. Broken links when Docs Viewer is stopped are acceptable for v1. | `DVSE-016` |
| Host runtime/service config | Host repo | `var/local/site.env` owns local Docs Viewer host, port, base URL, and manage capability settings. `_config.yml` owns static public/Jekyll defaults. Optional repo integration config is allowed only if those two surfaces and Docs Viewer-owned defaults are insufficient. | `DVSE-007` |
| Docs Viewer config defaults/schema | Docs Viewer | Route names, generated-data contract defaults, shell defaults, capability model, source config schema, UI text defaults, and runtime config schema belong under `docs-viewer/config/`. Repo-local host/port state must not be stored there. | `DVSE-007`, `DVSE-008` |
| Source markdown and scope config | Docs Viewer | Docs Viewer owns source Markdown roots, source/scope config readers and writers, source model validation, source settings, and scope manifests. The config may reference host-owned public routes and generated output paths. | `DVSE-008`, `DVSE-017` |
| Generated docs/search payloads | Host public output | Public generated docs/search JSON under `assets/data/docs/scopes/<scope>/` and `assets/data/search/<scope>/` remains host public output for v1. Docs Viewer owns the builders and generated-data contract; the host owns the publishable artifact location. | `DVSE-008`, `DVSE-009`, `DVSE-017` |
| Generated reads in manage mode | Docs Viewer service | Manage-mode reloads of generated docs, search, references, docs-log projections, and reference-target data are service reads owned by Docs Viewer. They should read the same host public output paths configured for each scope. | `DVSE-013`, `DVSE-014` |
| Local write APIs | Docs Viewer service | Metadata, viewability, create, rebuild, move, normalize order, archive, delete, source settings, import, broken-links, and scope lifecycle endpoints belong to the Docs Viewer service. Keep loopback binding, CORS restrictions, write allowlists, backup behavior, and preview/apply boundaries. | `DVSE-013`, `DVSE-014`, `DVSE-015` |
| API path prefix | Docs Viewer service | The stable API path set should remain the existing route constants for v1, but the host prefix changes from Local Studio ownership to Docs Viewer service ownership. Browser clients should use configured service base URL plus endpoint paths. | `DVSE-013`, `DVSE-014`, `DVSE-016` |
| Docs Viewer data-sharing APIs | Docs Viewer service with adapters | Docs document data-sharing endpoints remain part of Docs Viewer management because they mutate Docs Viewer source and generated docs state. Shared data-sharing orchestration may stay in Studio/shared modules only behind an explicit adapter until a later cross-domain extraction exists. | `DVSE-013`, `DVSE-019`, `DVSE-020` |
| Report registry | Docs Viewer contract, host public artifact | Report loader code and registry schema belong to Docs Viewer. The checked-in report registry file may remain in a host public data path for v1 because public and manage routes fetch it as a static artifact. The target layout should decide whether a source registry under `docs-viewer/` writes or copies to the host public path. | `DVSE-005`, `DVSE-008`, `DVSE-010` |
| Scope lifecycle route outputs | Split ownership | Docs Viewer owns New Scope validation, preview/apply workflow, scope config updates, manifest updates, and generated output creation. Host repo owns route-file creation for public Jekyll routes and the publishable generated output locations. | `DVSE-008`, `DVSE-013`, `DVSE-017` |
| Media and interactive assets | Split ownership | Docs Viewer owns parsing/rendering/import token behavior and scope media config. Host repo owns publishable media asset paths such as `assets/docs/...` for v1. | `DVSE-008`, `DVSE-013`, `DVSE-017` |
| CSS base | Split ownership with explicit contract | Docs Viewer owns reusable viewer, report, management, and standalone base CSS needed for its service shell. Public Jekyll routes may intentionally inherit the public site base, but portable manage mode must not depend on Studio CSS or implicit public `main.css`. | `DVSE-011`, `DVSE-012` |
| Docs watcher | Docs Viewer service/tooling | Source watching and same-scope docs/search rebuild behavior belong to Docs Viewer tooling, not `bin/local-studio`. Local Studio should not start the watcher after extraction except through a broader start-all runner. | `DVSE-013`, `DVSE-018` |
| Start-all runner | Host repo | The script that starts Live Preview, Local Studio, and Docs Viewer together is host repo integration. Each service must still have an independent start path. | `DVSE-018` |
| Tests and run-check profiles | Split ownership | Docs Viewer-owned tests/helpers should live with the Docs Viewer boundary where practical. Repo-level `studio/commands/run_checks.py` remains a discoverable host verification entrypoint that can call those tests. | `DVSE-019` |
| Cleanup hygiene | Host extraction cleanup | Current `.DS_Store` and `__pycache__` files under Docs Viewer paths are not architectural surfaces. Do not widen `DVSE-004` for cleanup. Remove or ignore them during the old-path cleanup slice if they are tracked or copied into the new boundary. | `DVSE-021` |

## Endpoint Contract

For v1, keep the existing endpoint names and behavior while changing the service owner.
The browser should build URLs from configured Docs Viewer service base URL plus these endpoint paths.
Studio should not translate, proxy, or remap these endpoints after extraction.

| Endpoint group | Paths | Owner |
| --- | --- | --- |
| Health and capabilities | `/health`, `/capabilities` | Docs Viewer service |
| Generated reads | `/docs/generated/index`, `/docs/generated/payload`, `/docs/generated/search`, `/docs/generated/docs-log`, `/docs/generated/references`, `/docs/generated/reference-target` | Docs Viewer service |
| Source/config reads | `/docs/source-config`, `/docs/source-config-settings`, `/docs/import-source-files`, `/docs/import-html-files` | Docs Viewer service |
| Source/config writes | `/docs/source-config-settings`, `/docs/open-source`, `/docs/import-source`, `/docs/import-html` | Docs Viewer service |
| Document writes | `/docs/update-metadata`, `/docs/update-viewability`, `/docs/update-viewability-bulk`, `/docs/create`, `/docs/rebuild`, `/docs/move`, `/docs/normalize-order`, `/docs/archive`, `/docs/delete-preview`, `/docs/delete-apply` | Docs Viewer service |
| Scope lifecycle | `/docs/scopes/create-preview`, `/docs/scopes/create-apply`, `/docs/scopes/delete-preview`, `/docs/scopes/delete-apply` | Docs Viewer service, with host route/output side effects when requested |
| Docs data sharing | Existing docs data-sharing endpoints currently mounted below the Docs API prefix | Docs Viewer service with explicit shared-data adapter boundary |

## Host Integration Rules

- Host routes and Studio navigation render configured links without service availability checks.
- Host Jekyll pages may include read-only Docs Viewer runtime assets, but must not host manage-mode write APIs.
- Local Studio may link to the Docs Viewer service and may show Docs Viewer URLs in navigation, but must not serve `/docs/`, static Docs Viewer assets, or Docs management endpoints after the relevant migration slices.
- Host-owned public generated payload paths remain stable until a later task explicitly changes the generated-data contract.
- Repo-local service state stays under `var/` or another host-owned local state path, not under `docs-viewer/`.

## Requirements For DVSE-005

The target layout doc should use this ownership contract to specify:

- the `docs-viewer/` directories for runtime, shell template, service code, config defaults/schema, source, build tools, tests, and docs-owned static assets
- the host integration locations for Jekyll route adapters, route files, `_config.yml`, `var/local/site.env`, generated public outputs, public media assets, and start-all runner
- the exact path convention for Docs Viewer-owned source registry files that write or copy host public artifacts such as report registry and generated browser config
- the no-shim update plan for old `/studio/docs-viewer/...` browser paths
- the line between Docs Viewer service start commands and host start-all orchestration
