---
doc_id: site-request-analytics-app-split-follow-on
title: Analytics App Split Follow-On Tasks
added_date: "2026-05-30 17:24"
last_updated: "2026-05-30 21:35"
ui_status: done
parent_id: site-request-analytics-app-split
---
# Analytics App Split Follow-On Tasks

This sets out the work required following completion of [Analytics App Split Request](/docs/?scope=studio&doc=site-request-analytics-app-split).

This is the second-phase tracker for making Local Analytics self-contained after the lift-and-shift split.
The split removed Studio route/API ownership, but intentionally left some path, helper, naming, and inventory carryover in place so the initial cutover could stay small and verifiable.

The purpose of this phase is to remove that carryover without adding new Analytics features.
Analytics should become the durable owner for tag data, tag mutation helpers, tag UI, Data Sharing workflow ownership, and future analysis/semantic-reference work.
Studio should focus on catalogue/public-site maintenance and should not know Analytics tag source paths directly unless a narrow app-specific adapter is explicitly required.

Key boundary decisions:

- Analytics may read catalogue/public-site generated data where needed, but it should do so through Analytics-owned helpers or app-specific adapters, not Studio helper imports.
- Data Sharing is an Analytics-owned workflow. Shared package dispatch/path mechanics can stay under `data-sharing/`, and Docs Viewer can remain the focused owner for document conversion/source helpers.
- Data Sharing should exchange document and tag data through adapters. It should not route through Docs Viewer HTTP endpoints, import broad Docs Viewer management authority, or depend on Studio tag helpers.
- Search should be treated as app-specific. Public-site search does not need tags, and Studio should not keep tag awareness just because old search build code read tag paths directly.
- No old-path compatibility shims should be added for retired Studio Analytics routes, source-data paths, helper imports, or runtime artifact roots.

## Status

### just done

- Completed tasks 13, 14, and 15:
  - refreshed durable docs for Analytics tag source ownership, Data Sharing ownership, public catalogue search boundaries, Analytics UI class naming, Run Checks profiles, data-model contracts, and semantic-enrichment references
  - fixed the remaining active carryover discovered during verification by moving catalogue cleanup/write allowlists to the Analytics `tag_source_paths` contract
  - renamed the remaining generic Local Studio save utility from `tag-studio-save.js` to `studio-save-utils.js` and updated Studio route imports
  - ran focused Python, pytest, Playwright module, quick-profile, analytics-smoke, stale-reference, and diff checks
  - created structured docs-log entry `change-2026-05-30-closed-analytics-app-split-follow-on-cleanup`

### steer for next task

- Follow-on request is closed.
- Docs source was updated directly; the docs watcher regenerated Studio docs payloads while running.
- The docs-log helper wrote the structured log entry and rebuilt change-log generated indexes.
- Historical request/log records were left intact except for the new close-out entry and generated change-log indexes.

### baseline verification set

Run only the checks warranted by each touched slice.
The final follow-on close-out should include:

- focused Python syntax/import checks for moved Analytics helpers and Data Sharing modules
- focused pytest for tag source/mutation/transaction helpers
- focused pytest for Data Sharing registry/path/adapter behavior
- focused catalogue/search/audit checks where those consumers previously read tag source paths directly
- `analytics-smoke` for route/API/module/modal/ready-state coverage after frontend naming/path changes
- stale-reference scans for retired Studio tag source paths, Data Sharing artifact roots, Analytics helper imports, and old frontend naming
- `git diff --check`

Codex sandbox note: local service, browser, and temporary localhost checks need elevated permissions even when the product code is healthy.

### general steer

- Keep current Analytics UI behavior, write safeguards, dry-run behavior, backup behavior, compact logging, and Data Sharing package semantics.
- Move ownership by changing active contracts, not by preserving old paths with compatibility layers.
- Studio may consume Analytics-owned data only through a narrow adapter/helper where the owning Studio feature genuinely needs that data.
- Prefer app-owned adapters for cross-app data. Docs Viewer owns document conversion/source helpers; Analytics owns the Data Sharing workflow; Studio should not become the coordinator for either.
- Keep implementation docs source-only unless a separate generated-payload rebuild is intentionally run.

## Confirmed Target Contracts

These contracts are the starting point for implementation tasks 2 and onward.
If a later inventory finds a stronger reason to change one, update this section before moving files.

### Tag Source Data

- Canonical tag source data moves from `studio/data/canonical/analytics/` to `analytics-app/data/canonical/`.
- Expected source files remain:
  - `tag-registry.json`
  - `tag-aliases.json`
  - `tag-assignments.json`
  - `tag-groups.json`
- Analytics APIs remain the primary browser-facing read/write contract:
  - `GET /analytics/api/tag-registry`
  - `GET /analytics/api/tag-aliases`
  - `GET /analytics/api/tag-assignments`
  - `GET /analytics/api/tag-groups`
  - existing write endpoints under `/analytics/api/...`
- Direct browser access to raw tag source data should not use `/studio/data/canonical/analytics/...`.
  If raw file access remains useful for local development or smoke tests, expose it under an Analytics-owned static route such as `/analytics/data/canonical/...`.
- Write allowlists, backups, dry-run responses, and compact logging must be updated to the Analytics-owned paths in the same slice that moves the source files.

### Cross-App Tag Consumption

- Studio should not embed Analytics tag source constants directly.
- If catalogue maintenance, audits, or projection checks still need tag data, they should consume it through an explicit Analytics-owned helper or adapter.
- Search is app-specific by default. Any tag-enriched search behavior must have an explicit owner:
  - public-site search does not currently read tags and does not need tag terms in the target state;
  - Analytics can own an Analytics-specific search surface if the use case is local analysis;
  - Studio-owned search/build code should not keep direct tag-source path knowledge as the default.

### Data Sharing Artifacts

- Data Sharing runtime artifacts move from `var/studio/data-sharing/<domain>/...` to `var/analytics/data-sharing/<domain>/...`.
- The expected domain folder shape remains:
  - `exports/`
  - `import-staging/`
  - `import-preview/`
  - `backups/` where a domain adapter needs apply backups
- `data-sharing/config/adapters.json`, `data-sharing/config/library-export-configs.json`, Data Sharing schemas, and Data Sharing path services should use the new artifact root.
- Existing files under `var/studio/data-sharing/...` are disposable. The old folder can be deleted when the runtime root moves, and the new runtime should not read it through fallback logic.

### Adapter Boundaries

- Analytics owns the Data Sharing prepare/review/apply route and API workflow.
- `data-sharing/` owns shared dispatch, adapter registry/config loading, schemas, path validation, package I/O, and operation workflow mechanics.
- Docs Viewer may provide document-domain adapter helpers for generated reads, source writes, conversion, backups, and rebuild follow-through.
- Analytics owns tag-domain adapter helpers.
- Data Sharing should call adapters/helpers in-process through narrow contracts. It should not call Docs Viewer HTTP endpoints, import broad Docs Viewer management services, or depend on Studio tag helper modules.

### Compatibility Rules

- Do not add compatibility routes, redirects, proxy handlers, import fallbacks, dual-read paths, dual-write paths, or static shims for:
  - `studio/data/canonical/analytics/...`
  - `/studio/data/canonical/analytics/...`
  - `var/studio/data-sharing/...`
  - `studio/services/analytics/...`
  - `studio.services.analytics`
- Tests and smoke fixtures should move to the current owner contracts instead of keeping old Studio paths alive.

## Task 2 Inventory

The inventory was gathered from active code, config, tests, smokes, and current source docs.
Historical split request docs and change-log entries are not treated as active cleanup targets unless a later task explicitly updates request history.
Generated change-request indexes contain historical `var/studio/data-sharing/...` text and should be ignored for this follow-on unless they are regenerated from source entries.

### Tag Source Path References

Current tag source path references to `studio/data/canonical/analytics/...` appear in these active groups:

- Source data to move:
  - `studio/data/canonical/analytics/tag-registry.json`
  - `studio/data/canonical/analytics/tag-aliases.json`
  - `studio/data/canonical/analytics/tag-assignments.json`
  - `studio/data/canonical/analytics/tag-groups.json`
- Analytics runtime and frontend:
  - `analytics-app/app/server/analytics_app/analytics_api.py`
  - `analytics-app/app/frontend/config/ui-text/series-tag-editor.json`
  - `analytics-app/app/frontend/config/ui-text/tag-aliases.json`
  - `analytics-app/app/frontend/config/ui-text/tag-groups.json`
  - `analytics-app/app/frontend/config/ui-text/tag-registry.json`
  - `analytics-app/app/frontend/js/tag-aliases.js`
  - `analytics-app/app/frontend/js/tag-aliases-save.js`
  - `analytics-app/app/frontend/js/tag-registry.js`
  - `analytics-app/app/frontend/js/tag-registry-save.js`
  - `analytics-app/app/frontend/js/analytics-tag-editor.js`
- Data Sharing tag adapter config:
  - `data-sharing/config/adapters.json`
- Current Analytics helper owner:
  - `studio/services/analytics/tag_source_model.py`
- Studio/catalogue/search/audit consumers:
  - `studio/services/catalogue/catalogue_cleanup.py`
  - `studio/services/catalogue/generate_work_pages.py`
  - `studio/services/catalogue/search/build_search.rb`
  - `studio/checks/audit_site_consistency.py`
  - `studio/checks/projection_contract.json`
- Tests and smokes:
  - `analytics-app/tests/python/test_analytics_app_server.py`
  - `analytics-app/tests/smoke/local_analytics_app_tag_groups.py`
  - `analytics-app/tests/smoke/local_analytics_app_tag_routes.py`
  - `analytics-app/tests/smoke/tag_aliases_modal.py`
  - `analytics-app/tests/smoke/tag_registry_modal.py`
  - `studio/tests/python/test_catalogue_cleanup.py`
  - `studio/tests/python/test_data_sharing_adapters.py`
  - `studio/tests/python/test_tags_data_sharing_adapter.py`
- Current docs to update during durable-docs follow-through:
  - `docs-viewer/source/studio/analytics.md`
  - `docs-viewer/source/studio/data-models-projection-contract.md`
  - `docs-viewer/source/studio/local-studio-server-architecture.md`
  - `docs-viewer/source/studio/scripts.md`
  - `docs-viewer/source/studio/source-tree-ownership.md`

### Search Coupling

Public-site search does not need tag terms, but current catalogue search code still reads Analytics tag files directly:

- `studio/services/catalogue/search/build_search.rb`
  - defaults `tag_assignments_path` and `tag_registry_path` to `studio/data/canonical/analytics/...`
  - exposes `--tag-assignments` and `--tag-registry`
  - loads tag assignments and registry during catalogue search generation
- `docs-viewer/source/studio/search-build-pipeline-catalogue.md`
  - documents the tag path flags

Task 5 should remove this Studio-owned direct tag dependency unless a concrete Analytics-owned search adapter need is identified.
Given the confirmed target state, public-site search should not consume Analytics tags.

### Data Sharing Artifact Root References

Current references to `var/studio/data-sharing/...` appear in these active groups:

- Data Sharing config and path contracts:
  - `data-sharing/config/adapters.json`
  - `data-sharing/config/library-export-configs.json`
  - `data-sharing/config/library-export-configs.schema.json`
  - `data-sharing/data_sharing/__init__.py`
  - `data-sharing/data_sharing/services/paths.py`
  - `data-sharing/README.md`
- Analytics server/frontend/tests:
  - `analytics-app/app/server/analytics_app/data_sharing_adapters.py`
  - `analytics-app/app/frontend/config/ui-text/data-sharing-review.json`
  - `analytics-app/app/frontend/js/data-sharing-review.js`
  - `analytics-app/tests/python/test_analytics_data_sharing_api.py`
  - `analytics-app/tests/smoke/data_sharing_prepare.py`
  - `analytics-app/tests/smoke/data_sharing_prepare_modules.py`
  - `analytics-app/tests/smoke/data_sharing_review.py`
  - `analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py`
- Data Sharing tests:
  - `studio/tests/python/test_data_sharing_adapters.py`
  - `studio/tests/python/test_data_sharing_service.py`
  - `studio/tests/python/test_data_sharing_subsystem_scaffold.py`
  - `studio/tests/python/test_tags_data_sharing_adapter.py`
- Current docs to update during durable-docs follow-through:
  - `docs-viewer/source/studio/config-data-sharing-adapters.md`
  - `docs-viewer/source/studio/config-library-export-configs.md`
  - `docs-viewer/source/studio/data-models-library.md`
  - `docs-viewer/source/studio/data-models-projection-contract.md`
  - `docs-viewer/source/studio/data-sharing.md`
  - `docs-viewer/source/studio/docs-viewer-media-handling.md`
  - `docs-viewer/source/studio/scripts-docs-export.md`
  - `docs-viewer/source/studio/scripts-docs-import.md`
  - `docs-viewer/source/studio/scripts-docs-management-server-operations.md`
  - `docs-viewer/source/studio/scripts.md`
  - `docs-viewer/source/studio/source-tree-ownership.md`
  - `docs-viewer/source/studio/studio-data-sharing.md`
  - `docs-viewer/source/studio/studio-data-sharing-technical-spec.md`

The old `var/studio/data-sharing/` folder is disposable and can be deleted when the runtime root moves.
Do not add runtime fallback reads for it.

### Analytics Python Helper Coupling

The current tag-domain helper package lives under `studio/services/analytics/`:

- `studio/services/analytics/tag_activity.py`
- `studio/services/analytics/tag_alias_mutations.py`
- `studio/services/analytics/tag_assignment_service.py`
- `studio/services/analytics/tag_promotion_mutations.py`
- `studio/services/analytics/tag_registry_mutations.py`
- `studio/services/analytics/tag_routes.py`
- `studio/services/analytics/tag_source_model.py`
- `studio/services/analytics/tag_write_transactions.py`

Active consumers and check definitions include:

- `analytics-app/app/server/analytics_app/analytics_api.py`
- `data-sharing/data_sharing/adapters/tags/adapter.py`
- `studio/commands/run_checks.py`
- `analytics-app/tests/python/test_analytics_app_server.py`
- `analytics-app/tests/python/test_analytics_data_sharing_api.py`
- tag helper tests under `studio/tests/python/test_tag_*.py`
- current docs:
  - `docs-viewer/source/studio/analytics.md`
  - `docs-viewer/source/studio/scripts-tag-write-server.md`
  - `docs-viewer/source/studio/scripts.md`
  - `docs-viewer/source/studio/source-tree-ownership.md`
  - `docs-viewer/source/studio/studio-python-ruby-script-inventory.md`

The shared path bootstrap in `studio/shared/python/studio_python_paths.py` currently places `studio/services` on `sys.path`, which is why `from analytics import ...` resolves to `studio/services/analytics`.
Task 3 should remove that dependency for Analytics rather than adding a replacement compatibility import path.

Task 3 moved this helper package to `analytics-app/app/server/analytics_app/tag_services/`.
Analytics API code, the tags Data Sharing adapter, tag helper tests, and check-profile syntax paths now import `tag_services` directly.
No `studio/services/analytics` compatibility package remains in active source.

Task 4 added `tag_services/tag_source_paths.py` as the Analytics-owned tag source path contract.
Current Python consumers now use that contract for tag assignment and tag source paths instead of embedding `studio/data/canonical/analytics/...` directly.
The source files themselves have not moved yet; task 6 owns that file move.
The remaining active direct tag source paths are catalogue search defaults in `studio/services/catalogue/search/build_search.rb` and static projection contract JSON, which are covered by task 5 and task 6.

### Analytics Frontend Naming Carryover

Task 9 moved the nine Analytics helper modules from `studio-*.js` to Analytics-owned names:

- `analytics-app/app/frontend/js/analytics-activity-context.js`
- `analytics-app/app/frontend/js/analytics-config.js`
- `analytics-app/app/frontend/js/analytics-data.js`
- `analytics-app/app/frontend/js/analytics-modal.js`
- `analytics-app/app/frontend/js/analytics-navigation.js`
- `analytics-app/app/frontend/js/analytics-route-state.js`
- `analytics-app/app/frontend/js/analytics-theme.js`
- `analytics-app/app/frontend/js/analytics-transport.js`
- `analytics-app/app/frontend/js/analytics-ui.js`

Task 10 moved the former `tag-studio*.js` route/domain modules to Analytics-owned names:

- `analytics-app/app/frontend/js/analytics-tag-editor-domain.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-index.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-interactions.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-modals.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-render.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-route-state.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-save-controller.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-save.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-state.js`
- `analytics-app/app/frontend/js/analytics-tag-editor-suggestions.js`
- `analytics-app/app/frontend/js/analytics-tag-editor.js`

Task 10 also moved shared UI tokens to Analytics-owned class families:

- `analytics__*`
- `analyticsPage*`
- `analyticsModal*`
- `analyticsForm*`
- `analyticsList*`
- `analyticsFilters*`
- `analyticsToolbar*`

The affected selectors, templates, and smoke checks live across:

- `analytics-app/app/assets/css/analytics.css`
- Analytics route modules under `analytics-app/app/frontend/js/`
- Analytics modal/module smokes under `analytics-app/tests/smoke/`
- Analytics route docs and UI primitive docs under `docs-viewer/source/studio/`

Legitimate Local Studio files under `studio/app/...` also use `studio-*` names and should not be renamed as part of Analytics frontend cleanup.
Task 9 and task 10 should keep that distinction explicit.

## Implementation Tasks

Work through the table by ID order.
A `deferred` row is intentionally out of the implementation path and includes the reason in the action.
Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | done | Confirm target contracts before moving files: canonical tag data moves out of `studio/data/canonical/analytics/...`; browser access uses an Analytics-owned static/API path; Data Sharing artifacts move from `var/studio/data-sharing/...` to `var/analytics/data-sharing/...`; old Studio paths are not kept as aliases, fallback reads, redirects, or static shims. |
| 2 | done | Inventory all live references to `studio/data/canonical/analytics`, `/studio/data/canonical/analytics`, `var/studio/data-sharing`, `studio.services.analytics`, `studio/services/analytics`, `tagStudio*`, `tag-studio*`, and Analytics frontend `studio-*` helper names. Use the result as the pre-change move map and final stale-reference checklist. |
| 3 | done | Move Analytics tag-domain Python helpers out of `studio/services/analytics/` into an Analytics-owned package, for example `analytics-app/app/server/analytics_app/tag_services/`. Update `analytics_api.py`, the tags Data Sharing adapter, check profiles, Python tests, smoke imports, and docs so Analytics no longer depends on Studio helper modules. |
| 4 | done | Add an Analytics-owned source path/helper contract for canonical tag data. Use it from Analytics APIs, Data Sharing tags adapter, and any catalogue/search/audit consumers that still need tag data. The helper should make Analytics the path owner and keep Studio from embedding tag source constants directly. |
| 5 | done | Resolve the search ownership boundary. Public search does not need tag terms, so remove direct tag reads from Studio-owned catalogue search unless a concrete Analytics-specific search surface is identified. Update build/search code so Studio does not directly know Analytics tag source paths. |
| 6 | done | Move canonical tag JSON from `studio/data/canonical/analytics/` to the chosen Analytics-owned source location, likely `analytics-app/data/canonical/`. Update Analytics static serving, read endpoints, runtime config/UI text, Data Sharing adapter config, projection contracts, catalogue/search consumers, tests, and docs. Old source paths should fail in active checks. |
| 7 | done | Move Data Sharing runtime artifact roots from `var/studio/data-sharing/` to `var/analytics/data-sharing/`. Update `data-sharing/config/*.json`, schemas, `data_sharing.services.paths`, Analytics server constants, smoke fixtures, tests, docs, validation messages, and examples. Do not add fallback reads for existing old artifacts. |
| 8 | done | Verify and tighten the Docs Viewer/Data Sharing boundary. Data Sharing should call document-domain adapters or helper functions for conversion/source work, not Docs Viewer HTTP endpoints or broad management-service handles. Tags should flow through an Analytics tags adapter. Document the adapter contract in the Data Sharing technical spec. |
| 9 | done | Rename Analytics frontend helper modules and exported APIs that still imply Studio ownership. The old `studio-config.js`, `studio-data.js`, `studio-transport.js`, `studio-ui.js`, `studio-modal.js`, `studio-route-state.js`, `studio-theme.js`, `studio-navigation.js`, and `studio-activity-context.js` files are now Analytics-owned `analytics-*.js` modules with matching generic helper exports. |
| 10 | done | Rename tag UI/module naming from `tagStudio*` and `tag-studio-*` to Analytics-owned naming. Include CSS classes in `analytics.css`, JS class tokens/templates, modal selectors, smoke tests, and docs. Use one consistent family such as `analytics*`, `analyticsModal*`, `analyticsForm*`, `analyticsList*`, and `analyticsToolbar*`. |
| 11 | done | Rename remaining runtime event/state names that still imply Studio ownership, including `studio:open-modal`, `initializeStudioRouteState`, and Analytics-local activity-context helper names where appropriate. Preserve behavior; only change ownership language and route-local contracts. |
| 12 | done | Refresh JavaScript and Python inventory docs for the post-follow-on state. Replace stale pre-split `assets/studio/js/tag-*` and `data-sharing-*` inventory rows with actual `analytics-app/app/frontend/js/` rows and rescore maintenance risk. Update Python/Ruby inventory rows for the moved Analytics helper package. |
| 13 | done | Update durable docs: Analytics, Data Sharing, Data Sharing technical spec, Source Tree Ownership, Run Checks, local setup/runtime docs, projection/data-model docs, tag docs, search docs, and script docs that mention old Studio-owned paths or helper ownership. Update source docs only; do not manually rebuild generated docs payloads. |
| 14 | done | Run the final focused verification set: Python syntax/import checks, focused tag helper pytest, focused Data Sharing adapter/path pytest, affected catalogue/search/audit tests, `analytics-smoke`, stale-reference scans for retired Studio paths/names, and `git diff --check`. |
| 15 | done | Close out the follow-on request with moved-path summary, removed old paths, adapter/search ownership decisions, verification results, generated-payload status, remaining risks, and structured docs-log entry. |

## Close-Out

Moved/confirmed ownership:

- tag source data and tag helper ownership are under `analytics-app/data/canonical/` and `analytics-app/app/server/analytics_app/tag_services/`
- Data Sharing runtime artifacts are under `var/analytics/data-sharing/<domain>/...`
- Analytics route UI class and module ownership uses `analytics*` class families and `analytics-app/app/frontend/js/` modules
- Local Studio's generic save utility is now `studio/app/frontend/js/studio-save-utils.js`, not a tag-named helper

Removed or rejected old ownership:

- no active code or durable doc contract depends on `studio/data/canonical/analytics/...`, `/studio/data/canonical/analytics/...`, `studio/services/analytics`, `studio.services.analytics`, `var/studio/data-sharing/...`, or `tag-studio*`
- remaining mentions of retired Data Sharing and tag-write paths are explicit historical/compatibility warnings
- public catalogue search remains catalogue-owned and does not consume Analytics tags or publish `tag_ids` / `tag_labels`

Verification:

- `$HOME/miniconda3/bin/python3 -m py_compile studio/services/catalogue/catalogue_cleanup.py studio/services/catalogue/catalogue_transactions.py`
- `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_catalogue_cleanup.py studio/tests/python/test_catalogue_transactions.py` passed, 15 tests
- focused tag/Data Sharing pytest passed, 61 tests
- `studio/tests/smoke/studio_operational_route_modules.py --site-root .` passed
- `studio/tests/smoke/catalogue_editor_route_boot_modules.py --site-root .` passed
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile quick --run-id analytics-split-follow-on-task13-quick` passed; summary at `var/test-runs/analytics-split-follow-on-task13-quick/summary.md`
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile analytics-smoke --run-id analytics-split-follow-on-task14-analytics-smoke` passed; summary at `var/test-runs/analytics-split-follow-on-task14-analytics-smoke/summary.md`
- final stale-reference scans and `git diff --check` passed

Generated payload status:

- Studio docs payloads changed because the docs watcher was running after source doc edits
- change-log generated indexes changed because the structured docs-log helper rebuilt them after writing the close-out entry

Remaining risks:

- no known implementation blockers remain for this follow-on request
- tag-write backups still use their current documented backup location; moving backup roots was not part of this follow-on close-out slice

## Change Log Entries

- `change-2026-05-30-closed-analytics-app-split-follow-on-cleanup`
