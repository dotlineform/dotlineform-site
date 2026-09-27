---
draft: false
doc_id: d-20260607-222033-2a494e
title: Scripts Overview
added_date: "2026-06-07 22:20:33"
last_updated: "2026-09-18 19:02:44"
parent_id: d-20260424-000000-04d75e
---
# Docs Viewer Management Script Overview

This is the ownership map for the scripts and service modules behind Docs Viewer management. Endpoint behavior is documented separately in [Endpoint Overview](Endpoint_Overview.md).

## Runtime And Dispatch

- [Service Entrypoints](Service_Entrypoints.md): `docs-viewer/bin/docs-viewer`, `docs-viewer/services/docs_viewer_service.py`
- [Route Dispatch Scripts](Route_Dispatch_Scripts.md): `docs_management_routes.py`, `docs_management_service.py`, `docs_management_context.py`

## Read And Config Helpers

- [Read And Config Scripts](Read_And_Config_Scripts.md): generated reads, capabilities, source-config report, source-config settings, and source model helpers

## Write Workflows

- [Source Mutation Scripts](Source_Mutation_Scripts.md): create, placement, delete and focused mutation apply helpers; common Title/Summary editing belongs to Source Save
- [Import Scripts](Import_Scripts.md): staged source import service and format conversion helpers
- [Source Editor Scripts](Source_Editor_Scripts.md): full source-session read, combined metadata/body Save and local editor open helpers
- [Rebuild Follow-Through Scripts](Rebuild_Follow_Through_Scripts.md): builder command orchestration and live-watcher suppression helpers
- [Audit Scripts](Audit_Scripts.md): broken-link route adapter and CLI audit engine

## Ownership Rule

Endpoint modules should parse and dispatch HTTP-shaped input. Workflow modules should own validation, planning, source writes, generated-output rebuilds, and activity/log side effects. Builders should own generated artifact formats.
