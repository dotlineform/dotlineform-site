---
doc_id: site-request-docs-viewer-shell-extraction-tasks
title: Docs Viewer Shell Extraction Tasks
added_date: 2026-05-24
last_updated: 2026-05-25
ui_status: done
parent_id: site-request-docs-viewer-shell-extraction
sort_order: 10021
viewable: true
---
This document is archived and is no longer maintained.

---

# Docs Viewer Shell Extraction Tasks

This is the tracker for implementing [Docs Viewer Shell Extraction Request](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction).

## Status

### just done

- Completed `DVSE-023` by closing out the parent request, task tracker, portable request outcome, structured docs-log source entry, and current owning docs that still contained stale extracted-service ownership wording.
- Marked the parent request and this tracker complete.
- Added close-out summary, final moved-path summary, verification results, generated payload status, and remaining known risk to the parent request.
- Updated the active Portable Docs Viewer request so it no longer describes the extracted Docs Viewer boundary as a future move from `studio/docs-viewer/`.
- Added structured docs-log source entry `change-2026-05-25-completed-docs-viewer-shell-extraction`.
- Generated Docs Viewer docs/search payloads and generated docs-log projections were intentionally not rebuilt during close-out.
- Completed `DVSE-022` with the agreed final verification set for the extracted Docs Viewer shell boundary.
- `quick` passed: `var/test-runs/docs-viewer-shell-final-quick/summary.md`.
- The first sandboxed `docs-viewer-smoke` run reproduced the expected localhost bind restriction after the temporary Jekyll build passed; the elevated rerun passed all 7 checks, including the standalone Docs Viewer manage shell, public `/library/` and `/analysis/` read-only smoke, Docs Viewer browser module smokes, management modal, action workflow modules, and Docs HTML import modules. Summary: `var/test-runs/docs-viewer-shell-final-docs-viewer-smoke-elevated/summary.md`.
- Elevated `studio-smoke` passed all 10 checks, including the public read-only smoke, Local Studio Data Sharing routes, Data Sharing prepare module, returned-package review flow, and retained Studio browser smokes. Summary: `var/test-runs/docs-viewer-shell-final-studio-smoke/summary.md`.
- Focused Local Studio integration smokes passed for the Docs Viewer boundary route, Studio navigation adapter, Data Sharing routes, and Data Sharing review with a mocked Docs Viewer service.
- Focused syntax/import checks passed for Docs Viewer JavaScript modules, `docs-viewer/build/build_docs.rb`, `docs-viewer/build/build_search.rb`, Docs Viewer services/tests, and the Local Studio Docs Viewer integration module.
- Active runtime/config/test path sweeps found only intentional negative assertions for retired `/studio/docs-viewer` and `/studio/api/docs` paths. A wider docs-source sweep still finds historical or inventory-style `docs_management_server.py` references; handle any needed cleanup in `DVSE-023`.
- No generated docs/search payloads were rebuilt manually.
- Completed `DVSE-021` by moving Docs Viewer Ruby builder implementations from `studio/docs-viewer/build/` to `docs-viewer/build/` and deleting the remaining old `studio/docs-viewer/` tree.
- Follow-up command cleanup removed the root `scripts/build_docs.rb` and `scripts/build_search.rb` aliases. Docs Viewer rebuilds now call `docs-viewer/build/build_docs.rb` and `docs-viewer/build/build_search.rb` directly; Catalogue search calls `studio/services/catalogue/search/build_search.rb` directly.
- `_config.yml` now excludes `docs-viewer/build/` from public Jekyll output and no longer carries retired `studio/docs-viewer/` excludes.
- Current owning docs for scripts, Docs Viewer portable files, docs builder behavior, search build ownership, semantic references, and script inventory were updated away from the active `studio/docs-viewer/build/` path.
- Targeted stale-reference checks found no old Studio-owned Docs Viewer paths in active code/config/runtime/service/test surfaces except intentional negative assertions and historical change-log test fixtures. No generated docs/search payloads were rebuilt manually.
- Completed `DVSE-020` by updating current command, setup, portable, runtime-boundary, source-organisation, config, and script docs for the extracted Docs Viewer boundary.
- Durable docs now describe `docs-viewer/` as the owner of source docs, runtime modules, CSS, config defaults, UI text, local services, management workflows, generated reads, and Docs Viewer-owned tests, while host/Jekyll adapters remain outside that boundary.
- Local setup and runner docs now distinguish `bin/local-studio` as the Studio app plus docs source watcher, `docs-viewer/bin/docs-viewer` as the standalone `/docs/` service, and `bin/local-all` as the combined public preview, Studio, and Docs Viewer runner.
- Current docs were corrected away from old `_docs*`, `assets/docs-viewer/*`, `studio/docs-viewer/source|services|config`, `docs_management_server.py`, and Local Studio `/studio/api/docs/...` ownership assumptions except where those paths are explicit retired-path or do-not-restore notes.
- No generated docs/search payloads were rebuilt manually. Verification for this docs-only slice used targeted stale-reference checks, `git diff --check`, and a changed-doc sanitization scan.
- Completed `DVSE-019` by moving Docs Viewer-owned Python tests and smoke scripts from `studio/tests/` into `docs-viewer/tests/`.
- Added `docs-viewer/tests/conftest.py` and `docs-viewer/tests/README.md` so Docs Viewer tests have local import-path setup and a discoverable boundary note while repo-level check profiles remain in `studio/commands/run_checks.py`.
- Updated `studio/commands/run_checks.py` so `quick`, `docs`, `docs-viewer-smoke`, and `studio-smoke` reference the moved test paths; `docs` now includes `docs-viewer/tests/python/test_docs_source_model.py`.
- Renamed moved Docs Viewer management smoke helpers from the old `local_studio_docs_management_*` names to `docs_viewer_management_*` and updated their local imports/docstrings for the Docs Viewer service boundary.
- Current docs with active test-path references were updated for the moved paths. Historical extraction/request docs were not exhaustively rewritten; broader command and service wording remains part of `DVSE-020`.
- Focused verification passed: Python compile for `run_checks.py`, `docs-viewer/tests/conftest.py`, all moved Docs Viewer Python tests, and moved Docs Viewer smoke scripts; 147 focused Docs Viewer pytest checks; sandboxed `docs-viewer-smoke` reproduced the expected localhost bind restriction; elevated `docs-viewer-smoke` passed all 7 checks; `quick` passed. Elevated smoke summary: `var/test-runs/docs-viewer-tests-boundary-elevated/summary.md`. Quick summary: `var/test-runs/docs-viewer-tests-boundary-quick/summary.md`. No generated docs/search payloads were rebuilt manually.
- Completed `DVSE-018` by adding the host-owned `bin/local-all` runner for public-site Live Preview, Local Studio, and Docs Viewer.
- `bin/local-all` loads `var/local/site.env`, resolves static host/port settings, checks for duplicate configured bindings, checks port availability before starting children, prints service URLs, starts the three existing independent entrypoints, traps shutdown signals, cleans up children, and reports the child name/status when a child exits.
- The existing independent start paths remain available: `bin/public-site-preview`, `bin/local-studio`, and `docs-viewer/bin/docs-viewer`.
- Source docs were updated for the start-all runner in the Local Studio runner, Studio, Docs Viewer dependency, and local setup environment docs.
- Focused verification passed: shell syntax for `bin/local-all`, `bin/local-studio`, `bin/public-site-preview`, and `docs-viewer/bin/docs-viewer`; isolated duplicate-binding failure smoke using a temporary copy of `bin/local-all`; stale start-all TODO copy check. No generated docs/search payloads were rebuilt manually.
- Completed `DVSE-017` by preserving the host-owned public read-only route contract while keeping New Scope creation inside the Docs Viewer boundary.
- `./docs-viewer/build/build_docs.rb --write` now refreshes both the full local Docs Viewer browser config and the public read-only config; the public config is projected from configured static route scopes and excludes the `/docs/` manage route.
- New Scope focused tests now pin that `public_readonly` scope creation writes a Jekyll route using `docs_viewer_readonly_route.html`, records the route file in the scope manifest, and configures route links without `scope` query parameters, while local-only scope creation skips public route files.
- Focused verification passed: Ruby syntax for `studio/docs-viewer/build/build_docs.rb`, Python compile for the touched focused tests, 34 focused pytest checks across Docs management service and Docs Viewer service, public Jekyll build to `/tmp/dlf-jekyll-build`, elevated public read-only smoke for `/library/` and `/analysis/`, and the `quick` profile. Quick summary: `var/test-runs/docs-viewer-public-route-ownership/summary.md`.
- Source docs were updated for Docs Viewer config generation and portable public scope setup. No generated docs/search payloads were rebuilt manually; local docs-watcher output may refresh published Studio docs/search JSON after these source edits.
- Completed `DVSE-016` by replacing Studio's old Docs Viewer proxy/hosting integration with configured peer-service links and endpoints.
- Local Studio runtime config now builds the `docs` view path, page implementation doc links, Docs Viewer service endpoints, generated reads, source-file open endpoint, and Data Sharing document endpoints from `DOCS_VIEWER_BASE_URL` in `var/local/site.env`; links are rendered without service availability probes.
- Removed the active `/studio/api/docs/...` handler path and deleted `studio/app/server/studio/studio_docs_api.py`; Local Studio no longer serves Docs Viewer management APIs, generated reads, or Data Sharing document routes.
- Studio Data Sharing and Project State browser modules now apply runtime-configured Docs Viewer service endpoints before probing or posting; unavailable-service UI copy now points users to `docs-viewer/bin/docs-viewer`.
- Focused tests and smokes were updated so Local Studio navigation/doc links expect peer-service Docs URLs, Data Sharing smokes mock direct Docs Viewer service paths, and Docs management fixture helpers import the Docs Viewer service directly.
- Focused verification passed: Python compile for changed server/test/smoke files, 33 focused pytest checks across Local Studio app server and Docs Viewer service config, JavaScript syntax checks for changed Studio modules, elevated Local Studio navigation smoke, elevated Local Studio Data Sharing route smoke, elevated Data Sharing prepare module smoke, elevated Data Sharing review/apply smoke, elevated Project State and Tag Groups route smokes, elevated Local Studio Docs Viewer boundary smoke, and the `quick` profile. Quick summary: `var/test-runs/docs-viewer-studio-peer-links/summary.md`.
- Source docs were updated for Local Studio, server architecture, Docs management service operations, Data Sharing, Project State, and portable Docs Viewer setup. No generated docs/search payloads were rebuilt manually; local docs-watcher output may refresh published Studio docs/search JSON after these source edits.
- Completed `DVSE-015` by moving `/docs/` manage-mode smoke coverage from Local Studio to the standalone Docs Viewer service and adding a Local Studio boundary smoke that proves `/docs/`, `/docs-viewer/runtime/`, and `/docs-viewer/static/` are no longer served by `StudioAppServer`.
- Local Studio no longer renders the Docs Viewer shell route or serves Docs Viewer runtime/static/config files; the temporary `/studio/api/docs/...` adapter noted in `DVSE-015` has now been removed by `DVSE-016`.
- Docs Viewer service smoke coverage now checks `/health`, `/capabilities`, loopback CORS rejection, `/docs/` manage shell root attributes, direct Docs Viewer service generated reads, direct management POSTs, Docs Broken Links report wiring, and absence of Studio/public host CSS in the standalone shell.
- Fixture-based Docs management workflow and UI smokes now start `DocsViewerServer` directly and call direct `/docs/...` management endpoints instead of `/studio/api/docs/docs/...`.
- Focused verification passed: Python compile for the changed service/server/test/check files, 61 focused pytest checks for Local Studio app server, Docs Viewer service, and Docs management service; elevated Local Studio boundary smoke; elevated standalone Docs Viewer manage shell smoke; elevated Docs Viewer management API workflow smoke; elevated Docs Viewer management UI workflow smoke; elevated Local Studio navigation adapter smoke; elevated `docs-viewer-smoke` profile. Profile summary: `var/test-runs/docs-viewer-service-boundary-elevated/summary.md`.
- Completed `DVSE-014` by adding the standalone Docs Viewer service shell at `docs-viewer/services/docs_viewer_service.py`, with the service launcher `docs-viewer/bin/docs-viewer` and service-owned shell template `docs-viewer/shell/docs-viewer-shell.html`.
- The standalone service reads `DOCS_VIEWER_HOST`, `DOCS_VIEWER_PORT`, `DOCS_VIEWER_BASE_URL`, `DOCS_VIEWER_MANAGEMENT_ENABLED`, `DOCS_VIEWER_GENERATED_READS_ENABLED`, and `DOCS_VIEWER_WATCH_ENABLED` from `var/local/site.env`, validates loopback-only local binding, and fails clearly when configured service settings are invalid or the port is unavailable.
- Built-in `/docs/` manage mode is now available from the Docs Viewer service, with Docs Viewer assets served from `/docs-viewer/`, generated reads and management requests using the configured Docs Viewer service base URL, and management markup gated by the local capability flag.
- The service exposes `/health`, `/capabilities`, generated read endpoints, data-sharing endpoints, local write endpoints, CORS-limited loopback APIs, and scoped static serving for Docs Viewer runtime/config/static and public generated docs assets.
- `_config.yml` now excludes `docs-viewer/bin/`, `docs-viewer/services/`, and `docs-viewer/shell/` from public Jekyll output while leaving browser-safe Docs Viewer runtime/static/config assets publishable.
- Focused tests were added in `studio/tests/python/test_docs_viewer_service.py` for static service config, local-only validation, manage shell attributes, capability flag shaping, and static path policy.
- Focused verification passed: `py_compile` for the new service/test, 32 focused Python tests across the standalone Docs Viewer service and shared management dispatcher, `docs-viewer/bin/docs-viewer --help`, public Jekyll build to `/tmp/dlf-jekyll-build`, built-output checks confirming service/shell/bin files are excluded while runtime/static assets remain publishable, and an elevated loopback startup/API smoke on `127.0.0.1:8916` for `/health`, `/capabilities`, and `/docs/?scope=studio&doc=docs-viewer&mode=manage`.
- Source docs were updated for the standalone service, shell ownership, config split, portable file manifest, source-tree ownership, and Jekyll exclusion contract. No generated docs/search payloads were rebuilt manually; local docs-watcher output may refresh published Studio docs/search JSON after these source edits.
- Completed `DVSE-013` by moving Docs Viewer service modules from `studio/docs-viewer/services/*.py` to `docs-viewer/services/*.py`.
- Moved service ownership includes management dispatch, route constants, generated-data reads, source/scope config helpers, mutation/write workflows, import/export helpers, broken-links auditing, data-sharing adapter, watcher suppression, and the live rebuild watcher.
- At the time of `DVSE-013`, Local Studio imported Docs management behavior from `docs-viewer/services/` through `studio/app/server/studio/studio_docs_api.py`; `DVSE-016` later removed that adapter from the active server path.
- Repo Python path bootstrap, run-check compile paths, projection contract paths, and focused docs tests now use the `docs-viewer/services/` boundary.
- Direct CLI help checks passed for `docs_live_rebuild_watcher.py`, `docs_export.py`, `docs_import.py`, `docs_html_import.py`, and `docs_broken_links.py`; `docs_scope_config.default_repo_root()` now resolves the repo root without relying on Studio's path helper.
- Focused verification passed: service compile check, 139 focused docs Python tests, Local Studio app server pytest (29 tests), elevated Local Studio Docs Viewer management smoke, and `quick` profile. Quick summary: `var/test-runs/20260525-112252/summary.md`.
- Live code/test/check reference checks found no remaining `studio/docs-viewer/services/` or old `scripts/docs/` service paths. Old `studio/docs-viewer/services/__pycache__/` files were left for the later cleanup task; no source `.py` files remain there.
- Source docs for the management service, watcher, Local Studio runner/app, management contract, and portable file manifest were updated for the moved service paths. Generated Studio docs/search JSON may have been refreshed by the local docs watcher; no manual docs/search rebuild was run.
- Completed `DVSE-012` with the broader browser runtime/CSS/static verification pass.
- Elevated `docs-viewer-smoke` passed all 6 checks: temporary Jekyll build, public Docs Viewer read-only smoke, index-panel module smoke, management modal smoke, management action workflow module smoke, and Docs HTML import module smoke. Summary: `var/test-runs/20260525-110629/summary.md`.
- Targeted built-page reference checks confirmed `/library/` and `/analysis/` load `/docs-viewer/static/css/docs-viewer-base.css`, `/docs-viewer/static/css/docs-viewer.css`, `/docs-viewer/static/css/docs-viewer-reports.css`, and `/docs-viewer/runtime/js/docs-viewer.js`, with no old `/studio/docs-viewer/runtime/` or `/studio/docs-viewer/assets/` paths.
- Targeted source reference checks found old Docs Viewer browser/static paths only in intentional negative tests and historical/request docs, not in live shell/server/test surfaces.
- A focused elevated desktop/mobile public layout smoke passed for built `/library/` and `/analysis/`, confirming public main CSS remains the host base, management CSS and Studio CSS are absent, runtime/static assets come from `docs-viewer/`, and desktop columns/mobile stacking still behave.
- JavaScript syntax passed for all `docs-viewer/runtime/js/**/*.js` files with `node --check`.
- No generated docs/search payloads were rebuilt manually. Source tracker edits may be refreshed into published Studio docs/search JSON by the local docs watcher.
- Completed `DVSE-011` by adding `docs-viewer/static/css/docs-viewer-base.css` as the explicit Docs Viewer base contract.
- The shared Docs Viewer include now loads base, viewer, and report CSS for public read-only routes, and adds management CSS only for management-enabled shells.
- The base stylesheet is intentionally scoped: public `/library/` and `/analysis/` can keep inheriting public `assets/css/main.css`, while standalone/local Docs Viewer shells can opt into Docs Viewer-owned body/container defaults without relying on public `main.css` or Studio CSS.
- `docs-viewer/static/css/docs-viewer.css` now resolves component color/radius tokens through explicit Docs Viewer theme variables, then Docs Viewer base variables, then host tokens and portable fallbacks.
- Focused verification passed: Local Studio app server pytest, public Jekyll build to `/tmp/dlf-jekyll-build`, elevated public Docs Viewer read-only smoke for `/library/` and `/analysis/`, and elevated Local Studio Docs Viewer management smoke.
- Source docs were updated for the CSS base contract and current `docs-viewer/` CSS/runtime paths. No generated docs/search payloads were rebuilt manually; local docs-watcher output may have refreshed the published Studio docs/search JSON after source doc edits.
- Completed `DVSE-010` by moving Docs Viewer browser runtime modules from `studio/docs-viewer/runtime/js/` to `docs-viewer/runtime/js/` and reusable/management CSS from `studio/docs-viewer/assets/css/` to `docs-viewer/static/css/`.
- Public route shells and Local Studio's temporary manage shell now reference `/docs-viewer/runtime/js/docs-viewer.js` and `/docs-viewer/static/css/docs-viewer*.css`; old `/studio/docs-viewer/runtime/` and `/studio/docs-viewer/assets/` static serving was removed rather than shimmed.
- Focused reference checks found no old Studio-owned runtime/static browser paths in the live shell/server/test surfaces. Remaining `studio/docs-viewer/...` references are for later service/build/docs slices or negative tests.
- JavaScript syntax passed for all moved `docs-viewer/runtime/js/**/*.js` modules with `node --check`.
- Python compile passed for Local Studio server/config/view modules, and focused Local Studio server pytest passed: 29 tests.
- Public Jekyll build passed to `/tmp/dlf-jekyll-build`; built `/library/` and `/analysis/` load the moved `/docs-viewer/static/` CSS and `/docs-viewer/runtime/` module, and no old `/studio/docs-viewer/runtime/` or `/studio/docs-viewer/assets/` paths appear in those built pages.
- Focused browser module smokes passed after rerunning elevated for sandbox loopback binding: index panel modules, Docs HTML import modules, management action workflow modules, and management modal coverage across desktop/mobile viewports.
- No generated docs/search payloads were rebuilt manually for the runtime/static move; `DVSE-012` has now completed the broader verification pass.

### completed earlier

- `DVSE-002` through `DVSE-009` are complete; the durable details live in the sibling docs for [Inventory](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-inventory), [Ownership Contract](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-ownership-contract), [Target Layout](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-target-layout), and [Baseline](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-baseline).
- Key carried decisions: use top-level `docs-viewer/` as the tracked extraction boundary; keep host/Jekyll public routes and generated docs/search outputs outside that boundary; avoid old `/studio/docs-viewer/...` compatibility shims; keep Local Studio as a peer integration after the service move; keep public read-only routes host-owned; keep manage mode local-only with explicit capability flags.
- Baseline evidence remains valid for comparison: `quick`, elevated `docs-viewer-smoke`, focused Local Studio Docs Viewer management smoke, dry-run docs/search builders for Studio/Library/Analysis, and public Jekyll build passed. The first sandboxed localhost smoke failed due to Codex localhost binding restrictions and passed when rerun elevated.
- Known carried issue: Analysis still has unresolved semantic reference `work:00638002` from `analysis/3-symbols`; treat this as pre-existing unless the active task touches semantic references.
- Generated Docs Viewer payloads may be refreshed by the local docs watcher when this source file changes. Do not manually rebuild generated docs/search payloads unless the active task explicitly requires it.

### steer for next task

- No remaining sequential task in this tracker.
- Treat the extracted Docs Viewer boundary as current state: `docs-viewer/` owns source docs, runtime, CSS, config defaults, UI text, build scripts, standalone service, management dispatcher, generated reads, import/export, live rebuild, and Docs Viewer-owned tests.
- Keep Local Studio as a peer integration that links to the configured Docs Viewer service; do not reintroduce Local Studio hosting for `/docs/`, `/docs-viewer/runtime/`, `/docs-viewer/static/`, or `/studio/api/docs/...`.
- Keep public `/library/` and `/analysis/` read-only routes Jekyll-hosted and host-owned while using Docs Viewer runtime/config/build contracts.
- Keep generated docs/search payload locations stable under `assets/data/docs/scopes/<scope>/` and `assets/data/search/<scope>/`.
- Future portability work should continue from [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer), not from this archived extraction tracker.
- Keep the table sequential: only begin the next non-deferred ID after the current one is `done`.
- If a task uncovers a new dependency, risk, or unresolved ownership question, add a new task row before continuing rather than widening the active task.
- Bunch work into coherent slices that reduce repeated verification, but do not combine tasks when the second task depends on evidence from the first.
- Put inventory-style tables in sibling documents, not in this task tracker.
- Keep `docs-viewer/` tracked in this repo for this extraction; defer package/submodule treatment until after the standalone service works.
- Keep Docs Viewer self-contained under `docs-viewer/`; do not leave hidden dependencies on Studio paths, Studio shell, or Studio runtime config.
- Use static Docs Viewer host, port, and base URL settings from `var/local/site.env` for v1.
- Render configured Docs Viewer links without probing service availability; if Docs Viewer is not running, links should fail normally.
- Preserve route ownership: Docs Viewer service owns built-in `/docs/` manage mode; public read-only scopes such as `/library/` and `/analysis/` remain repo/Jekyll-hosted routes installed or registered through Docs Viewer scope machinery.
- Keep manage mode local-only for v1 through loopback binding and explicit local capability flags.
- Use a lightweight `bin/local-studio`-style runner for the "start all" workflow; do not introduce a third-party process manager in v1.
- Do not rebuild generated docs/search payloads manually unless the active task explicitly requires it.
- Before archiving this request and tracker, copy any durable implementation decisions, contracts, command behavior, and close-out notes into permanent owning docs.

### baseline verification set

Use this set before and after extraction slices when the touched area warrants it:

- Core checks: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick`.
- Docs Viewer smoke checks: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke`.
- Local Studio smoke checks that prove Studio links and integration still work.
- Public Jekyll build check: `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`.
- Public scope checks for `/library/` and `/analysis/` when scope registration, generated payload locations, route shells, or public Docs Viewer runtime behavior changes.
- Focused Python, Ruby, and JavaScript syntax/import checks for moved files.
- Focused tests for Docs Viewer management write APIs, source/scope config, New Scope, generated-data builders, and local service launchers when those areas move.

Codex sandbox note: local service, browser, and temporary localhost checks may need elevated permissions even when the product code is healthy.

### general steer

- Treat this as an extraction and service-boundary migration, not a product redesign.
- Keep public GitHub Pages/Jekyll compatibility as a hard constraint.
- Keep Local Studio, Live Preview, and Docs Viewer as independent services.
- Prefer direct reference updates over compatibility shims for old Studio-owned Docs Viewer paths.
- Keep generated public docs/search payload locations stable until a specific task proves the config contract can safely move or abstract them.
- Keep public read-only route shells minimal and host-owned; Docs Viewer owns the scripts, scope machinery, generated-data contracts, and built-in `/docs/` manage route.
- Keep loopback binding, explicit write capability flags, write allowlists, compact logs, preview/apply boundaries, and backup behavior for local manage/write paths.
- During inventory, explicitly capture current-state docs that will need permanent updates after extraction, including standalone Docs Viewer service ownership, start-all runner behavior, route ownership, config paths, and CSS/base-shell assumptions.
- Use sibling docs for large inventories, target layouts, contract tables, or path maps so this tracker remains a concise sequential task list.

## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action. Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| DVSE-001 | done | Create this child task tracker with a Codex handover status section and a single sequential implementation table using the allowed statuses `planned`, `in progress`, `done`, and `deferred`. |
| DVSE-002 | done | Re-read the parent request decisions and owning docs for Docs Viewer, portable setup, runtime boundary, source organisation, config, scripts, local setup, and testing; update this tracker if any parent decision is missing or contradicted by an owning doc. |
| DVSE-003 | done | Inventory current Docs Viewer paths, imports, URL assumptions, generated payload reads/writes, service endpoints, CSS dependencies, scope/source config, tests, smoke scripts, and Studio/Jekyll integration points; record the inventory in a sibling doc such as `site-request-docs-viewer-shell-extraction-inventory.md`. |
| DVSE-004 | done | Resolve ambiguous ownership from the inventory before moving files; add sibling contract docs or new task rows for any unclear areas such as shell include ownership, public route adapters, Studio link behavior, `/studio/api/docs/*` endpoint mapping, Docs Viewer data-sharing APIs, generated payload locations, New Scope outputs, report inputs, local write APIs, docs watcher ownership, cleanup hygiene, or CSS base dependencies. |
| DVSE-005 | done | Define the target `docs-viewer/` layout, host integration surfaces, and stable public/Jekyll route responsibilities in a sibling target-layout or contract doc; do not start broad file moves until this layout is recorded. |
| DVSE-006 | done | Establish the baseline verification run for the current integrated tree, including the smallest useful Docs Viewer, Local Studio, public scope, build, and syntax checks needed to compare before and after extraction slices. |
| DVSE-007 | done | Introduce v1 Docs Viewer local service config using static `var/local/site.env` host, port, base URL, and manage capability settings; add only the necessary `_config.yml`, `.gitignore`, and `docs-viewer/config/` defaults/schema changes, with no dynamic runtime advertisement writer. |
| DVSE-008 | done | Move Docs Viewer-owned config, source/scope machinery, generated-data contract defaults, UI text, and non-runtime metadata into the tracked `docs-viewer/` boundary; update readers/writers directly and keep repo-local host/service state outside `docs-viewer/`. |
| DVSE-009 | done | Verify the config/source/scope move with focused syntax checks, dry-run builders where useful, source config validation, and public scope checks that prove generated JSON/search payload outputs still land where Jekyll routes expect them. |
| DVSE-010 | done | Move Docs Viewer browser runtime modules, rendering/search/router/report/bookmark/favourites code, reusable CSS, management CSS, and static assets into `docs-viewer/`; update public route shells, module imports, and asset references without adding old-path compatibility shims. |
| DVSE-011 | done | Define and apply the CSS base contract for standalone Docs Viewer pages, public read-only host routes, and local manage mode; add a Docs Viewer-owned base stylesheet if the host contract is not enough. |
| DVSE-012 | done | Verify the browser runtime/CSS/static move with Docs Viewer smoke checks, public `/library/` and `/analysis/` checks, desktop/mobile layout checks where relevant, and targeted JavaScript/CSS reference checks. |
| DVSE-013 | done | Move Docs Viewer service modules, management write workflows, local write API contracts, docs watcher or rebuild helpers owned by Docs Viewer, and shell server entrypoints into `docs-viewer/`; keep manage mode loopback-only with explicit local capability flags. |
| DVSE-014 | done | Implement the standalone Docs Viewer service shell for built-in `/docs/` manage mode using static `var/local/site.env` service location, clear port-unavailable failure, normal link failure when the service is stopped, and no deployed live manage-mode assumption. |
| DVSE-015 | done | Verify the service/API/shell move with focused Python syntax/import checks, management workflow tests, loopback/startup checks, `/docs/` manage-mode smoke coverage, and checks that Local Studio no longer hosts the Docs Viewer shell. |
| DVSE-016 | done | Replace Studio-specific Docs Viewer hosting behavior with Studio integration/link behavior that points to the configured Docs Viewer service; keep Studio navigation and UI links as peer-service integration, not embedded Docs Viewer hosting. |
| DVSE-017 | done | Preserve and verify public scope route ownership: New Scope continues to create or register static/Jekyll-compatible routes such as `/library/` and `/analysis/`, using `docs-viewer/` scripts and contracts while the pages remain repo/Jekyll-hosted. |
| DVSE-018 | done | Add the lightweight "start all" runner for Live Preview, Local Studio, and Docs Viewer, modeled on `bin/local-studio`: load `var/local/site.env`, validate static ports, print URLs, trap shutdown signals, clean up children, and fail clearly on child-process exits. |
| DVSE-019 | done | Move or update tests, smoke helpers, fixtures, checks, and run-check profiles so Docs Viewer-owned checks live with the new boundary where appropriate while repo/Codex verification entrypoints remain discoverable. |
| DVSE-020 | done | Update command docs, local setup docs, Docs Viewer portable setup, runtime boundary docs, source organisation docs, config docs, and script docs to describe the extracted boundary, service config, route ownership, runner behavior, standalone Docs Viewer service ownership, and retired current-state assumptions. |
| DVSE-021 | done | Delete old Studio-owned Docs Viewer source locations after references are updated; confirm removed paths are not retained through import aliases, copied files, static mount shims, or dual-read fallback logic. |
| DVSE-022 | done | Run the agreed final verification set: quick profile, Docs Viewer smoke profile, focused Local Studio integration smokes, public Jekyll build, public scope checks, syntax/import checks, and any changed-doc link/path checks. |
| DVSE-023 | done | Close out the parent request and this tracker: update statuses, summarize moved paths, record verification results and generated payload status, create structured docs-log entries, copy durable decisions/contracts into permanent owning docs, and note remaining risks before these request docs are archived. |
