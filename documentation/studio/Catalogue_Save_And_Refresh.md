---
draft: false
doc_id: d-20260927-223812-8042fc
title: Catalogue Save And Refresh
added_date: "2026-09-27 22:38:12"
last_updated: "2026-10-03 20:38:59"
summary: Current Catalogue Save, local Refresh, reader freshness and recovery boundaries.
ui_status: stable
parent_id: d-20260401-000000-a11bf3
---
# Catalogue Save And Refresh

## Current Workflow

Studio owns canonical Work, Series, Gallery and membership source in `studio/data/canonical/catalogue/`. **Save** completes an exact authoring change and the local media needed by the Works editor. **Refresh Catalogue** separately reconciles generated Catalogue readers in the configured Docs Working workspace. **Docs Publish** captures the current Working output and distributes a completed Preview under the separate [Catalogue Deployment](Catalogue_Deployment.md) owner. [Catalogue Hosting And Storage Options](Catalogue_Hosting_And_Storage_Options.md) records possible future changes to the editor host, canonical storage and public JSON destination.

```text
Save              canonical source + required shared local media + current editor records
Refresh Catalogue Working Catalogue JSON + private Docs metadata + local freshness receipt
Docs Publish      Preview and configured public destinations
```

## Save Boundary

The Work editor sends exact record IDs, server-issued revisions and, when applicable, expected Gallery memberships. Catalogue services validate the combined canonical state and persist the accepted mutation through the source transaction owner. This boundary covers single and New Work saves, bulk Gallery edits, Series and Gallery definitions, and supported deletes. A successful canonical transaction remains saved if later local completion fails.

Save prepares an image only for a new Work or a changed media source, and checks referenced local downloads and staged replacements. It writes complete local primary and thumbnail renditions to the shared Docs assets, measures dimensions and advances `media_version` when image bytes change. A metadata-only or membership-only edit does not regenerate the image. Missing source or download files and media-generation failures are reported as incomplete local Save completion; investigate the actual editor selection and source state before treating them as an expected retry case. Removed references do not automatically delete shared or remote media.

The response returns current canonical records, revisions and memberships for the editor's search, list, labels and reopened Work. Live Studio service reads remain authoritative for Work and Series search, focused records and Gallery definitions. Save does not generate consumer Catalogue JSON or private Docs report metadata. It makes no R2 request and does not run Docs Build, Search, Publish or deployment.

## Refresh Boundary

The **Refresh Catalogue** icon is in the **Catalogue Work Editor** header row, aligned with the Work search. Its result message appears to the right; successful timestamps display in Europe/London time as `YYYY-MM-DD HH:mm`. Refresh is disabled while the editor has unsaved changes or another operation is busy. An unavailable Refresh-status read reports its own error without blocking canonical editor loading.

The awaited server operation first requires a valid private `$DOTLINEFORM_DOCS_BASE_DIR/working/source/collections/catalogue/updates-pending.json`, then invalidates its prior receipt. It performs complete Work/Series/Gallery JSON generation under `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`, reconciles obsolete by-ID records, accumulates the generated Work by-ID `written` and `deleted` IDs in the pending list, and regenerates private `reports/catalogue-works/metadata.json`. A completed operation writes `var/studio/catalogue/refresh-receipt.json`; it does not run duplicate generator dry runs or complete generated-output read-backs. The pending list, private report metadata and receipt are not public Catalogue artifacts. Refresh does not write the retired persisted Studio lookup files.

Context's Subject column and heading sorts were removed on 2026-10-03. Their private Work/Series title file `reports/works/manifest.json`, reader, generator and report-serving allowance were retired with the last consumer. Refresh no longer generates or returns `works_collection_metadata`; Subject assignment uses its separate generated Catalogue provider.

The receipt binds exact canonical Works, Series, Galleries and Gallery memberships plus the media-policy configuration. Save invalidates it when source or local media completion changes or fails. A missing or mismatched receipt shows **Refresh needed** after reopening the editor. A missing or malformed pending list stops Refresh before generated writes; it must never be recreated as empty. A failed Refresh can leave partial generated output and pending entries as written, but it leaves no current receipt and reports the incomplete operation. Fix the cause and run Refresh again. Because an output written before failure may no longer appear in the retry's `written` or `deleted` result, inspect the pending list and Work/document inventory, then choose Full reconciliation manually if needed.

## Regenerate Timing

After a completed Refresh, **Regenerate Catalogue** in the Working Catalogue collection runs Pending updates by default. It uses the accumulated exact Work IDs to create missing documents, retitle an existing document when its Work title changed, build existing documents for other changes, and delete documents for removed Works. It removes pending entries only after the required source/delete and Build operation succeeds. A valid empty list remains for later Refreshes. Full reconciliation inventories current Works and Catalogue sources, repairs missing, changed and orphaned documents, and runs a complete Catalogue collection Build. Neither mode runs Refresh, Search, Publish or deployment. A partial Regenerate failure leaves completed writes for manual diagnosis and the next user-selected action.

## Reader And Publication Timing

The Works editor shows confirmed Save values immediately and on reopen. Docs Viewer Catalogue, subject and media-target readers use generated Working data and may show the prior Refresh until Refresh succeeds. A changed primary image can already exist in shared assets under the same filename while generated JSON still carries the old `media_version`; a browser with the old versioned URL may show cached pixels. Refresh updates the generated version so a normal reader reload requests the new URL. Clearing browser history is not part of this workflow.

Refresh is local generation only. Docs Publish does not run Refresh, Regenerate or enforce the Refresh receipt. Publishing while Refresh is needed can capture older Catalogue JSON alongside newer current media; review the Refresh status and Catalogue pending list before Publish. Publish, Git commit/push and public deployment remain separate explicit actions.

## Delivery Evidence And Remaining Limits

The user accepted the Save/Refresh interaction and header placement. In a manual Work `00008` image change, Save advanced the canonical image version from 5 to 6, and Refresh then exposed version 6 in the Working generated record. The user reported that tests completed okay, but the exact selection and scenarios were not supplied. Codex's focused lint, syntax, JSON and whitespace diagnostics passed; no test or fixture was changed for this delivery. Browser automation, Docs Publish, public deployment and exhaustive failure-path checks were not performed as part of it.

Read-only complete-generation planning considered 4,616 Works, 139 Series and 302 Galleries; four generated files would change and none would be deleted in that snapshot, and both private metadata aggregates would change. Save and Refresh latency has not been measured, so no performance magnitude is claimed. The unused persisted Studio lookup exporter, lookup refresh writer and completed one-time Gallery converter were removed after confirming that the active Studio API uses only live lookup payload builders. Historical lookup files remain tracked and have no active producer. Historical tests and check profiles were not changed in this code cleanup. A Publish freshness gate, shared-media cleanup and future hosting/storage changes are separate decisions.
