---
doc_id: scripts-docs-management-server
title: Docs Management Service
added_date: 2026-04-24
last_updated: 2026-05-22
parent_id: docs-viewer
sort_order: 15000
---
# Docs Management Service

Service module:

```text
scripts/docs/docs_management_service.py
```

This module owns shared Docs Viewer management behavior for Local Studio.
It is called by `scripts/studio/studio_docs_api.py`, and browser traffic reaches it through the Local Studio app at `/studio/api/docs/...`.

The old standalone `scripts/docs/docs_management_server.py` HTTP entrypoint has been removed.
There is no supported standalone Docs Management server process and no `127.0.0.1:8789` fallback.

## Local Studio Path

```text
browser -> /studio/api/docs/... -> studio_app_server.py -> studio_docs_api.py -> docs_management_service.py
```

The service expects the project to provide:

- a Jekyll `_config.yml` at the repo root
- `scripts/docs/docs_scopes.json` with at least one configured docs scope
- Python dependencies needed by the docs import/export helpers
- Ruby, Bundler, and Jekyll for rebuild commands reached through `./scripts/build_docs.rb` and `./scripts/build_search.rb`

## Responsibilities

- serves generated docs index, per-doc payload, docs-search, semantic-reference, source-config, and capability payloads to the Local Studio Docs API adapter
- creates, imports, updates, moves, archives, deletes, rebuilds, and opens docs source files for configured writable scopes
- owns the documents Data Sharing service calls for Library package preparation, returned-package review, and summary or hierarchy apply writes
- appends unified activity rows for covered docs import, Data Sharing package/apply, and broken-links audit actions when valid activity context is supplied
- coordinates successful source writes with the docs live watcher through short-lived suppression markers

Endpoint constants live in `scripts/docs/docs_management_routes.py`.
HTTP transport lives in the Local Studio app server, not in this Docs module.

## Child References

- [Generated Reads And Config](/docs/?scope=studio&doc=scripts-docs-management-server-generated-reads) lists generated-data, source-config, capability, and source-config settings endpoints.
- [Import And Rebuild](/docs/?scope=studio&doc=scripts-docs-management-server-import-rebuild) covers create/import, explicit rebuild, and broken-link audit endpoints.
- [Data Sharing](/docs/?scope=studio&doc=scripts-docs-management-server-data-sharing) covers Library package preparation, returned package review, and apply endpoints.
- [Write Actions](/docs/?scope=studio&doc=scripts-docs-management-server-write-actions) covers source-open, metadata, viewability, move, normalize, archive, delete, and scope lifecycle endpoints.
- [Operations](/docs/?scope=studio&doc=scripts-docs-management-server-operations) covers security constraints, operational notes, verification, and related references.
