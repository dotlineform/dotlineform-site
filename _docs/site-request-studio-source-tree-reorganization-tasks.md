---
doc_id: site-request-studio-source-tree-reorganization-tasks
title: Studio Source Tree Reorganization Tasks
added_date: 2026-05-24
last_updated: 2026-05-24
ui_status: planned
parent_id: site-request-studio-source-tree-reorganization
sort_order: 10011
viewable: true
---
# Studio Source Tree Reorganization Tasks

## Status

### just done

- Reframed the parent request around same-repo physical separation: Studio source and canonical data under `studio/`, public Jekyll publishing surface outside `studio/`.
- Removed repo-split-as-future-target language from the parent request and related Local Studio planning docs.
- Added the no-compatibility-layer rule: do not keep old Studio source paths alive through aliases, copied migration artifacts, or static serving shims.
- Created this sequential handover table so a future Codex session can pick up the next task without re-deciding the implementation order.

### steer for next task

- Start with `STSR-003`; do not move files until the inventory is complete and ambiguous ownership is resolved in the table or parent request.
- Treat the table as sequential: only begin the next non-deferred ID after the current one is `done`.
- Keep generated docs/search payloads untouched unless the active task explicitly says to rebuild them.
- Do not introduce compatibility paths for moved Studio source; update references to the new `studio/` locations and fix breakage directly.
- Keep Studio and the public Jekyll site in one repo; do not re-open repository split planning.

## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action.

| ID | status | action |
| --- | --- | --- |
| STSR-001 | done | Adopt the core architecture decision in the parent request: Studio is the same-repo authoring system, canonical website data and Studio source move under `studio/`, generated public artifacts stay in the Jekyll publishing surface, and a future Studio repo split is not a target. |
| STSR-002 | done | Create this child task tracker with a Codex handover status section and a single sequential implementation table using the allowed statuses `planned`, `in progress`, `done`, and `deferred`. |
| STSR-003 | planned | Inventory every current Studio-related path and classify it as Studio source, public Jekyll source, public generated output, Docs Viewer reusable source, or out-of-scope dependency; include `scripts/`, `assets/studio/`, `assets/ui-catalogue/`, `_includes/`, `_ui_catalogue_notes/`, `studio/`, tests, checks, local runner files, and generated-output-adjacent data. |
| STSR-004 | planned | Resolve ambiguous ownership from the inventory before moving files; update the parent request or this table for any path whose owner is unclear, especially canonical catalogue data, Studio projections, Docs Viewer integration files, projection checks, public route JavaScript, and UI Catalogue assets. |
| STSR-005 | planned | Define the final `studio/` layout using concrete repo paths for canonical data, config, app server, frontend, assets, services, UI Catalogue, tests, fixtures, and checks; do not start file moves until this layout is recorded. |
| STSR-006 | planned | Capture a baseline verification set for the current tree, including the smallest useful Local Studio smoke checks, public Jekyll build check, projection/public-surface check, and syntax/import checks needed to compare before and after moves. |
| STSR-007 | planned | Remove or finish any remaining transition-only Local Studio cleanup that would make file moves ambiguous, such as retired sibling-service fallbacks, old Jekyll route-host assumptions, stale static config fallbacks, or unused route adapters. |
| STSR-008 | planned | Move canonical website data and Studio-owned config into the chosen `studio/data/` paths, then update all generators, validators, services, checks, tests, and docs that read canonical source so public outputs are still written to the existing Jekyll-facing paths. |
| STSR-009 | planned | Verify the canonical-data move by running targeted source/projection checks and confirming the public Jekyll site still receives the generated JSON and assets it needs without reading canonical source directly. |
| STSR-010 | planned | Move Local Studio app server modules, route-family modules, local API adapters, and Studio-owned service orchestration into the chosen `studio/app/` and `studio/services/` paths; update imports directly rather than adding old-path aliases. |
| STSR-011 | planned | Verify the Python/server move with syntax/import checks, focused unit tests, and the smallest Local Studio API or route smoke checks that prove the moved server can boot and serve active routes. |
| STSR-012 | planned | Move Studio frontend JavaScript, shell modules, route modules, UI text, runtime config, and Studio-only static assets into the chosen `studio/app/frontend/` or `studio/app/assets/` paths; update HTML, runtime config, module imports, tests, and smoke scripts to load from those paths. |
| STSR-013 | planned | Update Local Studio static serving so Studio-owned frontend files are served from `studio/` source locations and no old public `assets/studio/...` source-serving path remains active. |
| STSR-014 | planned | Split Studio CSS from public `assets/css/main.css`: move Studio-only base tokens, shell rules, route/editor/modal/dashboard/operational selectors, and Studio primitive classes into Studio-owned CSS under `studio/`; leave only public-site or genuinely shared selectors in public CSS. |
| STSR-015 | planned | Verify the frontend/static/CSS move with Local Studio desktop and mobile smoke checks, UI route readiness checks, and a public Jekyll build or public route check that confirms public CSS and public runtime behavior still work without Studio source. |
| STSR-016 | planned | Move UI Catalogue demo source, notes, demo CSS/JS, fixtures, and assets under the Studio boundary; update local demo routes to read the new source paths and keep UI Catalogue out of the public Jekyll publishing surface. |
| STSR-017 | planned | Move Studio-owned tests, smoke helpers, fixtures, and projection/source-boundary checks under the chosen Studio test/check locations where appropriate; keep public-site tests outside `studio/` only when they validate the published Jekyll surface. |
| STSR-018 | planned | Update command entrypoints, local runner docs, development workflow docs, script docs, and task references so Codex and humans use the new `studio/` paths without relying on old source locations. |
| STSR-019 | planned | Delete old Studio source locations after references are updated; confirm removed paths are not retained through import aliases, copied files, static mount shims, or dual-read fallback logic. |
| STSR-020 | planned | Run the agreed final verification set: focused Local Studio smoke checks, UI Catalogue smoke checks, targeted Python/Ruby/JavaScript syntax or unit checks, public Jekyll build, projection/public-build-surface audit, and any changed-doc link/path checks. |
| STSR-021 | planned | Update the parent request, this tracker, related owning docs, and docs-log entry with final statuses, moved-path summary, verification results, generated payload status, and remaining risks; do not rebuild generated docs payloads unless explicitly requested. |
| STSR-D01 | deferred | Do not split Studio into a separate repository; reason: Studio owns canonical data and maintenance workflows for this Jekyll site, so a repo split has no practical target benefit for this request. |
| STSR-D02 | deferred | Do not create compatibility infrastructure for old Studio source paths; reason: the requested implementation model is to move files, update references, and get Studio working again from the new `studio/` locations. |
| STSR-D03 | deferred | Do not perform the full Docs Viewer portable extraction in this sequence; reason: reusable Docs Viewer portability is tracked by its own follow-on request and should not be combined with the Studio source-tree move. |
