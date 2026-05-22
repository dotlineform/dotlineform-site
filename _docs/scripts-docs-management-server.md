---
doc_id: scripts-docs-management-server
title: Docs Management Server
added_date: 2026-04-24
last_updated: 2026-05-22
parent_id: docs-viewer
sort_order: 15000
---
# Docs Management Server

Script:

```bash
./scripts/docs/docs_management_server.py
```

This is the retired default local-only HTTP service for the shared Docs Viewer management route.
The same management behavior is now hosted by the Local Studio App during normal `bin/dev-studio` runs through `scripts/studio/studio_docs_api.py` and `scripts/docs/docs_management_service.py`.
Start this standalone server only for fallback/debug work or standalone Docs Viewer management experiments.

`scripts/docs/docs_management_server.py` is now a thin HTTP wrapper.
Shared Docs management behavior, route dispatch payloads, write orchestration, capabilities, imports, Data Sharing, and scope lifecycle helpers live in `scripts/docs/docs_management_service.py`.

## Quick Start

```bash
./scripts/docs/docs_management_server.py --port 8789
```

Optional flags:

- `--port 8789`: override port
- `--repo-root /path/to/dotlineform-site`: override root auto-detection by parent-searching for `_config.yml`
- `--dry-run`: validate and return responses without writing source docs

The server expects the project to provide:

- a Jekyll `_config.yml` at the repo root
- `scripts/docs/docs_scopes.json` with at least one configured docs scope
- Python dependencies needed by the docs import/export helpers
- Ruby, Bundler, and Jekyll for rebuild commands reached through `./scripts/build_docs.rb` and `./scripts/build_search.rb`

## Responsibilities

- binds a loopback-only standalone HTTP server for explicit debug or portable management experiments
- parses request bodies, applies local CORS, and maps service exceptions to HTTP responses
- delegates generated reads, capabilities, source writes, import, Data Sharing, broken links, rebuild, and scope lifecycle behavior to `scripts/docs/docs_management_service.py`

Endpoint constants live in `scripts/docs/docs_management_routes.py`.
The server handler keeps GET and POST dispatch tables for the standalone HTTP wrapper, but shared behavior is not owned by this entrypoint.

## Child References

- [Generated Reads And Config](/docs/?scope=studio&doc=scripts-docs-management-server-generated-reads) lists generated-data, source-config, capability, and source-config settings endpoints.
- [Import And Rebuild](/docs/?scope=studio&doc=scripts-docs-management-server-import-rebuild) covers create/import, explicit rebuild, and broken-link audit endpoints.
- [Data Sharing](/docs/?scope=studio&doc=scripts-docs-management-server-data-sharing) covers Library package preparation, returned package review, and apply endpoints.
- [Write Actions](/docs/?scope=studio&doc=scripts-docs-management-server-write-actions) covers source-open, metadata, viewability, move, normalize, archive, delete, and scope lifecycle endpoints.
- [Operations](/docs/?scope=studio&doc=scripts-docs-management-server-operations) covers security constraints, operational notes, verification, and related references.
