---
doc_id: site-request-studio-source-tree-reorganization-tasks
title: Studio Source Tree Reorganization Tasks
added_date: 2026-05-24
last_updated: 2026-05-24
ui_status: done
parent_id: site-request-studio-source-tree-reorganization
sort_order: 10011
viewable: true
---

This document is archived and is no longer maintained.

---

# Studio Source Tree Reorganization Tasks

This is the tracker for implementing [Studio Source Tree Reorganization Request](/docs/?scope=studio&mode=manage&doc=site-request-studio-source-tree-reorganization).

## Status

### just done

- Completed `STSR-021` by closing out the request, task tracker, owning docs, and structured docs-log source record.
- Marked the parent request and this tracker complete.
- Recorded the final moved-path summary, verification results, generated payload status, and remaining risks in the parent request.
- Updated active owning docs that still described old source locations as current ownership.
- Added structured docs-log source entry `change-2026-05-24-completed-studio-source-tree-reorganization`.
- Generated Docs Viewer payloads, search payloads, and docs-log projections were intentionally not rebuilt during close-out.
- Final verification from `STSR-020` passed:
  - `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick --run-id stsr-020-quick-final-pass`; summary at `var/test-runs/stsr-020-quick-final-pass/summary.md`.
  - `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile studio-smoke --run-id stsr-020-studio-smoke-final-pass`; summary at `var/test-runs/stsr-020-studio-smoke-final-pass/summary.md`.
  - `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke --run-id stsr-020-docs-viewer-smoke-final-pass`; summary at `var/test-runs/stsr-020-docs-viewer-smoke-final-pass/summary.md`.
  - `$HOME/miniconda3/bin/python3 studio/checks/audit_public_build_surface.py --site-root /tmp/dlf-jekyll-build`.
  - Targeted checks: public Jekyll build to `/tmp/dlf-jekyll-build`, dry-run `./scripts/build_docs.rb --scope studio`, dry-run `./scripts/build_search.rb --scope studio`, focused Local Studio Docs Viewer/Catalogue/UI Catalogue/thumbnail-quality smokes, focused pytest for `test_studio_app_server.py` and `test_catalogue_routes.py`, and targeted JS/Ruby syntax checks.

### steer for next task

- No remaining sequential task in this tracker.
- Treat the removed old root source locations as gone; do not reintroduce `scripts/checks/`, root `tests/`, `scripts/docs/`, old public UI Catalogue assets, old public Docs Viewer assets, or empty Jekyll route-shell directories under `studio/`.
- Keep `scripts/run_checks.py` deleted; do not reintroduce a root check-profile wrapper.
- Keep public-site validation as Studio/Codex testing ownership even when a check validates generated public output.
- Keep check entrypoints at `studio/checks/...`; do not add old `studio/checks/...` wrappers or aliases.
- Include focused syntax/import verification and at least one representative smoke profile after moving test/check code.
- Keep `assets/studio/img/thumbnail-quality/` deleted; thumbnail-quality preview images now live under `studio/data/generated/thumbnail-quality/img/` and Local Studio serves that generated preview path directly.
- Treat `assets/docs-viewer/` and other empty old source folders as deletion/cleanup candidates in `STSR-019` unless `STSR-013` proves a serving rule still references them.
- Treat broad user-facing docs path cleanup as part of `STSR-018` unless a stale active path blocks verification before then.
- Keep generated docs/search payloads untouched unless the active verification step explicitly requires a rebuild.
- Treat the table as sequential: only begin the next non-deferred ID after the current one is `done`.
- Treat `studio/docs-viewer/runtime/`, `studio/docs-viewer/assets/`, and `studio/docs-viewer/config/` as Docs Viewer-owned runtime/static input after the frontend/static move; separate them from generated public docs/search payloads.
- Treat moved change-request workflow service code under `studio/workflows/change-requests/services/docs_logs/` as Studio-owned; generated log/report artifacts may be consumed by Codex or surfaced through `/docs/`, but that does not transfer source ownership to Docs Viewer.
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

- Core syntax/projection/data checks: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick`.
- Public build check: `bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build`.
- Public surface audit: `$HOME/miniconda3/bin/python3 studio/checks/audit_public_build_surface.py --site-root /tmp/dlf-jekyll-build`.
- Local Studio Docs Viewer smoke: `studio/tests/smoke/local_studio_app_docs_viewer.py`.
- Local Studio Catalogue dashboard smoke: `studio/tests/smoke/local_studio_app_catalogue_dashboard_route.py`.
- Local Studio UI Catalogue smoke: `studio/tests/smoke/local_studio_app_ui_catalogue_routes.py`.
- Add route-family or service-specific tests from `studio/commands/run_checks.py` profiles when a move touches that family.

Codex sandbox note: the Local Studio smoke scripts bind temporary localhost ports and launch Chromium. In sandboxed Codex runs they may need elevated permissions even when the product code is healthy.

### general steer

- Do not create compatibility infrastructure for old Studio source paths; reason: the requested implementation model is to move files, update references, and get Studio working again from the new `studio/` locations.
- Do not perform the full Docs Viewer portable extraction in this sequence; reason: this sequence keeps current Docs Viewer code, server/services, Docs Viewer source, config, and assets Studio-hosted under a clear internal home such as `studio/docs-viewer/`, while the later extraction will move that coherent subtree out to a true reusable boundary such as `docs-viewer/`.
- Treat future stale active-path cleanup as ordinary owning-doc maintenance unless it blocks runtime verification. Historical/generated records may still mention old paths until their own rebuild or archive refresh.


## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action.

| ID | status | action |
| --- | --- | --- |
| STSR-001 | done | Adopt the core architecture decision in the parent request: Studio is the same-repo authoring system, canonical website data and Studio source move under `studio/`, generated public artifacts stay in the Jekyll publishing surface, and a future Studio repo split is not a target. |
| STSR-002 | done | Create this child task tracker with a Codex handover status section and a single sequential implementation table using the allowed statuses `planned`, `in progress`, `done`, and `deferred`. |
| STSR-003 | done | Inventory every pre-move Studio-related path and classify it as Studio source, public Jekyll source, public generated output, future Docs Viewer extraction candidate, Studio generated/local working output, mixed ownership, or out-of-scope dependency; include previous path families such as `scripts/`, `assets/studio/`, `assets/docs-viewer/`, `assets/ui-catalogue/`, `_includes/`, `_docs/`, `_docs_analysis/`, `_docs_library/`, `_docs_catalogue/`, `_ui_catalogue_notes/`, `studio/`, tests, checks, local runner files, and generated-output-adjacent data. Inventory recorded in [Studio Source Tree Reorganization Inventory](/docs/?scope=studio&mode=manage&doc=site-request-studio-source-tree-reorganization-inventory). |
| STSR-004 | done | Resolve ambiguous ownership from the inventory before moving files; update the parent request, inventory, or this table for any path whose owner is unclear, especially canonical catalogue data, `_docs_catalogue/` publishing Markdown, Docs Viewer source scopes, Docs Viewer report source/config/runtime and generated public report registry/config payloads, Studio-owned `_docs_logs/` workflow data consumed by reports, Studio projections and lookup/read-model data, current Docs Viewer code/config/services/assets, generated Docs Viewer public payloads, generated change request log/report artifacts, projection checks, public route JavaScript, search builders/config/policy, tests, and UI Catalogue assets. |
| STSR-005 | done | Define the final `studio/` layout using concrete repo paths for canonical data, config, app server, frontend, assets, services, Studio-owned workflow data such as change request logs, UI Catalogue, tests, fixtures, checks, and a clear internal Docs Viewer home such as `studio/docs-viewer/`; save this layout in a sibling doc; do not start file moves until this layout is recorded. |
| STSR-006 | done | Capture a baseline verification set for the current tree, including the smallest useful Local Studio smoke checks, public Jekyll build check, projection/public-surface check, and syntax/import checks needed to compare before and after moves. |
| STSR-007 | done | Remove or finish any remaining transition-only Local Studio cleanup that would make file moves ambiguous, such as retired sibling-service fallbacks, old Jekyll route-host assumptions, stale static config fallbacks, or unused route adapters. |
| STSR-008 | done | Move canonical website data, `_docs_catalogue/` publishing Markdown, Studio-owned change request workflow data, and Studio-owned config into the chosen Studio canonical/config/workflow paths, and move Docs Viewer source Markdown into the chosen Docs Viewer source home under `studio/`; then update all generators, validators, services, checks, tests, and docs that read canonical source so public outputs are still written to the existing Jekyll-facing paths. |
| STSR-009 | done | Verify the canonical-data move by running targeted source/projection checks and confirming the public Jekyll site still receives the generated JSON and assets it needs without reading canonical source directly. |
| STSR-010 | done | Move Local Studio app server modules, route-family modules, local API adapters, Studio-owned workflow services such as docs-log/change-request-log code, and Studio-owned service orchestration into the chosen `studio/app/` and `studio/services/` paths; move current Docs Viewer server/services into the chosen internal Docs Viewer home under `studio/`; update imports directly rather than adding old-path aliases. |
| STSR-011 | done | Verify the Python/server move with syntax/import checks, focused unit tests, and the smallest Local Studio API or route smoke checks that prove the moved server can boot and serve active routes. |
| STSR-012 | done | Move Studio frontend JavaScript, shell modules, route modules, UI text, runtime config, and Studio-only static assets into the chosen `studio/app/frontend/` or `studio/app/assets/` paths; move current Docs Viewer runtime code, UI text, config, CSS, and assets into the chosen internal Docs Viewer home under `studio/`; update HTML, runtime config, module imports, tests, and smoke scripts to load from those paths. |
| STSR-013 | done | Update Local Studio static serving so Studio-owned frontend files are served from `studio/` source locations and no old public `assets/studio/...` source-serving path remains active. |
| STSR-014 | done | Split Studio CSS from public `assets/css/main.css`: move Studio-only base tokens, shell rules, route/editor/modal/dashboard/operational selectors, and Studio primitive classes into Studio-owned CSS under `studio/`; leave only public-site or genuinely shared selectors in public CSS. |
| STSR-015 | done | Verify the frontend/static/CSS move with Local Studio desktop and mobile smoke checks, UI route readiness checks, and a public Jekyll build or public route check that confirms public CSS and public runtime behavior still work without Studio source. |
| STSR-016 | done | Move UI Catalogue demo source, notes, demo CSS/JS, fixtures, and assets under the Studio boundary; update local demo routes to read the new source paths and keep UI Catalogue out of the public Jekyll publishing surface. |
| STSR-017 | done | Move tests, smoke helpers, fixtures, projection/source-boundary checks, public-surface checks, and Codex-run verification helpers under the chosen Studio or Docs Viewer test/check locations; public-site validation remains a Studio/Codex testing responsibility, not public-site source ownership. |
| STSR-018 | done | Update command entrypoints, local runner docs, development workflow docs, script docs, and task references so Codex and humans use the new `studio/` paths without relying on old source locations. |
| STSR-019 | done | Delete old Studio source locations after references are updated; confirm removed paths are not retained through import aliases, copied files, static mount shims, or dual-read fallback logic. |
| STSR-020 | done | Run the agreed final verification set: focused Local Studio smoke checks, UI Catalogue smoke checks, targeted Python/Ruby/JavaScript syntax or unit checks, public Jekyll build, projection/public-build-surface audit, and any changed-doc link/path checks. |
| STSR-021 | done | Update the parent request, this tracker, related owning docs, and docs-log entry with final statuses, moved-path summary, verification results, generated payload status, and remaining risks; do not rebuild generated docs payloads unless explicitly requested. |
