---
doc_id: site-request-docs-viewer-shell-extraction-tasks
title: Docs Viewer Shell Extraction Tasks
added_date: 2026-05-24
last_updated: 2026-05-24
ui_status: draft
parent_id: site-request-docs-viewer-shell-extraction
sort_order: 10021
viewable: true
---
# Docs Viewer Shell Extraction Tasks

This is the tracker for implementing [Docs Viewer Shell Extraction Request](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction).

## Status

### just done

- Completed `DVSE-007` by introducing the v1 static Docs Viewer local service config surfaces without adding a runtime advertisement writer or moving implementation files.
- Added tracked Docs Viewer service defaults and schema under `.docs-viewer/config/`, including loopback-only binding policy, stable manage/API route names, local capability defaults, and host-owned local state paths.
- Added static host/Jekyll defaults to `_config.yml`: Docs Viewer links remain enabled, public routes do not require the local service, and fallback behavior stays host-route based.
- Added `.gitignore` coverage for future `.docs-viewer/` local runtime state such as cache, temp, logs, run, and var directories.
- Added ignored local `var/local/site.env` defaults for `DOCS_VIEWER_HOST`, `DOCS_VIEWER_PORT`, `DOCS_VIEWER_BASE_URL`, `DOCS_VIEWER_MANAGEMENT_ENABLED`, `DOCS_VIEWER_GENERATED_READS_ENABLED`, and `DOCS_VIEWER_WATCH_ENABLED`.
- Verification passed: JSON parse/basic config assertion for `.docs-viewer/config/`, `_config.yml` YAML parse/key assertion, and public Jekyll build to `/tmp/dlf-jekyll-build`.
- Completed `DVSE-006` by establishing the current integrated-tree baseline before extraction file moves.
- Recorded the baseline in [Docs Viewer Shell Extraction Baseline](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-baseline).
- Baseline passed: `quick` profile, elevated `docs-viewer-smoke` profile, focused Local Studio Docs Viewer management shell smoke, dry-run docs builders for Studio/Library/Analysis, and dry-run search builders for Studio/Library/Analysis.
- First `docs-viewer-smoke` attempt failed because the Codex sandbox blocked temporary localhost binding; the elevated rerun passed, so treat the initial failure as an environment permission issue.
- Builder dry runs reported no generated payload drift. Analysis retains the known unresolved semantic reference `work:00638002` from `analysis/3-symbols`.
- Did not manually rebuild generated docs/search payloads.
- Completed `DVSE-005` by defining the target `.docs-viewer/` layout, host integration surfaces, public/Jekyll route responsibilities, URL conventions, config layers, shell/adapter split, service model, builder/generated output model, test layout, and move-sequence constraints.
- Recorded the layout in [Docs Viewer Shell Extraction Target Layout](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-target-layout).
- Target shape keeps `.docs-viewer/` tracked and self-contained for runtime, shell templates, services, config defaults/schema, source, builders, static CSS/assets, and Docs Viewer-owned tests.
- Host-owned surfaces remain outside `.docs-viewer/`: `_config.yml`, thin Jekyll route adapters, public route files such as `/library/` and `/analysis/`, generated docs/search payload locations, public media assets, `var/local/site.env`, `var/docs/`, Studio link integration, root script wrappers, and repo-level check entrypoints.
- Confirmed no compatibility aliases should be added for old `/studio/docs-viewer/...` browser paths; later move slices should update references directly and delete old paths after verification.
- Did not manually rebuild generated docs/search payloads.
- Completed `DVSE-004` by resolving the ambiguous ownership points from the inventory before target layout or file moves.
- Recorded the ownership decisions in [Docs Viewer Shell Extraction Ownership Contract](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-ownership-contract).
- Key decisions: shell markup is split between a Docs Viewer-owned reusable shell contract and host-owned adapters; built-in `/docs/` manage mode moves to the Docs Viewer service; public scope routes stay host/Jekyll-owned; generated docs/search payloads remain host public output for v1; Docs Viewer owns management APIs, generated reads, source/scope machinery, report schema/loader contract, docs watcher behavior, and reusable runtime/CSS.
- Kept endpoint names stable for v1 while changing the service owner from Local Studio to Docs Viewer service; Studio should link to configured service URLs without probing and should not proxy or host Docs Viewer after migration.
- Did not add new implementation rows from `DVSE-004`; existing tasks already cover target layout, config, moves, CSS contract, service shell, Studio link integration, public route preservation, runner, tests, docs, cleanup, and final verification.
- Did not manually rebuild generated docs/search payloads.
- Completed `DVSE-003` by inventorying current Docs Viewer paths, imports, URL assumptions, generated payload reads/writes, service endpoints, CSS dependencies, scope/source config, tests, smoke scripts, and Studio/Jekyll integration points.
- Recorded the inventory in [Docs Viewer Shell Extraction Inventory](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-shell-extraction-inventory).
- Confirmed the current tree already has a coherent interim Docs Viewer home at `studio/docs-viewer/`, while Jekyll route shells, generated payloads, public assets, Local Studio hosting, and check profiles remain outside it.
- Confirmed new or clarified ownership questions for `DVSE-004`, especially shell include ownership, Local Studio link behavior, `/studio/api/docs/*` endpoint mapping, Docs Viewer data-sharing API ownership, report registry ownership, scope lifecycle route outputs, CSS base contract, generated output ownership, docs watcher ownership, and cleanup of current `.DS_Store` / `__pycache__` noise.
- Did not rebuild generated docs/search payloads.
- Completed `DVSE-002` by reviewing the parent request against the owning Docs Viewer, portable setup, runtime boundary, source organisation, config, scripts, local setup, and testing docs.
- Found no blocker to the parent decisions.
- Confirmed that several owning docs intentionally describe the current integrated state and will need durable updates during `DVSE-020`, especially:
  - `scripts-docs-management-server`: currently says there is no standalone Docs Management server process because Local Studio owns HTTP transport today.
  - `scripts-local-studio`: currently says not to use a combined Studio-plus-Jekyll runner for normal work.
  - `docs-viewer-runtime-boundary`, `config-docs-viewer`, and portable setup docs still contain current-state path and route assumptions that the extraction will replace.
- Treat those differences as expected current-state documentation, not contradictions that block extraction planning.
- Generated Docs Viewer payloads may be refreshed by the local docs watcher when this source file changes.

### steer for next task

- Start with `DVSE-008`, moving Docs Viewer-owned config, source/scope machinery, generated-data contract defaults, UI text, and non-runtime metadata into `.docs-viewer/`.
- Keep the table sequential: only begin the next non-deferred ID after the current one is `done`.
- If a task uncovers a new dependency, risk, or unresolved ownership question, add a new task row before continuing rather than widening the active task.
- Bunch work into coherent slices that reduce repeated verification, but do not combine tasks when the second task depends on evidence from the first.
- Put inventory-style tables in sibling documents, not in this task tracker.
- Keep `.docs-viewer/` tracked in this repo for this extraction; defer package/submodule treatment until after the standalone service works.
- Keep Docs Viewer self-contained under `.docs-viewer/`; do not leave hidden dependencies on Studio paths, Studio shell, or Studio runtime config.
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
| DVSE-005 | done | Define the target `.docs-viewer/` layout, host integration surfaces, and stable public/Jekyll route responsibilities in a sibling target-layout or contract doc; do not start broad file moves until this layout is recorded. |
| DVSE-006 | done | Establish the baseline verification run for the current integrated tree, including the smallest useful Docs Viewer, Local Studio, public scope, build, and syntax checks needed to compare before and after extraction slices. |
| DVSE-007 | done | Introduce v1 Docs Viewer local service config using static `var/local/site.env` host, port, base URL, and manage capability settings; add only the necessary `_config.yml`, `.gitignore`, and `.docs-viewer/config/` defaults/schema changes, with no dynamic runtime advertisement writer. |
| DVSE-008 | planned | Move Docs Viewer-owned config, source/scope machinery, generated-data contract defaults, UI text, and non-runtime metadata into the tracked `.docs-viewer/` boundary; update readers/writers directly and keep repo-local host/service state outside `.docs-viewer/`. |
| DVSE-009 | planned | Verify the config/source/scope move with focused syntax checks, dry-run builders where useful, source config validation, and public scope checks that prove generated JSON/search payload outputs still land where Jekyll routes expect them. |
| DVSE-010 | planned | Move Docs Viewer browser runtime modules, rendering/search/router/report/bookmark/favourites code, reusable CSS, management CSS, and static assets into `.docs-viewer/`; update public route shells, module imports, and asset references without adding old-path compatibility shims. |
| DVSE-011 | planned | Define and apply the CSS base contract for standalone Docs Viewer pages, public read-only host routes, and local manage mode; add a Docs Viewer-owned base stylesheet if the host contract is not enough. |
| DVSE-012 | planned | Verify the browser runtime/CSS/static move with Docs Viewer smoke checks, public `/library/` and `/analysis/` checks, desktop/mobile layout checks where relevant, and targeted JavaScript/CSS reference checks. |
| DVSE-013 | planned | Move Docs Viewer service modules, management write workflows, local write API contracts, docs watcher or rebuild helpers owned by Docs Viewer, and shell server entrypoints into `.docs-viewer/`; keep manage mode loopback-only with explicit local capability flags. |
| DVSE-014 | planned | Implement the standalone Docs Viewer service shell for built-in `/docs/` manage mode using static `var/local/site.env` service location, clear port-unavailable failure, normal link failure when the service is stopped, and no deployed live manage-mode assumption. |
| DVSE-015 | planned | Verify the service/API/shell move with focused Python syntax/import checks, management workflow tests, loopback/startup checks, `/docs/` manage-mode smoke coverage, and checks that Local Studio no longer hosts the Docs Viewer shell. |
| DVSE-016 | planned | Replace Studio-specific Docs Viewer hosting behavior with Studio integration/link behavior that points to the configured Docs Viewer service; keep Studio navigation and UI links as peer-service integration, not embedded Docs Viewer hosting. |
| DVSE-017 | planned | Preserve and verify public scope route ownership: New Scope continues to create or register static/Jekyll-compatible routes such as `/library/` and `/analysis/`, using `.docs-viewer/` scripts and contracts while the pages remain repo/Jekyll-hosted. |
| DVSE-018 | planned | Add the lightweight "start all" runner for Live Preview, Local Studio, and Docs Viewer, modeled on `bin/local-studio`: load `var/local/site.env`, validate static ports, print URLs, trap shutdown signals, clean up children, and fail clearly on child-process exits. |
| DVSE-019 | planned | Move or update tests, smoke helpers, fixtures, checks, and run-check profiles so Docs Viewer-owned checks live with the new boundary where appropriate while repo/Codex verification entrypoints remain discoverable. |
| DVSE-020 | planned | Update command docs, local setup docs, Docs Viewer portable setup, runtime boundary docs, source organisation docs, config docs, and script docs to describe the extracted boundary, service config, route ownership, runner behavior, standalone Docs Viewer service ownership, and retired current-state assumptions. |
| DVSE-021 | planned | Delete old Studio-owned Docs Viewer source locations after references are updated; confirm removed paths are not retained through import aliases, copied files, static mount shims, or dual-read fallback logic. |
| DVSE-022 | planned | Run the agreed final verification set: quick profile, Docs Viewer smoke profile, focused Local Studio integration smokes, public Jekyll build, public scope checks, syntax/import checks, and any changed-doc link/path checks. |
| DVSE-023 | planned | Close out the parent request and this tracker: update statuses, summarize moved paths, record verification results and generated payload status, create structured docs-log entries, copy durable decisions/contracts into permanent owning docs, and note remaining risks before these request docs are archived. |
