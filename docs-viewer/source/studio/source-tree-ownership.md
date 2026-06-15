---
doc_id: source-tree-ownership
title: Source Tree Ownership
added_date: 2026-05-24
last_updated: 2026-06-14
parent_id: architecture
viewable: true
---
# Source Tree Ownership

This document is the maintained source-tree ownership contract after the Studio source-tree reorganization. It is the current reference for where source, generated output, local working output, checks, and command owners live.

## Core Boundary

Studio is the same-repo catalogue authoring and maintenance system for the site.
It lives under `studio/`.
Admin, Analytics, and Docs Viewer are separate local app boundaries in the same repository.

The public static site root is the publishing surface.
Its canonical files live under `site/`; validation and durable site-level settings live under `site-tools/`.
Publishable runtime files, public assets, and generated public output remain outside `studio/`.

The repo is intentionally one repository:

- Studio owns catalogue source, catalogue authoring workflows, Studio catalogue routes, Studio catalogue services, app UI, and catalogue/public-site tests.
- Admin owns cross-repo operational review, audit/risk/activity/testing routes, repo-scope checks, check profiles, and local check summaries.
- Analytics owns tag maintenance, Data Sharing route/API workflows, semantic-reference maintenance, and future analysis/visualisation workflows.
- Docs Viewer owns docs viewing, docs source management, Docs Viewer payloads, docs conversion helpers, and the `/docs/` manage-mode service.
- `site/` owns public route HTML, public route JavaScript/CSS, public media, and generated public runtime payloads.
- `site-tools/` owns deploy-root validation and durable site-level settings used by local Python tooling.
- `shared/` owns repo-system frontend assets intended for reuse by multiple local apps.
- Generated public artifacts can be produced by Studio or Docs Viewer but remain in public paths when published pages need them.
- Local working output, run logs, caches, and staging live under `var/` or other ignored output paths, not as source.

## Studio Source

The current Studio-owned source homes are:

| Path | Owner / role |
| --- | --- |
| `studio/app/server/` | Local Studio app server, API adapters, route views, runtime config projection, and local HTTP dispatch. |
| `studio/app/frontend/` | Studio browser modules, route modules, shell helpers, UI text config, and Studio runtime config source. |
| `studio/app/assets/` | Studio-only CSS and visual assets used by Local Studio routes. |
| `studio/data/canonical/` | Canonical source data maintained by Studio, including catalogue JSON, catalogue Markdown, and media-adjacent source records. |
| `studio/data/config/` | Studio-owned checked-in config, including catalogue and Studio runtime data contracts. |
| `studio/data/generated/` | Studio-generated read models and review output used by Local Studio, such as catalogue lookup data. Retired thumbnail-quality preview output is not an active served contract. |
| `studio/services/` | Domain services for catalogue, media, generation, validation, mutation, publication, import/export, and preview/apply workflows. Analytics helper modules may remain here only as current tag-domain helpers used by the Analytics app. |
| `studio/shared/` | Shared Python helpers used by Studio-owned commands, Docs Viewer builders, catalogue generation, and services. |
| `studio/tests/` | Studio-owned Python tests, smoke tests, and Codex-run verification helpers for catalogue/public-site behavior. |
| `studio/retired/thumbnail-quality/` | Retired thumbnail-quality experiment code kept as repo-local reference tooling with no active Studio route, API endpoint, or static-data mount. |

Risk operations are Admin-owned.
Risk dashboards and inventories live as Studio docs under `docs-viewer/source/studio/`; checks report producers live under `admin-app/checks/reports/`; ignored local checks reports and snapshots should default to `var/admin/checks/`.

## Shared Frontend

Shared frontend assets are app-neutral production UI modules and styles for the same-repo local app system.

| Path | Owner / role |
| --- | --- |
| `shared/frontend/js/` | Browser ES modules for reusable production UI behavior across Studio, Admin, Analytics, and Docs Viewer. |
| `shared/frontend/css/` | Baseline production UI styles paired with shared frontend behavior modules. |

Shared frontend code should not call app-specific APIs or depend on a specific route shell.
Apps should expose `/shared/frontend/...` when they consume these assets and keep route-specific data loading, rendering adapters, and commit behavior in the owning app.

## Admin App

Admin is the local app boundary for cross-repo operational review and verification.

Current Admin-owned source homes:

| Path | Owner / role |
| --- | --- |
| `admin-app/app/server/admin_app/` | Local Admin app server, Admin route views, runtime config projection, audit/checks/activity/testing API dispatch, and audit allowlist. |
| `admin-app/app/frontend/` | Admin browser modules, route modules, shell helpers, route state helpers, transport helpers, route registry, and Admin UI text config. |
| `admin-app/app/assets/` | Admin-only CSS and static assets used by Local Admin routes. |
| `admin-app/checks/` | Source-boundary, projection, public-surface, runtime, CSS, activity-contract, report producer, and other repo-scope verification checks. |
| `admin-app/commands/` | Developer and Codex command implementations such as `run_checks.py` and command-owned profile registries. |
| `admin-app/tests/` | Admin server tests, runner tests, audit/check contract tests, and Admin route smokes. |
| `var/admin/activity/` | Ignored local unified activity feed and journal. |
| `var/admin/checks/` | Ignored local Admin checks report runs, snapshots, and review artifacts. |
| `var/admin/test-runs/` | Ignored local check profile summaries and command logs. |

Admin routes and APIs live under `/admin/...` and `/admin/api/...`.
Do not add aliases, proxies, dual-read paths, or static-serving shims for retired `/studio/audits/...`, `/studio/risk/...`, `/studio/activity/...`, `/studio/ui-catalogue/...`, `/ui-catalogue/...`, or standalone `ui-catalogue-app` paths.

## Analytics App

Analytics is the local app boundary for tag and Data Sharing workflows.

Current Analytics-owned source homes:

| Path | Owner / role |
| --- | --- |
| `analytics-app/app/server/analytics_app/` | Local Analytics app server, Analytics route views, runtime config projection, static serving, tag API dispatch, and Data Sharing API dispatch. |
| `analytics-app/app/server/analytics_app/tag_services/` | Analytics tag-domain helper modules for source path contracts, validation, planning, dry-run/write transactions, route constants, and compact activity projection. |
| `analytics-app/app/frontend/` | Analytics browser modules, route modules, shell helpers, UI text config, and Analytics runtime config source. |
| `analytics-app/app/assets/` | Analytics-only CSS and static assets used by Local Analytics routes. |
| `analytics-app/tests/` | Analytics Python and browser smoke tests, including tag route/API checks and Data Sharing route/API checks. |
| `analytics-app/data/canonical/` | Canonical tag registry, alias, assignment, and group source data used by Analytics. Raw local browser access, where needed, is served through `/analytics/data/canonical/...`. |
| `data-sharing/` | Headless Data Sharing config, adapter registry, package path contracts, workflow dispatch, package I/O, and documents/tags adapters used by Analytics. |
| `var/analytics/data-sharing/` | Local Data Sharing package output, returned-package staging, and review artifacts. |

Analytics routes and APIs live under `/analytics/...` and `/analytics/api/...`.
Do not add aliases, proxies, dual-read paths, or static-serving shims for retired `/studio/analytics/...`, `/studio/data-sharing/...`, `/studio/api/analytics/...`, or `/studio/api/data-sharing/...` paths.

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

## Public Static Site Surface

Public static-site source and runtime remain outside `studio/`:

| Path family | Role |
| --- | --- |
| `site/` | Canonical tracked static deploy root uploaded to GitHub Pages. |
| `site/assets/js/` | Public browser runtime for published pages. |
| `site/assets/css/main.css` | Public site CSS and genuinely shared public primitives. Studio-only selectors live under `studio/app/assets/css/`. |
| `site/assets/data/docs/scopes/` | Generated Docs Viewer payloads consumed by public read-only installs. |
| `site/assets/data/search/` | Generated public search payloads. |
| `site/assets/data/*.json`, `site/assets/works/`, `site/assets/series/`, `site/assets/moments/`, `site/assets/work_details/`, `site/assets/site/` | Generated or published public catalogue/site data and media. |
| `site-tools/` | Static site validation CLI, validation config, and durable site-level media/config settings. |

Public route adapters for Docs Viewer should stay minimal.
Docs Viewer shell source, management shell source, config, CSS, reports, and services belong under `docs-viewer/`.

Public catalogue route construction and route-state parsing are owned by focused ES modules under `site/assets/js/catalogue/`.
Shared route URL helpers live in `site/assets/js/catalogue/shared/catalogue-urls.js`; public route entrypoints live under `site/assets/js/catalogue/routes/`.
First-party public pages, catalogue search rendering, Docs Viewer semantic references, and Studio public-link helpers should derive work, series, detail, and moment URLs through that shared URL contract or its Studio equivalent rather than serializing derivable URL fields in generated catalogue payloads.

## Generated Output Rule

Generated output paths should make the flow obvious:

```text
studio/ and docs-viewer services -> generated public files in site/assets/ -> site validation -> GitHub Pages artifact
```

Generated public files remain under `site/assets/` when public pages need them.
Examples include public catalogue JSON, public search indexes, public Docs Viewer payloads for `/library/` and `/analysis/`, public thumbnails, and public route media.

Generated Studio read models remain under `studio/data/generated/` when they are only for Local Studio authoring/review.
Generated committed manage-mode Docs Viewer payloads remain under `docs-viewer/generated/`; they are tracked for local manage-mode runtime use but are not public static assets.

`var/` remains local working output for staging, imports, generated run logs, temporary media derivatives, and test run summaries.

## Compatibility Rule

Do not preserve or reintroduce old Studio source paths through aliases, copied files, broad fallback reads, or static-serving shims.

Current active rules:

- do not restore `site/assets/studio/` as a Studio source or local static source path
- do not restore `site/assets/docs-viewer/` as Docs Viewer source; public copies are generated/runtime payloads only when explicitly needed
- do not restore root `site/assets/` as a public deploy source; use `site/assets/`
- do not restore `_docs_catalogue/` for catalogue Markdown source
- do not restore root `tests/`, root check folders, or `scripts/docs/` as active source homes
- keep `scripts/run_checks.py` deleted; use `admin-app/commands/run_checks.py`
- keep static-site validation checks under Admin/Codex check ownership, `site-tools/`, or the owning app test directory even when they inspect public generated output

Root wrappers may remain only as deliberate convenience entrypoints into the owning Studio or Docs Viewer implementation.
They must not become compatibility layers for old source paths.

## Related References

- [Projection Contract](/docs/?scope=studio&doc=data-models-projection-contract)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Source Organisation](/docs/?scope=studio&doc=docs-viewer-source-organisation)
- [Scripts](/docs/?scope=studio&doc=scripts)
- [Testing](/docs/?scope=studio&doc=testing)
- [Development Workflow](/docs/?scope=studio&doc=development-workflow)
