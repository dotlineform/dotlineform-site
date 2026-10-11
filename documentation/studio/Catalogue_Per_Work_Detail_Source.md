---
draft: false
doc_id: d-20260622-160612-b986f3
title: Catalogue Per-Work Detail Source
added_date: "2026-06-22 16:06:12"
last_updated: "2026-10-11 00:00:00"
parent_id: d-20260519-000000-a0da45

---
# Catalogue Per-Work Detail Source

Retired by the Gallery conversion on 2026-09-23. Converted images are independent Works; Gallery identity and membership belong to the sources described in [Catalogue Source Model](Catalogue_Source_Model.md).

## Historical Migration Input

The converter's old input was one aggregate at `studio/data/canonical/catalogue/work_details/<work_id>.json`. Each aggregate contained Work-owned sections with source-media subfolders and nested Detail records. The conversion tooling, archived `retired/work_details.flat.v2.json` and remaining source-schema helpers are removed. Git history owns historical recovery.

## Studio Retirement

The Work editor no longer has the Detail browser, section-edit modal, section actions, Detail-only multi-image picker wrapper or Detail preview/link helpers. The shared file picker, record lists, modal frame, Work media picker and Work/Series editing remain.

The disconnected section-creation/save service, Detail lookup target, Detail bulk-edit/delete branches and private lookup projections are removed. The focused Work response is `studio_catalogue_work_record_v3` and contains no Detail sections. Ordinary Studio write authority excludes retired Detail storage.

`CatalogueSourceRecords` now contains only `works` and `series`. Detail field declarations, identity normalization, sorting, parsing, serialization, validation and transaction expansion are removed. Work/Series mutation and Refresh callers use the two-map model. The unused generated Detail record helper and Detail field-registry families are removed. Ordinary source writes no longer expand or prune a retired Detail directory; current JSON/media replacement retains its existing transaction owner.

## Remaining Boundaries

Disposable authored Detail references remain unchanged, without aliases to converted Works. Frozen public archives and their media are outside this canonical-source cleanup. Gallery editing and ordinary Work creation use their current Work/Gallery owners.

Historical tests have not been changed. `studio/tests/python/test_catalogue_detail_section_service.py` imports the deleted section service, and `studio/tests/python/test_catalogue_lookup_dependencies.py` imports retired Detail lookup helpers. `studio/tests/fixtures/catalogue_factory.py` and `studio/tests/python/test_catalogue_source_mutation.py` still construct the removed Detail maps; `studio/tests/python/test_catalogue_generation_records.py` still calls the deleted Detail projection helper. Other historical Catalogue and Docs tests also retain Detail scenarios. These are unreviewed retirement residue, not current acceptance evidence, and require separately agreed test maintenance. No compatibility fields or helpers are retained for them.

## Retained Transaction Check

The existing selection is `studio/tests/python/test_catalogue_transactions.py -k execute_source_json_write`. It protects the current source-write wrapper after removing Detail expansion. No tests, fixtures or profile memberships were changed for this selection.

| Exact selector | Scenario and asserted result |
| --- | --- |
| `test_execute_source_json_write_dry_run_suppresses_write` | An existing temporary Work JSON is supplied with replacement data in dry-run mode; its content remains unchanged and the returned written-path list is empty. |
| `test_execute_source_json_write_reports_written_paths` | An existing temporary Work JSON receives replacement data; its content changes and its resolved path is returned. |
| `test_execute_source_json_write_rolls_back_replaced_files_on_failure` | Two existing temporary JSON files receive replacement data; an injected failure on the second `os.replace` restores both original JSON values, propagates the error and leaves no temporary files. |
| `test_execute_source_json_write_rejects_empty_payload_map` | An empty input mapping raises the source-write validation error. |

Each case uses `TemporaryDirectory`; the rollback case temporarily replaces `os.replace` and restores it in `finally`. The real JSON validation and transaction code execute against temporary local files. The shared Studio conftest configures import paths. There is no network, local server, real canonical-data write, external workspace, media producer or browser. Temporary files are cleaned up by the tests. Setup and execution are expected to take seconds with low CPU cost; repeat only after relevant transaction changes or a failure. This selection does not prove media replacement, live Save, Refresh, generation or publication behavior.

Run from the repository root using the configured Python environment:

```bash
python3 -m pytest studio/tests/python/test_catalogue_transactions.py -q -k execute_source_json_write
```
