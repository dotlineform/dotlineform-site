---
draft: false
doc_id: d-20261011-000000-c28b91
title: Report Descriptor Simplification
added_date: "2026-10-11 00:00:00"
last_updated: "2026-10-11 00:00:00"
parent_id: d-20260428-000000-f5ff18
---
# Report Descriptor Simplification

Status: complete. The user approved implementation on 2026-10-11.

## Outcome And Readiness

Report descriptors contain required `id` and include `collection` only for reports that use it. Retire unused preset support from report-source parsing, registry records, generated descriptors, browser readers, expanded-presentation identity and the Reports List column. Retain configured report IDs, collection validation, loader allowlists, normal rendering and publication eligibility.

The owning boundary is the report-source parser, local/public report registries and their executable readers. All 16 local registry entries had empty preset arrays; no current report selected a preset. This is one finishable slice. Report-specific controls, document source changes, publication policy, media, Search and tests are outside the scope. The maintained public registry is excluded from document distribution and is updated as configuration; prepared/public by-ID documents change only through an explicit Publish.

## Decisions And Verification Budget

- Remove the preset attribute from the parser's allowed keys; a source preset now follows the existing unknown-attribute failure path. Keep legacy front-matter rejection.
- Store registered report IDs in one immutable set without per-report preset definitions. Preserve unknown/duplicate report-ID and configured-collection validation.
- Emit no null optional descriptor fields. Collection reports keep their exact configured identity; other reports emit only `id`.
- Use one existing ordinary Working docs-only build with `--skip-media-builds --skip-recent` to reconcile the global descriptor contract. Current named-collection sources declare no report blocks and need no collection builds.
- Verify changed owners with lint/syntax, the owning build and read-only diagnostics over real saved payloads, then the required public code projection/check/site validation and bounded source review. Expected cost is seconds to a few minutes. The build writes configured generated documents as needed, while projection updates tracked public code. No tests, fixtures or browser automation are created, changed or run; [Testing](../Testing.md) owns separate test approval.

## Completion Gates

- [x] Confirm the approved scope, owners and credible blast radius.
- [x] Retire preset machinery and null descriptor fields; update durable contracts.
- [x] Reconcile Working's ordinary document payloads without media, Recents or Search work.
- [x] Complete saved-data diagnostics, required public projection checks and bounded code review.
- [x] Record final evidence limits and restart/reload requirements; recommend retaining or retiring this record.

The Working build processed 34 documents and rewrote 19 report payloads, with no removals, Index or Links writes and no warnings. Recents remained unchanged. Saved-data diagnostics found 19 descriptors using only `id` and optional `collection`, with four collection reports and zero null values. The selected document emitted only `id: selected_documents`; a collection host retained `id: docs_collection` and `collection: concepts`. Local/public registries retain 16/two reports. Changed-owner Python/JavaScript lint, Python syntax, whitespace, public projection/check and site validation passed; one public runtime module was projected. Bounded code review confirmed that unknown attributes and unknown/duplicate IDs still fail, collection validation and loader allowlists remain intact, and Reports List uses the existing one-column style. No active preset reading or compatibility path remains; legacy front-matter rejection is retained. Historical preset tests and fixtures are unchanged and unexecuted pending separately approved test work; manual report mounting and presentation remain unverified. Restart Docs Viewer services and reload the browser. No Publish, commit, push or deployment occurred.

Closeout recommendation: retain this delivery and its Planned link temporarily for recent evidence and restart/reload guidance; the durable owners already contain the lasting contract. No documentation deletion is required.

## Durable Owners

[Reports](../Reports.md), [Generated Data Contracts](../Generated_Data_Contracts.md#by-id-payload-contract), [Configuration And Extension Points](../Configuration_And_Extension_Points.md#add-a-report) and [Development Checklist](../Development_Checklist.md) own the lasting contracts.
