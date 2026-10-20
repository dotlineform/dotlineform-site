---
draft: false
doc_id: d-20261020-200307-e99246
title: Catalogue Medium
added_date: "2026-10-20 20:03:07"
last_updated: "2026-10-20"
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Medium

## Current And Next State

Implemented and reviewed on 2026-10-20; manual acceptance remains pending. [Catalogue Medium](/docs/?doc=d-20261020-200307-25af4e) follows Catalogue Works and defaults to Medium ascending. Current saved input produces 62 groups over 4,619 Works, including one unset Medium. Force-reload Docs Viewer before reviewing both sort headings, reload and Back. [Reports](../Reports.md) owns shipped behavior; this delivery is parented to [Planned Features](../Planned_Features.md).

## Requirements And Deliverables

- Show Medium and Works columns, counting each exact saved medium value once per Work. Preserve case, whitespace and punctuation; explicit null has its own No medium row.
- Default to Medium ascending and let either heading toggle ascending/descending. Reload saved metadata without running Refresh Catalogue; retain sorting through Back navigation.
- The browser owns grouping, counts, sorting and rendering over the existing `readCatalogueWorks()` endpoint. Keep the current producer, schema and saved file, with no new Python processing, endpoint or generated report dataset.
- Register `catalogue_medium` only in local composition and create ordinary Working host `d-20261020-200307-25af4e` immediately after Catalogue Works. Add its publication exclusion and existing private-report action identity.
- Generate only the new host with the explicit targeted docs-only command. Search, Refresh Catalogue, Publish, tests and browser automation are outside this delivery.

## Process

Refresh Catalogue advances the saved input. Open Catalogue Medium to count current saved values, choose either sort heading, or reload the saved metadata. Back keeps the existing report state. No running Studio server is needed to read the report.

## Delivery Steps

### CM-0 — Readiness

- [x] Confirm input fields, existing endpoint, local report composition, host placement and private/public boundaries.

Record: ready. The approved saved metadata provides every required value; the browser already has an appropriate report service. The configured Working source and navigation/policy controls are writable. Existing two-column report styling and retained views provide the required presentation. Stop for unavailable configured storage without introducing a fallback or widening publication.

### CM-1 — Implementation And Evidence

- [x] Add browser aggregation/rendering, local registry/loader and styling.
- [x] Create, place and exclude the report host; retain its private action policy.
- [x] Generate only the new document and inspect its descriptor and Index placement.
- [x] Update durable report behavior and guardrails.

Verification budget: explicit-path JavaScript lint, JSON parsing, whitespace/source review and one read-only invocation of the production aggregation/sort functions over current saved metadata. These address module/configuration errors and current-data grouping/order at an expected cost of seconds, without services, network, fixtures or new test code. One exact Working document build writes the new host and its required local/navigation/public-eligibility metadata while preserving Search and unrelated document payloads; it skips media production. Sorting interactions, reload/Back, empty/null/failure presentation and visual fit remain manual review. No test or browser suite is selected.

Record: complete. Explicit lint passed for `catalogue-medium-report.js`, `docs-viewer-reports.js` and `docs-viewer-action-definitions.js`; local registry, source hierarchy and exclusion JSON parsed successfully; tracked/new-file whitespace checks passed. A read-only Node invocation of the production aggregation and both sort directions over saved metadata returned 62 groups, 4,619 input Works and 4,619 summed counts, including one No medium Work. Initial order starts acrylic on board, acrylic on canvas, acrylic on paper; numeric descending starts digital c-type print (3,505), giclée print (290), photocopy (173). The exact command `python3 docs-viewer/build/build_docs.py --stage working --write --only-doc-ids d-20261020-200307-25af4e --skip-media-builds` ran with the required Miniconda interpreter: one document and one Index written, no removals, Recent unchanged and zero warnings. Output inspection confirmed `report: {id: catalogue_medium}`, the exact Catalogue Works → Catalogue Medium → Series and Galleries placement, explicit exclusion and absence from the public report registry. No tests, browser interaction, media production, Search, Refresh Catalogue or Publish ran.

### CM-2 — Code Review

- [x] Review final source/configuration/generated boundaries, exact grouping, null handling, sorting, retained disposal and failure reporting.
- [x] Complete the mandatory Redundancy And Defensive Behavior Review and resolve findings.

Record: complete. Distinct post-evidence review traced the local loader, report context, existing HTTP client, saved-file reader, retained owner and final host/configuration/style deltas. One load/reload fetches and groups once; heading changes reuse those groups. Exact Map keys preserve authored differences and null identity; numeric sorting uses Medium ties. Restored order feeds an in-flight read, detached retained reads can finish, and actual disposal releases rows and ignores late completion. The new host uses the existing private-report action restriction and publication exclusion. Required management/origin authority, confined JSON read/HTTP parsing, literal `textContent` rendering and busy/disposal checks remain with their owners. No redundant validation, schema audit, canonical read, generation, hash, freshness check, compatibility alias, repair, cache or speculative shared abstraction was added. No findings remain. New/changed local modules and styles are absent from the public runtime inventory, so no code projection is required. UI, HTTP/failure and synthetic case/whitespace/null-collision variants received source review only; tests remain unchanged and unrun. The pre-existing Catalogue Works note removal was preserved.

### CM-3 — Closeout

- [x] Reconcile evidence and durable documentation; present the report and reload requirements.
- [ ] Record user manual acceptance.

Record: implementation closeout complete. Reports and Development Checklist own the lasting behavior and guardrails. Force-reload Docs Viewer and review the report in its new Index position; no new endpoint or server process change is required. Tests, browser automation, Search, Publish, commit and push remain outside the completed work. Retain this compact delivery for manual acceptance and recent-evidence lookup; no separate feature/concept/architecture documents were created.
