---
doc_id: site-request-studio-source-tree-reorganization-tasks
title: Studio Source Tree Reorganization Tasks
added_date: 2026-05-24
last_updated: 2026-05-24
ui_status: in-progress
parent_id: site-request-studio-source-tree-reorganization
sort_order: 10011
viewable: true
---
# Studio Source Tree Reorganization Tasks

This is the tracker for implementing [Studio Source Tree Reorganization Request](/docs/?scope=studio&mode=manage&doc=site-request-studio-source-tree-reorganization).

## Status

### just done

- Completed `STSR-008` by moving the first canonical source/config slice under `studio/`.
- Moved Docs Viewer source Markdown from `_docs/`, `_docs_library/`, and `_docs_analysis/` to `studio/docs-viewer/source/studio/`, `studio/docs-viewer/source/library/`, and `studio/docs-viewer/source/analysis/`.
- Moved catalogue canonical JSON and publishing Markdown to `studio/data/canonical/catalogue/` and `studio/data/canonical/catalogue-markdown/`.
- Moved analytics/tag canonical JSON to `studio/data/canonical/analytics/`, with hyphenated filenames such as `tag-registry.json`, `tag-aliases.json`, and `tag-assignments.json`.
- Moved Studio config/data source to `studio/data/config/`, `studio/app/frontend/config/`, and Studio-generated read models to `studio/data/generated/`.
- Moved change-request workflow source from `_docs_logs/` to `studio/workflows/change-requests/`, with entry records under `studio/workflows/change-requests/logs/entries/`.
- Updated readers/writers, configs, checks, and tests to read the new paths directly; no old-path source aliases or dual-read fallback logic were added.
- Generated public docs/search payloads were intentionally not rebuilt. `scripts/build_docs.rb --scope studio` dry-run read `studio/docs-viewer/source/studio` successfully and reported one changed doc payload.
- Verification passed: focused Python pytest set for Docs Viewer source/generated reads, docs-log indexes, tags data sharing, and Studio app server; 59 passed.
- Verification passed: focused Catalogue source/prose/lookup pytest set; 25 passed.
- Verification passed: `scripts/checks/audit_projection_contract.py`.
- Verification passed: `./scripts/run_checks.py --profile quick --run-id stsr-008-canonical-move-quick-3`; summary: `var/test-runs/stsr-008-canonical-move-quick-3/summary.md`.

### steer for next task

- Start with `STSR-009`; verify the canonical-data move from the public-site side.
- Confirm public Jekyll still receives and serves existing generated JSON/assets without reading canonical source directly.
- Keep generated docs/search payloads untouched unless the active verification step explicitly requires a rebuild.
- Treat the table as sequential: only begin the next non-deferred ID after the current one is `done`.
- Treat current `assets/docs-viewer/` and current `scripts/docs/` as Docs Viewer-owned runtime/service inputs for later move slices; separate them from generated public docs/search payloads.
- Treat `scripts/docs_logs/` as Studio-owned change request workflow service code for a later service move; generated log/report artifacts may be consumed by Codex or surfaced through `/docs/`, but that does not transfer source ownership to Docs Viewer.
- Treat Docs Viewer reports as cross-domain readers: report source/config/runtime belongs with Docs Viewer, while report input data belongs with the domain that owns it.
- Treat `studio/data/canonical/catalogue-markdown/` as Studio-owned canonical publishing Markdown, not Docs Viewer-owned source.
- Treat current Jekyll-shaped Studio and UI Catalogue artifacts as cleanup targets, not as acceptable final ownership. `_includes/studio_header_nav.html` and `_includes/studio_module_script.html` were removed in `STSR-007`; remaining `_layouts/studio.html` usage is a UI Catalogue cleanup/move dependency.
- Treat Docs Viewer `_includes/` route files as route-integration debt to decide deliberately: public read-only route adapters may remain minimal Jekyll integration, but Docs Viewer shell/config/runtime source should live under Docs Viewer.
- Treat `studio/data/generated/catalogue-lookup/` as Studio-generated lookup/read-model data for editors, not public page data; disposable lookup/cache state belongs under `var/`.
- Treat checks and tests as Studio/Codex development infrastructure even when they validate the public published surface.
- Treat public-site build/preview commands as Studio/Codex development tooling, with only deliberate root convenience entrypoints allowed.
- Treat Catalogue search generation/policy as Studio-owned, Docs Viewer search generation/config as Docs Viewer-owned, and public search route JavaScript/payloads as public runtime/output.
- Use later moves to remove remaining root/public Studio source surfaces without reintroducing `_docs_logs/` or `_docs_catalogue/` naming.
- Preserve Docs Viewer's localized boundaries inside Studio; do not scatter its runtime, CSS, config, server/services, source, and assets across generic Studio folders.
- Do not introduce compatibility paths for moved Studio source; update references to the new `studio/` locations and fix breakage directly.
- Keep Studio and the public Jekyll site in one repo; do not re-open repository split planning.

### baseline verification set

Use this set before and after move slices when the touched area warrants it:

- Core syntax/projection/data checks: `./scripts/run_checks.py --profile quick`.
- Public build check: `bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`.
- Public surface audit: `./scripts/checks/audit_public_build_surface.py --site-root /tmp/dlf-jekyll-build`.
- Local Studio Docs Viewer smoke: `tests/smoke/local_studio_app_docs_viewer.py`.
- Local Studio Catalogue dashboard smoke: `tests/smoke/local_studio_app_catalogue_dashboard_route.py`.
- Local Studio UI Catalogue smoke: `tests/smoke/local_studio_app_ui_catalogue_routes.py`.
- Add route-family or service-specific tests from `scripts/run_checks.py` profiles when a move touches that family.

Codex sandbox note: the Local Studio smoke scripts bind temporary localhost ports and launch Chromium. In sandboxed Codex runs they may need elevated permissions even when the product code is healthy.

### general steer

- Do not create compatibility infrastructure for old Studio source paths; reason: the requested implementation model is to move files, update references, and get Studio working again from the new `studio/` locations.
- Do not perform the full Docs Viewer portable extraction in this sequence; reason: this sequence keeps current Docs Viewer code, server/services, Docs Viewer source, config, and assets Studio-hosted under a clear internal home such as `studio/docs-viewer/`, while the later extraction will move that coherent subtree out to a true reusable boundary such as `docs-viewer/`.


## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action.

| ID | status | action |
| --- | --- | --- |
| STSR-001 | done | Adopt the core architecture decision in the parent request: Studio is the same-repo authoring system, canonical website data and Studio source move under `studio/`, generated public artifacts stay in the Jekyll publishing surface, and a future Studio repo split is not a target. |
| STSR-002 | done | Create this child task tracker with a Codex handover status section and a single sequential implementation table using the allowed statuses `planned`, `in progress`, `done`, and `deferred`. |
| STSR-003 | done | Inventory every current Studio-related path and classify it as Studio source, public Jekyll source, public generated output, future Docs Viewer extraction candidate, Studio generated/local working output, mixed ownership, or out-of-scope dependency; include `scripts/`, `assets/studio/`, `assets/docs-viewer/`, `assets/ui-catalogue/`, `_includes/`, `_docs/`, `_docs_analysis/`, `_docs_library/`, `_docs_catalogue/`, `_ui_catalogue_notes/`, `studio/`, tests, checks, local runner files, and generated-output-adjacent data. Inventory recorded in [Studio Source Tree Reorganization Inventory](/docs/?scope=studio&mode=manage&doc=site-request-studio-source-tree-reorganization-inventory). |
| STSR-004 | done | Resolve ambiguous ownership from the inventory before moving files; update the parent request, inventory, or this table for any path whose owner is unclear, especially canonical catalogue data, `_docs_catalogue/` publishing Markdown, Docs Viewer source scopes, Docs Viewer report source/config/runtime and generated public report registry/config payloads, Studio-owned `_docs_logs/` workflow data consumed by reports, Studio projections and lookup/read-model data, current Docs Viewer code/config/services/assets, generated Docs Viewer public payloads, generated change request log/report artifacts, projection checks, public route JavaScript, search builders/config/policy, tests, and UI Catalogue assets. |
| STSR-005 | done | Define the final `studio/` layout using concrete repo paths for canonical data, config, app server, frontend, assets, services, Studio-owned workflow data such as change request logs, UI Catalogue, tests, fixtures, checks, and a clear internal Docs Viewer home such as `studio/docs-viewer/`; save this layout in a sibling doc; do not start file moves until this layout is recorded. |
| STSR-006 | done | Capture a baseline verification set for the current tree, including the smallest useful Local Studio smoke checks, public Jekyll build check, projection/public-surface check, and syntax/import checks needed to compare before and after moves. |
| STSR-007 | done | Remove or finish any remaining transition-only Local Studio cleanup that would make file moves ambiguous, such as retired sibling-service fallbacks, old Jekyll route-host assumptions, stale static config fallbacks, or unused route adapters. |
| STSR-008 | done | Move canonical website data, `_docs_catalogue/` publishing Markdown, Studio-owned change request workflow data, and Studio-owned config into the chosen Studio canonical/config/workflow paths, and move Docs Viewer source Markdown into the chosen Docs Viewer source home under `studio/`; then update all generators, validators, services, checks, tests, and docs that read canonical source so public outputs are still written to the existing Jekyll-facing paths. |
| STSR-009 | planned | Verify the canonical-data move by running targeted source/projection checks and confirming the public Jekyll site still receives the generated JSON and assets it needs without reading canonical source directly. |
| STSR-010 | planned | Move Local Studio app server modules, route-family modules, local API adapters, Studio-owned workflow services such as docs-log/change-request-log code, and Studio-owned service orchestration into the chosen `studio/app/` and `studio/services/` paths; move current Docs Viewer server/services into the chosen internal Docs Viewer home under `studio/`; update imports directly rather than adding old-path aliases. |
| STSR-011 | planned | Verify the Python/server move with syntax/import checks, focused unit tests, and the smallest Local Studio API or route smoke checks that prove the moved server can boot and serve active routes. |
| STSR-012 | planned | Move Studio frontend JavaScript, shell modules, route modules, UI text, runtime config, and Studio-only static assets into the chosen `studio/app/frontend/` or `studio/app/assets/` paths; move current Docs Viewer runtime code, UI text, config, CSS, and assets into the chosen internal Docs Viewer home under `studio/`; update HTML, runtime config, module imports, tests, and smoke scripts to load from those paths. |
| STSR-013 | planned | Update Local Studio static serving so Studio-owned frontend files are served from `studio/` source locations and no old public `assets/studio/...` source-serving path remains active. |
| STSR-014 | planned | Split Studio CSS from public `assets/css/main.css`: move Studio-only base tokens, shell rules, route/editor/modal/dashboard/operational selectors, and Studio primitive classes into Studio-owned CSS under `studio/`; leave only public-site or genuinely shared selectors in public CSS. |
| STSR-015 | planned | Verify the frontend/static/CSS move with Local Studio desktop and mobile smoke checks, UI route readiness checks, and a public Jekyll build or public route check that confirms public CSS and public runtime behavior still work without Studio source. |
| STSR-016 | planned | Move UI Catalogue demo source, notes, demo CSS/JS, fixtures, and assets under the Studio boundary; update local demo routes to read the new source paths and keep UI Catalogue out of the public Jekyll publishing surface. |
| STSR-017 | planned | Move tests, smoke helpers, fixtures, projection/source-boundary checks, public-surface checks, and Codex-run verification helpers under the chosen Studio or Docs Viewer test/check locations; public-site validation remains a Studio/Codex testing responsibility, not public-site source ownership. |
| STSR-018 | planned | Update command entrypoints, local runner docs, development workflow docs, script docs, and task references so Codex and humans use the new `studio/` paths without relying on old source locations. |
| STSR-019 | planned | Delete old Studio source locations after references are updated; confirm removed paths are not retained through import aliases, copied files, static mount shims, or dual-read fallback logic. |
| STSR-020 | planned | Run the agreed final verification set: focused Local Studio smoke checks, UI Catalogue smoke checks, targeted Python/Ruby/JavaScript syntax or unit checks, public Jekyll build, projection/public-build-surface audit, and any changed-doc link/path checks. |
| STSR-021 | planned | Update the parent request, this tracker, related owning docs, and docs-log entry with final statuses, moved-path summary, verification results, generated payload status, and remaining risks; do not rebuild generated docs payloads unless explicitly requested. |
