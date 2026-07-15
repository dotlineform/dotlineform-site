---
doc_id: studio
title: Studio
added_date: 2026-04-23
last_updated: 2026-07-15
summary: Entry point for using, operating, and changing the local catalogue authoring app.
parent_id: ""
viewable: true
---
# Studio

Studio is the local catalogue authoring and maintenance app. [Studio Overview](/docs/?scope=studio&doc=studio-overview) gives the short capability, execution, authority, extension, and weak-spot model.

## Use Studio

- [Catalogue Works](/docs/?scope=studio&doc=studio-works) — browse and open works.
- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor) — create and edit works and their detail sections.
- [Catalogue Series Editor](/docs/?scope=studio&doc=catalogue-series-editor) — create and edit series and membership.
- [Catalogue Drafts](/docs/?scope=studio&doc=catalogue-status) — find incomplete and draft records.
- [Bulk Add Work](/docs/?scope=studio&doc=bulk-add-work) — preview and apply workbook imports.
- [Catalogue Field Registry](/docs/?scope=studio&doc=catalogue-field-registry-review) — review field definitions and build participation.
- [Project State](/docs/?scope=studio&doc=project-state-page) — generate a report comparing project files with catalogue records.

## Operate Studio

- [Local Studio App](/docs/?scope=studio&doc=local-studio-app) — server, runtime config, and sibling-service boundary.
- [Local Runners](/docs/?scope=studio&doc=scripts-local-studio) — start Studio alone or with the other local apps.
- [Config And Save Flow](/docs/?scope=studio&doc=studio-config-and-save-flow) — browser reads, validated writes, and build follow-through.
- [Testing](/docs/?scope=studio&doc=testing) — choose focused service, route, or broader checks.

## Change The Architecture

- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime) — browser shell, route registry, templates, scripts, and ready-state execution.
- [Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json) — checked-in route and browser-safe data configuration.
- [Local Studio Routes](/docs/?scope=studio&doc=local-studio-routes) — exact mounted page inventory.
- [Local Studio APIs](/docs/?scope=studio&doc=local-studio-apis) — exact endpoint groups and adapter ownership.
- [Source Tree Ownership](/docs/?scope=studio&doc=source-tree-ownership) — Studio source, canonical data, generated data, public output, and local working boundaries.

## Code Authority

Verify exact current behavior in:

- `studio/app/frontend/config/` and `studio/app/server/studio/studio_app_config.py` for route and runtime configuration
- `studio/app/frontend/` for the shell, templates, route scripts, and shared browser helpers
- `studio/app/server/studio/` for local HTTP routing and catalogue API adaptation
- `studio/services/catalogue/` for catalogue domain behavior and write authority
- `studio/data/config/`, `studio/data/canonical/`, and `studio/data/generated/` for config and data ownership
- `studio/tests/python/` and `studio/tests/smoke/` for executable contracts

Use code/config search for exact fields, routes, endpoints, or modules. Copying them into this page would make the entry point harder to trust.

## Plan Studio Work

- [Change Requests](/docs/?scope=studio&doc=change-requests) — feature parents and finishable delivery requests.
