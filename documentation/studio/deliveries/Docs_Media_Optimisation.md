---
draft: false
doc_id: d-20261014-171409-bd41cf
title: Docs Media Optimisation
added_date: "2026-10-14 17:14:09"
last_updated: "2026-10-14 17:52:58"
parent_id: d-20260428-000000-f5ff18
---
# Docs Media Optimisation

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Media And Asset Handling](../Media_And_Asset_Handling.md#docs-media-inventory-report). The user approved four bounded optimisations on 2026-10-14 after reviewing the report's filesystem and browser responsibilities.

## Agreed Result

The service reads one saved dataset on opening, lists registered local media and extracts document references on explicit Refresh, and reveals a selected file in Finder on activation. The browser owns filename presentation, joins, orphan counts, search, collection filtering and sorting. No per-file display request is added. Coverage, exact identities, saved metadata shape, source freshness and explicit Refresh remain as delivered by [Docs Media Collections Delivery](Docs_Media_Collections_Delivery.md).

Use one narrow source read/parse with supplied token/metadata extraction, a filename-only local inventory without unused size reads or existence rechecks, one saved-representation validation boundary, and browser preparation of search text, collection counts and sort order. Source membership/parsing is shared with Broken Links through `docs_source_inspection.py`; other source-model consumers retain their owners. Configured Working media/build-source families are local, so the unused remote inventory parameters and adapter/authentication wrapper are removed without aliases. Thumbnail inventory and reference derivation are skipped at their selection boundaries. The approved follow-up [Artifact Listing And Export Cleanup](Artifact_Listing_And_Export_Cleanup.md) extends filename-only discovery to Mermaid and confines metadata-bearing listings to remote transfers.

## Completion Gates

- [x] Readiness: confirmed current callers, configured local storage, saved-data lifecycle and browser-owned decisions; user approved this finishable slice.
- [x] Implement narrow source reads, filename-only inventory and removal of repeated producer/browser audits.
- [x] Prepare browser search text and collection counts once per dataset, reuse one collator and sort only on dataset/sort changes.
- [x] Focused lint and Python compilation passed. Read-only generation returned all five configured owners, 477 file records, 245 documents with references and 341 references; the saved read accepted the existing five-owner snapshot. The existing Broken Links CLI completed with zero findings and no unavailable generated sources after the shared-reader extraction.
- [x] Complete the distinct code review and mandatory Redundancy And Defensive Behavior Review. Confirmed owner/role isolation, thumbnail exclusion, saved/empty/failure handoffs and sort/filter/restore call sites. Review removed the remaining owner-label completeness check and unused validation-key construction, and replaced per-source full path resolution with exact-parent/terminal-symlink checks under the carried resolved root. Affected lint/compilation and read-only generation/Broken Links diagnostics passed; retained safeguards and evidence limits are recorded in the durable owner.
- [x] Update the durable media owner and implementation guardrail. Changed JavaScript is local-only and outside the public projection inventory.
- [ ] User manual acceptance after restarting the local service and force-reloading Docs Viewer: opening the saved report, explicit Refresh, collection/search/sort behaviour, counts unaffected by search, retained sort on reopening, exact document links and Finder activation.

Verification uses the five changed Python modules' lint/compilation, the two local report modules' JavaScript lint, the existing production generator/saved-read helpers without their save operation, the existing Broken Links read-only CLI and whitespace/source review. Direct diagnostics inspect current positive data; they do not establish persisted Refresh, failed-scan/write or browser/Finder behaviour. No tests, fixtures or profiles were authored, changed or run under [Test Contract Discipline](../Test_Contract_Discipline.md). No real report metadata, sources, media, Docs/Search output, queues or publication output was written. Test migration and UI acceptance remain separate work.
