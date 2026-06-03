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
| CFG-002 | done | Local Studio data paths | Re-scanned `paths.data.studio` in `studio-config.json` against active frontend route modules, the Local Studio catalogue read API, catalogue services, Python tests, and route smokes. Removed unused `paths.data.studio.activity_log`; `activity_log` remains a live catalogue API read key, but no active frontend code uses the Studio config path as a fallback. Retained canonical catalogue source fallback reads, generated lookup search/open fallback payloads, and `catalogue_field_registry`. Added a focused runtime-config test assertion for the active Studio data-path key set so the browser-facing surface does not widen silently. Updated [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json). | Verified with JSON parsing for `studio-config.json`, focused `test_studio_app_server.py`, `git diff --check`, and changed-file sanitization scan. No live browser fallback path changed for active route behavior, so catalogue route browser smokes were not required. |
| CFG-003 | done | Studio domain config | Reviewed `studio/data/config/catalogue/catalogue-field-registry.json` against current verifier coverage for artifact family names, source-field coverage, fallback defaults, and representative field-aware build plans. Retained the current registry payload because current builders, planners, and verifier tests still understand the configured artifact families. Fixed the standalone verifier repo-root calculation and made `test_catalogue_field_registry.py` run the verifier as a real pytest test. Updated [Studio Data Config Files](/docs/?scope=studio&doc=config-studio-data-configs). | Verified with `$HOME/miniconda3/bin/python3 -m json.tool studio/data/config/catalogue/catalogue-field-registry.json`; `$HOME/miniconda3/bin/python3 studio/services/catalogue/verify_catalogue_field_registry.py`; `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_catalogue_field_registry.py studio/tests/python/test_catalogue_lookup_refresh.py`; `git diff --check`; and changed-file sanitization scan. |
| CFG-004 | done | Activity contract | Reviewed `studio/data/config/runtime/activity-contract.json` against current service-emitted script purposes, action ids, record groups, statuses, and route surfaces. Retained the current contract rows because the listed Studio, Docs, Analytics, and Data Sharing actions still have live emitters. Fixed the stale verifier path in `test_activity_contract.py`, made it run as a real pytest test, and updated `verify_activity_contract.py` to validate Analytics routes as a first-class activity surface. Kept visible labels in `activity-log.json`, not in the activity contract. Updated [Studio Data Config Files](/docs/?scope=studio&doc=config-studio-data-configs). | Verified with `$HOME/miniconda3/bin/python3 -m json.tool studio/data/config/runtime/activity-contract.json`; `$HOME/miniconda3/bin/python3 studio/checks/verify_activity_contract.py`; `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_activity_contract.py studio/tests/python/test_studio_activity_context.py studio/tests/python/test_studio_activity_feed.py`; `git diff --check`; and changed-file sanitization scan. |
| CFG-005 | done | Analytics site data paths | Re-scanned `paths.data.site.series_index` and `paths.data.site.works_index` in `analytics-config.json` against active Analytics frontend routes, server runtime config, and tests. Retained both keys as explicit Analytics browser read inputs: `series-tags.js`, `tag-registry.js`, and the series tag editor still load the public series index, and the series tag editor still loads the public works index. Moving these paths into hidden loader constants would not remove a runtime dependency or clarify ownership. Updated [Analytics Config JSON](/docs/?scope=studio&doc=config-analytics-config-json). | Verified with `$HOME/miniconda3/bin/python3 -m json.tool analytics-app/app/frontend/config/analytics-config.json`; `$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_analytics_app_server.py`; `git diff --check`; and changed-file sanitization scan. No Analytics data path changed, so browser smoke was not required. |
| CFG-006 | done | Analytics UI text | Audited every file under `analytics-app/app/frontend/config/ui-text/` against active `app.routes`, `loadAnalyticsConfigWithText(...)`, scoped `getAnalyticsText(...)` calls, route-local helper wrappers, and dynamic key families. Removed stale route-surface keys from Data Sharing review, series tag editor, series tags, tag aliases, and tag registry bundles. Kept dynamic `session_import_status_*` keys because `series-tags-modals.js` resolves them with `session_import_status_${status}`. Kept Data Sharing apply-action copy in `data-sharing/config/adapters.json`, where current review workflow reads action labels, statuses, confirmations, result titles, and count rows. Updated [Analytics UI Text Config](/docs/?scope=studio&doc=config-analytics-ui-text-json). | Verified with JSON parsing for touched bundles and all Analytics UI-text bundles, exact-key stale scans, `git diff --check`, and changed-file sanitization scan. No route module changed, so `node --check` and browser smoke were not required for this docs/config-only cleanup. |
| CFG-007 | done | Data Sharing browser config | Re-scanned Analytics-hosted Data Sharing config lookups and kept `/analytics/api/data-sharing/config` as the only browser-facing Data Sharing config lookup. Tightened the public payload whitelist in `analytics_data_sharing_api.py`: sharing profiles now expose only browser-needed identity, format, and limited selection UI fields, while output path patterns, metadata contracts, document field contracts, non-UI selection internals, and apply-action activity emit metadata stay server-owned. Static serving still rejects direct `data-sharing/config/...` reads. Updated [Data Sharing Config Files](/docs/?scope=studio&doc=config-data-sharing-files). | Verified with `$HOME/miniconda3/bin/python3 -m pytest analytics-app/tests/python/test_analytics_data_sharing_api.py studio/tests/python/test_data_sharing_adapters.py studio/tests/python/test_data_sharing_service.py`; focused Analytics Data Sharing route smoke; `git diff --check`; and changed-file sanitization scan. |
| CFG-008 | done | Docs Viewer config boundaries | Re-scanned active Docs Viewer config docs, runtime references, and source docs for stale Studio-config ownership claims. Kept Docs Viewer scope policy in `docs-viewer/config/scopes/docs_scopes.json`, route registries in `docs-viewer/config/routes/`, UI text in `docs-viewer/config/ui-text/ui-text.json`, reports source metadata in `docs-viewer/config/reports/reports.json`, and generated defaults under `docs-viewer/config/defaults/`. Clarified active report docs so `assets/data/docs/reports.json` is described as the browser-visible projection rather than the source owner. Historical `site-request-*` docs were left as history. | Verified with docs source link/path scans, `git diff --check`, and changed-file sanitization scan. No Docs Viewer source config or generated-default source changed, so generated-default builder tests were not required. |

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
