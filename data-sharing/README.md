# Data Sharing Subsystem

This directory is the top-level headless owner for Studio Data Sharing workflow code.

The subsystem owns shared Data Sharing concerns:

- adapter registry and config loading
- adapter implementations by data domain
- workflow dispatch for `prepare`, `list_returned`, `review`, and `apply`
- path contracts for `var/studio/data-sharing/<domain>/...`
- package I/O and schema contracts

It must not own:

- servers or HTTP route mounting
- Studio page shells or browser modules
- Docs Viewer UI routes
- local app runtime config publication

Studio remains the owner of Data Sharing UI pages and same-origin local API endpoints.
Domain helpers, such as docs source read/write helpers, stay domain-aware and reusable.

## Python Package

The importable Python package lives under `data-sharing/data_sharing/`.
When used directly, add `data-sharing/` to `PYTHONPATH` or `sys.path` and import `data_sharing`.

Current runtime behavior still lives in the pre-migration Studio and Docs Viewer modules.
Follow-up SDSA tasks move registry/config, adapters, workflows, Studio endpoints, artifact roots, and tests into this boundary in order.
