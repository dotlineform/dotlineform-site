---
doc_id: update-tests
title: Tests policy and refactoring
added_date: 2026-06-25
last_updated: 2026-06-25
ui_status: in-progress
parent_id: change-requests
---
# Tests policy and refactoring

The policy should be:

Tests protect data flows, server contracts, persistence, generated outputs, and integration boundaries. They should not police normal UI behavior, modal choreography, focus timing, button labels, or DOM layout. UI checks should be limited to “route boots and can talk to the server” unless there is a specific accessibility or public-read-only boundary that cannot be covered lower down.

**First Practical Cleanup Batch**

I would start with Docs Viewer:
1. Extract `test_docs_management_service.py` into 5-7 focused files.
2. Move current `default_doc_id` coverage into `test_docs_source_config_settings.py`.
3. Trim `docs_viewer_management_ui.py` back to route boot plus endpoint availability.
4. Retire most of `docs_viewer_management_modal.py`; keep only if we still want a reusable modal primitive contract.
5. Repeat the same pattern for Analytics modals and Studio catalogue modal smokes.

**Work Needed**

1. Codify the policy
   - Update `docs-viewer/source/studio/testing.md`, `testing-pytest.md`, `smoke-testing.md`, and `development-checklist.md`.
   - Add a clear rule: no new UI behavior assertions unless the acceptance contract is explicitly browser-bound.
   - Update `admin-app/commands/run_checks.py` profile descriptions so “smoke” does not imply broad UI workflow coverage.

done: Codified the testing policy.

Changes landed in:
- [testing.md](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/source/studio/testing.md:20): added the core policy that permanent tests should focus on data flows, server responses, generated contracts, ownership boundaries, and route/module integration, not UI choreography.
- [testing-pytest.md](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/source/studio/testing-pytest.md:55): clarified Python tests should cover payloads/responses/data flows, not modal timing, cursor state, copy, focus, or layout.
- [smoke-testing.md](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/source/studio/smoke-testing.md:19): narrowed browser smoke guidance to route/module/API boundaries and marked UI-heavy smokes as cleanup targets.
- [development-checklist.md](/Users/dlf/Developer/dotlineform/dotlineform-site/docs-viewer/source/studio/development-checklist.md:104): updated verification guidance so UI/layout work uses manual or temporary browser checks, not new permanent workflow tests.
- [run_checks.py](/Users/dlf/Developer/dotlineform/dotlineform-site/admin-app/commands/run_checks.py:428): changed smoke profile descriptions so modal-heavy checks are labelled legacy/focused, not the pattern to extend.

2. Split oversized Python tests by service boundary
   Biggest offenders:
   - `docs-viewer/tests/python/test_docs_management_service.py` at 1656 lines
   - `docs-viewer/tests/python/test_docs_import_service.py` at 1578 lines
   - `docs-viewer/tests/python/test_build_docs_python.py` at 983 lines
   - `studio/tests/python/test_studio_app_server.py` at 769 lines
   - `docs-viewer/tests/python/test_docs_viewer_service.py` at 749 lines
   - `analytics-app/tests/python/test_tags_data_sharing_adapter.py` at 673 lines

   These should become smaller files named by contract, for example:
   - `test_docs_source_config_settings.py`
   - `test_docs_management_create_delete.py`
   - `test_docs_management_scope_lifecycle.py`
   - `test_docs_management_generated_reads.py`
   - `test_docs_import_conversion.py`
   - `test_docs_import_media_plans.py`

done: Split `docs-viewer/tests/python/test_docs_management_service.py` by service boundary.

The deleted monolith is now:
- `docs-viewer/tests/python/docs_management_test_support.py`
- `docs-viewer/tests/python/test_docs_management_metadata.py`
- `docs-viewer/tests/python/test_docs_management_capabilities.py`
- `docs-viewer/tests/python/test_docs_scope_config.py`
- `docs-viewer/tests/python/test_docs_scope_lifecycle.py`
- `docs-viewer/tests/python/test_docs_source_config_settings.py`
- `docs-viewer/tests/python/test_docs_data_sharing_export.py`

`admin-app/commands/run_checks.py --profile docs` now references the split files directly.

done: Split `docs-viewer/tests/python/test_docs_import_service.py` by import contract.

The deleted import monolith is now:
- `docs-viewer/tests/python/docs_import_test_support.py`
- `docs-viewer/tests/python/test_docs_import_returned_packages.py`
- `docs-viewer/tests/python/test_docs_import_source_listing.py`
- `docs-viewer/tests/python/test_docs_import_source_html.py`
- `docs-viewer/tests/python/test_docs_import_source_formats.py`
- `docs-viewer/tests/python/test_docs_import_media_packages.py`
- `docs-viewer/tests/python/test_docs_import_apply_summaries.py`
- `docs-viewer/tests/python/test_docs_import_apply_hierarchy.py`

`admin-app/commands/run_checks.py --profile docs` now references the import split files directly.

done: Split `docs-viewer/tests/python/test_build_docs_python.py` by builder contract.

The deleted builder monolith is now:
- `docs-viewer/tests/python/build_docs_test_support.py`
- `docs-viewer/tests/python/test_build_docs_payloads.py`
- `docs-viewer/tests/python/test_build_docs_subscopes.py`
- `docs-viewer/tests/python/test_build_docs_public_payloads.py`
- `docs-viewer/tests/python/test_build_docs_cli.py`
- `docs-viewer/tests/python/test_build_docs_external_scopes.py`

`admin-app/commands/run_checks.py --profile docs` now includes the split builder pytest files.

done: Split `studio/tests/python/test_studio_app_server.py` by Studio server contract.

The deleted Studio app server monolith is now:
- `studio/tests/python/studio_app_server_test_support.py`
- `studio/tests/python/test_studio_app_runtime_config.py`
- `studio/tests/python/test_studio_catalogue_read_routes.py`
- `studio/tests/python/test_studio_catalogue_import_routes.py`
- `studio/tests/python/test_studio_catalogue_write_routes.py`

`admin-app/commands/run_checks.py` now references the split Studio app server files in its static Python path inventory.

done: Split `docs-viewer/tests/python/test_docs_viewer_service.py` by Docs Viewer service contract.

The deleted Docs Viewer service monolith is now:
- `docs-viewer/tests/python/docs_viewer_service_test_support.py`
- `docs-viewer/tests/python/test_docs_viewer_public_runtime_boundaries.py`
- `docs-viewer/tests/python/test_docs_viewer_management_runtime_boundaries.py`
- `docs-viewer/tests/python/test_docs_viewer_service_config.py`
- `docs-viewer/tests/python/test_docs_viewer_static_assets.py`

`admin-app/commands/run_checks.py --profile docs` and the static Python path inventory now reference the split Docs Viewer service files.

done: Split `analytics-app/tests/python/test_tags_data_sharing_adapter.py` by Analytics tags Data Sharing contract.

The deleted Analytics tags adapter monolith is now:
- `analytics-app/tests/python/tags_data_sharing_adapter_test_support.py`
- `analytics-app/tests/python/test_tags_data_sharing_prepare.py`
- `analytics-app/tests/python/test_tags_data_sharing_returned_registry_aliases.py`
- `analytics-app/tests/python/test_tags_data_sharing_returned_assignments.py`

`admin-app/commands/run_checks.py` now references the split Analytics tags Data Sharing files in its static Python path inventory.

3. Remove UI assertions from Python service tests
   Service tests should assert:
   - request payload validation
   - response JSON shape
   - written source/config files
   - generated output follow-through
   - activity rows/log events
   - publish/rebuild plans
   - error responses

   They should not assert:
   - modal open/close behavior
   - button text
   - focus wrapping
   - DOM class names
   - menu visibility
   - “user can click X then Y”

done: Removed UI assertions from Python service/server tests.

The cleanup removed Python assertions that inspected shell HTML, CSS selectors, visible navigation, modal/open choreography, and button/menu-level page details. Remaining tests focus on service configuration, route config JSON, request/response contracts, static path policy, generated payloads, and public/private runtime boundaries.

Changed areas:
- Deleted `docs-viewer/tests/python/test_docs_viewer_management_runtime_boundaries.py`, which was almost entirely management-shell UI assertions.
- Trimmed `docs-viewer/tests/python/test_docs_viewer_public_runtime_boundaries.py`, `test_docs_viewer_service_config.py`, and `test_docs_viewer_static_assets.py` back to data/config/static boundary checks.
- Trimmed `studio/tests/python/test_studio_app_runtime_config.py` and `admin-app/tests/python/test_admin_app_server.py` so they no longer assert rendered shell navigation, CSS ownership, or visible page content.
- Removed generated public route HTML shell assertions from `docs-viewer/tests/python/test_docs_scope_lifecycle.py`; the test still asserts the scope config, public route config, manifest records, and generated payload files.

4. Shrink smoke tests hard
   Current smoke layer is large: about 18k lines. Biggest UI smoke offenders include:
   - `studio/tests/smoke/catalogue_work_modal.py` 776 lines
   - `docs-viewer/tests/smoke/docs_viewer_management_modal.py` 709 lines
   - `analytics-app/tests/smoke/data_sharing_review.py` 708 lines
   - `docs-viewer/tests/smoke/docs_viewer_management_workflows.py` 674 lines
   - `analytics-app/tests/smoke/data_sharing_prepare.py` 612 lines

   Keep only:
   - route boots
   - essential server reachability
   - public/private boundary checks
   - one minimal “can submit to endpoint” path where no lower-level test can cover wiring

   Delete or retire modal-shell/focus/button-choreography tests.

done: Shrunk the smoke layer by removing the clearest UI-choreography scripts and runner entries.

Deleted smoke scripts:
- `studio/tests/smoke/catalogue_work_modal.py`
- `studio/tests/smoke/catalogue_series_modal.py`
- `docs-viewer/tests/smoke/docs_viewer_management_modal.py`
- `docs-viewer/tests/smoke/docs_viewer_management_import_modal.py`
- `docs-viewer/tests/smoke/docs_viewer_management_scope_lifecycle_modal.py`
- `docs-viewer/tests/smoke/docs_viewer_management_ui.py`
- `docs-viewer/tests/smoke/docs_viewer_management_import_ui.py`
- `docs-viewer/tests/smoke/docs_viewer_management_move_ui.py`
- `docs-viewer/tests/smoke/docs_viewer_management_scope_ui.py`
- `docs-viewer/tests/smoke/docs_viewer_management_workflows.py`
- `analytics-app/tests/smoke/data_sharing_prepare.py`
- `analytics-app/tests/smoke/data_sharing_review.py`
- `analytics-app/tests/smoke/tag_registry_modal.py`
- `analytics-app/tests/smoke/tag_aliases_modal.py`
- `analytics-app/tests/smoke/series_tags_modal.py`
- `analytics-app/tests/smoke/series_tag_editor_modal.py`

`analytics-app/tests/smoke/tag_route_shell_modules.py` was trimmed so the retained profile no longer runs embedded tag registry or tag aliases modal-workflow assertions. `admin-app/commands/run_checks.py` no longer lists or runs the retired modal and mocked browser-workflow smokes.

The smoke tree dropped from 18,163 lines to 11,235 lines. Remaining large smoke files are mostly route, API, public/private boundary, or JavaScript module contract checks; the next cleanup should move any retained workflow-module assertions that still prove browser behavior rather than contracts into direct API or lower-level module tests.

5. Move browser workflow coverage down to server/API tests
   For workflows like Docs Viewer settings, import, publish, catalogue save, tag edits:
   - test the endpoint directly
   - assert source/config/output changes
   - assert failure responses
   - do not drive the UI to prove the same thing

done: Retired duplicate browser workflow-module smokes where Python/API coverage already owns the durable contract.

Deleted smoke scripts:
- `docs-viewer/tests/smoke/docs_html_import_modules.py`
- `docs-viewer/tests/smoke/docs_viewer_management_action_workflow_modules.py`
- `analytics-app/tests/smoke/data_sharing_prepare_modules.py`
- `analytics-app/tests/smoke/tag_registry_modules.py`
- `studio/tests/smoke/catalogue_editor_action_workflow_modules.py`
- `studio/tests/smoke/bulk_add_work_workflow_modules.py`
- `docs-viewer/tests/smoke/docs_viewer_management_modal_support.py`

`admin-app/commands/run_checks.py` no longer compiles or runs those browser workflow scripts. The retained coverage is now direct Python/API coverage for Docs import, Docs management mutations, Analytics Data Sharing prepare, Analytics tag registry/mutation behavior, and Studio catalogue write routes. The obsolete Docs Viewer modal support helper was deleted after replacing its remaining generic helper imports locally. The smoke tree dropped from 11,235 lines after step 4 to 8,698 lines after step 5.

6. Centralize fixtures
   A lot of maintenance cost comes from each test building its own miniature repo/app world. Extract shared fixture builders per domain:
   - `docs-viewer/tests/fixtures/repo_factory.py`
   - `studio/tests/fixtures/catalogue_factory.py`
   - `analytics-app/tests/fixtures/tag_factory.py`
   - `admin-app/tests/fixtures/admin_factory.py`

   Keep them data-oriented, not UI-oriented.

done: Added the first shared, data-oriented fixture factories and routed representative tests through them.

Added fixture modules:
- `docs-viewer/tests/fixtures/repo_factory.py`
- `studio/tests/fixtures/catalogue_factory.py`
- `analytics-app/tests/fixtures/tag_factory.py`
- `admin-app/tests/fixtures/admin_factory.py`

The app test `conftest.py` files now add each app's `tests/fixtures/` directory to `sys.path`, and `admin-app/tests/conftest.py` was added for the same fixture-import convention. The first migration centralized repeated JSON/file helpers, Analytics tags Data Sharing repo setup, Admin fake repo setup, Studio catalogue JSON helpers, and Docs Management front-matter document writing.

Follow-up Docs Viewer fixture consolidation moved common Docs Viewer text/JSON, site-tools, scope-config, library-doc, staged-file, documents Data Sharing registry/profile, and Docs import repo setup into `docs-viewer/tests/fixtures/repo_factory.py`. The Docs import, Docs builder, Docs Viewer service, and Docs Management support modules now delegate their shared data setup there while keeping service-specific handlers local to the support modules.

Follow-up Analytics fixture consolidation added `analytics-app/tests/fixtures/data_sharing_factory.py` for documents Data Sharing registry payloads, scope/source-doc setup, prepare profiles, and temporary registry repos. The Analytics Data Sharing API, adapter registry, and service gateway tests now use those factories instead of hand-writing miniature registry and repo worlds inline.

Follow-up Analytics tag fixture consolidation moved tag mutation registry, alias, assignment, and row payload helpers into `analytics-app/tests/fixtures/tag_factory.py`. The alias and promotion mutation tests now import those helpers instead of maintaining local copies.

7. Add a review gate
   During future changes, ask:
   - Can this be tested as pure function/service behavior?
   - Can this be tested by direct HTTP request?
   - Is a browser required to verify a contract, or only to mimic a user?
   - Will this test fail because copy/layout/focus changed?

   If the answer is “it mimics a user,” skip it unless the request explicitly asks for browser acceptance coverage.

done: Added the review gate to the testing policy.

The gate now appears in:
- `docs-viewer/source/studio/testing.md`
- `docs-viewer/source/studio/testing-pytest.md`
- `docs-viewer/source/studio/smoke-testing.md`
- `docs-viewer/source/studio/development-checklist.md`

`admin-app/commands/run_checks.py` smoke command descriptions were tightened so route/browser smokes are described as boundary checks rather than broad UI workflow coverage.
