---
doc_id: site-request-docs-viewer-shell-extraction-inventory
title: Docs Viewer Shell Extraction Inventory
added_date: 2026-05-24
last_updated: 2026-05-24
ui_status: done
parent_id: site-request-docs-viewer-shell-extraction
sort_order: 10022
viewable: true
---

This document is archived and is no longer maintained.

---

# Docs Viewer Shell Extraction Inventory

This inventory records the current integrated Docs Viewer state before the shell extraction moves reusable ownership into `docs-viewer/`.
It supports [Docs Viewer Shell Extraction Tasks](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-tasks), especially `DVSE-003` and `DVSE-004`.

## Current Shape

| Area | Current paths | Current owner behavior | Extraction note |
| --- | --- | --- | --- |
| Browser runtime | `studio/docs-viewer/runtime/js/*.js`, `studio/docs-viewer/runtime/js/reports/*.js` | Reusable Docs Viewer modules load from the public path `/studio/docs-viewer/runtime/js/`. `docs-viewer.js` is the route boot module and dynamically imports management, report, import, and scope lifecycle modules. | Move into `docs-viewer/` runtime/static boundary and update shells/imports directly. |
| CSS | `studio/docs-viewer/assets/css/docs-viewer.css`, `docs-viewer-reports.css`, `docs-viewer-management.css` | Public and local routes load Docs Viewer CSS after their host base styles. CSS uses `--docs-viewer-*` tokens with fallbacks to public `--text`, `--muted`, `--border`, `--panel`, spacing, radius, and font variables. | CSS base contract must be made explicit before standalone manage shell work. |
| Jekyll shell includes | `_includes/docs_viewer_shell.html`, `_includes/docs_viewer_readonly_route.html`, `_includes/docs_viewer_management_route.html` | The shared shell emits DOM roots, data attributes, CSS links, management modal markup, import markup, and the `docs-viewer.js` module tag. Read-only and management includes pass route-specific settings. | Decide whether these become Docs Viewer-owned shell templates, host adapters, or a split between both. |
| Route files | `docs/index.md`, `library/index.md`, `analysis/index.md` | `/docs/` currently uses the management include. `/library/` and `/analysis/` use read-only includes and remain Jekyll/public routes. | Preserve route ownership: built-in `/docs/` moves to Docs Viewer service, public scopes stay host/Jekyll routes. |
| Runtime config | `docs-viewer/config/defaults/docs-viewer-config.json`, `docs-viewer-public-config.json` | Browser config lists scopes, `viewer_base_url`, generated docs/search URLs, default doc ids, search metadata, UI statuses, hidden nav color, and recent limit. `_config.yml` points public pages at `docs-viewer-public-config.json`. | Move defaults/schema into `docs-viewer/config/`; keep repo-local service location outside that boundary. |
| Scope/source config | `docs-viewer/config/scopes/docs_scopes.json`, `docs_scope_manifest.json` | Source config maps scopes to `docs-viewer/source/<scope>`, generated output under `assets/data/docs/scopes/<scope>`, media prefixes, public route behavior, settings, and import media storage. Manifest records source roots, route files, generated docs, and search indexes. | Move source/config machinery together and update path contracts without hidden Studio dependencies. |
| UI text | `studio/docs-viewer/config/ui-text/ui-text.json` | Browser modules fetch UI copy for management, settings, import, scope lifecycle, status pills, and modal copy. Studio config also references this file as the `docs_viewer` UI text namespace. | Move with Docs Viewer config; update Studio integration to consume it by configured URL only if still needed. |
| Source markdown | `docs-viewer/source/studio/*.md`, `source/library/*.md`, `source/analysis/*.md` | Flat source docs hold canonical Docs Viewer source for the `studio`, `library`, and `analysis` scopes. Current counts are 334 Studio docs, 15 Library docs, and 3 Analysis docs. | Move or re-root under `docs-viewer/source/` while preserving generated public output locations until a later contract says otherwise. |
| Build scripts | `docs-viewer/build/build_docs.rb`, `studio/docs-viewer/build/build_docs.rb`, `scripts/build_search.rb`, `studio/docs-viewer/build/build_search.rb`, `studio/commands/search-adapters.json` | Root scripts are wrappers/adapters. Docs build writes generated docs payloads and browser config on `--write`. Search adapter routes Docs Viewer scopes to the Docs Viewer search builder. | Move owned builders under `docs-viewer/`; keep repo entrypoints discoverable or update wrappers directly. |
| Services | `docs-viewer/services/*.py` | Local management logic, generated reads, source model, mutation workflows, import/export, source config reports, broken-links reports, data sharing adapter, watcher, backups/logs, and route constants live together under the current Studio Docs Viewer subtree. | Move service code into `docs-viewer/services/`; resolve cross-service imports from Studio shared/data-sharing before file moves. |
| Local Studio host | `studio/app/server/studio/studio_app_server.py`, `studio_app_views.py`, `studio_docs_api.py`, `studio_app_config.py` | Local Studio serves `/docs/`, static Docs Viewer assets/config, and `/studio/api/docs/*`; it renders the Jekyll include by token replacement and maps Docs API calls to Docs Viewer service functions. | Replace hosting with peer-service links and static integration. No embedded Docs Viewer shell should remain in Local Studio after extraction. |
| Local runner | `bin/local-studio` | Loads `var/local/site.env`, starts Local Studio, starts the Docs live rebuild watcher, optionally rebuilds configured docs/search scopes, and validates the Studio app port. | Future "start all" runner should start Live Preview, Local Studio, and Docs Viewer independently. |
| Generated payloads | `assets/data/docs/scopes/<scope>/index.json`, `by-id/*.json`, `references/*`, `assets/data/search/<scope>/index.json`, `assets/data/docs/reports.json` | Browser read-only routes read generated payloads directly from public paths. Manage mode can reload generated index/search/doc/reference data through local service endpoints. Current generated JSON counts: 315 Studio docs payload files, 17 Library files, and 8 Analysis files including indexes/references. | Keep public generated output paths stable during extraction unless a later task changes the config contract. |
| Media/assets | `assets/docs/interactive/<scope>/...`, `assets/docs/.gitkeep` | Docs Viewer generated content may reference interactive assets and staged/imported media through repo public asset paths. | Decide whether asset contract stays host-owned while Docs Viewer owns token/rendering behavior. |
| Local state | `var/docs/import-staging`, `var/docs/backups`, `var/docs/logs`, `var/docs/watch-suppressions` | Services use these repo-local directories for staged imports, write backups, compact logs, and watcher suppression. | Keep repo-local service state outside `docs-viewer/`; expose paths through host/runtime config if needed. |
| Tests and checks | `studio/tests/python/test_docs_*.py`, `studio/tests/smoke/*docs_viewer*.py`, `studio/tests/smoke/local_studio_docs_management_*.py`, `studio/commands/run_checks.py` | `quick` includes Docs Viewer Python and smoke checks. `docs-viewer-smoke` covers public read-only route, index panel modules, management modal, and management action workflow modules. | Tests should move or be re-pointed with the new boundary while repo-level check profiles remain discoverable. |

## Browser Runtime Imports

`studio/docs-viewer/runtime/js/docs-viewer.js` is the main entrypoint.
It imports tree, search, bookmarks, data, config, document, search-controller, render, sidebar, index-panel, and router modules.
It dynamically imports `docs-viewer-management.js` only when management mode is active.

Management runtime is split across focused modules:

- `docs-viewer-management.js` coordinates the management controller and dynamically imports `docs-html-import.js` and `docs-viewer-scope-lifecycle.js`.
- `docs-viewer-management-client.js` centralizes local management API requests.
- `docs-viewer-management-actions.js`, `docs-viewer-management-action-workflow.js`, `docs-viewer-management-interactions.js`, `docs-viewer-management-modals.js`, `docs-viewer-management-render.js`, `docs-viewer-management-capabilities.js`, `docs-viewer-management-config.js`, and `docs-viewer-management-parent-picker.js` own focused management behavior.
- `docs-html-import*.js` owns the browser-side import modal/workflow.
- `docs-viewer-reports.js` dynamically imports report loaders from `runtime/js/reports/`.

No browser module import currently leaves `studio/docs-viewer/runtime/js/` through relative imports, but several modules still contain fallback URLs such as `/studio/docs-viewer/config/...`, `/docs/`, and `/assets/data/docs/reports.json`.

## URL And Data Assumptions

| Assumption | Current value or pattern | Used by |
| --- | --- | --- |
| Runtime script URL | `/studio/docs-viewer/runtime/js/docs-viewer.js` | Jekyll include, Local Studio shell, Studio route config |
| Docs Viewer CSS URLs | `/studio/docs-viewer/assets/css/docs-viewer*.css` | Jekyll include, Local Studio shell |
| Browser config URL | Public default: `/docs-viewer/config/defaults/docs-viewer-public-config.json`; manage default: `/docs-viewer/config/defaults/docs-viewer-config.json` | `_config.yml`, includes, Local Studio shell, browser fallback code |
| UI text URL | `/studio/docs-viewer/config/ui-text/ui-text.json` | Shell data attributes, browser fallbacks, Studio config |
| Report registry URL | `/assets/data/docs/reports.json` | Shell data attribute and report loader fallback |
| Public generated docs | `/assets/data/docs/scopes/<scope>/index.json` and `/assets/data/docs/scopes/<scope>/by-id/<doc_id>.json` | Read-only routes, browser generated reads, management generated-read endpoints |
| Public generated search | `/assets/data/search/<scope>/index.json` | Browser search and search builder |
| Public viewer URLs | `/library/`, `/analysis/` | Scope config, route files, generated links |
| Current manage URL | `/docs/?mode=manage` and `/docs/?scope=studio&doc=<doc_id>&mode=manage` | Local Studio route config and docs references |
| Current management API base | `/studio/api/docs` | Local Studio shell and browser management/generated reloads |
| Docs API paths | `/capabilities`, `/docs/generated/index`, `/docs/generated/payload`, `/docs/generated/search`, `/docs/generated/docs-log`, `/docs/generated/references`, `/docs/generated/reference-target`, `/docs/source-config`, `/docs/source-config-settings`, `/docs/import-source-files`, `/docs/import-html-files`, `/docs/open-source`, `/docs/broken-links`, `/docs/import-source`, `/docs/import-html`, `/docs/update-metadata`, `/docs/update-viewability`, `/docs/update-viewability-bulk`, `/docs/create`, `/docs/rebuild`, `/docs/move`, `/docs/normalize-order`, `/docs/archive`, `/docs/delete-preview`, `/docs/delete-apply`, `/docs/scopes/create-preview`, `/docs/scopes/create-apply`, `/docs/scopes/delete-preview`, `/docs/scopes/delete-apply` | `docs_management_routes.py`, browser management client, report loaders, import workflow |

## Studio And Jekyll Integration Points

`_config.yml` currently disables public management mode, points public builds at `docs-viewer-public-config.json`, and excludes local-only Docs Viewer build/config/source/service paths from Jekyll output.
The Jekyll route files are intentionally small wrappers around the shared includes.

Local Studio currently has deeper coupling:

- `studio_app_server.py` serves `/docs/`, Docs Viewer static paths, and `/studio/api/docs/*`.
- `studio_app_views.py` reads `_includes/docs_viewer_shell.html` and performs token replacement to render a local manage-mode shell inside Studio chrome.
- `studio_docs_api.py` imports `docs-viewer/services/docs_management_service.py` and adapts Local Studio API requests to Docs Viewer service functions.
- `studio_app_config.py` lists `docs` as a Studio view, points route help links to `/docs/`, and includes Docs Viewer files in asset-version calculation.
- `bin/local-studio` starts the docs watcher and validates Docs Viewer scope ids from `docs-viewer/config/scopes/docs_scopes.json`.

These are the main places that must change from "Studio hosts Docs Viewer" to "Studio links to the Docs Viewer service".

## CSS Dependency Notes

Current Docs Viewer CSS is mostly namespaced, but it assumes a host base exists.
Important fallback variables include `--text`, `--muted`, `--border`, `--border-strong`, `--panel`, `--panel-2`, `--bg`, `--radius`, `--font-small`, `--line-snug`, and spacing tokens.
The shell markup also uses shared utility classes such as `container`, `content`, `muted`, `small`, and `visually-hidden`.

Extraction needs a clear answer for each page type:

- standalone Docs Viewer manage shell must not depend implicitly on Studio chrome or public `main.css`
- public read-only host routes may deliberately inherit the public site base
- reusable Docs Viewer CSS should keep Docs Viewer-prefixed tokens and document host-provided fallbacks

## Current Verification Entry Points

Useful current checks before and after extraction slices:

| Check | Current command or file |
| --- | --- |
| Quick profile | `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick` |
| Docs Viewer smoke profile | `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke` |
| Docs management Python tests | `studio/tests/python/test_docs_management_routes.py`, `test_docs_management_mutations.py`, `test_docs_management_service.py`, `test_docs_live_rebuild_watcher.py` |
| Public read-only smoke | `studio/tests/smoke/public_docs_viewer_readonly.py` |
| Docs Viewer route smoke | `studio/tests/smoke/docs_viewer_routes.py`, `docs_viewer_index_panel_route.py` |
| Browser module smokes | `studio/tests/smoke/docs_viewer_index_panel_modules.py`, `docs_viewer_management_action_workflow_modules.py`, `docs_viewer_management_modal.py` |
| Local Studio integration smokes | `studio/tests/smoke/local_studio_app_docs_viewer.py`, `local_studio_docs_management_*.py` |
| Public Jekyll build | `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build` |

## DVSE-004 Ownership Questions

The inventory confirms the existing `DVSE-004` ownership-resolution task is necessary before file moves.
Resolve these points before starting the target layout:

- whether `_includes/docs_viewer_shell.html` moves whole into `docs-viewer/`, stays as a host adapter, or splits into a Docs Viewer shell template plus host route adapters
- how Local Studio docs navigation and `doc_href` values should build configured Docs Viewer service links without probing service availability
- how `/studio/api/docs/*` maps to standalone Docs Viewer service endpoints, and whether the path prefix should change for v1
- whether Docs Viewer data-sharing endpoints remain under Docs Viewer management APIs or move behind a separate Studio/data-sharing integration adapter
- where the report registry (`assets/data/docs/reports.json`) belongs after extraction
- how scope lifecycle outputs should write host route files while source/config machinery lives under `docs-viewer/`
- what exact CSS base contract standalone manage mode owns versus what public Jekyll routes provide
- which generated outputs are host-owned public artifacts and which are Docs Viewer-owned build artifacts
- how docs watcher ownership changes when Docs Viewer is independent of `bin/local-studio`
- whether current `.DS_Store` and `__pycache__` files under Docs Viewer paths should be cleaned in a separate hygiene task
