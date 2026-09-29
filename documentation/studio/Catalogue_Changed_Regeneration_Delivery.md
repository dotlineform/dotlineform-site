---
draft: false
doc_id: d-20260928-231649-bf8a13
title: Catalogue Changed Regeneration - Delivery
added_date: "2026-09-28 23:16:49"
last_updated: "2026-09-29 11:43:31"
summary: Reconcile Catalogue documents with new, changed and deleted Works using a durable update list, targeted Regenerate and Build.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Changed Regeneration - Delivery

Proposed under [Planned Features](Planned_Features.md). Catalogue documents remain normal Docs Viewer collection documents. Each retains its immutable `doc_id`, the current Work title in front matter, timestamps, explicit `draft`, exact five-digit `work_id`, generated body and Links. Work IDs do not change: a Work ID is new or deleted, while edits to a Work retain the same ID. After a completed Refresh and Catalogue update, Working has exactly one Catalogue document for each current Work and none for a deleted Work. This delivery uses Refresh's Work changes to select source Regenerate, targeted Build or document deletion without changing the [bound image token](Catalogue_Image_Token_Metadata_Delivery.md). It extends [Catalogue Work Record Regeneration](Catalogue_Work_Regeneration.md).

## Requirements

- Keep normal Catalogue document front matter. `title` remains the literal Work title; `doc_id`, `work_id`, `added_date`, `last_updated` and `draft` retain their existing meanings. Do not introduce a title placeholder, Work-specific title resolution in shared document readers, or a new document identity scheme. Regenerate owns the generated token body; Links keep their existing separate owner.
- Replace the modal's **Only create new docs** checkbox with **Pending updates** (default) and **Full reconciliation**. Pending updates processes queued new, changed and deleted Works. Full reconciliation inventories all current Works and Catalogue documents once, repairs source titles and generated bodies, creates missing documents, deletes orphaned documents and builds current documents. One requested action runs the selected mode and reports its result; there is no Preview/Apply split.
- Studio Refresh owns detection. Its existing generated Work by-ID `written` result identifies new Works and changed records under their existing IDs; `deleted` identifies removed Work IDs. Ignore generation timestamp-only differences. Queue exact five-digit IDs in current or deleted sets, with the latest Refresh result for an ID determining which set contains it. There is no Work-ID rename or old-to-new mapping.
- Keep one durable private list at `$DOTLINEFORM_DOCS_BASE_DIR/working/source/collections/catalogue/updates-pending.json`, outside `documents/`. It records a schema, current Work IDs and deleted Work IDs, without Work versions or action revisions. Refresh accumulates pending entries across runs; Docs removes entries after their required operation succeeds. The list is local coordination state, not a generated Catalogue consumer payload or public artifact. Preview preparation may include its bytes in the Working source revision but must not promote it into captured build or public output.
- Require the list to exist and validate when Refresh or Catalogue update reads it. A missing or malformed list stops the action visibly; neither silently recreates, seeds or treats it as empty. Initialize it once as a visible delivery migration: read the existing generated Work index and by-ID records, queue every current Work ID, and inventory existing Catalogue documents to queue absent Work IDs for deletion. Then run Refresh to reconcile canonical changes. Keep a valid empty list after successful processing.
- On a Refresh failure, stop at the error and leave generated output and the pending list as written. Report the failure without rollback, an incomplete-state flag, automatic requeue or automatic repair. Diagnose the cause and retry Refresh manually. A retry may not repeat a `written` or `deleted` result for output already changed before the failure; inspect the resulting list and Work/document inventory, and choose Full reconciliation manually if needed. Only a completed Refresh gets the existing completion receipt.
- Regenerate reads the selected pending IDs or inventories current Works and Catalogue sources for Full reconciliation. It validates exact `work_id` associations as they are used and stops on missing, invalid or duplicate identities. For a pending current Work, read its exact by-ID JSON. A missing document requires source creation and targeted Build; a changed source title requires source regeneration and targeted Build; any other pending change requires targeted Build without a Markdown write or `last_updated` advance. Full reconciliation may also replace a divergent generated token body. Before deleting a document, check that its exact Work ID is absent from the current index and that the source belongs to the Catalogue collection, then delete through the owning collection path, including generated-output and selected-document reconciliation. Inspect deleted-document Links cleanup at readiness.
- Refresh, Regenerate and Build each execute from the request and inputs they need. Validate inputs while reading or using them, perform the work once, stop on the first failure and report success when the operation returns successfully. Do not add a preliminary dry run, a saved execution plan, a plan-freshness recheck, a second generator pass or a complete output read-back to compare results with a plan. An internal write set needed to perform an operation is allowed; it is not a second verification phase. Preserve source identity, `added_date`, `draft` and existing Links during retitle or Build-only work; only new documents receive Links initialization. Advance `last_updated` only when source changes. Remove a pending entry after its source/delete and required Build work succeeds; on failure, leave completed writes as they stand and report the error for manual diagnosis and retry. Full reconciliation uses its one Work/document inventory to find missing or orphaned documents, including missed queue entries.
- Remove independent Catalogue **New** and **Delete** document actions. New is already absent from the Catalogue UI; remove the detail Delete control and reject direct Catalogue New/Delete management requests while retaining the shared actions for other collections. Regenerate retains internal exact create/delete operations. Keep Catalogue Source, Draft and other document controls; the one-to-one rule applies to successfully reconciled Working membership, while existing draft/publication eligibility remains in force.
- Keep the Catalogue collection report on Docs-generated `manage-manifest.json` and public `manifest.json`. Its document titles, IDs, timestamps, Work associations, filter, sort, pagination, detail URL and thumbnails remain document-driven. The browser does not read a Work manifest or infer Work identity from a title, filename, route or selected row.

## Update List And Action Boundary

The pending list has current and deleted exact Work-ID sets. Refresh moves each changed ID into the set matching its latest generated result; Regenerate processes those IDs and removes each entry after its required work succeeds. The list does not hold Work versions, source revisions, expected outputs or a reusable execution plan. The generated Work record's own `header.version` and `media_version` retain their existing owners and meanings; Docs does not compare them to pending-list values.

Gallery membership and image facts may change a Work payload without changing its rendered Catalogue document. This can queue an extra targeted Build; that cost is accepted. Studio's `var/studio/catalogue/refresh-receipt.json` records a completed Refresh and does not replace the pending list or trigger another verification pass. Every maintained generated Work by-ID write/delete path must participate in the list or explicitly require Full reconciliation.

## Deliverables

- Explicit one-time initialization of `updates-pending.json` from generated Works and existing Catalogue associations; Studio-side accumulation for current and deleted Works and clear failure reporting. Keep the existing generated Work payload and Refresh receipt contracts; failed Refresh leaves partial writes for manual diagnosis and retry. Remove Refresh's duplicate generator dry runs and complete output read-backs.
- Docs-side Pending updates and Full reconciliation selection with one awaited Run action, targeted Build and pending-entry removal after success. Preserve immutable document IDs, normal front matter and unaffected Links. Remove Regenerate's preview/replan cycle and any Build dry run or complete output read-back added solely to compare actual work with a prior plan.
- Remove independent Catalogue New/Delete controls and reject their direct management requests without changing other collections or Regenerate's internal operations.
- Update the modal's choices, completed operation counts, empty state, deletion and result text. Explain first-run reconciliation and missing-list or failed-Refresh errors.
- Update durable Catalogue Regenerate and Save/Refresh owners after implementation. Do not change image-token grammar, Search, Works or ordinary-document selection, Publish, public Info, public deployment or the Catalogue artifact inventory.

## Process

1. Initialize the list once, then run **Refresh Catalogue** to reconcile current canonical Works. Later Studio Saves update the editor as usual; Refresh generates Work JSON and accumulates exact new, changed and deleted IDs. If Refresh fails, stop, diagnose and retry it manually before updating Catalogue documents.
2. Open **Regenerate Catalogue** in the Working Catalogue collection and run Pending updates or Full reconciliation. Pending updates reads the list and selected exact Work/document inputs. Full reconciliation inventories current Works and Catalogue documents once. A Work title change is a change to its existing ID, never an ID change.
3. Regenerate creates missing documents, updates changed titles or Full-mode bodies, deletes documents for absent Works and awaits targeted Builds for selected current documents. Metadata-only changes Build without a source write. Each operation validates the inputs it uses and stops on failure.
4. Remove a pending entry after its required source/delete/Build work succeeds. Entries not reached remain; a valid empty list stays available for the next Refresh. Report completion from the operation result without a second verification pass.

A full Docs Build refreshes bound Work image tokens in other collections, including Works and ordinary documents. This Catalogue operation covers only Catalogue documents and does not substitute for that broader Build. Token-structure migration and public Info visibility are separate decisions.

## Delivery Steps

### CCR-0 — Readiness

- [ ] Confirm normal Catalogue front matter, immutable Work IDs, one-to-one Working membership after reconciliation, the private list location, explicit initialization, missing-list stop, existing Refresh completion receipt and exclusion from Preview/public output.
- [ ] Identify maintained Work by-ID write/delete paths and their `written`/`deleted` comparison. Inspect the existing Catalogue New/Delete request boundary, deletion cleanup including Links, source/Build ownership, Docs-manifest collection report and exact checks needed before document deletion.
- [ ] Confirm one awaited action per mode, title-versus-build-only classification, completed-entry removal, failure stop/manual retry and modal wording. Identify existing duplicate dry runs, stale-plan checks and complete read-backs in Refresh, Regenerate and Build for removal. Select the smallest existing evidence for new, retitled, metadata-only and deleted Works, multiple Refreshes and failure stop; new or changed tests need a separately agreed specification under [Test Contract Discipline](Test_Contract_Discipline.md).

Gate: present the bounded list, Regenerate/Build/deletion and action-removal contract for implementation approval. Record: proposed; no code, pending list, modal or tests changed by this document.

### CCR-1 — Initialize And Maintain Update List

- [ ] Explicitly create the initial list with every current generated Work pending and existing documents for absent Works pending deletion; validate records as they are read.
- [ ] Accumulate exact current and deleted IDs in maintained Refresh paths. On an error, stop and report the partial writes without rollback or automatic requeue.
- [ ] Stop Refresh and Catalogue update on missing/invalid list state; keep a valid empty list after processing and retain the existing Refresh completion receipt as a status record. Remove duplicate generator dry runs and complete output read-backs. Record a proportional evidence budget after owner inspection.

Gate: inspect initialization, missing-list failure, accumulated and no-change Refreshes, and a failed Refresh's stop/report behavior. Manual diagnosis and retry remain the response to a real failure; do not run a live full collection operation solely for this gate. Record: pending.

### CCR-2 — Targeted Regenerate, Build And Actions

- [ ] Implement one awaited Pending updates or Full reconciliation action from the relevant generated Work records, Catalogue source inventory and pending list; read selected by-ID JSON only in pending mode. Remove preview/replan and stale-plan checks.
- [ ] Reuse source creation, targeted Build and exact collection deletion with correct Links, selected-document and failure-stop behavior; remove each pending entry after its required work succeeds. Remove redundant Build dry runs and complete output read-backs while retaining input validation and ordinary write errors.
- [ ] Remove independent Catalogue New/Delete UI and direct management requests while preserving other collections and Regenerate's internal operations.
- [ ] Replace the checkbox and review create, retitle, delete, build-only, empty-state and result behavior in the local UI.

Gate: present selected Working output and the modal for user manual review. Record: pending.

### CCR-3 — Code Review

- [ ] Review Refresh/list ordering, immutable identities, deletion checks, pending-entry removal after Build/delete, private/public boundary, duplicated mode logic and any remaining repeated verification passes.
- [ ] Resolve findings and update durable owner docs; rerun only evidence affected by review changes.

Gate: no unresolved issue inside the accepted delivery scope. Record: pending.

### CCR-4 — Closeout

- [ ] Confirm one-to-one Working membership after a completed update, normal titles, cumulative list behavior, selected evidence and manual review. State any unverified failure path plainly.
- [ ] Present the retain-or-retire recommendation for this temporary delivery document and working notes. Do not commit, push, Publish or deploy as part of closeout.

Gate: explicit user closeout after the complete result and durable owners are current. Record: pending.

## Follow-on

The exact Catalogue document inventory still scans sources for missing Works, orphaned documents and duplicate associations. A maintained Work-to-document index is a separate optimization if that cost becomes material. Bound Work tokens in other collections, Search freshness, token-structure migration and public Info visibility remain separate decisions.
