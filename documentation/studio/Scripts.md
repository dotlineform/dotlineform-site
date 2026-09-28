---
draft: false
doc_id: d-20260423-000000-d274d3
title: Scripts
added_date: "2026-04-23 00:00:00"
last_updated: "2026-08-14 21:25:46"
parent_id: d-20260419-000000-d2e47b
---
# Scripts

This page is the signpost for active script and runner documentation.
It should not duplicate command flags, output paths, endpoint contracts, or operational caveats that belong in the owning script docs.

Use this page to find the right owner:

- local runners, environment setup, and cloud runtime assumptions
- repository check profiles, focused audits, and test operations
- Docs Viewer builds, live rebuild, management services, import/export, and link checks
- catalogue source, scoped builds, write services, lookup exports, and field-registry checks
- media derivation and R2 publishing

For repo folder ownership, see [Source Tree Ownership](Source_Tree_Ownership.md).
For environment bootstrap and local prerequisites, see [Local Setup](Local_Setup.md).
For test strategy and profile selection, see [Testing](Testing.md) and [Run Checks](Run_Checks.md).

## Local Runtime

- [Local Runners](Local_Runners.md) covers `bin/local-studio`, `bin/local-all`, sibling services, ports, and local service lifecycle.
- [Cloud Environments](Cloud_Environments.md) covers shared local/cloud runtime expectations, environment variables, and R2-backed media workflows.

## Checks And Audits

- [Run Checks](Run_Checks.md) is the entry point for check profiles and local run logs.

Focused standalone audit commands:

- [Projection Contract Audit](Projection_Contract_Validation.md)
- [Route Ready-State Audit](Route_Ready_State_Audit.md)
- [Site Consistency Audit](Site_Consistency_Audit.md)

## Docs Viewer

- [Docs Viewer Builder](Builder.md) covers docs and search payload builds for configured Docs Viewer scopes.
- [Docs Live Rebuild Watcher](Live_Rebuild_Watcher.md) covers local source watching and same-scope rebuild behavior.
- [Docs Management Service](Management_Services.md) is the parent page for generated reads, import/rebuild, write actions, operations, and retired Data Sharing management endpoints.
- [Docs Broken Links Audit](Broken_Links_Script.md) covers docs link checks.
- [Documents Package Preparation Script](Package_Prepare_Script.md) and [Documents Returned Package Script](Package_Return_Parser.md) cover documents Data Sharing package export/import flows.

## Catalogue

- [Catalogue Services](Catalogue_Services.md) explains the active adapter, mutation, transaction, and safety boundary.
- [Catalogue Source Model](Catalogue_Source_Model.md) covers canonical families, source validation, field-change order, and Series ordering.
- [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) describes current Save completion, explicit maintenance commands and the proposed Refresh action.
- [Catalogue Field Registry](Catalogue_Field_Registry.md) covers field-impact review and the read-only registry verifier.

## Media

- [Catalogue Media Pipeline Config](Catalogue_Media_Pipeline_Config.md) covers shared media policy and standalone derivative generation.
- [Publish Media To R2](Publish_Media_To_R2.md) covers previewing and uploading approved catalogue primary-image derivatives to Cloudflare R2.
