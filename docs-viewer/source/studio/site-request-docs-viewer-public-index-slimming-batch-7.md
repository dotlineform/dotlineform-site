---
doc_id: site-request-docs-viewer-public-index-slimming-batch-7
title: Docs Viewer Public Index Slimming Batch 7
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: planned
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 7: Documentation and Closeout

This is the delivery specification for [Batch 7 in Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 7: Documentation and Closeout

Summary: Update durable runtime, data model, search, lifecycle, and testing documentation after the contract is implemented and verified, then close out the tracker and parent request.

| ID | status | action |
| --- | --- | --- |
| 7.1 | planned | Update the runtime boundary docs after the contract is durable: keep [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) as policy, update [Docs Viewer Runtime Surfaces](/docs/?scope=studio&doc=docs-viewer-runtime-surfaces) for route/config/CSS/scope lifecycle surfaces, update [Docs Viewer Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts) for tree/recent/by-id/search payload contracts, and update [Docs Viewer Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) for final runtime owner responsibilities. |
| 7.2 | planned | Update [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) only for changed browser module ownership, risk notes, or row-level evidence; do not duplicate the runtime surface or generated-data contract tables there. |
| 7.3 | planned | Update public scope data model docs, including [Data Models Library](/docs/?scope=studio&doc=data-models-library) and [Data Models Analysis](/docs/?scope=studio&doc=data-models-analysis), so they describe public `index-tree.json`, recently-added payloads, by-id reader metadata, search payloads, and retired public flat `index.json` route ownership. |
| 7.4 | planned | Update search, scope lifecycle, and testing docs for the implemented contract: search build inputs no longer depend on retired public docs `index.json`, scope lifecycle creates/deletes required tree/recent outputs through manifest-recorded generated files only, and smoke/contract tests assert new payload loads plus absence of public `index.json` requests. |
| 7.5 | planned | Cleanup confirmation: confirm removed paths and artifacts are not retained through import aliases, copied files, static mount shims, route-config fallback logic, generated-read fallback logic, or dual-read public `index.json` paths. |
| 7.6 | planned | Verification record: record final verification commands, pass/fail results, generated payload status, and any manual checks that remain. |
| 7.7 | planned | Close out this batch, the task tracker, and the parent request with final statuses, changed-path summary, durable decisions, remaining risks, and any follow-on work. |

## Steer for these tasks

- Durable docs should describe the implemented contract, not the migration path.
- Keep source docs as the edited source of truth; generated Docs Viewer payloads are only rebuilt when explicitly run or by the watcher.
- Closeout must confirm no compatibility layer remains for retired public flat-index route loading.
- If any follow-on work remains, record it with ownership and removal criteria instead of leaving it implicit.

## Deliverables

- Updated runtime boundary policy doc.
- Updated runtime surface map.
- Updated generated-data contract doc.
- Updated runtime module ownership doc.
- Updated JavaScript inventory, only where module ownership or risk evidence changed.
- Updated Library and Analysis data model docs.
- Updated search, scope lifecycle, and testing docs.
- Cleanup confirmation for retired public flat-index route dependencies.
- Final verification log.
- Parent request and tracker status updates.

## Implementation and policy guidance

- Move durable decisions and current contracts out of temporary request/task docs into permanent owning docs.
- Keep [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) concise; put surface matrices in [Docs Viewer Runtime Surfaces](/docs/?scope=studio&doc=docs-viewer-runtime-surfaces), payload contracts in [Docs Viewer Generated Data Contracts](/docs/?scope=studio&doc=docs-viewer-generated-data-contracts), and grouped owner maps in [Docs Viewer Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership).
- Do not duplicate row-level JavaScript inventory detail in runtime boundary docs; link to [Docs Viewer JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) when file-level risk evidence is needed.
- Do not preserve old public `index.json` runtime behavior as a compatibility path.
- Record generated payload status explicitly.
- Keep closeout concise but complete enough for a future maintainer to understand changed paths, validation, and remaining risk.

## Proposed verification set

- `git diff --check`.
- Changed-doc link/path checks where practical.
- Focused stale-reference scans for retired `index.json` runtime loading and rich public flat-index fields.
- Focused scans that public runtime docs do not describe public flat `index.json` as an active route payload after retirement.
- Final verification commands recorded from Batch 6.
- Optional final Docs Viewer smoke profile if docs closeout touches executable smoke docs or scripts.

## completed verification

- Not started.

## follow-on tasks

- To be completed during the task.

## task close

- Set this document, the tracker, and the parent request to `done` when implementation is complete and durable docs are updated.
- Record changed files, verification results, generated payload status, and remaining risks before closeout.
