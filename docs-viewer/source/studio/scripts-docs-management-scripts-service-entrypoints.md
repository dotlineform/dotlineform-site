---
doc_id: scripts-docs-management-scripts-service-entrypoints
title: Service Entrypoints
added_date: 2026-06-07
last_updated: 2026-07-11
parent_id: scripts-docs-management-scripts
---
# Docs Viewer Service Entrypoints

## `docs-viewer/bin/docs-viewer`

Purpose: project-local launcher for the standalone Docs Viewer service.

Ownership: owns interpreter selection and process handoff only.

Responsibilities:

- changes the working directory to the repo root
- prefers `$HOME/miniconda3/bin/python3` when available
- falls back to `PYTHON_BIN` or `python3`
- executes `docs-viewer/services/docs_viewer_service.py` with the original arguments

Not responsible for:

- endpoint dispatch
- source validation
- generated-data reads
- rebuild behavior

## `docs-viewer/services/docs_viewer_service.py`

Purpose: HTTP transport and static/runtime host for the standalone Docs Viewer service.

Ownership: owns the local HTTP server boundary for `/docs/` and `/docs-review/`, Docs Viewer assets/config, generated read passthroughs, management API transport, and independently gated review API transport.

Responsibilities:

- loads local Docs Viewer service config from `.env.local`
- enforces loopback service binding
- serves `/docs/` management shell HTML
- serves `/docs-review/` returned-package shell HTML
- gates returned-package review through `DOCS_VIEWER_REVIEW_ENABLED` independently of canonical management
- dispatches package-rooted review reads, builds, assets, temporary Markdown, and hierarchy writes without canonical mutation routes
- serves Docs Viewer runtime, static assets, and route config
- applies CORS and request-size handling for management API calls
- forwards allowlisted GET and POST API paths to management dispatch modules
- sends JSON responses with no-store caching
- fails startup when the configured port is unavailable

Not responsible for:

- planning source mutations
- parsing Markdown source models
- deciding which docs/search outputs are rebuilt after a write
- converting staged import files
