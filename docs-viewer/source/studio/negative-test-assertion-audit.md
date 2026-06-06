---
doc_id: negative-test-assertion-audit
title: Negative Test Assertion Audit
added_date: 2026-06-06
last_updated: 2026-06-06
summary: Audit and cleanup plan for tests that assert retired behavior is absent instead of asserting current contracts.
parent_id: audit
viewable: true
---
# Negative Test Assertion Audit

Status: active

Purpose:

- find tests that permanently assert retired behavior does not happen
- remove or rewrite those tests so permanent coverage asserts current contracts
- keep negative tests only where they protect an active boundary

Policy:

- keep negative assertions for active security, permissions, validation, unsafe-path rejection, rollback/no-write, privacy, and static-file allowlist boundaries
- remove tests whose only purpose is proving old behavior, retired files, removed fields, obsolete flags, or legacy calls are absent
- rewrite broad forbidden-key tests into positive shape tests when the current contract can be stated exactly
- use temporary negative tests during migration only; remove them before closeout unless they enforce a current architecture contract

Inventory command:

```bash
rg -n "assert not |not in |is False|does not|must not|should not|retired|obsolete|legacy|removed|forbidden|no longer|not .*exists\\(|not any\\(|not .*requested|should fail|expected .*fail|rejects_" docs-viewer/tests studio/tests -g '*.py' -g '*.js' -g '*.ts'
```

Classification values:

| Value | Meaning |
| --- | --- |
| `keep` | Negative assertion protects an active boundary such as security, validation, permissions, rollback, privacy, or allowlists. |
| `remove` | Assertion only memorializes retired behavior or an obsolete file, field, flag, or call. |
| `rewrite` | Test is useful, but should assert the current positive contract or exact payload shape instead. |
| `review` | Needs owner context before editing. |

Current completed cleanup:

| Area | Files | Action | Status |
| --- | --- | --- | --- |
| Docs Viewer generated docs flat `index.json` retirement | `test_build_docs_python.py`, `test_build_search_python.py`, `test_docs_generated_reads.py`, `test_docs_management_service.py`, `public_docs_viewer_readonly.py`, `docs_viewer_service_manage.py` | Removed retired-file, retired-endpoint, old-key, and obsolete-flag negative assertions; kept positive `index-tree.json`, `recently-added.json`, by-id, search, and references coverage. | done |
| Docs search `--source-index` compatibility rejection | `docs-viewer/build/build_search.py`, `test_build_search_python.py` | Removed the hidden obsolete option and its negative test. | done |

Pending audit buckets:

| Area | Example files | Likely action | Notes |
| --- | --- | --- | --- |
| Data Sharing generated-docs source guard fixtures | `docs-viewer/tests/python/test_docs_data_sharing_source_metadata.py` | review/rewrite | Contains guard strings for generated docs indexes and fixtures that write retired docs index paths. Confirm whether the current positive source-metadata contract is enough. |
| Docs export/import public flat index fixtures | `docs-viewer/tests/python/test_docs_export.py`, `docs-viewer/tests/python/test_docs_import.py` | review/rewrite | Fixtures still create `assets/data/docs/scopes/library/index.json`. Check whether these are stale setup leftovers or still exercise source-metadata migration behavior. |
| Retired field cleanup tests | `docs-viewer/tests/python/test_docs_import_service.py`, `docs-viewer/tests/python/test_docs_source_model.py`, `studio/tests/python/test_catalogue_retired_notes_field.py` | review | Some may be temporary migration checks for `sort_order` or old catalogue fields. Keep only if they protect an active write contract. |
| Static path and service allowlist negatives | `studio/tests/python/test_studio_app_server.py`, `docs-viewer/tests/python/test_docs_viewer_service.py`, route tests | keep/rewrite | Many negative assertions are active security or static-serving boundaries. Prefer grouped allowlist shape tests where practical, but do not remove boundary coverage. |
| Generated-output forbidden-key fixtures | `studio/tests/python/test_generated_output_contract_fixtures.py` | keep/rewrite | Some forbidden keys are public data minimization contracts. Prefer exact allowed-key assertions when payload shape is stable. |
| Local Studio retired route smokes | `studio/tests/smoke/local_studio_navigation_adapter.py`, `studio/tests/smoke/local_studio_app_docs_viewer.py` | review | Determine whether these are active navigation/security boundaries or old migration checks that can be replaced by current route inventory assertions. |

Batch process:

1. Pick one pending bucket.
2. Read the owning source, service, and current docs before editing tests.
3. Classify each negative assertion as `keep`, `remove`, `rewrite`, or `review`.
4. Remove temporary retired-behavior checks.
5. Rewrite useful checks as positive current-contract assertions.
6. Run the smallest focused test set for that bucket.
7. Update this audit table with status and any remaining risk.
