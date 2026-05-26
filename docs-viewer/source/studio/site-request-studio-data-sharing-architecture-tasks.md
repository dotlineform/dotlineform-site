---
doc_id: site-request-studio-data-sharing-architecture-tasks
title: Studio Data Sharing Architecture Tasks
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: in-progress
parent_id: site-request-studio-data-sharing-architecture
sort_order: 100
viewable: true
---
# Studio Data Sharing Architecture Tasks

This is the tracker for implementing [Studio Data Sharing Architecture Request](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture).

## Status

### just done

- Completed SDSA-005 by adding Studio-owned same-origin `/studio/api/data-sharing/...` endpoints for health, selectable records, returned-package listing, prepare, review, and apply. Local Studio runtime config now publishes these endpoints under `app.runtime.services.data_sharing`, and the Local Studio Data Sharing route smoke verifies health/selectable-record API availability.
- Completed SDSA-004 by moving the Data Sharing adapter registry, schemas, and Library sharing profiles from `studio/data/config/data-sharing/` to `data-sharing/config/`. Updated Studio browser config paths, JS fallbacks, server adapter resolution, docs export defaults, fixture tests, and current docs to use the new config boundary directly without old-path compatibility reads.
- Completed SDSA-003 by adding the top-level `data-sharing/` subsystem scaffold, including the importable `data_sharing` Python package roots for adapters, config, schemas, services, workflows, path contracts, package I/O, registry constants, and operation constants. Added a focused scaffold check confirming the package imports, expected roots exist, and no server/UI/browser files live under `data-sharing/`.
- Completed SDSA-002 by adding [Studio Data Sharing Call Graph Inventory](/docs/?scope=studio&doc=site-request-studio-data-sharing-call-graph-inventory), covering browser modules, runtime config, transport, service dispatch, adapters, helper dependencies, path roots, and tests.
- Completed SDSA-001 by updating the stable Data Sharing docs with the target Studio API, headless `data-sharing/` subsystem, adapter-owned selectable records, reusable docs-domain helpers, and `var/studio/data-sharing/<domain>/...` artifact roots.
- Created this task tracker from the architecture request.
- Folded the settled open-question decisions back into the parent request so it reads as the design target.

### steer for next task

- Start with SDSA-006: add the adapter selectable-record contract to the prepare page so document selection comes from the active adapter response rather than a generic generated-docs-index read.
- Keep the implementation aligned with the parent request: Studio owns the UI and local API, `data-sharing/` owns headless workflow and adapters, and docs-domain helpers remain callable without Docs Viewer HTTP.
- Do not build compatibility reads for disposable `var/studio/export-import/...` packages.

### baseline verification set

- Focused Python tests: `$HOME/miniconda3/bin/python3 -m pytest studio/tests/python/test_data_sharing_adapters.py studio/tests/python/test_data_sharing_service.py docs-viewer/tests/python/test_docs_import_service.py studio/tests/python/test_tags_data_sharing_adapter.py`.
- Focused Data Sharing route smoke: `$HOME/miniconda3/bin/python3 studio/tests/smoke/local_studio_app_data_sharing_routes.py` when Local Studio route behavior, runtime config paths, or Data Sharing browser config paths change.
- Focused static/module smokes: `$HOME/miniconda3/bin/python3 studio/tests/smoke/data_sharing_prepare_modules.py --site-root .` and `$HOME/miniconda3/bin/python3 studio/tests/smoke/data_sharing_review_workflow_modules.py --site-root .` when prepare/review browser workflow modules change.
- Runtime config tests that assert Studio no longer publishes Data Sharing endpoints under `app.runtime.services.docs`.
- Syntax/import checks for changed Python modules under `data-sharing/`, `studio/app/server/studio/`, `docs-viewer/services/`, and `studio/services/analytics/`.
- Browser checks for prepare/review pages when frontend endpoint or selectable-record behavior changes.
- Broader `quick` or Docs Viewer smoke profiles only when the touched slice changes shared runtime behavior, Docs Viewer service behavior, generated docs/search contracts, or route readiness.

Codex sandbox note: local service, browser, and temporary localhost checks will need elevated permissions even when the product code is healthy.

### general steer

- Treat this as a boundary implementation, not a visual redesign.
- Prefer direct moves and reference updates over compatibility shims for old service endpoints or old artifact roots.
- The target state is not wrapper-first: docs-domain package, review, apply, backup, and rebuild helpers should have explicit reusable module boundaries in this slice.
- Prepare-page document selection belongs behind the active adapter, not behind a generic Studio generated-docs-index endpoint.
- `var/studio/data-sharing/<domain>/...` is the target runtime artifact convention for this implementation.
- Use sibling docs for large inventories, target layouts, contract tables, or path maps so this tracker remains a concise sequential task list.

## Implementation Tasks

Work through the table by ID order. A `deferred` row is intentionally out of the implementation path and includes the reason in the action. Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| SDSA-001 | done | Update `studio-data-sharing.md`, `studio-data-sharing-technical-spec.md`, and `config-data-sharing-adapters.md` with the target boundary: Studio same-origin API, headless `data-sharing/`, adapter-owned selectable records, reusable docs-domain helpers, and `var/studio/data-sharing/<domain>/...` artifact roots. |
| SDSA-002 | done | Inventory the current Data Sharing call graph: browser modules, runtime config, Studio transport, Studio dispatch modules, Docs Viewer service endpoints, documents adapter, tags adapter, docs export/import helpers, backup/rebuild hooks, config reads, and tests. |
| SDSA-003 | done | Create the top-level headless `data-sharing/` subsystem for workflow code, adapter code, registry/config loading, schemas, path contracts, package I/O, and operation dispatch. Confirm it contains no servers, UI routes, or browser modules. |
| SDSA-004 | done | Move Data Sharing adapter registry, schemas, and sharing profile config to the target `data-sharing/` ownership boundary. Update Studio and adapter readers directly, without old-path compatibility shims. |
| SDSA-005 | done | Define and implement Studio-owned same-origin Data Sharing API endpoints for health, adapter selectable records, prepare, returned-package listing, review, and apply. |
| SDSA-006 | planned | Add the adapter selectable-record contract and update the prepare page so document selection comes from the active adapter response rather than a generic generated-docs-index read. |
| SDSA-007 | planned | Move shared prepare, list-returned, review, and apply workflow dispatch into `data-sharing/`, preserving existing response contracts where they remain valid. |
| SDSA-008 | planned | Define and implement the target docs-domain helper modules for document package generation, returned-package review, summary/hierarchy apply planning, source writes, backups, and docs/search rebuild follow-through. These helpers must be callable without Docs Viewer HTTP or UI/service wrapper modules. |
| SDSA-009 | planned | Move the documents adapter to the `data-sharing/` adapter boundary and have it call the docs-domain helpers directly for generated reads, package creation, review, apply, backups, and rebuilds. |
| SDSA-010 | planned | Move or update the tags adapter so it is resolved through the same `data-sharing/` adapter registry and workflow dispatch while preserving Analytics tag validation, backup, write, and activity behavior. |
| SDSA-011 | planned | Standardize active package, staging, and review roots under `var/studio/data-sharing/<domain>/...`. Remove `var/studio/export-import/...` assumptions and do not add compatibility reads for disposable packages. |
| SDSA-012 | planned | Update `studio-transport.js` and related frontend modules so Data Sharing uses Studio-owned same-origin endpoints and no longer depends on `DOCS_VIEWER_BASE_URL`. |
| SDSA-013 | planned | Remove Data Sharing endpoint publication from `app.runtime.services.docs` and remove the temporary Docs Viewer service endpoint helpers once Studio endpoints are live. Keep Docs Viewer links for nav and `doc_href` only. |
| SDSA-014 | planned | Update focused tests and smokes for the new service boundary, adapter resolution, selectable-record contract, document prepare/review/apply flows, tags prepare/review/apply flows, artifact roots, and unavailable-service states. |
| SDSA-015 | planned | Update owning docs and add a structured docs-log entry describing moved modules, endpoint ownership, helper boundaries, artifact roots, verification results, generated payload status, and remaining risks. |
| SDSA-016 | planned | Run the final verification set appropriate to the changed files, then close out the parent request and this tracker by updating statuses, recording verification evidence, and noting any follow-on work before archival. |
