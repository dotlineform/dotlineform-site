---
doc_id: scripts-docs-management-server
title: Docs Management Server
added_date: 2026-04-24
last_updated: 2026-05-19
parent_id: docs-viewer
sort_order: 15000
---
# Docs Management Server

Script:

```bash
./scripts/docs/docs_management_server.py
```

This is the local-only write and generated-data read service for the shared Docs Viewer management route.
`bin/dev-studio` starts it on `http://127.0.0.1:8789`; standalone installs can start it directly when they only need Docs Viewer management.

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

- serves generated docs index, per-doc payload, docs-search, semantic-reference, source-config, and capability JSON to local Docs Viewer clients
- creates, imports, updates, moves, archives, deletes, rebuilds, and opens docs source files for configured writable scopes
- hosts the documents Data Sharing adapter endpoints for Library package preparation, returned-package review, and summary or hierarchy apply writes
- appends unified activity rows for covered docs import, Data Sharing package/apply, and broken-links audit actions when valid activity context is supplied
- coordinates successful source writes with the docs live watcher through short-lived suppression markers

Endpoint constants live in `scripts/docs/docs_management_routes.py`; the server handler uses explicit GET and POST dispatch tables.

## Child References

- [Generated Reads And Config](/docs/?scope=studio&doc=scripts-docs-management-server-generated-reads) lists generated-data, source-config, capability, and source-config settings endpoints.
- [Import And Rebuild](/docs/?scope=studio&doc=scripts-docs-management-server-import-rebuild) covers create/import, explicit rebuild, and broken-link audit endpoints.
- [Data Sharing](/docs/?scope=studio&doc=scripts-docs-management-server-data-sharing) covers Library package preparation, returned package review, and apply endpoints.
- [Write Actions](/docs/?scope=studio&doc=scripts-docs-management-server-write-actions) covers source-open, metadata, viewability, move/undo, normalize, archive, delete, and scope lifecycle endpoints.
- [Operations](/docs/?scope=studio&doc=scripts-docs-management-server-operations) covers security constraints, operational notes, verification, and related references.
