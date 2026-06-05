---
doc_id: site-request-docs-viewer-public-index-slimming-batch-8
title: Docs Viewer Public Index Slimming Batch 8
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: done
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 8: Nested Tree Payload Correction

This is the correction batch for [Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 8: Nested Tree Payload Correction

Summary: Correct `index-tree.json` so build time owns parent/child tree construction as specified in the request's Proposed Direction, while preserving the shared public/manage loading and document-selection behavior.

The prior implementation completed the hard public-index slimming work, including compact payload fields, recently-added payloads, selected by-id metadata hydration, public flat-index retirement, and public/manage smoke coverage.
It did not complete the request's tree-construction requirement because `index-tree.json` is still a flat adjacency-list payload and the runtime still derives the hierarchy from `parent_id` rows.

| ID | status | action |
| --- | --- | --- |
| 8.1 | done | Re-audit current runtime tree consumers before implementation. Confirm whether child nodes need `parent_id` before selected by-id payloads are loaded, including index rendering, active-trail expansion, non-loadable target resolution, manage-only root omission, non-viewable ancestor handling, drag/drop eligibility, context actions, info-panel trail projection, search/recent result navigation, and manage-mode behavior. |
| 8.2 | done | Decide whether Batch 8 remains self-contained. If the audit shows broad shared-core changes, public/manage mode switches, management capability leakage, or a need to redesign route/session ownership, stop and open a fresh request instead of stretching this batch. |
| 8.3 | done | Update the builder so `index-tree.json` contains a nested tree payload with build-time parent/child construction, root and sibling ordering, public viewability filtering, manage visibility/loadability projection, compact public-safe fields, and the same tree node structure for public and manage scopes. |
| 8.4 | done | Update runtime loading so basic tree loading, tree adaptation, hierarchy traversal, document selection, expansion/collapse, active highlighting, non-loadable fallback, and route navigation remain shared public/manage behavior. Manage mode may add capabilities only through manage-loaded modules and manage-local services; do not move management controls, services, drag/drop, context menus, mutation calls, source/edit workflows, or local-service reads into public payloads or shared public adapters. |
| 8.5 | done | Update focused tests and smokes around current behavior: route boot, tree navigation, default/selected document loading, visibility/loadability behavior, recently-added, search result navigation, info-panel hydration, and public absence of flat `index.json` requests. Do not add assertions whose only purpose is to preserve historical flat rows, historical `parent_id` shape, or historical files. |
| 8.6 | done | Update durable docs and closeout notes to describe the final nested `index-tree.json` contract, parent-id decision, shared loading ownership, verification run, generated payload status, and any follow-on ownership if the batch is deferred into a fresh request. |

## Steer for these tasks

- Align with the request's Proposed Direction: public and manage routes load route-appropriate `index-tree.json` payloads; build time owns parent/child tree construction; runtime owns loading, adaptation to renderer needs, expansion/collapse, active highlighting, and routing.
- Preserve the public/manage entrypoint boundary. Basic index loading and document selection should be shared. Manage mode should only add capability through additional manage modules loaded in manage mode.
- Keep the file name `index-tree.json`. The correction is the payload shape and runtime interpretation, not a route/file rename.
- Keep public tree nodes free of management/tooling metadata.
- Keep recently-added on `recently-added.json`, selected-document rendering and info metadata on by-id payloads, and search on the separate search payload.
- Parent IDs on child nodes are undecided. Confirm whether they are needed before by-id hydration; if not, let the nested structure carry the relationship.
- Do not test historical shapes or files. Tests should prove current user-visible and architecture behavior works.
- Do not preserve compatibility aliases, dual-read fallbacks, or old flat-tree shims as an end state.

## Deliverables

- Audit result for whether nested tree nodes need `parent_id` before by-id payload loading.
- Self-contained/fresh-request decision before implementation expands.
- Nested `index-tree.json` builder output for public and manage scopes, if Batch 8 remains self-contained.
- Runtime loader/adapter updates that consume nested tree payloads through shared public/manage behavior.
- Focused behavior tests and route smokes for current behavior, not historical shape preservation.
- Updated generated-data contract and runtime ownership docs.
- Updated tracker/request closeout state.

## Proposed verification set

Run only the checks warranted by implementation scope.
Likely checks if implementation proceeds:

- `$HOME/miniconda3/bin/python3 -m py_compile` for changed builder, service, smoke, and test files.
- Focused pytest for builder output shape, generated-output contract fixtures, generated reads, scope lifecycle generated-output records, and runtime payload projection.
- Focused JavaScript syntax/import checks for changed runtime modules.
- `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke` if runtime loading or smoke expectations change.
- Public `/library/` and `/analysis/` route checks against a fresh temporary Jekyll build if public route behavior changes.
- `git diff --check`.

## completed verification

- 2026-06-05: Runtime consumer audit found child parent relationships are needed before selected by-id hydration, but only in the normalized in-memory runtime model. Tree rendering, active-trail expansion, non-loadable fallback, manage-only omission, non-viewable ancestor checks, drag/drop, context actions, route navigation, and search/recent parent labels can all keep using derived runtime `parent_id` values.
- 2026-06-05: Batch 8 remained self-contained. The change stayed inside the builder, shared tree payload adapter, generated-read helper, focused tests, durable generated-data/runtime docs, and the Studio generated `index-tree.json` payload. No public/manage route/session redesign or management capability movement was needed.
- 2026-06-05: `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/build/build_docs.py docs-viewer/services/docs_generated_reads.py docs-viewer/tests/python/test_build_docs_python.py docs-viewer/tests/python/test_docs_generated_reads.py` passed.
- 2026-06-05: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_build_docs_python.py docs-viewer/tests/python/test_docs_generated_reads.py` passed, 22 tests.
- 2026-06-05: Focused Node module check passed for nested tree normalization, derived runtime parent ids, nested expected-doc retry detection, and rejection of `parent_id` inside `index-tree.json` nodes.
- 2026-06-05: Dry-run generated checks completed for `library`, `analysis`, and `studio`. `library` and `analysis` had no nested tree writes needed; `analysis` retained the existing unresolved semantic reference warning for `work:00638002`.
- 2026-06-05: `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --scope studio --write --diagnostics` passed for the nested tree contract and wrote `docs-viewer/generated/docs/studio/index-tree.json`.
- 2026-06-05: After closeout docs-source edits, Studio generated docs were rebuilt with `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --scope studio --write --diagnostics` so checked-in generated Studio payloads match the closed request state.
- 2026-06-05: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke` passed; summary at `var/test-runs/20260605-210337/summary.md`.

## follow-on tasks

- None for Batch 8. Remaining non-route rich metadata consumers stay under their existing owning requests and should not restore public flat-index route behavior.

## task close

- Batch 8 corrected `index-tree.json` to a nested build-time tree payload.
- Generated tree nodes do not carry `parent_id`; `docs-viewer-tree-payload-adapter.js` derives runtime-only `parent_id` values from nested position so current shared public/manage rendering, navigation, active-trail expansion, non-loadable fallback, and manage interactions continue to use the existing normalized state contract.
- The Studio generated tree payload was rebuilt because the route payload contract changed. Studio generated docs were also rebuilt after closeout source-doc edits so checked-in Studio generated data matches the closed request state. Public Library/Analysis tree payloads were checked and did not require writes because they are root-only under the nested contract.
- This document, the tracker row, and the parent request were set to `done`.
