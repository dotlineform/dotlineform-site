---
doc_id: config
title: Config
added_date: 2026-03-31
last_updated: 2026-05-26
parent_id: ""
sort_order: 14000
---
# Config

Checked-in configuration artifacts that the current site and build scripts load directly:

- site-wide Jekyll config in `_config.yml`
- shared catalogue/media/runtime defaults in `_data/pipeline.json`
- shared Studio/search browser config in `assets/studio/data/studio_config.json`
- the Studio/search config loader in `assets/studio/js/studio-config.js`
- Docs Viewer source scope config in `docs-viewer/config/scopes/docs_scopes.json`
- Docs Viewer browser config defaults in `docs-viewer/config/defaults/docs-viewer-config.json` and `docs-viewer/config/defaults/docs-viewer-public-config.json`
- Docs Viewer service defaults/schema in `docs-viewer/config/defaults/docs-viewer-service.json` and `docs-viewer/config/schema/docs-viewer-service.schema.json`
- Docs Viewer UI text in `docs-viewer/config/ui-text/ui-text.json`
- dedicated `/catalogue/search/` runtime policy in `assets/data/search/policy.json`
- build-owned search source-family config in `scripts/search/build_config.json`
- Library sharing profile config patterns in `data-sharing/config/library-export-configs.json`
- Library sharing profile config schema in `data-sharing/config/library-export-configs.schema.json`
- Data Sharing adapter dispatch in `data-sharing/config/adapters.json`
- Data Sharing adapter schema in `data-sharing/config/adapters.schema.json`

Key documents:

1. **[Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config)**
2. **[Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json)**
3. **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**
4. **[Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)**
5. **[Docs Viewer Config](/docs/?scope=studio&doc=config-docs-viewer)**
6. **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**
7. **[Search Build Config JSON](/docs/?scope=studio&doc=config-search-build-json)**
8. **[Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)**
9. **[Data Sharing Adapters](/docs/?scope=studio&doc=config-data-sharing-adapters)**

Related subsystem docs:

- **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)**
- **[Search Overview](/docs/?scope=studio&doc=search-overview)**
- **[JSON Schema Adoption Request](/docs/?scope=studio&doc=site-request-json-schema-adoption)**
