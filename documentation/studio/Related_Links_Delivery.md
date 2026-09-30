---
draft: false
doc_id: d-20260930-221742-069a8a
title: Related Links Delivery
added_date: "2026-09-30 22:17:42"
last_updated: "2026-09-30 22:42:00"
summary: Deliver the editable related-links directive and retire the separate per-document Links view.
ui_status: in-progress
parent_id: d-20260930-195002-b3417e
---
# Related Links Delivery

## Requirements And Decisions

Deliver the approved `[[links|related links]]` block directive, an editable plain heading, a title-sorted combined incoming/outgoing list and the chosen collection icons. Omit self-links, duplicates and empty sections. Embed the result in generated document JSON using the existing icon renderer and currently persisted version-4 relationship JSON. Full and targeted builds read the same saved incoming/outgoing summaries; section rendering does not derive relationships or depend on build order. Publish captures those records and filters entries to its already selected eligible document IDs. The user explicitly confirmed that this replaces the separate per-document Links view; remove its control, adapter and read endpoint. Keep the original build flow, workspace diagnostic aggregate and existing incremental relationship maintenance. Info-panel presentation, styling refinement and test changes are separate.

## RL-0 — Readiness

- [x] Confirm the source directive, insertion placeholder, icon selection and retirement scope.
- [x] Inspect the source, payload, incremental relationship, full Build, captured Preview and public-projection owners.
- [x] Use [Development Checklist](Development_Checklist.md) and [Development Workflow](Development_Workflow.md) for implementation and closeout.

Gate: one complete feature using persisted relationships, no reader-time fetching and no manufactured reciprocal relationships. Verification budget: explicit Python/JavaScript lint and Python compilation; a production ordinary-document dry run with media, Recents and browser writes skipped to verify the restored build path; required reader-config regeneration, site-code projection/check and site validation; scoped source/diff and whitespace review. Expected cost is seconds plus bounded review. The dry run writes no document/Search payloads; configuration/projection writes are intentional tracked output. No tests, fixtures, regression scripts, browser automation, live source mutations, Search build, Publish, deployment, commit or push are included. [Testing](Testing.md) owns the separate test-work policy.

## RL-1 — Implementation

- [x] Add the standalone Markdown directive and selected-heading insertion action.
- [x] Read currently persisted relationship JSON for both full and targeted section rendering.
- [x] Capture and filter persisted relationship records for temporary Preview inputs.
- [x] Restore the original collection build flow and incremental relationship maintenance.
- [x] Render the sorted list with self-contained decorative icons and portable document targets.
- [x] Exclude generated links from authored-anchor/backlink collection.
- [x] Remove the separate document Links UI, runtime reads and endpoint without compatibility aliases.
- [x] Complete config/runtime projection and selected static verification.

Gate: code and public projection are ready for review. Explicit lint and compilation passed for the nine Python sources touched by the simplification; the retained JavaScript passed its earlier explicit lint. The restored production ordinary-document dry run processed 42 sources with no warnings, payload/index changes or relationship writes/removals. The local reader config lost only the retired activation field; public settings were unchanged. The retained site projection changes 13 runtime/CSS files and removes the Links adapter; projection check and site validation passed after the simplification. Whitespace review passed. Current sources contain no directive, so the build run proves restored build wiring and unchanged existing content, rather than token expansion or visual acceptance.

## RL-2 — Review

- [x] Review persisted-record ownership, freshness, literal syntax, escaping, routing, icon reuse and generated-anchor exclusion.
- [x] Inspect the exact public delta and resolve findings.

Gate: no blocking code-review findings. Source-graph derivation, preloaded-source plumbing, the combined-build mode and full-graph reconciliation are removed. Section rendering only reads exact persisted records. Exact collection/document identities own deduplication and routes, heading/title text is escaped, and icons use the existing sanitized portable masks. Generated anchors bypass authored-link rewriting and collection. Publish uses captured relationship inputs outside the generated snapshot root and filters entries with its existing eligible IDs; distribution does not derive them. The Links-only target-layout map and dispatch were removed with the view, while the aggregate's summary/target helpers remain. Retired-view tests, including `docs-viewer/tests/js/docs_viewer_links_contract.mjs` and the per-document Links-read cases in `docs-viewer/tests/python/test_docs_generated_reads.py`, remain unchanged and unrun; they require a separately agreed specification before retirement or replacement. Publish and Review-package expansion were not exercised in this delivery.

## RL-3 — Closeout

- [x] Transfer current behavior to [Related Links](Related_Links.md), [Builder](Builder.md), [Runtime](Docs_Viewer_Runtime.md#links-presentation) and [Source Editor Scripts](Source_Editor_Scripts.md#directives).
- [ ] Record user manual acceptance of insertion, editable heading, icon/list appearance, navigation and full-build freshness.

Gate: manual acceptance. Restart local services and hard-refresh the browser for the changed runtime. Use Directives → Insert related links in a document with saved relationships, then run a full Docs Build to refresh embedded sections from the currently persisted JSON. Keep this delivery through acceptance; archive only by an explicit later action.
