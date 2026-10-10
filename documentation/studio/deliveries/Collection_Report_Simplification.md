---
draft: false
doc_id: d-20261011-000000-17bd8a
title: Collection Report Simplification
added_date: "2026-10-11 00:00:00"
last_updated: "2026-10-11 00:00:00"
parent_id: d-20260428-000000-f5ff18
---
# Collection Report Simplification

Status: complete. The user approved implementation on 2026-10-11.

## Outcome And Readiness

Collection reports consume their configured document rows directly. Retire the empty manifest customisation envelope, Subject/report generation hashes and browser customisation machinery that has no active consumer. Retain scalar Subjects, authoring validation/assignment/import/publication preparation, normal title/date sorting, selection, actions and retained-list navigation.

The owning boundary is the collection builder, Subject server registration, shared collection reader and local Works/Project State reports. This is one finishable slice. Changing Subject semantics, Catalogue input ownership, public membership or tests would widen it and is excluded. Source data, Search, Publish, commit and deployment are outside the write boundary.

## Decisions

- Collection manifests contain exactly one root `docs` array. Targeted reconstruction rejects obsolete envelopes and requires an explicit complete collection Build; no conversion or fallback is introduced.
- Project State uses `docs_project_state_report_v5`, retaining assembly time, input ownership, summary and rows without hashes.
- Standard management controls use one caller-owned adapter. Server customisation registrations remain independent of browser composition.
- A complete Working Works docs-only build reconciles the changed global manifest contract. Shared runtime follows the existing tracked public projection.
- Verification uses changed-owner lint/syntax, the owning collection build and direct production-reader diagnostics over current data, plus required projection/site validation and bounded source review. These are expected to cost seconds to a few minutes; the collection build writes configured generated output and browser config, projection writes tracked runtime files, and diagnostic readers perform no writes. No tests or browser automation are created, changed or run. [Testing](../Testing.md) owns separate test approval.

## Completion Gates

- [x] Confirm approved scope, owners and credible blast radius.
- [x] Remove unused production machinery and update durable contracts.
- [x] Reconcile Working Works without media production or Search.
- [x] Complete focused diagnostics, required public projection checks and bounded code review.
- [x] Record final evidence limits and restart/reload requirements; recommend retaining or retiring this delivery record.

Changed-owner lint/syntax, the Works docs-only build, current-data report diagnostics, public projection/check and site validation passed. Works retained 235 rows with no by-ID or Links writes; Project State returned 205 folder rows, and coverage returned 140 Series rows with 20 containing documents. Bounded review removed remaining inactive CSS, export and callback references and confirmed that Subject authoring stays server-owned. Durable evidence limits live in [Subject Associations](../data/subject-associations.md#artifact-retirement). Restart Docs Viewer services and reload the browser; manual interaction remains unverified. Tests remain unchanged and unexecuted, including legacy fixtures that require separately approved review. No Search rebuild, Publish, commit, push or deployment occurred.

Closeout recommendation: retain this delivery and its Planned link temporarily for the recent evidence/restart pointer; the linked durable owners already contain the lasting contracts. No documentation deletion is required for this delivery.

## Durable Owners

[Generated Data Contracts](../Generated_Data_Contracts.md), [Subject Associations](../data/subject-associations.md), [collection browsing](../Sub_Scope_Index_Architecture.md), [report composition](../Report_Capability_And_Composition.md), [Reports](../Reports.md) and [Development Checklist](../Development_Checklist.md) own the lasting contracts. This delivery remains only a closeout/evidence pointer.
