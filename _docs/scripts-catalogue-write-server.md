---
doc_id: scripts-catalogue-write-server
title: Catalogue Write Server
added_date: 2026-04-22
last_updated: 2026-05-19
parent_id: servers
sort_order: 4000
---
# Catalogue Write Server

Script:

```bash
./scripts/catalogue/catalogue_write_server.py
```

This is the local-only write service for mutable catalogue source JSON, catalogue prose imports, scoped public catalogue rebuilds, derived Studio lookup refreshes, publication actions, and catalogue Studio Activity rows.
It does not write back into Excel.

## Optional Flags

- `--port 8788`: override port
- `--repo-root /path/to/dotlineform-site`: override root auto-detection by parent-searching for `_config.yml`
- `--dry-run`: validate and return a response without writing source JSON

## Current Behavior

The server can:

- serve allowlisted catalogue source and lookup payloads for Studio
- create draft work, work-detail, and series records
- save existing work, work-detail, series, and moment records in canonical catalogue source JSON
- bulk-save existing work/work-detail records
- import new work/work-detail records from the configured bulk-import workbook
- import staged work, series, and moment prose Markdown into repo-local catalogue prose source files
- run scoped JSON-source rebuilds for work, series, and moment scopes
- apply shared publication preview/apply actions for works, work details, series, and moments
- write the local project-state report

## Child References

- [Endpoint Reference](/docs/?scope=studio&doc=scripts-catalogue-write-server-endpoints) lists read, save, create, delete, publication, prose import, workbook import, series, and build endpoint request contracts.
- [Build And Lookup](/docs/?scope=studio&doc=scripts-catalogue-write-server-build-lookup) covers scoped build media, moment import behavior, derived lookup refresh, and field-aware build planning.
- [Operations](/docs/?scope=studio&doc=scripts-catalogue-write-server-operations) covers module ownership, validation, security, `bin/dev-studio` integration, artifacts, and related references.
