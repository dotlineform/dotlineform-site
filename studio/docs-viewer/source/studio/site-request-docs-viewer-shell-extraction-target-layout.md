---
doc_id: site-request-docs-viewer-shell-extraction-target-layout
title: Docs Viewer Shell Extraction Target Layout
added_date: 2026-05-24
last_updated: 2026-05-24
ui_status: draft
parent_id: site-request-docs-viewer-shell-extraction
sort_order: 10024
viewable: true
---
# Docs Viewer Shell Extraction Target Layout

This document defines the v1 target layout for the Docs Viewer shell extraction.
It follows [Docs Viewer Shell Extraction Inventory](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-inventory) and [Docs Viewer Shell Extraction Ownership Contract](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-ownership-contract).

The goal is a tracked, self-contained `.docs-viewer/` source boundary inside this repo.
It is not a submodule or external package for v1.
Host-owned Jekyll routes, generated public outputs, local service settings, and repo orchestration stay outside `.docs-viewer/`.

## Target Tree

```text
.docs-viewer/
  README.md
  bin/
    docs-viewer
  build/
    build_docs.rb
    build_search.rb
  config/
    defaults/
      docs-viewer-config.json
      docs-viewer-public-config.json
    schema/
      docs-viewer-config.schema.json
      docs-scopes.schema.json
      docs-scope-manifest.schema.json
    scopes/
      docs_scopes.json
      docs_scope_manifest.json
    ui-text/
      ui-text.json
    reports/
      reports.json
  runtime/
    js/
      docs-viewer.js
      *.js
      reports/
        *.js
  shell/
    docs-viewer-shell.html
    docs-viewer-readonly-adapter.html
    docs-viewer-manage-page.html
  services/
    docs_viewer_service.py
    docs_management_routes.py
    docs_management_service.py
    *.py
  source/
    studio/
      *.md
    library/
      *.md
    analysis/
      *.md
  static/
    css/
      docs-viewer-base.css
      docs-viewer.css
      docs-viewer-reports.css
      docs-viewer-management.css
  tests/
    python/
    smoke/
```

The exact file names may change during implementation, but the ownership shape should not.
Do not leave reusable Docs Viewer code in `studio/` after the cleanup slice.

## Host Integration Tree

```text
_config.yml
_includes/
  docs_viewer_readonly_route.html
  docs_viewer_public_adapter.html
docs/
  index.md
library/
  index.md
analysis/
  index.md
assets/
  data/
    docs/
      reports.json
      scopes/
        <scope>/
          index.json
          by-id/
          references/
    search/
      <scope>/
        index.json
  docs/
    interactive/
      <scope>/
bin/
  local-studio
  local-all
scripts/
  build_docs.rb
  build_search.rb
studio/
  app/
    integrations/
      docs-viewer/
        docs_viewer_links.py
        docs_viewer_config.py
  commands/
    run_checks.py
  tests/
    integration/
      docs-viewer/
var/
  local/
    site.env
  docs/
    import-staging/
    backups/
    logs/
    watch-suppressions/
```

Host integration files can be named differently if the implementation finds a better local pattern.
The boundary rule is the important part: host files point to Docs Viewer through config and adapters; they do not become a second copy of Docs Viewer.

## Path Ownership

| Surface | Target path | Owner | Notes |
| --- | --- | --- | --- |
| Reusable JS runtime | `.docs-viewer/runtime/js/` | Docs Viewer | Move current `studio/docs-viewer/runtime/js/` here. Relative JS imports should stay local to this tree. |
| Report JS loaders | `.docs-viewer/runtime/js/reports/` | Docs Viewer | Move current report loaders here and keep registry-driven dispatch. |
| Reusable CSS | `.docs-viewer/static/css/` | Docs Viewer | Include standalone base CSS plus viewer, report, and management CSS. |
| Shell template | `.docs-viewer/shell/docs-viewer-shell.html` | Docs Viewer | Owns DOM/data-attribute contract and management modal markup. |
| Manage shell page | `.docs-viewer/shell/docs-viewer-manage-page.html` | Docs Viewer | Used by the standalone service for built-in `/docs/`. |
| Public read-only adapter contract | `.docs-viewer/shell/docs-viewer-readonly-adapter.html` | Docs Viewer | Documents or provides reusable adapter markup for host read-only route includes. |
| Host Jekyll includes | `_includes/docs_viewer_readonly_route.html`, optional `_includes/docs_viewer_public_adapter.html` | Host repo | Thin route adapters only. No manage write UI or Local Studio coupling. |
| Public route files | `library/index.md`, `analysis/index.md` | Host repo | Remain Jekyll routes and should stay minimal. |
| Built-in manage route | `.docs-viewer/services/` plus `.docs-viewer/shell/docs-viewer-manage-page.html` | Docs Viewer service | Local service owns `/docs/`. Local Studio must stop serving it. |
| Source docs | `.docs-viewer/source/<scope>/` | Docs Viewer | Re-root current source docs here and update scope config. |
| Scope config | `.docs-viewer/config/scopes/` | Docs Viewer | May reference host-owned output and route paths. |
| Runtime config defaults/schema | `.docs-viewer/config/defaults/`, `.docs-viewer/config/schema/` | Docs Viewer | No repo-local host/port state in this folder. |
| UI text | `.docs-viewer/config/ui-text/ui-text.json` | Docs Viewer | Browser and management UI copy source. |
| Report registry source | `.docs-viewer/config/reports/reports.json` | Docs Viewer | Source of registry schema/content. V1 may copy or write public artifact to `assets/data/docs/reports.json`. |
| Docs builders | `.docs-viewer/build/` | Docs Viewer | Root scripts may remain wrappers for discoverability. |
| Docs service code | `.docs-viewer/services/` | Docs Viewer | Includes management APIs, generated reads, source model, watcher, and service shell entrypoint. |
| Independent launcher | `.docs-viewer/bin/docs-viewer` | Docs Viewer | Starts only Docs Viewer service/watcher behavior required by that service. |
| Local service config | `var/local/site.env` | Host repo | Owns host, port, base URL, and manage enablement for local v1. |
| Static Jekyll defaults | `_config.yml` | Host repo | Owns public link defaults, public config URL, and generated/static route defaults. |
| Generated docs JSON | `assets/data/docs/scopes/<scope>/` | Host public output | Builders write here for v1. |
| Generated search JSON | `assets/data/search/<scope>/index.json` | Host public output | Search builder writes here for v1. |
| Public docs media | `assets/docs/` | Host public output | Docs Viewer source/config can reference this host-owned public asset tree. |
| Local state | `var/docs/` | Host repo | Staging, backups, logs, and watch suppressions stay out of `.docs-viewer/`. |
| Studio Docs Viewer integration | `studio/app/integrations/docs-viewer/` or existing local pattern | Studio integration | Link/config helpers only. No shell rendering, static hosting, or management API proxy after migration. |
| Start-all runner | `bin/local-all` or similarly named repo script | Host repo | Starts Live Preview, Local Studio, and Docs Viewer as independent child processes. |
| Repo check entrypoint | `studio/commands/run_checks.py` | Host repo | Remains discoverable and delegates to moved Docs Viewer tests. |

## Public URL Conventions

The implementation should update references directly instead of preserving old Studio-owned paths.

| URL type | V1 convention |
| --- | --- |
| Docs Viewer service base | From `var/local/site.env`, for example `DOCS_VIEWER_BASE_URL` or host plus port-derived equivalent. |
| Built-in manage route | `<docs-viewer-base-url>/docs/` with query parameters such as `scope`, `doc`, and `mode=manage`. |
| Docs Viewer API base | `<docs-viewer-base-url>` plus stable endpoint paths such as `/capabilities` and `/docs/generated/index`. |
| Public read-only route | Host Jekyll route such as `/library/` or `/analysis/`. |
| Runtime assets in public routes | Configured Docs Viewer asset URL, not `/studio/docs-viewer/...`. |
| Public generated docs | `/assets/data/docs/scopes/<scope>/index.json` and `/assets/data/docs/scopes/<scope>/by-id/<doc_id>.json`. |
| Public generated search | `/assets/data/search/<scope>/index.json`. |
| Report registry artifact | `/assets/data/docs/reports.json` for v1, generated or copied from `.docs-viewer/config/reports/reports.json` if that source move is implemented. |

Do not add compatibility aliases for `/studio/docs-viewer/runtime/`, `/studio/docs-viewer/assets/`, or `/studio/docs-viewer/config/`.
After each move slice, update the import, include, script, test, and config references that still point at those paths.

## Config Model

Use three config layers:

| Layer | Path | Purpose |
| --- | --- | --- |
| Docs Viewer defaults/schema | `.docs-viewer/config/` | Portable defaults, schema, scope config, UI text, report source registry, generated-data contract defaults, and capability model. |
| Host public defaults | `_config.yml` and any minimal host integration config if needed | Jekyll/static defaults such as public route behavior and public Docs Viewer config URL. |
| Host local runtime | `var/local/site.env` | Local host, port, base URL, loopback binding, manage capability enablement, startup flags, and local-only service settings. |

Do not store local host, port, PID, logs, caches, or runtime advertisement files inside `.docs-viewer/config/`.
If later tasks need generated runtime advertisement files, they should live under host-owned `var/`, but v1 should not require them.

## Shell And Adapter Model

The reusable Docs Viewer shell template owns:

- `docsViewerRoot` and required child DOM structure
- data attributes for index URL, viewer base URL, scope, scope-query behavior, default doc id, search index URL, config URL, UI text URL, report registry URL, generated base URL, management base URL, and management enablement
- viewer controls, sidebar, content, result list, bookmark, status, management action, context menu, metadata modal, import modal, and settings modal markup
- references to Docs Viewer-owned CSS and JS assets

Host adapters own:

- selecting public or manage route mode
- mapping host config values into shell data attributes
- adding public route layout/front matter
- deciding whether public routes inherit the public site base styles
- omitting management write surfaces from public read-only Jekyll routes

Local Studio must not own a second shell renderer after extraction.
If Studio needs Docs Viewer links, it should use a link/config helper that returns configured URLs.

## Service Model

`.docs-viewer/services/` should contain the standalone local Docs Viewer service and the existing management service modules after they move.
The service owns:

- loopback binding for v1
- clear startup failure when the configured port is unavailable
- built-in `/docs/` manage route
- stable management API paths
- generated read endpoints
- local write workflows
- docs watcher and rebuild helpers
- backups, compact logs, and watch suppression behavior using host-owned `var/docs/`

Local Studio should not proxy Docs Viewer APIs after the migration slice.
The host start-all runner may start the Docs Viewer service as a child process, but independent service startup must remain available.

## Builder And Generated Output Model

Root-level scripts may stay as compatibility entrypoints for command discoverability:

- `scripts/build_docs.rb` can load or invoke `.docs-viewer/build/build_docs.rb`
- `scripts/build_search.rb` can delegate Docs Viewer scopes to `.docs-viewer/build/build_search.rb`

The actual Docs Viewer builder implementation belongs under `.docs-viewer/build/`.
For v1, generated outputs remain in the existing host public paths:

- `assets/data/docs/scopes/<scope>/`
- `assets/data/search/<scope>/`
- `assets/data/docs/reports.json`

Scope config should make these host output paths explicit.
Do not move generated public payloads under `.docs-viewer/` during the extraction unless a later task changes the generated-data contract and verifies public routes.

## Test Layout

Move Docs Viewer-owned tests where practical:

```text
.docs-viewer/tests/
  python/
  smoke/
```

Keep the host check entrypoint discoverable:

```text
studio/commands/run_checks.py
```

`run_checks.py` may call moved Docs Viewer tests by path.
Local Studio integration tests that only prove Studio links to the Docs Viewer service can remain host/Studio tests.

## Move Sequence Constraints

- Establish baseline verification before file moves (`DVSE-006`).
- Add host/runtime config before moved readers require it (`DVSE-007`).
- Move config/source/scope machinery before browser and service paths depend on the new root (`DVSE-008`).
- Move browser runtime/static/CSS before removing old public asset paths (`DVSE-010` and `DVSE-011`).
- Move service code and implement standalone shell before removing Local Studio hosting (`DVSE-013` through `DVSE-016`).
- Preserve public scope route behavior while New Scope route creation changes ownership (`DVSE-017`).
- Move/update tests before cleanup (`DVSE-019`).
- Delete old Studio-owned Docs Viewer locations only after references are updated and verified (`DVSE-021`).

## DVSE-006 Handoff

The next task should establish the current integrated-tree baseline before any moves.
Use the target layout above to choose checks that cover:

- current `/docs/` manage shell through Local Studio
- public `/library/` and `/analysis/` read-only routes
- docs builders and search builders for configured Docs Viewer scopes
- Docs Viewer browser module imports
- Docs management Python service and route tests
- Jekyll build with current public assets and generated payload paths
