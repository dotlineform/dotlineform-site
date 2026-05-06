---
doc_id: config
title: Config
added_date: 2026-03-31
last_updated: "2026-05-06 20:49"
parent_id: ""
sort_order: 120
---
# Config

This section documents the checked-in configuration artifacts that the current site and build scripts load directly.

Use this section for:

- site-wide Jekyll config in `_config.yml`
- shared catalogue/media/runtime defaults in `_data/pipeline.json`
- shared Studio/search browser config in `assets/studio/data/studio_config.json`
- the Studio/search config loader in `assets/studio/js/studio-config.js`
- dedicated `/search/` runtime policy in `assets/data/search/policy.json`
- build-owned search source-family config in `scripts/search/build_config.json`
- Library export config patterns in `assets/studio/data/library_export_configs.json`
- Library export config schema in `assets/studio/data/library_export_configs.schema.json`
- export/import adapter dispatch in `assets/studio/data/export_import_adapters.json`
- export/import adapter schema in `assets/studio/data/export_import_adapters.schema.json`

This section is not for:

- local shell exports and machine-specific setup
- detailed payload schemas, which belong in [Data Models](/docs/?scope=studio&doc=data-models)

Read this section in this order:

1. **[Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config)**
2. **[Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json)**
3. **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**
4. **[Studio Config Loader JS](/docs/?scope=studio&doc=config-studio-config-js)**
5. **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**
6. **[Search Build Config JSON](/docs/?scope=studio&doc=config-search-build-json)**
7. **[Library Export Configs](/docs/?scope=studio&doc=config-library-export-configs)**
8. **[Export Import Adapters](/docs/?scope=studio&doc=config-export-import-adapters)**

Related subsystem docs:

- **[Studio Config and Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow)**
- **[Search Overview](/docs/?scope=studio&doc=search-overview)**
- **[Scripts](/docs/?scope=studio&doc=scripts)**
- **[JSON Schema Adoption Request](/docs/?scope=studio&doc=site-request-json-schema-adoption)**
