---
doc_id: scripts-docs-management-scripts
title: Docs Viewer Management Script Overview
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: scripts-docs-management-server
---
# Docs Viewer Management Script Overview

This is the ownership map for the scripts and service modules behind Docs Viewer management. Endpoint behavior is documented separately in [Endpoint Overview](/docs/?scope=studio&doc=scripts-docs-management-endpoints).

## Runtime And Dispatch

- [Service Entrypoints](/docs/?scope=studio&doc=scripts-docs-management-scripts-service-entrypoints): `docs-viewer/bin/docs-viewer`, `docs-viewer/services/docs_viewer_service.py`
- [Route Dispatch Scripts](/docs/?scope=studio&doc=scripts-docs-management-scripts-route-dispatch): `docs_management_routes.py`, `docs_management_service.py`, `docs_management_context.py`

## Read And Config Helpers

- [Read And Config Scripts](/docs/?scope=studio&doc=scripts-docs-management-scripts-read-config): generated reads, capabilities, source-config report, source-config settings, and source model helpers

## Write Workflows

- [Source Mutation Scripts](/docs/?scope=studio&doc=scripts-docs-management-scripts-source-mutations): create, metadata, viewability, move, delete, and scope lifecycle apply helpers
- [Import Scripts](/docs/?scope=studio&doc=scripts-docs-management-scripts-import): staged source import service and format conversion helpers
- [Source Editor Scripts](/docs/?scope=studio&doc=scripts-docs-management-scripts-source-editor): source body read/rebuild and local editor open helpers
- [Rebuild Follow-Through Scripts](/docs/?scope=studio&doc=scripts-docs-management-scripts-rebuild-follow-through): builder command orchestration and live-watcher suppression helpers
- [Audit Scripts](/docs/?scope=studio&doc=scripts-docs-management-scripts-audit): broken-link route adapter and CLI audit engine

## Ownership Rule

Endpoint modules should parse and dispatch HTTP-shaped input. Workflow modules should own validation, planning, source writes, generated-output rebuilds, and activity/log side effects. Builders should own generated artifact formats.
