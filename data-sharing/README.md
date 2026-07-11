# Data Sharing Subsystem

This directory is the top-level headless owner for Data Sharing workflow code.

The subsystem owns shared Data Sharing concerns:

- adapter registry and config loading
- adapter implementations by data domain
- workflow dispatch for `prepare`, `list_returned`, `review`, and `apply`
- marker-rooted path contracts under `$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/`
- package I/O and schema contracts

It must not own:

- servers or HTTP route mounting
- local app page shells or browser modules
- Docs Viewer UI routes
- local app runtime config publication

Local Analytics owns the active Data Sharing UI pages and same-origin local API endpoints.
Domain helpers, such as docs source read/write helpers, stay domain-aware and reusable.

## Python Package

When used directly, add `data-sharing/` to `PYTHONPATH` or `sys.path` and import the top-level ownership packages:

- `adapters`
- `services`
- `workflows`

The source-controlled adapter registry and registry schema live under `data-sharing/config/`.
Adapter-specific config, such as documents prepare profiles, lives with the owning adapter.
Current shared workflow dispatch and the implemented documents and tags adapters live under `data-sharing/services/`, `data-sharing/workflows/`, and `data-sharing/adapters/`.
Analytics owns the local API, browser routes, and adapter resolver gateway; Docs Viewer still supplies reusable docs-domain helpers for document workflows.
