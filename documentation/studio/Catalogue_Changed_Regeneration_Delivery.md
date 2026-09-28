---
draft: false
doc_id: d-20260928-231649-bf8a13
title: Catalogue Changed Regeneration - Delivery
added_date: "2026-09-28 23:16:49"
last_updated: "2026-09-28 23:30:19"
summary: Add new, changed and full Catalogue Regenerate modes using an accumulated Work-change list maintained by Catalogue Refresh.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Changed Regeneration - Delivery

Proposed under [Planned Features](Planned_Features.md). Studio **Refresh Catalogue** already determines which generated Work by-ID JSON files changed. This delivery retains their Work IDs in a small pending list until Docs Viewer **Regenerate Catalogue** has successfully processed them. **New and changed** then reads the list rather than comparing every Work JSON with a saved version for every Catalogue document. It still inventories Catalogue document identities to find missing documents and preserve exact Work associations. This extends [Catalogue Work Record Regeneration](Catalogue_Work_Regeneration.md) without changing the [bound image token](Catalogue_Image_Token_Metadata_Delivery.md).

## Requirements

- Replace the modal's **Only create new docs** checkbox with three mutually exclusive choices: **Only new**, **New and changed**, and **Full**. **New and changed** is the default after Refresh: create missing Work documents and process existing documents whose Work ID is pending. **Only new** creates missing documents and leaves pending existing Works queued. **Full** processes every current Work and can clear the pending list after success. Preview shows create, regenerate and skip counts for the selected choice.
- Studio Refresh owns detection: compare each newly generated `works/index/<work_id>.json` with the previous generated file using the existing content comparison, which ignores `generated_at_utc`. Its existing `written` result identifies created or changed Work files. Append those exact Work IDs to the pending list, preserving IDs from earlier Refreshes. Do not add an ID merely because Refresh ran or its timestamp changed. Remove deleted Work IDs from the pending list after verified deletion; retain the existing policy of not deleting their Catalogue documents.
- Keep one durable private list at `$DOTLINEFORM_DOCS_BASE_DIR/working/source/collections/catalogue/regeneration-pending.json`, outside `documents/`. It records a schema, Refresh completion state and pending exact Work IDs with their latest generated `header.version`. Studio's maintained Work-JSON write paths add or update entries; Docs Viewer removes only entries it has successfully processed. The list is local coordination state, not a generated Catalogue consumer payload or public artifact. Preview preparation may include its bytes in the Working source revision but must not promote it into the captured build or public output.
- Require the list to exist and validate before either Refresh or Regenerate proceeds. A missing or malformed list stops both actions with an explicit error; neither action silently recreates, seeds or treats it as empty. Investigate missing state before an explicit restoration or reconciliation. Keep a valid empty list after successful Regenerate so the next Refresh can accumulate new changes without deleting the file.
- Initialize the list once as a visible delivery migration before enabling the new actions. Validate the existing generated Work index and by-ID records, then seed every available Work ID with its `header.version` as pending. This makes no claim that the generated data or existing Catalogue documents are current; run Refresh after initialization to reconcile canonical changes. The first **New and changed** run may process all Works once. Verify the initialized file and record its creation before normal Refresh or Regenerate use.
- Make a partially failed Refresh recoverable. Mark the list as Refresh-incomplete before writing Work outputs; Regenerate cannot consume it in that state. A subsequent complete Refresh must conservatively queue all current Works if the prior Refresh may have written output before failing, because those files may no longer appear in the next run's `written` result. If marking the state fails, abort before changing output. Mark it complete only after generated JSON, private report metadata and the Refresh completion receipt verify. Preserve any previously pending current Work IDs throughout.
- Regenerate reads the Work index and inventories current Catalogue sources by exact five-digit `work_id`, retaining the duplicate-association error. **New and changed** reads by-ID Work JSON only for missing or pending Works, not every existing document. Validate each selected Work's exact identity and that its current `header.version` agrees with the pending entry; include those selected versions, source revisions, choice and pending-list revision in the preview receipt. Apply rejects changed inputs and requests a new preview. An ordinary document Build never removes an ID from the pending list.
- After selected source writes and the targeted Catalogue document build complete, atomically remove only the pending IDs that were processed at the previewed versions. **Only new** removes an ID only when it created that Work's document. A failed build or list write must not report a completed Regenerate or acknowledge any selected pending ID; retry may rebuild some documents again. Preserve current partial-source-write reporting, immutable document IDs, `draft`, Links and the policy that only newly created documents receive Links initialization.
- A selected Work whose generated body and title already equal its source still needs the targeted Build for bound metadata, but must not rewrite Markdown or advance `last_updated`. An existing document edited manually while its Work ID is not pending is skipped by **New and changed**; **Full** explicitly replaces its body. No mode infers Work identity from title, filename, route or selected row.

## Version And List Contract

| Value | When it changes | Use here |
| --- | --- | --- |
| Work `header.version` | Studio recalculates this deterministic content hash when Refresh generates the projected Work record, sections and schema. It does not change from a generation timestamp alone. | Saved with a pending Work ID and checked against that selected by-ID JSON at preview/apply. It is not a numeric counter and Docs Viewer never increments it. |
| Work `media_version` | Studio's image-change workflow advances this separate media value; Refresh later projects it into Work JSON. | It may change `header.version`, but neither the list nor Regenerate increments or compares `media_version` separately. |
| Pending list | Each successful Refresh unions its changed Work IDs with all unprocessed IDs; Regenerate removes only successfully processed IDs. | Cumulative work awaiting Catalogue document regeneration, not a per-document version baseline or a single-Refresh receipt. |

Refreshing Gallery membership or image facts can change a whole Work payload without changing its displayed metadata. That may queue an extra Catalogue document build; this cost is accepted. The list survives multiple Refreshes and partial Regenerate attempts. Studio's `var/studio/catalogue/refresh-receipt.json` continues to describe freshness of one Refresh against canonical inputs; it does not replace the pending list. All maintained paths that write generated Work by-ID JSON must participate in the same pending-list rule or explicitly require a **Full** Regenerate, so a direct writer cannot silently bypass change detection.

## Deliverables

- One-time explicit initialization of the private list from validated existing generated Work records, followed by Studio-side accumulation coupled to verified Work JSON Refresh. Include incomplete-Refresh recovery, exact Work-ID filtering and private-state validation; never initialize implicitly in the normal actions. Keep the existing generated Work payload and Refresh freshness receipt contracts.
- Docs-side three-mode selection and selected-Work reads, one preview/apply receipt, targeted source/build operation and acknowledgement after success. Preserve report refresh, Links, exact identity and partial-failure behavior.
- Modal choice control and mode-specific preview, empty-state and result text. Explain the one-time reconciliation after delivery initialization and make a missing-list error visible.
- Update the durable Catalogue Regenerate and Save/Refresh owners after implementation. Do not revise image-token grammar, add a rendered-field registry, change Search, Works or ordinary document selection, or alter Publish, public deployment or the Catalogue artifact inventory.

## Process

1. Initialize and verify the pending list once during this delivery, then run **Refresh Catalogue** to reconcile current canonical Works. Thereafter, save Work changes in Studio and run Refresh as usual. Save updates the editor but does not append to the list. Refresh identifies changed generated Work records and merges their IDs into the existing durable list. If the list is missing, stop and investigate before another Refresh.
2. Open **Regenerate Catalogue** in the Working Catalogue collection and select **Only new**, **New and changed**, or **Full**. Preview inventories exact Work-to-document associations and reads by-ID JSON only for selected Works. A missing list stops every choice; if Refresh left the list incomplete, complete Refresh before using it.
3. Apply rechecks the previewed choice, selected inputs and pending list, creates missing documents, replaces selected existing sources only where their generated title or body differs, and awaits the targeted document build.
4. After the build succeeds, atomically remove the selected pending entries at the versions just processed and report completion. Unselected entries remain for a later run. A valid empty list remains available for the next Refresh.

Adding a rendered metadata field to the existing bound image token does not change token structure or Work JSON by itself, so it does not add IDs to this list. A full Docs Build refreshes rendered metadata in every affected collection, including Works and ordinary documents with Work image tokens. **Full** Regenerate rebuilds all Catalogue documents but is not a token-structure migration or a substitute for the broader Build. A token-structure change needs a separately designed source migration and impact review.

## Delivery Steps

### CCR-0 — Readiness

- [ ] Confirm the private list location, explicit one-time initialization, missing-list stop, incomplete-Refresh recovery and exclusion from prepared Preview/public output against current workspace and Refresh owners.
- [ ] Identify every maintained Work by-ID JSON write path and ensure none can bypass pending-list updates. Confirm the existing `written` comparison, exact Work identity and the current Regenerate source/build boundary.
- [ ] Confirm the three modes, **New and changed** default, one-time reconciliation, partial acknowledgement and modal wording. Select the smallest existing evidence for a missing list, multiple Refreshes, incomplete Refresh, metadata-only change and failed build/list write; new or changed tests need a separate agreed specification under [Test Contract Discipline](Test_Contract_Discipline.md).

Gate: present the bounded queue and mode contract for implementation approval. Record: proposed; no code, pending list, modal or tests changed by this document.

### CCR-1 — Initialize And Maintain Change List

- [ ] Explicitly create and verify the initial list with every current generated Work pending before enabling the new actions; do not infer that existing documents have already processed those versions.
- [ ] Add validated, durable accumulation of changed Work IDs to the maintained Refresh write path, including conservative recovery after partial output writes.
- [ ] Stop both Refresh and Regenerate if the list disappears or becomes invalid. Keep a complete empty list after successful acknowledgement and block Regenerate while Refresh state is incomplete. Record a proportional verification budget after inspecting the owners.

Gate: inspect explicit initialization, missing-list failure, two accumulated Refreshes, a no-change Refresh and failed-then-retried Refresh without running a live full collection operation solely for this gate. Record: pending.

### CCR-2 — Regenerate Selection And Modal

- [ ] Implement three-mode preview/apply selection from the Work index, exact Catalogue source inventory and pending list; read selected by-ID JSON only.
- [ ] Retain source-write, targeted-build, Links and partial-failure behavior; acknowledge only successfully processed pending versions after the build.
- [ ] Replace the checkbox with the three choices and review mode-specific preview, Apply, stale-preview and result behavior in the local UI.

Gate: present selected Working output and the modal for user manual review. Record: pending.

### CCR-3 — Code Review

- [ ] Review Refresh/list ordering, missing and incomplete state, exact identity, selected versions, acknowledgement after build, private/public boundary and duplicated mode logic.
- [ ] Resolve findings and update the durable owner docs; rerun only evidence affected by review changes.

Gate: no unresolved issue inside the accepted delivery scope. Record: pending.

### CCR-4 — Closeout

- [ ] Confirm the three-mode outcome, cumulative list behavior, selected evidence and manual review. State any unverified failure path plainly.
- [ ] Present the retain-or-retire recommendation for this temporary delivery document and any working notes. Do not commit, push, Publish or deploy as part of closeout.

Gate: explicit user closeout after the complete result and durable owners are current. Record: pending.

## Follow-on

The current exact Catalogue document inventory still scans source documents to find missing Works and duplicate Work associations; this delivery removes the per-document Work-JSON comparison and most document builds. A maintained Work-to-document index would be a separate optimization if that inventory cost becomes material. Bound Work image tokens in Works and ordinary documents, Search freshness and token-structure migration remain separate decisions.
