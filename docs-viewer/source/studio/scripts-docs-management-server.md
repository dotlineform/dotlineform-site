---
doc_id: scripts-docs-management-server
title: Management Services
added_date: 2026-04-24
last_updated: 2026-06-07
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Management Services

Docs Viewer management is the local service boundary that lets `/docs/?mode=manage` read generated Docs Viewer data, inspect source configuration, edit Markdown source docs, import staged files, run rebuilds, and perform local-only maintenance actions.

The management surface is served by the standalone Docs Viewer service:

```text
docs-viewer/bin/docs-viewer
docs-viewer/services/docs_viewer_service.py
docs-viewer/services/docs_management_service.py
```

The browser talks to the standalone service at `DOCS_VIEWER_BASE_URL`. Local Studio renders links to Docs Viewer, but it does not host `/docs/`, proxy `/studio/api/docs/...`, or provide generated-data passthroughs.

## Runtime Boundary

```text
browser -> /docs/                  -> docs_viewer_service.py
browser -> /assets/docs/...        -> docs_viewer_service.py
browser -> /docs/... API endpoints -> docs_viewer_service.py -> docs_management_service.py
```

The service expects:

- a project `_config.yml` at the repo root
- `docs-viewer/config/scopes/docs_scopes.json`
- generated docs/search artifacts for read endpoints
- Python rebuild entrypoints at `docs-viewer/build/build_docs.py` and `docs-viewer/build/build_search.py`
- local runtime settings in `var/local/site.env`

Loopback host and port are configured with:

```text
DOCS_VIEWER_HOST
DOCS_VIEWER_PORT
DOCS_VIEWER_BASE_URL
DOCS_VIEWER_MANAGEMENT_ENABLED
DOCS_VIEWER_GENERATED_READS_ENABLED
DOCS_VIEWER_WATCH_ENABLED
```

`DOCS_VIEWER_HOST` and `DOCS_VIEWER_BASE_URL` must remain loopback-only. If the configured port is unavailable, startup fails instead of silently choosing another port.

## Reference

- [Endpoint Overview](/docs/?scope=studio&doc=scripts-docs-management-endpoints) lists all GET and POST management endpoints and links to focused endpoint contracts.
- [Script Overview](/docs/?scope=studio&doc=scripts-docs-management-scripts) lists the service entrypoints, route dispatchers, helper modules, rebuild helpers, and maintenance scripts.
- [Operations](/docs/?scope=studio&doc=scripts-docs-management-server-operations) records security constraints, operational notes, and verification references.
