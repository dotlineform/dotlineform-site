---
doc_id: site-request-admin-app-structure-batch-6
title: Admin App Structure Batch 6
added_date: 2026-06-06
last_updated: 2026-06-06
ui_status: done
parent_id: site-request-admin-app-structure-tasks
viewable: true
---
# Durable Docs, Verification, and Closeout

This is the delivery specification for Batch 6 in [Admin App Structure Tasks](/docs/?scope=studio&doc=site-request-admin-app-structure-tasks).

### Batch 6: Durable Docs, Verification, and Closeout

Summary: update durable docs, run final focused verification, record moved ownership, and close the request.

| ID | status | action |
| --- | --- | --- |
| 6.1 | done | Update durable ownership docs for Admin, Studio, UI Catalogue, testing, local setup, route ownership, scripts, output paths, and fixture ownership. |
| 6.2 | done | Update request and task docs with final statuses, moved paths, verification results, and any remaining follow-on work. |
| 6.3 | done | Run focused final verification for Admin home, Admin routes, Admin runner, Admin UI Catalogue, retained Studio routes, and moved fixtures/checks. |
| 6.4 | done | Record final check summaries and run-log locations under `var/admin/test-runs/` when runner verification writes logs. |
| 6.5 | done | Close the parent request when durable docs contain the current ownership contract and the planned migration is complete. |

## Steer for these tasks

- Durable docs should describe the final current-state boundary rather than the migration history.
- Final tests should assert that current Admin and retained Studio behavior works.
- Verification should include runner output paths and route behavior owned by Admin.

## Deliverables

- Updated durable docs.
- Final request and tracker status updates.
- Final verification summary.
- Closeout notes for moved source, routes, scripts, tests, and fixtures.

## Implementation and policy guidance

- Keep docs source updates in `docs-viewer/source/studio/`.
- Regenerate Docs Viewer payloads only if the implementation task explicitly includes that follow-through.
- Record remaining risks or follow-on work in the request docs before marking them done.

## Proposed verification set

- Admin server/config pytest
- Admin route smokes for moved route families
- Admin UI Catalogue smoke
- Admin runner/profile pytest and representative small profile run
- focused retained Studio route smokes
- syntax checks for changed Python and JavaScript
- docs/source review for updated route and command references

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile ...` passed for the Admin runner/server/check/smoke files plus retained Studio server files.
- `node --check ...` passed for Admin route modules, Admin UI Catalogue modules, and retained Studio shell modules.
- `$HOME/miniconda3/bin/python3 -m json.tool admin-app/app/frontend/config/admin-config.json` passed.
- `$HOME/miniconda3/bin/python3 -m pytest -q admin-app/tests/python/test_admin_app_server.py admin-app/tests/python/test_admin_operations.py admin-app/tests/python/test_admin_runner_contract.py admin-app/tests/python/test_admin_ui_catalogue.py admin-app/tests/python/test_activity_contract.py admin-app/tests/python/test_risk_evidence_pack.py studio/tests/python/test_studio_app_server.py studio/tests/python/test_studio_activity_feed.py docs-viewer/tests/python/test_docs_viewer_v2_custom_token_fixtures.py docs-viewer/tests/python/test_generated_output_contract_fixtures.py` passed with 69 tests.
- `$HOME/miniconda3/bin/python3 -m pytest -q studio/tests/python/test_studio_app_server.py` passed with 20 tests after the narrow Studio Works static-serving fix.
- `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile quick --run-id admin-batch-6-quick-final` passed; summary: `var/admin/test-runs/admin-batch-6-quick-final/summary.md`.
- `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile admin-smoke --run-id admin-batch-6-admin-smoke` passed with elevated localhost/browser permissions; summary: `var/admin/test-runs/admin-batch-6-admin-smoke/summary.md`.
- `$HOME/miniconda3/bin/python3 admin-app/commands/run_checks.py --profile ui-catalogue-smoke --run-id admin-batch-6-ui-catalogue-smoke` passed with elevated localhost/browser permissions; summary: `var/admin/test-runs/admin-batch-6-ui-catalogue-smoke/summary.md`.
- Retained Studio route smokes passed with elevated localhost/browser permissions for `/studio/project-state/`, `/studio/bulk-add-work/`, `/studio/catalogue-field-registry/`, `/studio/catalogue-status/`, `/studio/studio-works/`, and the catalogue editor route family.
- Source/config review scan confirmed remaining active references to retired `/studio/audits`, `/studio/risk`, `/studio/activity`, `/studio/ui-catalogue`, `ui-catalogue-app`, old runner paths, and old output paths are historical request notes, intentional retired-route notes, or negative tests.

## follow-on tasks

- none.

## task close

- Durable source docs now describe the current Admin boundary, retained Studio catalogue boundary, Admin-hosted UI Catalogue ownership, Admin runner/check ownership, test and fixture ownership, local setup, and `bin/local-all` sibling-service behavior.
- `admin-app/commands/run_checks.py` syntax coverage now points at `admin-app/app/server/admin_app/audit_runner.py`.
- Local Studio now narrowly serves `studio/data/generated/activity/work-storage-index.json`, which is required by `/studio/studio-works/`; the broader generated activity directory remains unserved.
- Docs Viewer payloads were not regenerated.
