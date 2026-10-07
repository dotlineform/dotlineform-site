---
draft: false
doc_id: d-20260423-000000-d015e6
title: Studio
added_date: "2026-04-23 00:00:00"
last_updated: "2026-10-07 16:46:38"
summary: Entry point for using, operating, and changing the local catalogue authoring app.
parent_id: ""

---
# Studio

Studio is the local catalogue authoring and maintenance app. [Studio Overview](Studio_Overview.md) gives the short capability, execution, authority, extension, and weak-spot model.

## Use Studio

- [Catalogue Work Editor](Catalogue_Work_Editor.md) — create and edit works and their detail sections.
- [Catalogue Series Editor](Catalogue_Series_Management.md) — create and edit series and membership.
- [Catalogue Field Registry](Catalogue_Field_Registry.md) — review field definitions and build participation.

Keep Analysis open in another tab for document browsing and Concept work. Work Details folder import is available inside the Work editor.

## Operate Studio

- [Local Studio App](Local_Studio_App.md) — server, runtime config, and sibling-service boundary.
- [Local Runners](Local_Runners.md) — start Studio alone or with the other local apps.
- [Config And Save Flow](Studio_Read_And_Save_Flow.md) — browser reads, validated writes, and build follow-through.
- [Testing](Testing.md) — choose focused service, route, or broader checks.

## Change The Architecture

- [Studio Runtime](Studio_Runtime.md) — browser shell, route registry, templates, scripts, and ready-state execution.
- [Catalogue Architecture](Catalogue_Architecture.md) — canonical source and generated read-model boundaries.
- [Catalogue Services](Catalogue_Services.md) — mutation, transaction, build, lookup, and media-service boundaries.
- [Studio Domain Config](Studio_Domain_Config.md) — checked Catalogue policy.
- [Catalogue Media Pipeline Config](Catalogue_Media_Pipeline_Config.md) — shared source-media and derivative policy.
- [Publish Media To R2](Publish_Media_To_R2.md) — confined remote media transport and confirmed versions.
- [Source Tree Ownership](Source_Tree_Ownership.md) — Studio source, canonical data, generated data, public output, and local working boundaries.

## Code Authority

Verify exact current behavior in:

- `studio/app/frontend/config/` and `studio/app/server/studio/studio_app_config.py` for route and runtime configuration
- `studio/app/frontend/` for the shell, templates, route scripts, and shared browser helpers
- `studio/app/server/studio/` for local HTTP routing and Catalogue API adaptation
- `studio/services/catalogue/` for domain behavior and write authority
- `studio/data/config/` and `studio/data/canonical/` for config and canonical data ownership
- `studio/tests/python/` for focused deterministic evidence
- `studio/tests/smoke/` for the retained route-integration boundaries

Use code/config search for exact fields, routes, endpoints, or modules. Copying them into this page would make the entry point harder to trust.

## Plan Studio Work

- [Planned Features](Planned_Features.md) is used for new feature, concept, architecture, and delivery model development.
