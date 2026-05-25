---
doc_id: site-request-docs-viewer-shell-extraction-tasks
title: Docs Viewer Shell Extraction Tasks
added_date: 2026-05-24
last_updated: 2026-05-25
ui_status: draft
parent_id: site-request-docs-viewer-shell-extraction
sort_order: 10021
viewable: true
---
# Docs Viewer Shell Extraction Tasks

This is the tracker for implementing [Docs Viewer Shell Extraction Request](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction).

## Status

### just done

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

- Start with `DVSE-013`, moving Docs Viewer service modules, management write workflows, local write API contracts, docs watcher or rebuild helpers owned by Docs Viewer, and shell server entrypoints into `docs-viewer/`.
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
| DVSE-013 | planned | Move Docs Viewer service modules, management write workflows, local write API contracts, docs watcher or rebuild helpers owned by Docs Viewer, and shell server entrypoints into `docs-viewer/`; keep manage mode loopback-only with explicit local capability flags. |
| DVSE-014 | planned | Implement the standalone Docs Viewer service shell for built-in `/docs/` manage mode using static `var/local/site.env` service location, clear port-unavailable failure, normal link failure when the service is stopped, and no deployed live manage-mode assumption. |
| DVSE-015 | planned | Verify the service/API/shell move with focused Python syntax/import checks, management workflow tests, loopback/startup checks, `/docs/` manage-mode smoke coverage, and checks that Local Studio no longer hosts the Docs Viewer shell. |
| DVSE-016 | planned | Replace Studio-specific Docs Viewer hosting behavior with Studio integration/link behavior that points to the configured Docs Viewer service; keep Studio navigation and UI links as peer-service integration, not embedded Docs Viewer hosting. |
| DVSE-017 | planned | Preserve and verify public scope route ownership: New Scope continues to create or register static/Jekyll-compatible routes such as `/library/` and `/analysis/`, using `docs-viewer/` scripts and contracts while the pages remain repo/Jekyll-hosted. |
| DVSE-018 | planned | Add the lightweight "start all" runner for Live Preview, Local Studio, and Docs Viewer, modeled on `bin/local-studio`: load `var/local/site.env`, validate static ports, print URLs, trap shutdown signals, clean up children, and fail clearly on child-process exits. |
| DVSE-019 | planned | Move or update tests, smoke helpers, fixtures, checks, and run-check profiles so Docs Viewer-owned checks live with the new boundary where appropriate while repo/Codex verification entrypoints remain discoverable. |
| DVSE-020 | planned | Update command docs, local setup docs, Docs Viewer portable setup, runtime boundary docs, source organisation docs, config docs, and script docs to describe the extracted boundary, service config, route ownership, runner behavior, standalone Docs Viewer service ownership, and retired current-state assumptions. |
| DVSE-021 | planned | Delete old Studio-owned Docs Viewer source locations after references are updated; confirm removed paths are not retained through import aliases, copied files, static mount shims, or dual-read fallback logic. |
| DVSE-022 | planned | Run the agreed final verification set: quick profile, Docs Viewer smoke profile, focused Local Studio integration smokes, public Jekyll build, public scope checks, syntax/import checks, and any changed-doc link/path checks. |
| DVSE-023 | planned | Close out the parent request and this tracker: update statuses, summarize moved paths, record verification results and generated payload status, create structured docs-log entries, copy durable decisions/contracts into permanent owning docs, and note remaining risks before these request docs are archived. |
