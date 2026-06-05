---
doc_id: site-request-docs-viewer-public-index-slimming-batch-3
title: Docs Viewer Public Index Slimming Batch 3
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: planned
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 3: Runtime Loading and Boundary Check

This is the delivery specification for [Batch 3 in Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 3: Runtime Loading and Boundary Check

Summary: Add tree payload adapters, switch public and manage route loading to `index-tree.json` and the small recently-added payload, and coordinate with the entrypoint split request if shared-core ownership issues appear.

| ID | status | action |
| --- | --- | --- |
| 3.1 | planned | Add public and manage tree payload adapters that preserve the shared-core boundary owned by [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints); do not move manage-only controls, services, drag/drop, context menus, mutation calls, source/edit workflows, or local-service reads into public payloads or shared payload adapters. |
| 3.2 | planned | Coordinate with the entrypoint split request if tree payload switching exposes shared-core public/manage mode switches or manage-only rendering in shared modules; this request owns the payload/data contract, while the entrypoint split request owns the shared-core cleanup work. |
| 3.3 | planned | Switch public and manage route config/data loading so frontend index-panel rendering reads route-appropriate `index-tree.json` payloads and recently-added reads its small generated payload; missing required payloads should surface as visible data-load failures with no fallback to `index.json`. |

## Steer for these tasks

- The adapter should bridge the new tree payload to the existing renderer contract without making public code aware of manage-only capabilities.
- Missing `index-tree.json` is a visible load failure, not a reason to fallback to `index.json`.
- Recently-added should load from its own route-appropriate payload.
- Coordinate explicitly if this exposes shared-core public/manage mode switches that belong to the entrypoint split request.

## Deliverables

- Public tree payload adapter.
- Manage tree payload adapter using the same tree record structure.
- Route config/data loading switched to route-appropriate `index-tree.json`.
- Recently-added runtime loading switched to the small generated payload.
- Visible missing-payload behavior with no `index.json` fallback.
- Boundary notes for any entrypoint split coordination needed.

## Implementation and policy guidance

- Do not move management controls, services, drag/drop, context menus, mutation calls, source/edit workflows, or local-service reads into public payloads or shared public adapters.
- Keep shared-core and shared-renderer cleanup within the entrypoint split request unless the payload switch requires an explicitly coordinated change.
- Avoid compatibility shims for old `index.json` runtime loading.

## Proposed verification set

- JavaScript syntax/import checks for changed runtime modules.
- Focused browser or module smoke for public and manage tree loading.
- Request/asset assertions proving route-appropriate `index-tree.json` and recently-added payloads load.
- Negative request assertions proving public routes do not request public `index.json`.

## completed verification

- Not started.

## follow-on tasks

- To be completed during the task.

## task close

- Add a handoff note to Batch 4 with selected-document state behavior and any adapter assumptions that affect info-panel hydration.
- Set this document and the tracker row status to `done` when the batch is complete.
