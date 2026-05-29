---
doc_id: source-tree-ownership
title: Source Tree Ownership
added_date: 2026-05-24
last_updated: 2026-05-25
parent_id: architecture
sort_order: 12100
viewable: true
---
# Source Tree Ownership

This document is the maintained source-tree ownership contract after the Studio source-tree reorganization. It is the current reference for where source, generated output, local working output, checks, and command owners live.

## Core Boundary

Studio is the same-repo authoring and maintenance system for the site.
It lives under `studio/`.

The public Jekyll site remains the publishing surface.
It lives outside `studio/` and should contain only public publishing source, public runtime files, public assets, and generated public output needed by GitHub Pages/Jekyll.

The repo is intentionally one repository:

- Studio owns canonical source, authoring workflows, local services, app UI, checks, tests, and developer commands.
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
| `studio/data/canonical/` | Canonical source data maintained by Studio, including catalogue JSON, catalogue Markdown, analytics/tag data, and media-adjacent source records. |
| `studio/data/config/` | Studio-owned checked-in config, including catalogue, data-sharing, and runtime data contracts. |
| `studio/data/generated/` | Studio-generated read models and review output used by Local Studio, such as catalogue lookup, activity, and thumbnail-quality preview data. |
| `studio/services/` | Domain services for catalogue, analytics, media, data-sharing, generation, validation, mutation, publication, import/export, and preview/apply workflows. |
| `studio/shared/` | Shared Python/Ruby helpers used by Studio-owned commands and services. |
| `studio/checks/` | Source-boundary, projection, public-surface, runtime, CSS, and other verification checks. |
| `studio/tests/` | Python tests, smoke tests, fixtures, and Codex-run verification helpers. |
| `studio/commands/` | Developer and Codex command implementations such as `run_checks.py` and command-owned registries. |
| `studio/ui-catalogue/` | UI Catalogue demos, notes, fixtures, and assets. |
| `studio/workflows/change-requests/` | Structured change-request workflow source, docs-log source entries, generated workflow projections, reports, and helper services. |

Studio-owned source should not be reintroduced under old public paths such as `assets/studio/`, `_docs_catalogue/`, `_docs_logs/`, root `tests/`, root check folders, or Studio-only Jekyll route shells.

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
Generated change-history projections remain under `studio/workflows/change-requests/generated/`.
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
