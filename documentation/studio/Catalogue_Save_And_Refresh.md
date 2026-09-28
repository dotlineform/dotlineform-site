---
draft: false
doc_id: d-20260927-223812-8042fc
title: Catalogue Save And Refresh
added_date: "2026-09-27 22:38:12"
last_updated: "2026-09-28 13:01:30"
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

The response returns current canonical records, revisions and memberships for the editor's search, list, labels and reopened Work. Live Studio service reads remain authoritative for Work and Series search, focused records and Gallery definitions. Save does not generate consumer Catalogue JSON, private Docs report metadata or the old persisted Studio lookup export. It makes no R2 request and does not run Docs Build, Search, Publish or deployment.

## Refresh Boundary

The **Refresh Catalogue** icon is in the **Catalogue Work Editor** header row, aligned with the Work search. Its result message appears to the right; successful timestamps display in Europe/London time as `YYYY-MM-DD HH:mm`. Refresh is disabled while the editor has unsaved changes or another operation is busy. An unavailable Refresh-status read reports its own error without blocking canonical editor loading.

The awaited server operation invalidates its prior receipt, performs complete Work/Series/Gallery JSON generation under `$DOTLINEFORM_DOCS_BASE_DIR/working/generated/catalogue/`, reconciles obsolete by-ID records, and regenerates private `reports/catalogue-works/metadata.json` and `reports/works/manifest.json`. It verifies the generated JSON and both private metadata aggregates before writing `var/studio/catalogue/refresh-receipt.json`. The private aggregates and receipt are not public Catalogue artifacts. The old persisted Studio lookup export has no active editor or Docs reader and is outside Refresh.

The receipt binds exact canonical Works, Series, Galleries and Gallery memberships plus the media-policy configuration. Save invalidates it when source or local media completion changes or fails. A missing or mismatched receipt shows **Refresh needed** after reopening the editor. A failed Refresh can leave partial generated output, but it leaves no current receipt and reports the incomplete operation. Fix the cause and run Refresh again; it reconciles from canonical source rather than relying on the previous generated state.

## Reader And Publication Timing

The Works editor shows confirmed Save values immediately and on reopen. Docs Viewer Catalogue, subject and media-target readers use generated Working data and may show the prior Refresh until Refresh succeeds. A changed primary image can already exist in shared assets under the same filename while generated JSON still carries the old `media_version`; a browser with the old versioned URL may show cached pixels. Refresh updates the generated version so a normal reader reload requests the new URL. Clearing browser history is not part of this workflow.

Refresh is local generation only. Docs Publish does not run Refresh or enforce its receipt. Publishing while Refresh is needed can capture older Catalogue JSON alongside newer current media; review the Refresh status before Publish. Publish, Git commit/push and public deployment remain separate explicit actions.

## Delivery Evidence And Remaining Limits

The user accepted the Save/Refresh interaction and header placement. In a manual Work `00008` image change, Save advanced the canonical image version from 5 to 6, and Refresh then exposed version 6 in the Working generated record. The user reported that tests completed okay, but the exact selection and scenarios were not supplied. Codex's focused lint, syntax, JSON and whitespace diagnostics passed; no test or fixture was changed for this delivery. Browser automation, Docs Publish, public deployment and exhaustive failure-path checks were not performed as part of it.

Read-only complete-generation planning considered 4,616 Works, 139 Series and 302 Galleries; four generated files would change and none would be deleted in that snapshot, and both private metadata aggregates would change. Save and Refresh latency has not been measured, so no performance magnitude is claimed. The inactive manual persisted Studio lookup exporter and one-time Gallery converter still refer to the old lookup files; their retirement needs its own consumer and test/profile review. A Publish freshness gate, shared-media cleanup and future hosting/storage changes are separate decisions.
