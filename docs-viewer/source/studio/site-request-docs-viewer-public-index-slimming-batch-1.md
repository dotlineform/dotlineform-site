---
doc_id: site-request-docs-viewer-public-index-slimming-batch-1
title: Docs Viewer Public Index Slimming Batch 1
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: planned
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 1: Discovery and Contract Lock

This is the delivery specification for [Batch 1 in Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 1: Discovery and Contract Lock

Summary: Audit current public flat-index generation and consumption, then define the generated-data contracts before implementation starts.

| ID | status | action |
| --- | --- | --- |
| 1.1 | planned | Audit current public flat-index generation and consumption, including browser/runtime tree construction, info-panel reads, search build inputs, recently-added behavior, scope lifecycle, tests/fixtures, reports, export/import, and Data Sharing references. Classify dependencies as Docs Viewer-owned work for this request or separate tooling ownership such as [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index). |
| 1.2 | planned | Define the generated-data contracts before implementation: shared public/manage `index-tree.json`, small recently-added payload, selected by-id reader metadata for the info panel, route config fields, visible missing-payload behavior, and public flat `index.json` retirement semantics. |

## Steer for these tasks

- Start by locating every current public `index.json` producer and consumer before proposing code edits.
- Separate Docs Viewer-owned dependencies from tooling consumers such as Data Sharing, reports, export/import, and generated-output inspection.
- Lock the payload names and field contracts before builder or runtime changes begin.
- If the audit finds a consumer that still needs rich document metadata, classify it as either selected by-id hydration, search/build input, manage-only data, or separate tooling ownership.

## Deliverables

- Dependency inventory for public flat-index generation and consumption.
- Confirmed contract for public and manage `index-tree.json`.
- Confirmed contract for recently-added payloads.
- Confirmed selected by-id metadata contract for info-panel hydration.
- Confirmed route config fields and missing-payload behavior.
- Confirmed retirement semantics for public flat `index.json`.

## Implementation and policy guidance

- Follow the parent request: no fallback to `index.json` after the route contract moves.
- Do not treat tests or generated fixtures as the implementation contract; update them to match the locked contract.
- Avoid compatibility aliases or dual-read paths. If a temporary transition path appears necessary, record the exception with removal criteria before implementation.
- Coordinate with [Data Sharing Docs Internal Index Request](/docs/?scope=studio&doc=site-request-data-sharing-docs-internal-index) for non-Docs Viewer metadata needs.

## Proposed verification set

- Source review and scoped `rg` evidence for producers and consumers.
- `git diff --check` if the audit or contract is recorded in source docs.
- No browser smoke is expected for this batch unless executable contract probes are added.

## completed verification

- Not started.

## follow-on tasks

- To be completed during the task.

## task close

- Add a handoff note to Batch 2 with the locked contracts and any classified non-Docs Viewer dependencies.
- Set this document and the tracker row status to `done` when the batch is complete.
