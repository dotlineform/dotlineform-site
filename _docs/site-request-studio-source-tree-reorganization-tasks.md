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

- Completed `STSR-004` by resolving the ambiguous ownership rows in [Studio Source Tree Reorganization Inventory](/docs/?scope=studio&mode=manage&doc=site-request-studio-source-tree-reorganization-inventory).
- Recorded that current Jekyll-shaped Studio/UI Catalogue route hosts are Studio-owned cleanup targets, not public-site source.
- Recorded that Docs Viewer shell, runtime config, UI text, CSS, reports, services, source scopes, interactive assets, and search builder logic should move as a coherent internal subtree under `studio/docs-viewer/`, while public read-only routes may keep only minimal Jekyll adapters and generated runtime payloads.
- Recorded that `_docs_logs/` source and generated workflow output remain Studio workflow-owned, while Docs Viewer reports may read them only through explicit report/config allowlists.
- Recorded that derived catalogue lookup payloads are Studio editor read models with a schema contract, while disposable lookup/cache state belongs under `var/`.
- Recorded that checks, tests, fixtures, public-surface audits, root build/preview helpers, and smoke tests are Studio/Codex development infrastructure.
- Recorded the search split: Catalogue search generation/config/policy belongs to Studio, Docs Viewer search generation/config belongs to Docs Viewer, and public search route JavaScript/generated payloads remain public runtime/output.

### steer for next task

- Start with `STSR-005`; define the final concrete `studio/` layout before moving files.
- Do not move files in `STSR-005`; record concrete repo paths for each owner so later move tasks can update references directly.
- Treat the table as sequential: only begin the next non-deferred ID after the current one is `done`.
- Keep generated docs/search payloads untouched unless the active task explicitly says to rebuild them.
- Treat `_docs/`, `_docs_analysis/`, `_docs_library/`, current `assets/docs-viewer/`, and current `scripts/docs/` as Docs Viewer-owned source/runtime/service inputs that should move into a clear internal Docs Viewer home under `studio/`; separate them from generated public docs/search payloads.
- Treat `_docs_logs/` and `scripts/docs_logs/` as Studio-owned change request workflow source/service paths, not Docs Viewer-owned paths. Generated log/report artifacts may be consumed by Codex or surfaced through `/docs/`, but that does not transfer source ownership to Docs Viewer.
- Treat Docs Viewer reports as cross-domain readers: report source/config/runtime belongs with Docs Viewer, while report input data belongs with the domain that owns it.
- Treat `_docs_catalogue/` as Studio-owned canonical publishing Markdown, not Docs Viewer-owned source; it should move under Studio canonical data.
- Treat current Jekyll-shaped Studio and UI Catalogue artifacts as cleanup targets, not as acceptable final ownership. If Studio still depends on `_layouts/studio.html`, `_includes/studio_header_nav.html`, `_includes/studio_module_script.html`, or UI Catalogue includes, resolve that as unfinished Local Studio cleanup.
- Treat Docs Viewer `_includes/` route files as route-integration debt to decide deliberately: public read-only route adapters may remain minimal Jekyll integration, but Docs Viewer shell/config/runtime source should live under Docs Viewer.
- Treat `assets/studio/data/catalogue_lookup/` as Studio-generated lookup/read-model data for editors, not public page data; disposable lookup/cache state belongs under `var/`.
- Treat checks and tests as Studio/Codex development infrastructure even when they validate the public published surface.
- Treat public-site build/preview commands as Studio/Codex development tooling, with only deliberate root convenience entrypoints allowed.
- Treat Catalogue search generation/policy as Studio-owned, Docs Viewer search generation/config as Docs Viewer-owned, and public search route JavaScript/payloads as public runtime/output.
- Use the Studio move to reduce `_docs` prefix confusion: any remaining `_docs` naming should refer only to Docs Viewer-owned source scopes, while `_docs_logs/` and `_docs_catalogue/` move into non-Docs-Viewer Studio homes.
- Preserve Docs Viewer's localized boundaries inside Studio; do not scatter its runtime, CSS, config, server/services, source, and assets across generic Studio folders.
- Do not introduce compatibility paths for moved Studio source; update references to the new `studio/` locations and fix breakage directly.
- Keep Studio and the public Jekyll site in one repo; do not re-open repository split planning.

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
| STSR-005 | planned | Define the final `studio/` layout using concrete repo paths for canonical data, config, app server, frontend, assets, services, Studio-owned workflow data such as change request logs, UI Catalogue, tests, fixtures, checks, and a clear internal Docs Viewer home such as `studio/docs-viewer/`; save this layout in a sibling doc; do not start file moves until this layout is recorded. |
| STSR-006 | planned | Capture a baseline verification set for the current tree, including the smallest useful Local Studio smoke checks, public Jekyll build check, projection/public-surface check, and syntax/import checks needed to compare before and after moves. |
| STSR-007 | planned | Remove or finish any remaining transition-only Local Studio cleanup that would make file moves ambiguous, such as retired sibling-service fallbacks, old Jekyll route-host assumptions, stale static config fallbacks, or unused route adapters. |
| STSR-008 | planned | Move canonical website data, `_docs_catalogue/` publishing Markdown, Studio-owned change request workflow data, and Studio-owned config into the chosen Studio canonical/config/workflow paths, and move Docs Viewer source Markdown into the chosen Docs Viewer source home under `studio/`; then update all generators, validators, services, checks, tests, and docs that read canonical source so public outputs are still written to the existing Jekyll-facing paths. |
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
