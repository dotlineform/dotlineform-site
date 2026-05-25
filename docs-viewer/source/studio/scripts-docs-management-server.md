---
doc_id: scripts-docs-management-server
title: Docs Management Service
added_date: 2026-04-24
last_updated: 2026-05-25
parent_id: docs-viewer
sort_order: 15000
---
# Docs Management Service

Service modules:

```text
docs-viewer/services/docs_viewer_service.py
docs-viewer/services/docs_management_service.py
```

`docs-viewer/services/docs_viewer_service.py` is the standalone local Docs Viewer HTTP service.
It serves the built-in `/docs/` manage shell, Docs Viewer runtime/config/static files, generated-data reads, and the management API from the Docs Viewer service base URL configured in `var/local/site.env`.

`docs-viewer/services/docs_management_service.py` owns the shared Docs Viewer management route dispatcher used by the standalone service.
Local Studio no longer serves the Docs Viewer `/docs/` shell, Docs Viewer runtime/static/config files, or `/studio/api/docs/...` proxy routes.
Studio links and document Data Sharing calls use the configured Docs Viewer service base URL from `var/local/site.env`.

The old standalone `docs-viewer/services/docs_management_server.py` HTTP entrypoint remains removed.
Use `docs-viewer/services/docs_viewer_service.py` or `docs-viewer/bin/docs-viewer` for the standalone Docs Viewer service.

## Local Service Path

```text
browser -> /docs/ -> docs_viewer_service.py -> docs_management_service.py
browser -> /docs/... API path -> docs_viewer_service.py -> docs_management_service.py
```

The service expects the project to provide:

- a Jekyll `_config.yml` at the repo root
- `docs-viewer/config/scopes/docs_scopes.json` with at least one configured docs scope
- Python dependencies needed by the docs import/export helpers
- Ruby, Bundler, and Jekyll for rebuild commands reached through `./scripts/build_docs.rb` and `./scripts/build_search.rb`

Local service location is static for v1 and comes from `var/local/site.env`:

```text
DOCS_VIEWER_HOST
DOCS_VIEWER_PORT
DOCS_VIEWER_BASE_URL
DOCS_VIEWER_MANAGEMENT_ENABLED
DOCS_VIEWER_GENERATED_READS_ENABLED
DOCS_VIEWER_WATCH_ENABLED
```

`DOCS_VIEWER_HOST` and `DOCS_VIEWER_BASE_URL` must remain loopback-only.
If the configured port is unavailable, startup fails with a clear error instead of falling back to another port.
Links to `/docs/` or the configured Docs Viewer service URL are rendered without probing service availability; when the service is stopped, they fail normally.

## Responsibilities

`docs-viewer/services/docs_management_service.py` dispatches route paths and keeps compatibility imports for existing tests and adapters.
Focused modules own the workflow behavior behind it:

- `docs-viewer/services/docs_management_context.py` owns shared paths, backups, repo/root helpers, CORS origin checks, compact logs, and path formatting.
- `docs-viewer/services/docs_management_read_service.py` owns generated docs/search/reference reads and GET dispatch.
- `docs-viewer/services/docs_management_capabilities_service.py` owns capability and scope availability payloads.
- `docs-viewer/services/docs_management_mutation_service.py` owns docs source create, metadata, viewability, move, order normalization, archive, delete apply, and scope lifecycle apply routes.
- `docs-viewer/services/docs_management_import_service.py` owns Docs/HTML import-source dependency wiring.
- `docs-viewer/services/docs_management_data_sharing_service.py` owns Data Sharing dependency wiring and handler registry assembly.
- `docs-viewer/services/docs_management_source_service.py` owns source-file open behavior.
- `docs-viewer/services/docs_management_broken_links_service.py` owns broken-links audit route behavior.

Together these modules serve generated docs index, per-doc payload, docs-search, semantic-reference, source-config, and capability payloads; coordinate source mutations, imports, rebuilds, and Data Sharing; append unified activity rows for covered actions; and coordinate successful source writes with the docs live watcher through short-lived suppression markers.

Endpoint constants live in `docs-viewer/services/docs_management_routes.py`.
HTTP transport for built-in manage mode lives in `docs-viewer/services/docs_viewer_service.py`.
The Local Studio API adapter is temporary peer-integration scaffolding during the extraction and should not be treated as the long-term Docs Viewer shell owner.

## Child References

- [Generated Reads And Config](/docs/?scope=studio&doc=scripts-docs-management-server-generated-reads) lists generated-data, source-config, capability, and source-config settings endpoints.
- [Import And Rebuild](/docs/?scope=studio&doc=scripts-docs-management-server-import-rebuild) covers create/import, explicit rebuild, and broken-link audit endpoints.
- [Data Sharing](/docs/?scope=studio&doc=scripts-docs-management-server-data-sharing) covers Library package preparation, returned package review, and apply endpoints.
- [Write Actions](/docs/?scope=studio&doc=scripts-docs-management-server-write-actions) covers source-open, metadata, viewability, move, normalize, archive, delete, and scope lifecycle endpoints.
- [Operations](/docs/?scope=studio&doc=scripts-docs-management-server-operations) covers security constraints, operational notes, verification, and related references.
