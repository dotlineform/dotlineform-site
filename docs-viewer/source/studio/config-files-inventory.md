---
doc_id: config-files-inventory
title: Config Files Inventory
added_date: 2026-06-02
last_updated: 2026-06-02
parent_id: studio
viewable: true
---
# Config Files Inventory

This inventory is the starting point for config contract reviews.
It lists source-controlled config files by app or domain and points to focused contract docs.

Generated payloads such as `assets/data/docs/scopes/...`, `assets/data/search/.../index.json`, `assets/works/index/...`, `studio/data/generated/...`, and `_site/...` are not source config.
They may be read at runtime, but they are builder outputs and belong in data-model or generated-payload docs.

## Review Contract

Every config contract review should answer:

- what file or file family owns
- which runtime, service, script, or builder reads it
- whether it is user-editable, maintainer-editable, or code infrastructure
- whether the file is source config, schema, generated output, or runtime-injected config
- what cleanup is still needed for dead keys, duplicate ownership, redundant helpers, or stale docs

## Local Studio

| file | role | edit class | contract doc |
| --- | --- | --- | --- |
| `studio/app/frontend/config/studio-config.json` | Local Studio browser bootstrap and route/data manifest | maintainer-editable code infrastructure | [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json) |
| `studio/app/frontend/config/ui-text/*.json` | route-scoped Local Studio UI copy bundles | maintainer-editable copy config | [Studio UI Text Config](/docs/?scope=studio&doc=config-studio-ui-text-json) |
| `studio/data/config/catalogue/catalogue-field-registry.json` | catalogue field-to-artifact build rules and defaults | maintainer-editable domain config | [Studio Data Config Files](/docs/?scope=studio&doc=config-studio-data-configs) |
| `studio/data/config/runtime/activity-contract.json` | activity log grouping and display contract | code infrastructure | [Studio Data Config Files](/docs/?scope=studio&doc=config-studio-data-configs) |

## Analytics App

| file | role | edit class | contract doc |
| --- | --- | --- | --- |
| `analytics-app/app/frontend/config/analytics-config.json` | Local Analytics browser route/data manifest | maintainer-editable code infrastructure | [Analytics Config JSON](/docs/?scope=studio&doc=config-analytics-config-json) |
| `analytics-app/app/frontend/config/ui-text/*.json` | route-scoped Local Analytics UI copy bundles | maintainer-editable copy config | [Analytics UI Text Config](/docs/?scope=studio&doc=config-analytics-ui-text-json) |

## Docs Viewer

| file | role | edit class | contract doc |
| --- | --- | --- | --- |
| `docs-viewer/config/scopes/docs_scopes.json` | source scope registry used by docs/search builders | maintainer-editable app config | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |
| `docs-viewer/config/scopes/docs_scope_manifest.json` | portable source-scope manifest | maintainer-editable app config | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |
| `docs-viewer/config/routes/docs-viewer-routes.json` | local/manage and public route registry | maintainer-editable app config | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |
| `docs-viewer/config/routes/docs-viewer-public-routes.json` | public route subset registry | maintainer-editable app config | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |
| `docs-viewer/config/defaults/docs-viewer-config.json` | local/manage browser default config | generated-by-builder default, source-controlled | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |
| `docs-viewer/config/defaults/docs-viewer-public-config.json` | public browser default config | generated-by-builder default, source-controlled | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |
| `docs-viewer/config/defaults/docs-viewer-service.json` | standalone Docs Viewer service defaults and endpoints | code infrastructure | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |
| `docs-viewer/config/ui-text/ui-text.json` | Docs Viewer UI copy | maintainer-editable copy config | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |
| `docs-viewer/config/reports/reports.json` | Docs Viewer report registry source | maintainer-editable app config | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |
| `docs-viewer/config/schema/docs-viewer-service.schema.json` | service config schema | code infrastructure | [Docs Viewer Config Files](/docs/?scope=studio&doc=config-docs-viewer-files) |

## Data Sharing

| file | role | edit class | contract doc |
| --- | --- | --- | --- |
| `data-sharing/config/adapters.json` | Data Sharing domain, adapter, capability, and path registry | maintainer-editable workflow config | [Data Sharing Config Files](/docs/?scope=studio&doc=config-data-sharing-files) |
| `data-sharing/config/adapters.schema.json` | adapter config schema | code infrastructure | [Data Sharing Config Files](/docs/?scope=studio&doc=config-data-sharing-files) |
| `data-sharing/config/library-export-configs.json` | Library export profiles | user/maintainer-editable workflow config | [Data Sharing Config Files](/docs/?scope=studio&doc=config-data-sharing-files) |
| `data-sharing/config/library-export-configs.schema.json` | Library export profile schema | code infrastructure | [Data Sharing Config Files](/docs/?scope=studio&doc=config-data-sharing-files) |

## Public Site And Build

| file | role | edit class | contract doc |
| --- | --- | --- | --- |
| `_config.yml` | public Jekyll site config | maintainer-editable build config | [Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config) |
| `_data/pipeline.json` | shared catalogue/media pipeline defaults | maintainer-editable build config | [Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json) |
| `assets/data/search/policy.json` | public catalogue search runtime policy | maintainer-editable runtime config | [Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json) |
| `studio/services/catalogue/search/build_config.json` | catalogue search build policy | maintainer-editable build config | [Search Build Config JSON](/docs/?scope=studio&doc=config-search-build-json) |
| `studio/checks/projection_contract.json` | projection contract audit rules | code infrastructure | [Projection Contract](/docs/?scope=studio&doc=data-models-projection-contract) |
| `ui-catalogue-app/source/palette/palette.yml` | UI Catalogue palette source | maintainer-editable design config | [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue) |

## Cleanup Queue

The first cleanup queue is:

- Local Studio: `paths.routes` values, unused site/docs/search helper exports, `paths.data.studio.catalogue_lookup_meta`, `paths.data.ui_text.site_series_index`, and broad `catalogue.series_type_options` have been removed; continue reviewing remaining `paths.data.studio` and `paths.data.ui_text` keys only with active call-site scans and focused tests
- Local Studio docs: active config docs now use `studio/app/frontend/config/studio-config.json`; historical request docs may still contain old paths and should be treated as history
- Analytics app: decide whether remaining public site data paths should stay in Analytics config or move behind narrower data loaders
- Docs Viewer: keep source scope config, generated defaults, and route registries distinct in docs and tests
- Data Sharing: keep user-editable export profiles separate from adapter/service dispatch infrastructure; keep `/analytics/api/data-sharing/config` on a UI-safe public payload whitelist

## Subsequent Session Notes

Use the focused config docs above as the authoritative source for cleanup work.
Historical `site-request-*` docs preserve request context and may contain retired paths or old ownership boundaries.

For later sessions:

- do not revert generated docs/search payloads solely because they are dirty; docs-watcher may regenerate them after source doc edits
- if the public Data Sharing config payload grows, extract its shaping helpers from `analytics_data_sharing_api.py` into a focused module with tests
- when pruning more Studio or Analytics config keys, start with active call-site scans, then update the owning config doc and focused server/runtime tests in the same change
