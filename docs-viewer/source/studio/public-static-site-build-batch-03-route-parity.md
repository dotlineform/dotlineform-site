---
doc_id: public-static-site-build-batch-03-route-parity
title: Public Static Site Build Batch 3 Public Route Rendering Parity
added_date: 2026-06-12
last_updated: 2026-06-12
ui_status: planned
parent_id: public-static-site-build-implementation-plan
---
# Public Static Site Build Batch 3 Public Route Rendering Parity

This is the delivery specification for Batch 3 in [Public Static Site Build Implementation Plan](/docs/?scope=studio&doc=public-static-site-build-implementation-plan).

Purpose: render production-equivalent public route shells without Jekyll or Liquid.

## Steer for these tasks

- This batch must be re-planned after Batch 1 closes.
- Route parity must come from [Public Route Model](/docs/?scope=studio&doc=public-route-model) and the Batch 1 route inventory.
- Do not redesign public routes, visual design, or route behavior. Batch 1 must record a required migration exception before this batch changes them.
- Use local dual-running preview for route parity: serve the Jekyll baseline and `_public_site/` static comparison target on separate ports and smoke the same route list against both.

## Deliverables

- Static-builder render helpers for shared layout, head metadata, navigation, footer, asset includes, catalogue shells, search shell, and Docs Viewer shell mounts.
- Generated HTML for the public root, static pages, catalogue shells, query-state shells, catalogue search, `/library/`, `/analysis/`, and `404.html`.
- Route parity checks against the active Jekyll output while Jekyll remains available.

## Implementation and policy guidance

- Page renderers pass structured data into focused helpers and return complete HTML files.
- Keep escaping and URL generation explicit.
- Avoid recreating broad Liquid semantics.

## Proposed verification set

- Static build success.
- Route file presence checks in the generated artifact.
- Browser smoke checks for representative catalogue routes and public Docs Viewer mounts against the static preview.
- Baseline-vs-static browser checks for the same route list when route shells or runtime boot behavior changes.
- Jekyll/static parity comparison for routes touched by this batch while Jekyll still exists.

## Tasks

### Batch 3: Public Route Rendering Parity

| ID | status | action |
| --- | --- | --- |
| 3.1 | planned | Re-plan this batch from Batch 1 route and Liquid responsibility inventories. |
| 3.2 | planned | Implement shared render helpers and static page renderers. |
| 3.3 | planned | Implement fixed catalogue, work, work-detail, moment, and search route shells. |
| 3.4 | planned | Implement public Docs Viewer route shells for `/library/` and `/analysis/`. |
| 3.5 | planned | Add route presence and representative browser smoke checks for the static preview. |
| 3.6 | planned | Add local preview parity checks that compare the Jekyll baseline and static output on the same route list. |

## completed verification

- Not started.

## follow-on tasks

- Update Batch 4 with any route-specific asset or payload copy needs discovered during rendering.

## batch close

- Add a handoff note to [Batch 4](/docs/?scope=studio&doc=public-static-site-build-batch-04-assets-docs-viewer).
- Set this batch status and front matter `ui_status` to `done` after route parity is verified.
