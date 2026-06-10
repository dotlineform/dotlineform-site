---
doc_id: site-request-docs-publish-gate-implementation-plan
title: Docs Public Publish Gate Implementation Plan
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: done
parent_id: site-request-docs-publish-gate
viewable: true
---
# Docs Public Publish Gate Implementation Plan

This is the implementation plan for [Docs Public Publish Gate](/docs/?scope=studio&doc=site-request-docs-publish-gate).

## Steer

- Keep v1 local and file-based.
- Public-scope source edits should rebuild working generated output under `docs-viewer/generated/`, not publish to `assets/data/`.
- The public snapshot roots remain `assets/data/docs/` and `assets/data/search/`.
- Publish is confirmation plus apply. Do not add stored confirmation ids, rollback, unpublish, persistent manifests, or persistent publish summary artifacts in v1.
- Do not add compatibility warnings or dual writes for old public-scope builder output paths.
- Public routes must not fall back to `docs-viewer/generated/`.
- Cross-scope public links should remain public route links and must read published snapshots, not working generated payloads.
- Data Sharing already avoids public `index-tree.json`; Docs Viewer reports such as broken-links and any remaining non-public public-`by-id` consumers should move to working generated payloads or source metadata helpers.
- `New scope` and `Delete scope` must handle the new split between working generated roots and published snapshot roots for public scopes.
- Update the Admin Checks target map for new publish-gate files. Prefer existing routes and areas unless the implementation creates a clearly distinct publication workflow area.

## Handoff

- Parent request has the locked v1 design, including artifact roots, publish action shape, API sketch, public route contract, and non-public consumer boundary.
- Existing durable docs to update during implementation include [Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts), [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder), [Live Rebuild Watcher](/docs/?scope=studio&doc=scripts-docs-live-rebuild-watcher), and [Public Scopes](/docs/?scope=studio&doc=docs-viewer-public-scopes).
- Admin Checks target-map ownership is documented in [Config and Target Map](/docs/?scope=studio&doc=admin-checks-target-map-architecture). Update `admin-app/checks/config/admin-checks.json` and run the target-map audit after adding publish-gate files.
- The current scope config still writes public scopes directly to `assets/data/...`; implementation starts by separating working generated paths from publish paths.
- Scope lifecycle planning currently lives in `docs-viewer/services/docs_scope_manifest.py`; update create/delete preview and apply paths alongside the config split.

## Implementation Tasks

| ID | status | action |
| --- | --- | --- |
| 1 | done | Audit current public-scope docs/search output paths, public route data URLs, cross-scope link behavior, broken-links report reads, non-public by-id consumers, manage generated-read behavior, builder tests, watcher behavior, and public route smokes. |
| 2 | done | Extend docs scope config and config loading to support separate working generated and public publish paths for public scopes. |
| 3 | done | Change public-scope docs and search builders to write working generated output under `docs-viewer/generated/` while preserving public route URL generation. |
| 4 | done | Update Docs Viewer scope lifecycle create/delete preview and apply flows so public scopes manage working generated paths and published snapshot paths separately. |
| 5 | done | Update manage-mode generated reads so public scopes preview working generated docs/search payloads rather than published snapshots. |
| 6 | done | Implement a publish confirmation/apply service that safely syncs working generated docs/search output to public snapshot roots. |
| 7 | done | Add Docs management endpoints for publish status, confirmation, and apply. |
| 8 | done | Add a manage-mode `Publish docs` UI command for public scopes with confirmation and apply. This can be a menu item `🌍 Publish` in the existing Actions button. |
| 9 | done | Update the live rebuild watcher and docs-management write follow-through so public-scope edits rebuild working generated output without publishing. |
| 10 | done | Update the Admin Checks target map for the new publish-gate files, routes, and shared dependencies. Keep existing route ids and families if accurate; add a new `publishing` area only if `docs-build`, `management`, and `config` do not describe the workflow clearly. |
| 11 | done | Add focused tests for config validation, builder output routing, cross-scope link rewriting, broken-links report generated-root reads, scope lifecycle path planning, publish diff/apply behavior, stale published file removal, and unsafe path rejection. |
| 12 | done | Add focused route smokes proving public routes read only published snapshots, public cross-scope links stay on public routes, and manage mode can see working generated changes. |
| 13 | done | Update durable Docs Viewer docs and Admin Checks docs for generated-data ownership, builder commands, live watcher behavior, scope lifecycle behavior, public scopes, and target-map coverage. |
| 14 | done | Run final verification and close the request. |

## Verification Run

- `$HOME/miniconda3/bin/python3 -m py_compile ...` passed for changed Python modules.
- `node --check` passed for changed Docs Viewer runtime modules.
- `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python` passed: 224 tests.
- `$HOME/miniconda3/bin/python3 -m pytest admin-app/tests/python/test_admin_checks_config.py admin-app/tests/python/test_target_map_resolver.py` passed: 10 tests.
- `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --scope library --write` wrote working generated Library docs under `docs-viewer/generated/docs/library/`.
- `$HOME/miniconda3/bin/python3 docs-viewer/build/build_search.py --scope library --write` wrote working generated Library search under `docs-viewer/generated/search/library/index.json`.
- `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --scope analysis --write` wrote working generated Analysis docs under `docs-viewer/generated/docs/analysis/`; it reported the existing unresolved semantic reference warning for `analysis/3-symbols`.
- `$HOME/miniconda3/bin/python3 docs-viewer/build/build_search.py --scope analysis --write` wrote working generated Analysis search under `docs-viewer/generated/search/analysis/index.json`.
- Publish confirmation initially reported Library `4 changed, 0 stale` and Analysis `4 changed, 1 stale`; publish apply synced both public snapshots and removed stale `assets/data/docs/scopes/analysis/.DS_Store`.
- Publish confirmation after apply reported both Library and Analysis up to date: `0 changed, 0 stale`.
- `$HOME/.rbenv/shims/bundle exec jekyll build --quiet --destination /tmp/dlf-jekyll-build` passed.
- `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/public_docs_viewer_readonly.py --site-root /tmp/dlf-jekyll-build` passed after rerunning with elevated Playwright permissions because the sandboxed Chromium launch hit a macOS Mach port permission error.
- `$HOME/miniconda3/bin/python3 admin-app/checks/audit_target_map.py` exited 0. The new `docs_publish_gate.py` is classified under `/docs/`, `management`, and `docs-build`; the audit still reports pre-existing stale-pattern inventory.
- `git diff --check` passed.
- Focused sanitization scan found only benign existing matches such as media token docs and toolchain references.

## Proposed Verification

- `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/...` for focused builder/config/publish tests added by this request.
- `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --scope library --write` writes only working generated output.
- `$HOME/miniconda3/bin/python3 docs-viewer/build/build_search.py --scope library --write` writes only working generated search output.
- Publish confirmation reports changed docs/search payloads without writing public assets.
- Publish apply updates `assets/data/docs/scopes/library/` and `assets/data/search/library/index.json`.
- New public scope preview/apply reports separate working generated and published snapshot paths.
- Delete public scope preview/apply reports and removes both working generated and published snapshot paths for eligible user-created scopes.
- Public `/library/` and `/analysis/` smokes prove public routes do not request `docs-viewer/generated/`.
- Cross-scope link fixtures prove a public `/analysis/` to `/library/` link reads published Library data, while explicit manage links can read working generated data through `/docs/?scope=library&mode=manage`.
- Manage-mode smoke proves `/docs/?scope=library&mode=manage` can see working generated changes before publish.
- Broken-links report verification proves public-scope audits read working generated roots, not published snapshot roots.
- Focused scans or tests prove non-public Data Sharing/document tooling does not read published public `index-tree.json` or `by-id` payloads as source-of-truth data.
- Admin Checks target-map audit proves the new publish-gate files are classified without stale patterns, unexpected `_unclassified` files, or likely-unmapped area/route hints.

## Closeout

- Set this plan status and front matter `ui_status` to `done`.
- Update the parent request status when implementation and verification are complete.
