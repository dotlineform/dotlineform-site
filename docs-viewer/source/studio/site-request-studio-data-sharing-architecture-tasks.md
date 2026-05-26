---
doc_id: site-request-studio-data-sharing-architecture-tasks
title: Studio Data Sharing Architecture Tasks
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: done
parent_id: site-request-studio-data-sharing-architecture
sort_order: 100
viewable: true
---
# Studio Data Sharing Architecture Tasks

This is the tracker for implementing [Studio Data Sharing Architecture Request](/docs/?scope=studio&doc=site-request-studio-data-sharing-architecture).

## Status

### just done

- Completed SDSA-016 by running the final focused verification set and closing the architecture request. Focused Python tests passed 63 tests; prepare/review module smokes passed; the Local Studio Data Sharing route smoke passed; mocked and blocked prepare/review browser smokes passed in `--local-app` mode. Static `--site-root .` full-route prepare/review smokes timed out because the Local-Studio-owned route roots stayed hidden outside the Local Studio host.
- Completed SDSA-015 by updating the stable Studio Data Sharing docs with architecture traceability for moved modules, Studio endpoint ownership, docs-domain helper boundaries, artifact roots, verification evidence, generated Docs Viewer payload status, and remaining close-out risk. Added structured docs-log entry `change-2026-05-26-completed-studio-data-sharing-architecture-boundary`. Codex did not manually rebuild Docs Viewer generated payloads; local docs-watcher output from source doc changes is expected.
- Completed SDSA-014 by aligning focused tests and smokes with the Studio-owned Data Sharing API boundary. Studio API tests now cover returned-package listing, review, and apply dispatch through registered handlers; Docs Management route tests assert no `/data-sharing/...` publication; prepare/review smokes now use only `--mock-data-sharing-api` and `--block-data-sharing-api` flags; mocked, blocked, and route-level Data Sharing smokes passed against `/studio/api/data-sharing/...`.
- Completed SDSA-013 by removing Data Sharing endpoint publication from `app.runtime.services.docs`, retiring the Docs Viewer `/data-sharing/...` HTTP bridge, and updating focused tests to assert that Docs Management routes no longer publish Data Sharing endpoints. Docs Viewer links remain for nav and `doc_href`; Data Sharing browser calls now rely on `app.runtime.services.data_sharing`.
- Completed SDSA-012 by switching `studio-transport.js` Data Sharing defaults and runtime overrides to `app.runtime.services.data_sharing` same-origin `/studio/api/data-sharing/...` endpoints. The prepare/review pages now use Studio Data Sharing API unavailable-state copy, and focused smokes mock or block Studio API paths instead of Docs Viewer service paths.
- Completed SDSA-011 by enforcing Data Sharing runtime artifact roots in the adapter registry validator. `outbound_package_root`, `returned_package_staging_root`, and `review_output_root` must now resolve to `var/studio/data-sharing/<data_domain>/exports`, `import-staging`, and `import-preview`; a focused registry test rejects old `var/studio/export-import/...` roots.
- Completed SDSA-010 by moving the Analytics tags adapter implementation from `studio/services/analytics/tags_data_sharing_adapter.py` to `data-sharing/data_sharing/adapters/tags/adapter.py`. Studio and Docs Viewer service handler maps now import the Data Sharing-owned tags adapter directly, and direct tags adapter tests pass resolved adapter context explicitly so validation, backup, write, and activity behavior runs through the shared workflow dispatch contract.
- Completed SDSA-009 by moving the documents adapter implementation from `docs-viewer/services/documents_data_sharing_adapter.py` to `data-sharing/data_sharing/adapters/documents/adapter.py`. Studio and Docs Viewer service bridges now import the Data Sharing-owned documents adapter directly, and direct adapter tests pass resolved adapter context explicitly.
- Completed SDSA-008 by extracting reusable Docs Viewer docs-domain helpers under `docs-viewer/services/docs_data_sharing/` for Data Sharing package/selectable-record reads, returned-package listing and review rows, summary/hierarchy apply planning, and source write backup/rebuild follow-through. The documents adapter now delegates to those helpers while preserving the current Studio/Data Sharing response contracts.
- Completed SDSA-007 by moving shared operation dispatch and adapter handler selection into `data-sharing/data_sharing/services/dispatch.py`, exposing headless workflow entry points for prepare, list-returned, review, and apply, and narrowing `studio/app/server/studio/data_sharing_service.py` to a compatibility gateway that supplies the current Studio adapter resolver.
- Completed SDSA-006 by adding selectable-record dispatch to the Data Sharing adapter handler contract, moving Library document selectable-record shaping into the documents adapter, returning a profile-only empty selectable-record payload for the tags adapter, and updating the prepare page to load document selection from `/studio/api/data-sharing/selectable-records` instead of the generic generated-docs-index endpoint.
- Completed SDSA-005 by adding Studio-owned same-origin `/studio/api/data-sharing/...` endpoints for health, selectable records, returned-package listing, prepare, review, and apply. Local Studio runtime config now publishes these endpoints under `app.runtime.services.data_sharing`, and the Local Studio Data Sharing route smoke verifies health/selectable-record API availability.
- Completed SDSA-004 by moving the Data Sharing adapter registry, schemas, and Library sharing profiles from `studio/data/config/data-sharing/` to `data-sharing/config/`. Updated Studio browser config paths, JS fallbacks, server adapter resolution, docs export defaults, fixture tests, and current docs to use the new config boundary directly without old-path compatibility reads.
- Completed SDSA-003 by adding the top-level `data-sharing/` subsystem scaffold, including the importable `data_sharing` Python package roots for adapters, config, schemas, services, workflows, path contracts, package I/O, registry constants, and operation constants. Added a focused scaffold check confirming the package imports, expected roots exist, and no server/UI/browser files live under `data-sharing/`.
- Completed SDSA-002 by adding [Studio Data Sharing Call Graph Inventory](/docs/?scope=studio&doc=site-request-studio-data-sharing-call-graph-inventory), covering browser modules, runtime config, transport, service dispatch, adapters, helper dependencies, path roots, and tests.
- Completed SDSA-001 by updating the stable Data Sharing docs with the target Studio API, headless `data-sharing/` subsystem, adapter-owned selectable records, reusable docs-domain helpers, and `var/studio/data-sharing/<domain>/...` artifact roots.
- Created this task tracker from the architecture request.
- Folded the settled open-question decisions back into the parent request so it reads as the design target.

### closeout steer

- The architecture request is complete and ready for archival when the current change-request practice calls for it.
- Keep future work aligned with the closed boundary: Studio owns the UI and local API, `data-sharing/` owns headless workflow and adapters, and docs-domain helpers remain callable without Docs Viewer HTTP.
- Do not reintroduce compatibility reads for disposable `var/studio/export-import/...` packages.

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
| SDSA-006 | done | Add the adapter selectable-record contract and update the prepare page so document selection comes from the active adapter response rather than a generic generated-docs-index read. |
| SDSA-007 | done | Move shared prepare, list-returned, review, and apply workflow dispatch into `data-sharing/`, preserving existing response contracts where they remain valid. |
| SDSA-008 | done | Define and implement the target docs-domain helper modules for document package generation, returned-package review, summary/hierarchy apply planning, source writes, backups, and docs/search rebuild follow-through. These helpers must be callable without Docs Viewer HTTP or UI/service wrapper modules. |
| SDSA-009 | done | Move the documents adapter to the `data-sharing/` adapter boundary and have it call the docs-domain helpers directly for generated reads, package creation, review, apply, backups, and rebuilds. |
| SDSA-010 | done | Move or update the tags adapter so it is resolved through the same `data-sharing/` adapter registry and workflow dispatch while preserving Analytics tag validation, backup, write, and activity behavior. |
| SDSA-011 | done | Standardize active package, staging, and review roots under `var/studio/data-sharing/<domain>/...`. Remove `var/studio/export-import/...` assumptions and do not add compatibility reads for disposable packages. |
| SDSA-012 | done | Update `studio-transport.js` and related frontend modules so Data Sharing uses Studio-owned same-origin endpoints and no longer depends on `DOCS_VIEWER_BASE_URL`. |
| SDSA-013 | done | Remove Data Sharing endpoint publication from `app.runtime.services.docs` and remove the temporary Docs Viewer service endpoint helpers once Studio endpoints are live. Keep Docs Viewer links for nav and `doc_href` only. |
| SDSA-014 | done | Update focused tests and smokes for the new service boundary, adapter resolution, selectable-record contract, document prepare/review/apply flows, tags prepare/review/apply flows, artifact roots, and unavailable-service states. |
| SDSA-015 | done | Update owning docs and add a structured docs-log entry describing moved modules, endpoint ownership, helper boundaries, artifact roots, verification results, generated payload status, and remaining risks. |
| SDSA-016 | done | Run the final verification set appropriate to the changed files, then close out the parent request and this tracker by updating statuses, recording verification evidence, and noting any follow-on work before archival. |
