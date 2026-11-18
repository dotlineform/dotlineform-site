---
draft: false
doc_id: d-20260625-162242-b0b6c7
title: Route Ready State
added_date: "2026-06-25 16:22:42"
last_updated: "2026-11-18"
parent_id: d-20260419-000000-d2e47b

---
# Route Ready State

Async Studio and Docs Viewer routes expose one main route root. Ready means startup has settled into an inspectable success, empty, unavailable or error state. It does not mean every command is available.

## Contract

| State | Meaning |
| --- | --- |
| `ready="false"` | Root exists; startup has not settled |
| `ready="true"` | First stable presentation is inspectable |
| `busy="true"` | Route-level blocking work is in flight |
| `busy="false"` | No route-level blocking operation is in flight |

Templates start ready/busy false. Boot sets busy during acquisition, renders success or stable failure, clears busy and sets ready. Commands project busy for actual loading, saving, publishing, importing or generation; local menus, focus and panels do not make the route busy.

Studio's [route-state helper](../../studio/app/frontend/js/studio-route-state.js) owns `data-studio-ready`, `data-studio-busy` and the bubbling `studio:ready` event. Docs [boot](../../docs-viewer/runtime/js/shared/docs-viewer-app-boot.js) owns `data-docs-viewer-ready`, `data-docs-viewer-busy` and `docs-viewer:ready`; operation status subsequently projects current busy state. Detail attributes may describe route, mode, service and loaded record.

Read root attributes when waiting for readiness; a listener attached after boot can miss the event. A failed service can leave the route ready with affected controls disabled. [Local Setup](Local_Setup.md) owns startup and recovery.

## Nested Import And Audit Limits

The nested Docs Import controller still emits Studio-prefixed attributes/events. This is an existing cross-app naming seam; do not use it as a pattern for a new route root.

The existing read-only [route audit](../../tests/audits/route_ready_state.py) parses configured HTML templates for missing/duplicate roots and initial attributes. It does not execute boot or prove operation busy state. Its current path list includes the reusable public template and Manage shell but still names removed `site/analysis/index.html`; absent paths are skipped, so it does not inspect installed `site/index.html` or Review. That coverage gap is logged in the [tracker](../deliveries/Rationalise_Documentation.md). [Testing](../development/Verification.md) owns selection and separately approved changes; the [earlier audit delivery](../deliveries/Route_Ready_State_Audit.md) preserves its original evidence.
