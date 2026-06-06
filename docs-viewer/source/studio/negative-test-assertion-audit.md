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

Status: complete

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
| Catalogue search obsolete `targeted` config rejection | `studio/services/catalogue/search/build_search.py`, `studio/tests/python/test_catalogue_search_builder_python.py` | Removed stale v1 config-field rejection code and its fixture mode/test; current v2 policy and operation validation remains covered. | done |
| Deprecated tag route and Data Sharing operation wording | `studio/tests/python/test_tag_routes.py`, `studio/tests/python/test_data_sharing_adapters.py` | Removed redundant `/build-docs` negative route assertion covered by exact current route-set equality; renamed legacy-operation fixture to an active unknown-operation allowlist check. | done |
| Local Studio legacy service-port smokes | `studio/tests/smoke/local_studio_app_activity_route.py`, `studio/tests/smoke/local_studio_app_bulk_add_work_route.py`, `studio/tests/smoke/local_studio_app_catalogue_editor_routes.py`, `studio/tests/smoke/local_studio_app_catalogue_status_route.py`, `studio/tests/smoke/local_studio_app_project_state_route.py`, `studio/tests/smoke/local_studio_app_audits_route.py` | Removed old-port request traps for retired local services; kept current runtime-config, local API, shell bootstrap, and route ready-state assertions. | done |
| Catalogue detail media-section compatibility wording | `studio/services/catalogue/catalogue_source.py`, `studio/services/catalogue/validate_catalogue_source.py`, `studio/tests/python/test_catalogue_source_media_section_schema.py` | Kept active compatibility-read and target-schema rejection behavior for detail `project_subfolder`, but renamed stale legacy wording to compatibility/current-schema language. | done |
| Studio route-registry validation wording | `studio/app/server/studio/studio_app_config.py`, `studio/tests/python/test_studio_app_server.py` | Kept active route-registry fail-closed checks, but renamed obsolete/legacy fixture and constant names to unserved/compatibility wording. | done |
| Catalogue lookup stale-folder cleanup | `studio/services/catalogue/catalogue_lookup.py`, `studio/tests/python/test_catalogue_lookup_refresh.py` | Removed cleanup code for old `work_files`/`work_links` lookup folders; current lookup writer only manages active root, works, work_details, and series payloads. | done |
| Neutral stale-term fixture literals | `docs-viewer/tests/python/test_docs_source_model.py`, `studio/tests/python/test_catalogue_generation_records.py` | Renamed harmless `legacy-*` fixture literals to neutral IDs so audit scans no longer surface them as possible retired-behavior assertions. | done |
| Series ID slug compatibility wording | `studio/services/catalogue/series_ids.py`, `studio/tests/python/test_catalogue_generation_records.py` | Kept active slug-series-id parsing, but renamed internal legacy-slug wording to slug-id wording. | done |
| Catalogue build operator messages | `studio/services/catalogue/generate_work_pages.py` | Reworded direct-entrypoint and Studio series-page skip messages from deprecated/retired language to unsupported/disabled language. | done |

Reviewed audit buckets:

| Area | Example files | Likely action | Notes |
| --- | --- | --- | --- |
| Data Sharing generated-docs source guard fixtures | `docs-viewer/tests/python/test_docs_data_sharing_source_metadata.py` | rewrite | Removed generated-docs artifact fixture writes and broad forbidden-string guards; kept positive source-metadata owner and package-record assertions. Status: done. |
| Docs export/import public flat index fixtures | `docs-viewer/tests/python/test_docs_export.py`, `docs-viewer/tests/python/test_docs_import.py` | rewrite | Removed stale generated docs/search artifact fixture writes and renamed tests around positive source-metadata export/import behavior. Status: done. |
| Retired field cleanup tests | `docs-viewer/tests/python/test_docs_import_service.py`, `docs-viewer/tests/python/test_docs_source_model.py`, `studio/tests/python/test_catalogue_retired_notes_field.py` | rewrite/remove | Deleted retired catalogue `notes` field test. Rewrote docs source/import `sort_order` checks as exact current front-matter shape assertions because source-write normalization is an active write contract. Status: done. |
| Static path and service allowlist negatives | `studio/tests/python/test_studio_app_server.py`, `docs-viewer/tests/python/test_docs_viewer_service.py`, route tests | keep/rewrite | Removed retired thumbnail-quality and legacy-handler assertions from Studio server tests, and rewrote static examples around current allowed prefixes and generic denied boundaries. Kept active security/static-serving deny checks. Status: done for the first pass. |
| Generated-output forbidden-key fixtures | `studio/tests/python/test_generated_output_contract_fixtures.py` | rewrite | Removed permanent forbidden-key lists from the contract fixture and relied on allowed-key payload assertions for current data-minimization contracts. Status: done. |
| Local Studio retired route smokes | `studio/tests/smoke/local_studio_navigation_adapter.py`, `studio/tests/smoke/local_studio_app_docs_viewer.py` | rewrite | Removed retired thumbnail-quality route/data probes and obsolete Docs header/generated-index checks; kept current Studio runtime/navigation assertions and Docs Viewer boundary checks. Status: done. |

Batch process:

1. Pick one pending bucket.
2. Read the owning source, service, and current docs before editing tests.
3. Classify each negative assertion as `keep`, `remove`, `rewrite`, or `review`.
4. Remove temporary retired-behavior checks.
5. Rewrite useful checks as positive current-contract assertions.
6. Run the smallest focused test set for that bucket.
7. Update this audit table with status and any remaining risk.
