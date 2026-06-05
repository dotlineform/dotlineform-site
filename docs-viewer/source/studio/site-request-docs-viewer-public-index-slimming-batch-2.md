---
doc_id: site-request-docs-viewer-public-index-slimming-batch-2
title: Docs Viewer Public Index Slimming Batch 2
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: done
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 2: Builder Outputs

This is the delivery specification for [Batch 2 in Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 2: Builder Outputs

Summary: Add public and manage tree/recently-added generation, wire scope lifecycle generated outputs, and move search build inputs away from retired public docs indexes.

| ID | status | action |
| --- | --- | --- |
| 2.1 | done | Add build-time public `index-tree.json` and recently-added payload generation under `assets/data/docs/scopes/<scope>/`, using public-safe compact tree records, current public viewability filtering, and no recently-added-only date fields in tree rows. |
| 2.2 | done | Add build-time manage `index-tree.json` and recently-added payload generation under `docs-viewer/generated/docs/<scope>/`, using the same tree record structure as public scopes while preserving manage visibility/loadability behavior. |
| 2.3 | done | Update scope lifecycle create/delete behavior so `write_generated_outputs` creates required `index-tree.json` and recently-added payloads for new scopes and delete removes only manifest-recorded generated outputs for user-created scopes; existing scopes are backfilled through the normal `build_docs.py --scope <scope> --write` path. |
| 2.4 | done | Update search build inputs so search continues to produce and read its separate search payload without depending on retired public docs `index.json`. |

## Steer for these tasks

- Use the Batch 1 locked contracts as the source of truth.
- Keep public and manage `index-tree.json` record structures identical even though generation inputs and visibility rules differ.
- Keep recently-added as a separate compact payload limited to the configured recently-added count.
- Update scope lifecycle in the same implementation slice that introduces generated tree outputs.
- Move search build inputs at the builder-source level; do not widen public runtime search behavior.

## Deliverables

- Public `assets/data/docs/scopes/<scope>/index-tree.json` generation.
- Public recently-added payload generation.
- Manage `docs-viewer/generated/docs/<scope>/index-tree.json` generation.
- Manage recently-added payload generation.
- Scope lifecycle create/delete manifest handling for new generated outputs.
- Search build input path no longer depends on retired public docs `index.json`.
- Focused generated-output contract tests or fixtures for the new payloads.

## Implementation and policy guidance

- Public tree rows should exclude `summary`, `last_updated`, `source_path`, `viewer_url`, `content_text_length`, and other default or derivable fields.
- Do not add `added_date` or `last_updated` to tree rows only to support recently-added.
- Manage tree rows may preserve manage visibility/loadability behavior but should not add richer row fields unless a manage interaction needs them before selected by-id is loaded.
- Existing scopes should be backfilled through the normal generated-docs write path, not a custom migration path.

## Batch 1 Handoff

Batch 1 locked the generated-data contracts and dependency classification.

- Generate `index-tree.json` beside each scope's by-id root: public under `assets/data/docs/scopes/<scope>/index-tree.json`, manage/local under `docs-viewer/generated/docs/<scope>/index-tree.json`.
- Use schema `docs_index_tree_v1` with top-level `generated_at`, `viewer_options`, and `docs`.
- Keep public and manage tree row structure identical. Allowed tree row fields are `doc_id`, `title`, `content_url`, optional non-empty `parent_id`, optional `viewable: false`, and optional non-empty `ui_status`.
- Exclude `summary`, `added_date`, `last_updated`, `source_path`, `viewer_url`, `content_text_length`, report metadata, source/edit metadata, management action metadata, and default/derivable values from tree rows.
- Generate `recently-added.json` beside `index-tree.json` for each scope with schema `docs_recently_added_v1`, top-level `generated_at`, `limit`, and `docs`.
- Recently-added rows allow `doc_id`, `title`, `content_url`, `added_date`, optional `parent_id`, and optional `parent_title`; limit rows at build time by the configured recently-added limit.
- Move route config from generic flat `docs_paths.index_url` to explicit `docs_paths.index_tree_url`, `docs_paths.recently_added_url`, and existing `docs_paths.search_index_url`.
- Do not add fallback reads from `index-tree.json` to `index.json`.
- Search runtime remains on `search_index_url`; search builder input must move away from retired public flat `index.json`.
- Info-panel metadata must hydrate from selected by-id payloads in Batch 4, not from tree rows.
- Data Sharing export/import needs rich metadata and is classified under [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index), not Batch 2 public payload scope.

## Proposed verification set

- Python syntax/import checks for changed builder and scope lifecycle modules.
- Focused generated-output contract tests for public tree, manage tree, and recently-added payloads.
- Focused search build tests proving search output is still produced without reading retired public docs `index.json`.
- Dry-run or write run of `docs-viewer/build/build_docs.py --scope studio --write` only when the touched builder path warrants it.

## completed verification

- 2026-06-05: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/build/build_docs.py docs-viewer/build/build_search.py docs-viewer/services/docs_scope_manifest.py docs-viewer/tests/python/test_build_docs_python.py docs-viewer/tests/python/test_build_search_python.py studio/tests/python/test_generated_output_contract_fixtures.py docs-viewer/tests/python/test_docs_management_service.py` passed.
- 2026-06-05: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_build_docs_python.py docs-viewer/tests/python/test_build_search_python.py studio/tests/python/test_generated_output_contract_fixtures.py docs-viewer/tests/python/test_docs_management_service.py` passed, 56 tests.
- 2026-06-05: `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --scope studio --diagnostics` dry run passed; after the running docs watcher regenerated source-doc changes, the final dry run reported no pending docs, tree, recently-added, search, or reference writes.
- 2026-06-05: `$HOME/miniconda3/bin/python3 docs-viewer/build/build_search.py --scope studio` dry run passed; search output was unchanged.

## follow-on tasks

- Batch 3 should switch route config/data loading to `index-tree.json` and `recently-added.json` with visible failures for missing payloads and no fallback to `index.json`.
- Batch 5 still owns public flat `index.json` retirement after tree, selected-document, search, and recently-added runtime dependencies have moved.

## task close

- Batch 2 is complete.
- Codex did not manually run `build_docs.py --write`; the running docs watcher regenerated the affected Studio generated payloads after source docs changed, including `index-tree.json` and `recently-added.json`.
