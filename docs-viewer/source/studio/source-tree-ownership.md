---
doc_id: source-tree-ownership
title: Source Tree Ownership
added_date: 2026-05-24
last_updated: 2026-05-31
parent_id: architecture
viewable: true
---
# Source Tree Ownership

This document is the maintained source-tree ownership contract after the Studio source-tree reorganization. It is the current reference for where source, generated output, local working output, checks, and command owners live.

## Core Boundary

Studio is the same-repo catalogue authoring and maintenance system for the site.
It lives under `studio/`.
Analytics, Docs Viewer, and UI Catalogue are separate local app boundaries in the same repository.

The public Jekyll site remains the publishing surface.
It lives outside `studio/` and should contain only public publishing source, public runtime files, public assets, and generated public output needed by GitHub Pages/Jekyll.

The repo is intentionally one repository:

- Studio owns catalogue source, catalogue authoring workflows, Studio operational routes, Studio local services, app UI, checks, tests, and developer commands.
- Analytics owns tag maintenance, Data Sharing route/API workflows, semantic-reference maintenance, and future analysis/visualisation workflows.
- Docs Viewer owns docs viewing, docs source management, Docs Viewer payloads, docs conversion helpers, and the `/docs/` manage-mode service.
- UI Catalogue owns isolated UI demos and reference assets outside Local Studio.
- Jekyll owns public layouts, includes, route pages, public route JavaScript/CSS, public media, and generated public runtime payloads.
- Generated public artifacts can be produced by Studio or Docs Viewer but remain in public paths when published pages need them.
- Local working output, backups, run logs, caches, and staging live under `var/` or other ignored output paths, not as source.

## Studio Source

The current Studio-owned source homes are:

| Path | Owner / role |
| --- | --- |
| `studio/app/server/` | Local Studio app server, API adapters, route views, runtime config projection, and local HTTP dispatch. |
| `studio/app/frontend/` | Studio browser modules, route modules, shell helpers, UI text config, and Studio runtime config source. |
| `studio/app/assets/` | Studio-only CSS and visual assets used by Local Studio routes. |
| `studio/data/canonical/` | Canonical source data maintained by Studio, including catalogue JSON, catalogue Markdown, and media-adjacent source records. |
| `studio/data/config/` | Studio-owned checked-in config, including catalogue and Studio runtime data contracts. |
| `studio/data/generated/` | Studio-generated read models and review output used by Local Studio, such as catalogue lookup and activity data. Risk summaries belong here only when they are intentionally served by Local Studio; ordinary local risk artifacts belong under `var/studio/risk/`. Retired thumbnail-quality preview output is not an active served contract. |
| `studio/services/` | Domain services for catalogue, media, generation, validation, mutation, publication, import/export, and preview/apply workflows. Analytics helper modules may remain here only as current tag-domain helpers used by the Analytics app. |
| `studio/shared/` | Shared Python helpers used by Studio-owned commands, Docs Viewer builders, catalogue generation, and services. |
| `studio/checks/` | Source-boundary, projection, public-surface, runtime, CSS, risk, and other verification checks. |
| `studio/tests/` | Python tests, smoke tests, fixtures, and Codex-run verification helpers. |
| `studio/commands/` | Developer and Codex command implementations such as `run_checks.py` and command-owned registries. |
| `studio/retired/thumbnail-quality/` | Retired thumbnail-quality experiment code kept as repo-local reference tooling with no active Studio route, API endpoint, or static-data mount. |
| `studio/workflows/change-requests/` | Structured change-request workflow source, docs-log source entries, generated workflow projections, reports, and helper services. |

Risk operations are Studio-owned.
Risk dashboards and inventories live as Studio docs under `docs-viewer/source/studio/`; risk checks live under `studio/checks/`; ignored local risk reports and snapshots should default to `var/studio/risk/`; and any Studio-readable generated risk summaries should use `studio/data/generated/risk/` only when they are deliberately served by Local Studio.

Studio-owned source should not be reintroduced under old public paths such as `assets/studio/`, `_docs_catalogue/`, `_docs_logs/`, root `tests/`, root check folders, or Studio-only Jekyll route shells.

## Analytics App

Analytics is the local app boundary for tag and Data Sharing workflows.

Current Analytics-owned source homes:

| Path | Owner / role |
| --- | --- |
| `analytics-app/app/server/analytics_app/` | Local Analytics app server, Analytics route views, runtime config projection, static serving, tag API dispatch, and Data Sharing API dispatch. |
| `analytics-app/app/server/analytics_app/tag_services/` | Analytics tag-domain helper modules for source path contracts, validation, planning, dry-run/write transactions, backups, route constants, and compact activity projection. |
| `analytics-app/app/frontend/` | Analytics browser modules, route modules, shell helpers, UI text config, and Analytics runtime config source. |
| `analytics-app/app/assets/` | Analytics-only CSS and static assets used by Local Analytics routes. |
| `analytics-app/tests/` | Analytics Python and browser smoke tests, including tag route/API checks and Data Sharing route/API checks. |
| `analytics-app/data/canonical/` | Canonical tag registry, alias, assignment, and group source data used by Analytics. Raw local browser access, where needed, is served through `/analytics/data/canonical/...`. |
| `data-sharing/` | Headless Data Sharing config, adapter registry, package path contracts, workflow dispatch, package I/O, and documents/tags adapters used by Analytics. |
| `var/analytics/data-sharing/` | Local Data Sharing package output, returned-package staging, review artifacts, and backups. |

Analytics routes and APIs live under `/analytics/...` and `/analytics/api/...`.
Do not add aliases, proxies, dual-read paths, or static-serving shims for retired `/studio/analytics/...`, `/studio/data-sharing/...`, `/studio/api/analytics/...`, or `/studio/api/data-sharing/...` paths.

## UI Catalogue

UI Catalogue is an isolated local demo system, not a Local Studio route family.

| Path | Owner / role |
| --- | --- |
| `ui-catalogue-app/` | UI Catalogue demo source, demo app server, CSS, JavaScript helpers, reference assets, fixtures, and tests. |

The active demo route namespace is `/ui-catalogue/demos/...`.
Retired Studio-hosted UI Catalogue routes should not be recreated.

## Docs Viewer

Docs Viewer is extracted into the tracked `docs-viewer/` boundary.
It remains in this repository for v1, while public route adapters, generated publishable output, local service settings, and orchestration runners stay host-owned.

Current Docs Viewer-owned source homes:

| Path | Owner / role |
| --- | --- |
| `docs-viewer/source/studio/` | Studio docs source scope. |
| `docs-viewer/source/library/` | Library docs source scope. |
| `docs-viewer/source/analysis/` | Analysis docs source scope. |
| `docs-viewer/runtime/` | Shared Docs Viewer browser runtime, management runtime, report modules, and browser shell behavior. |
| `docs-viewer/static/` | Docs Viewer CSS and runtime-owned static assets. |
| `docs-viewer/shell/` | Standalone Docs Viewer service shell template for built-in `/docs/` manage mode. |
| `docs-viewer/config/` | Scope config, runtime config source, UI text, report/source config, and local service defaults/schema. |
| `docs-viewer/generated/` | Tracked non-public generated Docs Viewer runtime payloads for committed manage-mode scopes such as Studio. |
| `docs-viewer/services/` | Standalone Docs Viewer service, Docs management, import/export, generated-read, scope, live rebuild, and data-sharing services. |
| `docs-viewer/bin/` | Docs Viewer-owned launcher for the standalone local service. |

Public read-only installs such as `/library/` and `/analysis/` consume generated Docs Viewer payloads outside `studio/`.
Manage-mode `/docs/` is owned by the standalone Docs Viewer service.
Local Studio may link to that configured service, but it should not be the durable owner of the Docs Viewer shell or management endpoints.

## Public Jekyll Surface

Public Jekyll source and runtime remain outside `studio/`:

| Path family | Role |
| --- | --- |
| `_config.yml`, `.ruby-version`, `Gemfile`, `Gemfile.lock` | Jekyll and package infrastructure. |
| `_layouts/` and public `_includes/` | Public layouts/includes used by published routes. Studio-only and Docs Viewer shell internals do not belong here. |
| `_works/`, `_series/`, `_moments/`, `_work_details/`, `_works_print/` | Public Jekyll collection/page source. |
| `works/`, `series/`, `catalogue/`, `recent/`, `search/`, `analysis/`, `library/`, `docs/`, `data/`, `logs/` | Public route surfaces and minimal route adapters when they publish pages or generated runtime payloads. |
| `assets/js/` | Public browser runtime for published pages. |
| `assets/css/main.css` | Public site CSS and genuinely shared public primitives. Studio-only selectors live under `studio/app/assets/css/`. |
| `assets/data/docs/scopes/` | Generated Docs Viewer payloads consumed by public read-only installs. |
| `assets/data/search/` | Generated public search payloads. |
| `assets/data/*.json`, `assets/works/`, `assets/series/`, `assets/moments/`, `assets/work_details/`, `assets/home/`, `assets/site/` | Generated or published public catalogue/site data and media. |

Public route adapters for Docs Viewer should stay minimal.
Docs Viewer shell source, management shell source, config, CSS, reports, and services belong under `docs-viewer/`.

## Generated Output Rule

Generated output paths should make the flow obvious:

```text
studio/ source and services -> generated public artifacts -> Jekyll/GitHub Pages site
```

Generated public artifacts remain outside `studio/` when public pages need them.
Examples include public catalogue JSON, public search indexes, public Docs Viewer payloads for `/library/` and `/analysis/`, public thumbnails, and public route media.

Generated Studio read models remain under `studio/data/generated/` when they are only for Local Studio authoring/review.
The generated change-history search projection remains under `studio/workflows/change-requests/generated/`.
Generated committed manage-mode Docs Viewer payloads remain under `docs-viewer/generated/`; they are tracked for local manage-mode runtime use but are not public static assets.

`var/` remains local working output for staging, backups, imports, generated run logs, temporary media derivatives, and test run summaries.

## Compatibility Rule

Do not preserve or reintroduce old Studio source paths through aliases, copied files, broad fallback reads, or static-serving shims.

Current active rules:

- do not restore `assets/studio/` as a Studio source or local static source path
- do not restore `assets/docs-viewer/` as Docs Viewer source; public copies are generated/runtime payloads only when explicitly needed
- do not restore `_docs_catalogue/` for catalogue Markdown source
- do not restore `_docs_logs/` for structured change-history source
- do not restore root `tests/`, root check folders, or `scripts/docs/` as active source homes
- keep `scripts/run_checks.py` deleted; use `studio/commands/run_checks.py`
- keep public-site validation checks under Studio/Codex test ownership even when they inspect public generated output

Root wrappers may remain only as deliberate convenience entrypoints into the owning Studio or Docs Viewer implementation.
They must not become compatibility layers for old source paths.

## Related References

- [Projection Contract](/docs/?scope=studio&doc=data-models-projection-contract)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Testing](/docs/?scope=studio&doc=testing)
- [Development Workflow](/docs/?scope=studio&doc=development-workflow)
