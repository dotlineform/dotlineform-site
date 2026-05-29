---
doc_id: development-checklist
title: Development Checklist
added_date: 2026-05-23
last_updated: 2026-05-23
parent_id: dev-home
viewable: true
---
# Development Checklist

This checklist holds detailed implementation rules that are too specific for [Development Workflow](/docs/?scope=studio&doc=development-workflow).

Use the workflow doc for lifecycle decisions.
Use this checklist when a change touches local Studio route migration, public/local URL boundaries, shared route helpers, or generated follow-through.

## Local Studio Route Migration

Before moving or adding a Studio route:

- classify the route family: Catalogue, Analytics, Docs Viewer, Data Sharing, Audit, operational report, UI Catalogue, or shared Studio shell
- put route shell rendering in the owning view module, not in `studio_app_server.py`
- add runtime view config in `studio/app/server/studio/studio_app_config.py`
- keep route entry modules as orchestration shells for boot, required elements, event wiring, state handoff, and route-ready projection
- keep service or mutation behavior in the owning API/domain modules
- preserve existing DOM ids, `data-role` hooks, ready-state attributes, and UI text contracts unless the slice intentionally changes them
- add or update a focused smoke for local app route readiness and representative behavior
- retire the old Jekyll route file once the local route is verified, unless there is a documented transition reason to keep it

## Public Link Resolver

Local Studio and public Jekyll preview are separate hosts.
Studio links to public content must not accidentally resolve on the Studio app host.

When a route adds or touches public-content links:

- use `buildPublicSiteUrl(config, path, params)` for general public routes such as `/library/` and `/analysis/`
- use `studio/app/frontend/js/catalogue-public-links.js` for public catalogue routes such as works, series, work details, and moments
- keep editor-to-editor and Studio navigation links on local Studio routes
- do not use relative public-content hrefs such as `/works/...`, `/series/...`, `/moments/...`, `/library/`, or `/analysis/` directly in migrated Studio route output
- do not default to `https://dotlineform.com` unless the action is explicitly a live-site action
- let missing public preview base config fail visibly rather than silently falling back to the Studio host
- add smoke assertions that public links start with the configured public preview base

Future route families still need to use the helper if they add public links.
The current migrated route audit covered the existing local Studio route surfaces, not routes that will be created later.

## Studio Route URL Builder

Configured Studio routes may already contain query state such as `?mode=manage`.

When a browser module appends record parameters to a configured Studio route:

- use `buildStudioRouteUrl(config, routeKey, params)`
- preserve configured query state such as `mode=manage`
- avoid hand-built `?` or `&` concatenation for work, series, detail, moment, or tag editor links
- keep fixed static navigation links acceptable when they do not append dynamic params
- add smoke assertions for representative generated URLs when route config changes

## UI Catalogue Demos

UI Catalogue demos are first-class Studio reference surfaces even though they do not mutate catalogue data.

Treat them as durable Studio surfaces because they are not public-site pages and otherwise have no visible runtime home.

When changing UI Catalogue demo visibility:

- keep demo markup, CSS, JS, and ready-state contracts separate from production Studio route contracts
- keep demo routes discoverable from local Studio navigation or an equivalent local Studio entry surface
- do not treat demos as proof that live production CSS is correct
- verify representative demo pages through a browser smoke when routing, assets, or demo-ready behavior changes

## Closeout

At closeout:

- update the owning docs and any implementation plan or change request status that changed
- create a `studio/workflows/change-requests/logs/entries/*.json` entry for meaningful behavior, workflow, runtime, or documentation changes
- rebuild docs-log generated indexes after adding a log entry unless the slice explicitly defers generated follow-through
- do not rebuild Docs Viewer payloads unless the slice explicitly calls for that follow-through
- report generated payload status separately from source-doc edits

## Source Tree Ownership

When adding or moving repo source:

- use [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) as the maintained ownership contract
- keep Studio source, local services, frontend modules, checks, tests, UI Catalogue, and workflow source under `studio/`
- keep public Jekyll layouts, includes, route pages, public runtime files, public CSS/assets, and generated public payloads outside `studio/`
- keep Docs Viewer source, runtime, CSS, config, build code, and services together under `docs-viewer/`
- keep local working output, backups, staging, and test logs under `var/` or other ignored output paths
- do not reintroduce old source homes such as `assets/studio/`, `assets/docs-viewer/`, `_docs_catalogue/`, `_docs_logs/`, root `tests/`, root check folders, or `scripts/docs/`
