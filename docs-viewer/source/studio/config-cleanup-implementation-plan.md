---
doc_id: config-cleanup-implementation-plan
title: Config Cleanup Implementation Plan
added_date: 2026-06-03
last_updated: 2026-06-03
parent_id: studio
viewable: true
---
# Config Cleanup Implementation Plan

This document consolidates the remaining config cleanup work from the focused config docs and the temporary Studio cleanup notes.
Use it as the implementation tracker for pruning redundant config keys, keeping config ownership explicit, and avoiding broad route or runtime refactors.

## Current State

Completed cleanup already recorded in the focused docs:

- Local Studio route metadata now lives under `app.routes`; `paths.routes` was removed from `studio/app/frontend/config/studio-config.json`.
- Stale Local Studio public-route keys and unused Studio config helper exports were removed.
- `paths.data.ui_text.site_series_index`, `site-series-index.json`, `paths.data.studio.catalogue_lookup_meta`, and broad `catalogue.series_type_options` were removed.
- Analytics route metadata now lives under `app.routes`; stale public-content route keys were removed from `analytics-app/app/frontend/config/analytics-config.json`.
- Data Sharing source config paths were removed from Analytics bootstrap config; Analytics browser routes read the UI-safe payload from `/analytics/api/data-sharing/config`.
- Docs Viewer scope config, route config, public route config, generated defaults, service defaults, reports, and UI text have focused source locations under `docs-viewer/config/...`.

The remaining work is not a single blind deletion pass.
Most remaining Local Studio `paths.data.studio` keys are active catalogue editor, status, lookup, activity, or field-registry inputs.
Cleanup should be done as small verification-backed slices.

## Implementation Rules

- Start every slice with active call-site scans, not historical request docs.
- Remove a key only when no active route, service, test, or generated-default pipeline consumes it.
- Keep browser bootstrap config, source domain config, generated output config, and runtime-injected config separate.
- Keep UI copy in route UI-text bundles unless the string is operation-owned Data Sharing metadata.
- Update the owning config doc in the same change as any config key move or deletion.
- Do not rebuild Docs Viewer payloads manually for docs-only edits.

## Work Items

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| id | status | area | implementation work | verification |
| --- | --- | --- | --- | --- |
| CFG-001 | done | Local Studio UI text | Audited every file under `studio/app/frontend/config/ui-text/` against `paths.data.ui_text`, `loadStudioConfigWithText(...)`, scoped `getStudioText(...)` calls, route-local helper wrappers, and dynamic field-label families. Removed stale `catalogue-work-editor.json` keys: `search_multiple_matches`, `details_search_empty`, `details_open_label`, `summary_readonly_label`, and `summary_rebuild_label`. Kept dynamic `field_label_*` and import-preview field keys because route modules still resolve them through template keys. Updated [Studio UI Text Config](/docs/?scope=studio&doc=config-studio-ui-text-json). | Verified with JSON parsing for the touched bundle, full Local Studio UI-text bundle parse, exact-key stale scans, `git diff --check`, and changed-file sanitization scan. No route module changed, so `node --check` and browser smoke were not required for this docs/config-only cleanup. |
| CFG-002 | planned | Local Studio data paths | Re-scan `paths.data.studio` in `studio-config.json`. Current active keys include catalogue source JSON fallbacks, generated lookup search/open payloads, `activity_log`, and `catalogue_field_registry`. Keep active catalogue read keys. If a narrower resolver replaces `catalogue_field_registry`, move that path out of browser bootstrap config and update service/browser callers together. Update [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json). | `$HOME/miniconda3/bin/python3 -m json.tool studio/app/frontend/config/studio-config.json`; `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_studio_app_server.py`; focused catalogue route smokes for any affected read key. |
| CFG-003 | planned | Studio domain config | Review `studio/data/config/catalogue/catalogue-field-registry.json` for rules tied to retired generated outputs and defaults that no longer match catalogue generator behavior. Keep artifact-family names only when current builders, planners, or tests still understand them. | `$HOME/miniconda3/bin/python3 studio/services/catalogue/verify_catalogue_field_registry.py`; `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_catalogue_field_registry.py studio/tests/python/test_catalogue_lookup_refresh.py`. |
| CFG-004 | planned | Activity contract | Review `studio/data/config/runtime/activity-contract.json` against current service-emitted script purposes, action ids, record groups, and statuses. Remove retired activity families only after service tests prove they are no longer emitted. Keep visible labels in `activity-log.json`, not in the activity contract. | `$HOME/miniconda3/bin/python3 scripts/checks/verify_activity_contract.py`; `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_activity_contract.py studio/tests/python/test_studio_activity_context.py studio/tests/python/test_studio_activity_feed.py`. |
| CFG-005 | planned | Analytics site data paths | Decide whether `paths.data.site.series_index` and `paths.data.site.works_index` should remain in `analytics-config.json` as public read inputs or move behind narrower loaders in `analytics-app/app/frontend/js/analytics-data.js`. Current call sites use them for series/tag views, and tests assert the runtime paths. Recommended first pass: keep them as Analytics browser data inputs unless the replacement removes config surface area without hiding ownership. Update [Analytics Config JSON](/docs/?scope=studio&doc=config-analytics-config-json). | `$HOME/miniconda3/bin/python3 -m json.tool analytics-app/app/frontend/config/analytics-config.json`; `$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_analytics_app_server.py`; focused Local Analytics tag route smoke. |
| CFG-006 | planned | Analytics UI text | Audit every file under `analytics-app/app/frontend/config/ui-text/` against active `app.routes`, `loadAnalyticsConfigWithText(...)`, `getAnalyticsText(...)`, and route-local helper wrappers. Keep Data Sharing operation copy separate from adapter capability config unless the copy is operation-owned. Update [Analytics UI Text Config](/docs/?scope=studio&doc=config-analytics-ui-text-json). | `$HOME/miniconda3/bin/python3 -m json.tool` on touched bundles; `node --check` for touched Analytics route modules; focused route smokes for affected Analytics routes. |
| CFG-007 | planned | Data Sharing browser config | Keep `/analytics/api/data-sharing/config` as the only browser-facing Data Sharing config lookup for Analytics-hosted Data Sharing routes. Preserve its whitelist: do not expose adapter path contracts, source write targets, output path patterns, metadata contracts, or document field contracts. If the public payload needs more shaping or more domains, extract helpers from `analytics_data_sharing_api.py` into a focused module with tests. Update [Data Sharing Config Files](/docs/?scope=studio&doc=config-data-sharing-files). | `$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_analytics_data_sharing_api.py studio/tests/python/test_data_sharing_adapters.py studio/tests/python/test_data_sharing_service.py`; Data Sharing prepare/review smoke when payload shape changes. |
| CFG-008 | planned | Docs Viewer config boundaries | Keep Docs Viewer scope policy in `docs-viewer/config/scopes/docs_scopes.json`, route registries in `docs-viewer/config/routes/`, UI text in `docs-viewer/config/ui-text/ui-text.json`, reports in `docs-viewer/config/reports/reports.json`, and generated defaults under `docs-viewer/config/defaults/`. Remove stale docs that still describe Docs Viewer status, scope, or UI text config as living in Studio config. | Focused docs config tests for the touched owner; generated-default builder tests if source scope or route config changes; docs source link/path scan for stale Studio-config references. |

## Suggested Slice Order

1. Run CFG-001 and CFG-006 first.
   UI-text pruning has the lowest runtime risk and will expose stale route/bundle assumptions.
2. Run CFG-002 after UI-text cleanup.
   Studio data-path keys are active today, so this should be a keep-or-move decision per key rather than a deletion batch.
3. Run CFG-003 and CFG-004 together only if the current field-registry or activity-contract tests are already green.
   These files affect build planning and activity interpretation.
4. Run CFG-005 before any Analytics data-loader refactor.
   The likely outcome may be "keep current config keys and document ownership."
5. Run CFG-007 only when Data Sharing payload shape changes or a real domain/operation retirement is planned.
6. Run CFG-008 as a docs/test cleanup pass after the app/domain slices.

## Call-Site Scan Seeds

Useful starting scans:

```bash
rg -n "loadStudioConfigWithText|getStudioText|paths\\.data\\.ui_text|catalogue_lookup_|catalogue_field_registry|activity_log" studio/app/frontend/js studio/app/server studio/services studio/tests
rg -n "loadAnalyticsConfigWithText|getAnalyticsText|paths\\.data\\.site|series_index|works_index|/analytics/api/data-sharing/config|data-sharing/config" analytics-app/app analytics-app/tests data-sharing studio/tests
rg -n "docs-viewer.*Studio config|Studio config.*docs|paths\\.data\\.docs|paths\\.data\\.search" docs-viewer/source/studio docs-viewer/runtime docs-viewer/config studio analytics-app
```

Treat historical `site-request-*` docs as context, not active ownership proof.

## Close-Out Checklist

For each completed slice:

- update this tracker row status
- update the owning focused config doc
- record removed keys and retained keys with owner/reason
- run proportional JSON, Python, JavaScript, and smoke checks
- leave generated docs/search payload changes alone if docs-watcher produced them
- do not add compatibility aliases, direct static reads, or fallback config keys for retired paths
