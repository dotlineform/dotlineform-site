---
draft: false
doc_id: d-20261024-000000-95fca2
title: Bulk Series Editing
added_date: "2026-10-24 00:00:00"
last_updated: "2026-10-24"
parent_id: d-20260428-000000-f5ff18
---
# Bulk Series Editing

## Requirements

Allow the Works selected in one displayed Series to move to another Series through ordinary bulk Save. Keep the browser on the original Series and remove moved Works from its list. Retire direct comma-separated/range entry so bulk selections always share a Series, with no mixed-Series state.

## Deliverables

- Single-Work search and `work` URL entry, with bulk selection supplied directly by the Series member list.
- Editable bulk Series choice with browser-owned validation, existing bulk persistence and saved-record/list adoption.
- Current behavior and evidence limits in [Catalogue Work Editor](../Catalogue_Work_Editor.md#bulk-editing) and [Catalogue Series Management](../Catalogue_Series_Management.md).

## Process

Choose a Series, select multiple member Works with Shift-click or Command-click, choose a destination in the Work editor's Series field and Save. Moved Works leave the displayed list while its Series selection stays in place. The bulk editor keeps the completed saved selection/destination. Untouched Series and Gallery memberships remain unchanged; normal Refresh, Regenerate and Publish carry the saved effects downstream.

## Delivery Steps

- [x] **0 — Readiness:** the user agreed the single-Series selection model and retirement of ID/range entry. The existing Work `series_id`, transaction and completion owners support the change without a schema migration. Browser selection, draft intent, authoring validation and list state remain frontend responsibilities; Python patches selected canonical records and queues known effects. The credible risks are search/list wiring, missing explicit Series intent and saved-list adoption. Public runtime, media processing, test work and lifecycle writes are outside this implementation.
- [x] **1 — Implementation:** direct search/URL entry opens one Work, list selection supplies exact IDs without parsing text, and bulk Series Save reuses the existing request/completion flow. The browser uses one saved Series in the draft and summary; the list retains its existing membership filter and returned-record adoption. Verification budget: changed-source JavaScript/Python lint, Python compilation, whitespace and bounded source review; seconds-long local checks with no application writes, services, browser or test code. Seven changed JavaScript owners and the bulk service passed focused lint; Python compilation and whitespace checks passed. Evidence is static; interaction and persistence await manual acceptance.
- [x] **2 — Code Review:** completed the distinct final source/diff and mandatory Redundancy And Defensive Behavior Review. Removed obsolete range parsing/formatting and repeated multi-Series summary scans; one browser parser rejects malformed multi-ID input before record lookup. Series selection reaches existing explicit-field validation/serialization, the bulk allowlist accepts it, and existing old/new Work facts select private Work-source updates. Returned saved records refresh list membership/count without changing the browsed Series. Retained selected full-record reads, exact target/request boundaries, confined transactions and incomplete-completion reporting have concrete existing owners; no extra Series lookup, corpus audit, media processing, compatibility alias or recovery policy was added. No unresolved source-review findings remain. The summary refinement passed its own focused lint; durable behavior and evidence limits are recorded in the Work editor owner.
- [ ] **3 — Manual Acceptance And Closeout:** restart Local Studio and reload the editor. Confirm single-ID/title-result entry, rejected typed/URL ranges, list multi-selection, Series reassignment including the last members, retained browsed Series and unchanged untouched metadata/Galleries. Live Save, UI interaction and downstream lifecycle execution remain unexercised by Codex. Retain this delivery until normal-use acceptance, then recommend archive; Git actions remain separate.

## Follow-on

No additional product scope or test work is proposed. Existing legacy bulk-write route tests remain unreviewed under [Test Contract Discipline](../Test_Contract_Discipline.md); this delivery neither changes nor relies on them.
