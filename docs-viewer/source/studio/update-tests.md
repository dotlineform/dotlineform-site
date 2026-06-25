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

   Delete or retire modal-shell/focus/button-choreography tests unless they cover a reusable modal primitive with a stable contract.

5. Move browser workflow coverage down to server/API tests
   For workflows like Docs Viewer settings, import, publish, catalogue save, tag edits:
   - test the endpoint directly
   - assert source/config/output changes
   - assert failure responses
   - do not drive the UI to prove the same thing

6. Centralize fixtures
   A lot of maintenance cost comes from each test building its own miniature repo/app world. Extract shared fixture builders per domain:
   - `docs-viewer/tests/fixtures/repo_factory.py`
   - `studio/tests/fixtures/catalogue_factory.py`
   - `analytics-app/tests/fixtures/tag_factory.py`
   - `admin-app/tests/fixtures/admin_factory.py`

   Keep them data-oriented, not UI-oriented.

7. Add a review gate
   During future changes, ask:
   - Can this be tested as pure function/service behavior?
   - Can this be tested by direct HTTP request?
   - Is a browser required to verify a contract, or only to mimic a user?
   - Will this test fail because copy/layout/focus changed?

   If the answer is “it mimics a user,” skip it unless the request explicitly asks for browser acceptance coverage.